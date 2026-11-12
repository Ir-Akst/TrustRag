"""Six core signals (F1..F6) plus optional FilterRAG Freq-Density heuristic for G2 MSD.

Core TrustRAG Signals:
- F1: Perplexity Anomaly (`perplexity`) — optional model-based measurement, z-score normalized.
- F2: Embedding-Norm Anomaly (`embedding_norm`) — actual embedding L2 norm z-score normalized.
- F3: Query Match (`query_match`) — cosine relevance normalized while preserving raw similarity.
- F4: Suspicious Instruction Content (`instruction_content`) — adversarial/injection instruction detector.
- F5: Consensus Deviation (`consensus_deviation`) — semantic & factual peer comparison across pool.
- F6: Provenance Prior (`provenance`) — configurable source priors & metadata traceability; UNKNOWN when absent.

Optional Supplementary Heuristic (strictly separate from core signals & w · f(d) + b):
- FilterRAG Freq-Density (`freq_density`)

CRITICAL INTEGRITY INVARIANT:
Signals never invent perplexity, embedding norms, or provenance priors, and never read
ground-truth benchmark labels (`clean_poison_label`, `attack_family`, `expected_security_outcome`).
"""

from __future__ import annotations

import math
import re
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from trustrag.config.engine_config import MSDConfig
from trustrag.data.preprocessing.cleaning import is_empty_text
from trustrag.engine.schemas import EvidenceDocument, SignalDetail
from trustrag.engine.text_utils import (
    check_repetitive_flood,
    compute_lexical_overlap,
    count_fullwidth_ascii_confusables,
    detect_obfuscation,
    extract_numbers_and_units,
    fold_mixed_script_confusables,
    has_strict_negation,
    match_threat_patterns,
    tokenize_content_words,
)

# Subtle markdown/HTML comment injection directives in retrieved passages
_HTML_DIRECTIVE_RE = re.compile(
    r"<!--\s*(?:SYSTEM|INSTRUCTION|IGNORE|OVERRIDE|INJECT)[^>]*-->",
    re.IGNORECASE,
)

# Explicit antonym conflict groups representing factual contradictions on shared topics
_ANTONYM_CONFLICT_PAIRS: Tuple[Tuple[Set[str], Set[str]], ...] = (
    (
        {"confirmed", "verified", "detected", "present", "raised", "increased", "safe", "infeasible"},
        {"refuted", "disproved", "dissolved", "zero", "broken", "vulnerable", "backdoor", "false", "denied"},
    ),
)


# ---------------------------------------------------------------------------
# F1 — Perplexity Anomaly
# ---------------------------------------------------------------------------

def evaluate_perplexity_signal(
    doc: EvidenceDocument,
    config: MSDConfig,
    *,
    perplexity_callable: Optional[Callable[[str], float]] = None,
    raw_perplexity: Optional[float] = None,
) -> SignalDetail:
    """Evaluate F1: Perplexity Anomaly using a configured backend without fabricating values."""
    w = config.weight_perplexity
    basis = "Model-based document perplexity z-score against configured reference distribution."

    if is_empty_text(doc.text):
        return SignalDetail(
            signal_id="F1",
            signal_name="perplexity",
            available=False,
            value=None,
            raw_value=None,
            configured_weight=w,
            effective_weight=0.0,
            is_heuristic=False,
            status="UNAVAILABLE",
            basis=basis,
            explanation="Document is empty; perplexity unavailable.",
        )

    if config.perplexity_backend == "disabled" and perplexity_callable is None and raw_perplexity is None:
        return SignalDetail(
            signal_id="F1",
            signal_name="perplexity",
            available=False,
            value=None,
            raw_value=None,
            configured_weight=w,
            effective_weight=0.0,
            is_heuristic=False,
            status="UNAVAILABLE",
            basis=basis,
            explanation="Perplexity model unavailable (perplexity_backend='disabled').",
        )

    ppl_val: Optional[float] = raw_perplexity
    if ppl_val is None and perplexity_callable is not None:
        try:
            ppl_val = float(perplexity_callable(doc.text))
        except Exception as exc:
            return SignalDetail(
                signal_id="F1",
                signal_name="perplexity",
                available=False,
                value=None,
                raw_value=None,
                configured_weight=w,
                effective_weight=0.0,
                is_heuristic=False,
                status="UNAVAILABLE",
                basis=basis,
                explanation=f"Perplexity backend failed: {exc}",
            )

    if ppl_val is None or not math.isfinite(ppl_val) or ppl_val <= 0.0:
        return SignalDetail(
            signal_id="F1",
            signal_name="perplexity",
            available=False,
            value=None,
            raw_value=None,
            configured_weight=w,
            effective_weight=0.0,
            is_heuristic=False,
            status="UNAVAILABLE",
            basis=basis,
            explanation="No valid perplexity measurement produced.",
        )

    z = (ppl_val - config.perplexity_reference_mean) / config.perplexity_reference_std
    # Higher value = closer to expected linguistic naturalness (monotonically penalizes anomaly magnitude)
    score = math.exp(-0.5 * (abs(z) / config.perplexity_z_threshold) ** 2)
    score = min(1.0, max(0.0, round(score, 4)))
    flags = ["PERPLEXITY_ANOMALY"] if abs(z) >= config.perplexity_z_threshold else []

    return SignalDetail(
        signal_id="F1",
        signal_name="perplexity",
        available=True,
        value=score,
        raw_value=round(float(ppl_val), 4),
        z_score=round(float(z), 4),
        configured_weight=w,
        effective_weight=w,
        is_heuristic=False,
        status="AVAILABLE",
        basis=basis,
        explanation=f"perplexity={ppl_val:.2f}, z_score={z:.2f} (ref_mean={config.perplexity_reference_mean}, ref_std={config.perplexity_reference_std}).",
        flags=flags,
    )


# ---------------------------------------------------------------------------
# F2 — Embedding-Norm Anomaly
# ---------------------------------------------------------------------------

def evaluate_embedding_norm_signal(
    embedding_vector: Optional[np.ndarray],
    peer_norms: Optional[Sequence[float]],
    config: MSDConfig,
) -> SignalDetail:
    """Evaluate F2: Embedding-Norm Anomaly strictly from real embedding vectors."""
    w = config.weight_embedding_norm
    basis = "L2 norm of actual retrieval/embedding vector z-scored against reference distribution."

    if config.embedding_backend == "disabled" or embedding_vector is None:
        return SignalDetail(
            signal_id="F2",
            signal_name="embedding_norm",
            available=False,
            value=None,
            raw_value=None,
            configured_weight=w,
            effective_weight=0.0,
            is_heuristic=False,
            status="UNAVAILABLE",
            basis=basis,
            explanation="Embeddings unavailable or embedding_backend='disabled'.",
        )

    vec = np.asarray(embedding_vector, dtype=float).ravel()
    if vec.size == 0:
        return SignalDetail(
            signal_id="F2",
            signal_name="embedding_norm",
            available=False,
            value=None,
            raw_value=None,
            configured_weight=w,
            effective_weight=0.0,
            is_heuristic=False,
            status="UNAVAILABLE",
            basis=basis,
            explanation="Empty embedding vector.",
        )

    norm = float(np.linalg.norm(vec))
    if not math.isfinite(norm) or norm <= 0.0:
        return SignalDetail(
            signal_id="F2",
            signal_name="embedding_norm",
            available=False,
            value=None,
            raw_value=None,
            configured_weight=w,
            effective_weight=0.0,
            is_heuristic=False,
            status="UNAVAILABLE",
            basis=basis,
            explanation="Zero or non-finite embedding norm.",
        )

    if config.embedding_norm_reference_mean is not None and config.embedding_norm_reference_std is not None:
        ref_mean = config.embedding_norm_reference_mean
        ref_std = config.embedding_norm_reference_std
        ref_source = "configured clean reference distribution"
        extra_flags: List[str] = []
    elif config.embedding_norm_reference_policy != "allow_empirical_fallback":
        return SignalDetail(
            signal_id="F2",
            signal_name="embedding_norm",
            available=False,
            value=None,
            raw_value=round(norm, 4),
            configured_weight=w,
            effective_weight=0.0,
            is_heuristic=False,
            status="UNAVAILABLE",
            basis=basis,
            explanation=(
                f"Measured L2 norm={norm:.4f}, but configured clean-reference statistics are absent "
                "(embedding_norm_reference_policy='require_configured'); batch-local statistics are never treated "
                "as a clean reference by default."
            ),
        )
    else:
        valid_peers = [float(n) for n in (peer_norms or []) if math.isfinite(n) and n > 0.0]
        if len(valid_peers) < 3:
            return SignalDetail(
                signal_id="F2",
                signal_name="embedding_norm",
                available=False,
                value=None,
                raw_value=round(norm, 4),
                configured_weight=w,
                effective_weight=0.0,
                is_heuristic=False,
                status="UNAVAILABLE",
                basis=basis,
                explanation=(
                    f"Measured L2 norm={norm:.4f}, but opt-in empirical batch fallback requires at least 3 peer vectors."
                ),
            )
        from collections import Counter

        arr = np.asarray(valid_peers, dtype=float)
        ref_mean = float(np.mean(arr))
        ref_std = float(np.std(arr))
        rounded_counts = Counter(round(x, 4) for x in valid_peers)
        sorted_freqs = rounded_counts.most_common()
        is_bimodal_tie = len(sorted_freqs) == 2 and sorted_freqs[0][1] == sorted_freqs[1][1]
        is_symmetric_split = False
        if ref_std > 1e-6:
            z_abs = np.abs((arr - ref_mean) / ref_std)
            if float(np.min(z_abs)) > 0.70 and float(np.max(z_abs) - np.min(z_abs)) < 0.25:
                is_symmetric_split = True

        if ref_std <= 1e-6 or is_bimodal_tie or is_symmetric_split:
            return SignalDetail(
                signal_id="F2",
                signal_name="embedding_norm",
                available=False,
                value=None,
                raw_value=round(norm, 4),
                configured_weight=w,
                effective_weight=0.0,
                is_heuristic=False,
                status="UNAVAILABLE",
                basis=basis,
                explanation=(
                    f"Measured L2 norm={norm:.4f}, but opt-in empirical batch statistics are "
                    f"{'symmetric/bimodal across duplicated or evenly split clusters' if (is_bimodal_tie or is_symmetric_split) else 'zero-variance'} "
                    "and cannot serve as a clean reference baseline."
                ),
            )
        ref_source = (
            f"opt-in empirical batch baseline (n={len(valid_peers)}; caveat: batch-local, not an independent clean corpus reference)"
        )
        extra_flags = ["EMPIRICAL_BATCH_BASELINE"]

    if ref_std <= 1e-6:
        z = 0.0
        score = 1.0
    else:
        z = (norm - ref_mean) / ref_std
        score = math.exp(-0.5 * (abs(z) / config.embedding_norm_z_threshold) ** 2)
        score = min(1.0, max(0.0, round(score, 4)))

    flags = list(extra_flags)
    if abs(z) >= config.embedding_norm_z_threshold:
        flags.append("EMBEDDING_NORM_ANOMALY")
    return SignalDetail(
        signal_id="F2",
        signal_name="embedding_norm",
        available=True,
        value=score,
        raw_value=round(norm, 4),
        z_score=round(float(z), 4),
        configured_weight=w,
        effective_weight=w,
        is_heuristic=False,
        status="AVAILABLE",
        basis=basis,
        explanation=f"l2_norm={norm:.4f}, z_score={z:.2f} via {ref_source} (mean={ref_mean:.4f}, std={ref_std:.4f}).",
        flags=flags,
    )


# ---------------------------------------------------------------------------
# F3 — Query Match
# ---------------------------------------------------------------------------

def evaluate_query_match_signal(
    query: str,
    doc: EvidenceDocument,
    raw_similarity: Optional[float],
    config: MSDConfig,
) -> SignalDetail:
    """Evaluate F3: Query Match preserving raw cosine similarity and normalized score."""
    w = config.weight_query_match
    basis = "Cosine similarity from retrieval/embedding vectors combined with query token coverage."

    if is_empty_text(query) or is_empty_text(doc.text) or raw_similarity is None or not math.isfinite(raw_similarity):
        return SignalDetail(
            signal_id="F3",
            signal_name="query_match",
            available=False,
            value=None,
            raw_value=None,
            configured_weight=w,
            effective_weight=0.0,
            is_heuristic=False,
            status="UNAVAILABLE",
            basis=basis,
            explanation="Query, document text, or similarity score unavailable.",
        )

    raw_clamped = min(1.0, max(0.0, float(raw_similarity)))
    q_tokens = set(tokenize_content_words(query, include_negations=False))
    d_tokens = set(tokenize_content_words(doc.text, include_negations=False))
    q_cov = len(q_tokens & d_tokens) / len(q_tokens) if q_tokens else 0.0

    # Monotonic normalization in [0, 1] while keeping raw cosine preserved in raw_value
    norm_val = min(1.0, max(0.0, 0.75 * min(1.0, raw_clamped * 1.4) + 0.25 * q_cov))
    flags = ["LOW_QUERY_MATCH"] if norm_val < 0.25 else []

    return SignalDetail(
        signal_id="F3",
        signal_name="query_match",
        available=True,
        value=round(norm_val, 4),
        raw_value=round(float(raw_similarity), 4),
        configured_weight=w,
        effective_weight=w,
        is_heuristic=False,
        status="AVAILABLE",
        basis=basis,
        explanation=f"raw_similarity={raw_similarity:.4f}, query_token_coverage={q_cov:.3f}, normalized={norm_val:.4f}.",
        flags=flags,
    )


# ---------------------------------------------------------------------------
# F4 — Suspicious Instruction Content
# ---------------------------------------------------------------------------

def evaluate_instruction_content_signal(
    doc: EvidenceDocument,
    config: MSDConfig,
) -> Tuple[SignalDetail, float]:
    """Evaluate F4: Detect RAG-targeting prompt injections while sparing benign procedural text.

    Returns (SignalDetail, instruction_risk_score).
    """
    w = config.weight_instruction_content
    basis = "Heuristic pattern analysis for prompt overrides, safety disabling, AI-targeting directives, and command exfiltration."

    if is_empty_text(doc.text):
        return (
            SignalDetail(
                signal_id="F4",
                signal_name="instruction_content",
                available=False,
                value=None,
                raw_value=None,
                configured_weight=w,
                effective_weight=0.0,
                is_heuristic=True,
                status="UNAVAILABLE",
                basis=basis,
                explanation="Document is empty; instruction analysis unavailable.",
            ),
            0.0,
        )

    risks: List[float] = []
    flags: List[str] = []
    indicators: List[str] = []

    has_obf, cleaned_obf_text, obf_count = detect_obfuscation(doc.text)
    folded_text, mixed_conf_count = fold_mixed_script_confusables(cleaned_obf_text or doc.text)
    fullwidth_conf_count = count_fullwidth_ascii_confusables(doc.text)

    texts_to_scan: List[str] = [doc.text]
    if cleaned_obf_text and cleaned_obf_text != doc.text:
        texts_to_scan.append(cleaned_obf_text)
    if folded_text and folded_text not in texts_to_scan:
        texts_to_scan.append(folded_text)

    seen_rules: Set[Tuple[str, str]] = set()
    evasive_norm_hit = False
    for scan_idx, scan_txt in enumerate(texts_to_scan):
        for spec, _ in match_threat_patterns(scan_txt, target="document"):
            key = (spec.rule_name, spec.category)
            if key in seen_rules:
                continue
            seen_rules.add(key)
            if scan_idx > 0:
                evasive_norm_hit = True
            risks.append(spec.severity)
            flags.append(f"DOC_{spec.category}")
            indicators.append(f"rule={spec.rule_name}(category={spec.category})")

    raw_html_hit = bool(_HTML_DIRECTIVE_RE.search(doc.text))
    if raw_html_hit or any(_HTML_DIRECTIVE_RE.search(scan_txt) for scan_txt in texts_to_scan[1:]):
        if not raw_html_hit:
            evasive_norm_hit = True
        risks.append(0.80)
        flags.append("DOC_HIDDEN_DIRECTIVE")
        indicators.append("rule=html_directive(category=HIDDEN_DIRECTIVE)")

    total_obf_count = obf_count + mixed_conf_count + fullwidth_conf_count
    if has_obf or mixed_conf_count > 0 or fullwidth_conf_count > 0 or evasive_norm_hit:
        eff_count = max(total_obf_count, 1)
        risks.append(0.75 if eff_count >= 5 else 0.40)
        flags.append("DOC_OBFUSCATION")
        indicators.append(f"zero_width_or_format_or_confusable_chars={eff_count}")

    is_flood, _ = check_repetitive_flood(doc.text)
    if is_flood:
        risks.append(0.70)
        flags.append("DOC_DOS_FLOOD")
        indicators.append("rule=repetitive_token_flood(category=DOS_FLOOD)")

    if not risks:
        risk_score = 0.0
        safety_val = 1.0
        explanation = "No adversarial instructions, prompt overrides, or answer-manipulation directives detected."
    else:
        max_r = max(risks)
        risk_score = min(1.0, round(max_r + 0.08 * max(0, len(risks) - 1), 4))
        safety_val = max(0.0, round(1.0 - risk_score, 4))
        explanation = f"Adversarial/manipulation instruction indicators detected: {', '.join(indicators[:4])}."

    return (
        SignalDetail(
            signal_id="F4",
            signal_name="instruction_content",
            available=True,
            value=safety_val,
            raw_value=round(risk_score, 4),
            configured_weight=w,
            effective_weight=w,
            is_heuristic=True,
            status="AVAILABLE",
            basis=basis,
            explanation=explanation,
            flags=list(dict.fromkeys(flags)),
        ),
        risk_score,
    )


# ---------------------------------------------------------------------------
# F5 — Consensus Deviation
# ---------------------------------------------------------------------------

def _pair_has_numeric_conflict(nums_a: List[Tuple[str, str]], nums_b: List[Tuple[str, str]]) -> bool:
    if not nums_a or not nums_b:
        return False
    units_a: Dict[str, List[float]] = {}
    units_b: Dict[str, List[float]] = {}
    for val_str, unit in nums_a:
        try:
            units_a.setdefault(unit, []).append(float(val_str))
        except ValueError:
            continue
    for val_str, unit in nums_b:
        try:
            units_b.setdefault(unit, []).append(float(val_str))
        except ValueError:
            continue
    for unit, vals_a in units_a.items():
        if unit and unit in units_b:
            vals_b = units_b[unit]
            if max(vals_a) < min(vals_b) or max(vals_b) < min(vals_a):
                return True
    return False


def _pair_has_polarity_conflict(text_a: str, text_b: str) -> bool:
    if has_strict_negation(text_a) != has_strict_negation(text_b):
        return True
    toks_a = set(tokenize_content_words(text_a))
    toks_b = set(tokenize_content_words(text_b))
    for pos_set, neg_set in _ANTONYM_CONFLICT_PAIRS:
        a_pos, a_neg = bool(toks_a & pos_set), bool(toks_a & neg_set)
        b_pos, b_neg = bool(toks_b & pos_set), bool(toks_b & neg_set)
        if (a_pos and b_neg and not a_neg) or (b_pos and a_neg and not b_neg):
            return True
    return False


def _are_topical_peers(text_a: str, text_b: str, lex_overlap: float, sem_cos: float) -> bool:
    if sem_cos >= 0.20 or lex_overlap >= 0.22:
        return True
    toks_a = set(tokenize_content_words(text_a, include_negations=False))
    toks_b = set(tokenize_content_words(text_b, include_negations=False))
    shared = toks_a & toks_b
    if len(shared) >= 3:
        return True
    if len(shared) >= 2 and any("-" in tok or any(ch.isdigit() for ch in tok) for tok in shared):
        return True
    return False


def evaluate_consensus_deviation_signals(
    docs: Sequence[EvidenceDocument],
    doc_embeddings: Optional[Sequence[Optional[np.ndarray]]],
    config: MSDConfig,
) -> Dict[str, Tuple[SignalDetail, List[str]]]:
    """Evaluate F5: Cross-document consensus deviation across retrieved candidates.

    Uses both semantic cosine matrix (when vectors exist) and lexical/numeric/polarity peer conflict detection.
    """
    w = config.weight_consensus_deviation
    basis = "Heuristic semantic and factual peer comparison across candidate pool (outlier/conflict detection)."

    non_empty_indices = [i for i, d in enumerate(docs) if not is_empty_text(d.text)]
    if len(non_empty_indices) < 2:
        out: Dict[str, Tuple[SignalDetail, List[str]]] = {}
        for d in docs:
            out[d.doc_id] = (
                SignalDetail(
                    signal_id="F5",
                    signal_name="consensus_deviation",
                    available=False,
                    value=None,
                    raw_value=None,
                    configured_weight=w,
                    effective_weight=0.0,
                    is_heuristic=True,
                    status="UNAVAILABLE",
                    basis=basis,
                    explanation="Consensus deviation unavailable: requires at least 2 non-empty documents in candidate pool.",
                ),
                [],
            )
        return out

    n = len(docs)
    # Build pairwise semantic cosine matrix if real vectors are supplied for non-empty docs
    sem_matrix = np.zeros((n, n), dtype=float)
    has_sem_matrix = False
    if doc_embeddings is not None and len(doc_embeddings) == n:
        valid_vecs: List[Tuple[int, np.ndarray]] = []
        for i in non_empty_indices:
            vec = doc_embeddings[i]
            if vec is not None:
                valid_vecs.append((i, vec))
        if len(valid_vecs) >= 2:
            # Ensure matching dimensions before cosine computation
            dim = len(valid_vecs[0][1])
            if dim > 0 and all(len(v) == dim for _, v in valid_vecs):
                mat = np.vstack([np.asarray(v, dtype=float).ravel() for _, v in valid_vecs])
                cos_mat = cosine_similarity(mat)
                for row_idx, (orig_i, _) in enumerate(valid_vecs):
                    for col_idx, (orig_j, _) in enumerate(valid_vecs):
                        sem_matrix[orig_i, orig_j] = float(np.clip(cos_mat[row_idx, col_idx], 0.0, 1.0))
                has_sem_matrix = True

    conflicts_by_doc: Dict[str, List[str]] = {d.doc_id: [] for d in docs}
    peers_by_doc: Dict[str, List[str]] = {d.doc_id: [] for d in docs}
    nums_cache = {d.doc_id: extract_numbers_and_units(d.text) for d in docs}

    for i_idx in range(len(non_empty_indices)):
        i = non_empty_indices[i_idx]
        for j_idx in range(i_idx + 1, len(non_empty_indices)):
            j = non_empty_indices[j_idx]
            di, dj = docs[i], docs[j]
            if (di.content_hash and di.content_hash == dj.content_hash) or di.text.strip() == dj.text.strip():
                peers_by_doc[di.doc_id].append(dj.doc_id)
                peers_by_doc[dj.doc_id].append(di.doc_id)
                continue

            lex_ov = compute_lexical_overlap(di.text, dj.text)
            sem_cos = float(sem_matrix[i, j]) if has_sem_matrix else lex_ov
            if not _are_topical_peers(di.text, dj.text, lex_ov, sem_cos):
                continue

            peers_by_doc[di.doc_id].append(dj.doc_id)
            peers_by_doc[dj.doc_id].append(di.doc_id)

            polarity_flip = _pair_has_polarity_conflict(di.text, dj.text)
            num_conflict = _pair_has_numeric_conflict(nums_cache[di.doc_id], nums_cache[dj.doc_id])
            if polarity_flip or num_conflict:
                conflicts_by_doc[di.doc_id].append(dj.doc_id)
                conflicts_by_doc[dj.doc_id].append(di.doc_id)

    results: Dict[str, Tuple[SignalDetail, List[str]]] = {}
    for idx, d in enumerate(docs):
        if is_empty_text(d.text):
            results[d.doc_id] = (
                SignalDetail(
                    signal_id="F5",
                    signal_name="consensus_deviation",
                    available=False,
                    value=None,
                    raw_value=None,
                    configured_weight=w,
                    effective_weight=0.0,
                    is_heuristic=True,
                    status="UNAVAILABLE",
                    basis=basis,
                    explanation="Document is empty; consensus deviation unavailable.",
                ),
                [],
            )
            continue

        c_ids = conflicts_by_doc[d.doc_id]
        p_ids = peers_by_doc[d.doc_id]
        reported_conflicts: List[str] = list(c_ids)
        peer_sims = [
            float(sem_matrix[idx, k]) if has_sem_matrix else compute_lexical_overlap(d.text, docs[k].text)
            for k in non_empty_indices
            if k != idx
        ]
        mean_peer_sim = float(np.mean(peer_sims)) if peer_sims else 0.0

        if not c_ids:
            if p_ids:
                score = 0.95
                explanation = f"Consistent with {len(p_ids)} topical peer document(s) (mean_peer_sim={mean_peer_sim:.3f})."
            elif mean_peer_sim < 0.06 and len(non_empty_indices) >= 3:
                score = 0.65
                explanation = f"No direct contradictions, though semantically isolated from peers (mean_peer_sim={mean_peer_sim:.3f})."
            else:
                score = 0.85
                explanation = f"No conflicting assertions detected across candidate pool (mean_peer_sim={mean_peer_sim:.3f})."
            flags: List[str] = []
        else:
            non_conflicting = len(p_ids) - len(c_ids)
            if non_conflicting >= 1 and non_conflicting >= len(c_ids):
                score = 0.85
                reported_conflicts = []
                explanation = f"Supported by agreeing peer cluster; isolated minority contradiction(s): {c_ids}."
                flags = []
            elif len(c_ids) > non_conflicting and len(c_ids) >= 2:
                score = 0.15
                explanation = f"Minority outlier contradicting {len(c_ids)} peer document(s): {c_ids}."
                flags = ["CONSENSUS_DEVIATION_CONFLICT", "MINORITY_OUTLIER"]
            else:
                score = 0.35
                explanation = f"Direct factual/numeric conflict detected with peer document(s): {c_ids}."
                flags = ["CONSENSUS_DEVIATION_CONFLICT"]

        results[d.doc_id] = (
            SignalDetail(
                signal_id="F5",
                signal_name="consensus_deviation",
                available=True,
                value=round(score, 4),
                raw_value=round(mean_peer_sim, 4),
                configured_weight=w,
                effective_weight=w,
                is_heuristic=True,
                status="AVAILABLE",
                basis=basis,
                explanation=explanation,
                flags=flags,
            ),
            reported_conflicts,
        )

    return results


# ---------------------------------------------------------------------------
# F6 — Provenance Prior
# ---------------------------------------------------------------------------

def evaluate_provenance_signal(
    doc: EvidenceDocument,
    config: MSDConfig,
) -> SignalDetail:
    """Evaluate F6: Provenance Prior from actual metadata & explicit configured priors.

    Marks missing/unknown provenance honestly as status='UNKNOWN', available=False, value=None
    rather than inventing domain trust values or equating missing provenance with poisoning.
    """
    w = config.weight_provenance
    basis = "Configured provenance priors and explicit metadata verification/traceability fields (never fabricated)."

    if is_empty_text(doc.text):
        return SignalDetail(
            signal_id="F6",
            signal_name="provenance",
            available=False,
            value=None,
            raw_value=None,
            configured_weight=w,
            effective_weight=0.0,
            is_heuristic=False,
            status="UNAVAILABLE",
            basis=basis,
            explanation="Document is empty; provenance evaluation skipped.",
        )

    prov = (doc.provenance or "").strip()
    src_ds = (doc.source_dataset or "").strip()
    src_id = (doc.source_id or "").strip()
    src_type = str(doc.metadata.get("source_type") or "").strip().lower()
    explicit_trust = str(doc.metadata.get("source_trust") or "").strip().lower()
    trust_tier = str(doc.metadata.get("trust_tier") or doc.metadata.get("provenance_tier") or "").strip().lower()
    domain = str(doc.metadata.get("source_domain") or doc.metadata.get("domain") or "").strip().lower()
    verified_flag = doc.metadata.get("verified")

    # 1. Explicit configured priors lookup (exact match or domain suffix)
    for key in (src_ds, prov, src_type, domain):
        if key and key in config.provenance_priors:
            prior = float(config.provenance_priors[key])
            return SignalDetail(
                signal_id="F6",
                signal_name="provenance",
                available=True,
                value=round(prior, 4),
                raw_value=round(prior, 4),
                configured_weight=w,
                effective_weight=w,
                is_heuristic=False,
                status="AVAILABLE",
                basis=basis,
                explanation=f"Matched configured provenance prior for '{key}' (prior={prior:.2f}).",
                flags=["LOW_CONFIGURED_PRIOR"] if prior < 0.40 else [],
            )
    if domain:
        for prior_key, prior_val in config.provenance_priors.items():
            norm_pk = prior_key.strip().lower()
            if norm_pk and (domain == norm_pk or domain.endswith(f".{norm_pk}")):
                prior = float(prior_val)
                return SignalDetail(
                    signal_id="F6",
                    signal_name="provenance",
                    available=True,
                    value=round(prior, 4),
                    raw_value=round(prior, 4),
                    configured_weight=w,
                    effective_weight=w,
                    is_heuristic=False,
                    status="AVAILABLE",
                    basis=basis,
                    explanation=f"Matched domain provenance prior '{prior_key}' for domain '{domain}' (prior={prior:.2f}).",
                    flags=["LOW_CONFIGURED_PRIOR"] if prior < 0.40 else [],
                )

    # 2. Explicit verification and trust-tier attributes in document metadata
    if (
        verified_flag is True
        or explicit_trust in {"trusted", "high", "verified", "official"}
        or trust_tier in {"high", "tier_1", "authoritative", "verified"}
    ):
        return SignalDetail(
            signal_id="F6",
            signal_name="provenance",
            available=True,
            value=0.90,
            raw_value=0.90,
            configured_weight=w,
            effective_weight=w,
            is_heuristic=False,
            status="AVAILABLE",
            basis=basis,
            explanation="Metadata contains explicit verified/high-trust tier indicator.",
        )
    if explicit_trust in {"medium", "moderate", "curated"} or trust_tier in {"medium", "tier_2", "curated"}:
        return SignalDetail(
            signal_id="F6",
            signal_name="provenance",
            available=True,
            value=0.65,
            raw_value=0.65,
            configured_weight=w,
            effective_weight=w,
            is_heuristic=False,
            status="AVAILABLE",
            basis=basis,
            explanation="Metadata contains medium/curated trust tier indicator.",
        )
    if (
        verified_flag is False
        or explicit_trust in {"untrusted", "low", "unverified"}
        or trust_tier in {"low", "tier_3", "untrusted"}
    ):
        return SignalDetail(
            signal_id="F6",
            signal_name="provenance",
            available=True,
            value=0.25,
            raw_value=0.25,
            configured_weight=w,
            effective_weight=w,
            is_heuristic=False,
            status="AVAILABLE",
            basis=basis,
            explanation="Metadata contains explicit unverified/untrusted indicator.",
            flags=["EXPLICIT_UNTRUSTED_METADATA"],
        )

    # 3. Source-type and authoritative domain differentiation (strictly when metadata exists)
    if src_type in {"official_docs", "peer_reviewed", "government", "academic", "encyclopedia", "verified_kb"} or (
        domain and (domain.endswith((".gov", ".edu")) or domain.startswith("docs.") or domain in {"arxiv.org", "nih.gov", "wikipedia.org"})
    ):
        return SignalDetail(
            signal_id="F6",
            signal_name="provenance",
            available=True,
            value=0.85,
            raw_value=0.85,
            configured_weight=w,
            effective_weight=w,
            is_heuristic=False,
            status="AVAILABLE",
            basis=basis,
            explanation="Explicit authoritative source_type/domain metadata present.",
        )
    if src_type in {"news", "editorial", "curated_kb"}:
        return SignalDetail(
            signal_id="F6",
            signal_name="provenance",
            available=True,
            value=0.70,
            raw_value=0.70,
            configured_weight=w,
            effective_weight=w,
            is_heuristic=False,
            status="AVAILABLE",
            basis=basis,
            explanation=f"Explicit curated source_type='{src_type}' present.",
        )
    if src_type in {"blog", "forum", "user_generated", "social", "anonymous", "unverified_upload", "community_post"}:
        return SignalDetail(
            signal_id="F6",
            signal_name="provenance",
            available=True,
            value=0.30,
            raw_value=0.30,
            configured_weight=w,
            effective_weight=w,
            is_heuristic=False,
            status="AVAILABLE",
            basis=basis,
            explanation=f"Explicit low-trust/unvetted source_type='{src_type}' present.",
            flags=["LOW_TRUST_SOURCE_TYPE"],
        )

    # 4. Concrete non-generic provenance traceability
    prov_lower = prov.lower()
    ds_lower = src_ds.lower()
    is_unknown_prov = (not prov) or prov_lower in {"unknown", "unavailable", "none", "anonymous"}
    is_generic_ds = (not src_ds) or ds_lower in {"local", "unknown", "unavailable", "none"}

    if not is_unknown_prov and src_id and not is_generic_ds:
        return SignalDetail(
            signal_id="F6",
            signal_name="provenance",
            available=True,
            value=0.75,
            raw_value=0.75,
            configured_weight=w,
            effective_weight=w,
            is_heuristic=False,
            status="AVAILABLE",
            basis=basis,
            explanation=f"Complete provenance traceability present (source_dataset='{src_ds}', source_id='{src_id}').",
        )

    # 5. Missing or unknown provenance -> honestly mark UNKNOWN / UNAVAILABLE (not malicious!)
    return SignalDetail(
        signal_id="F6",
        signal_name="provenance",
        available=False,
        value=None,
        raw_value=None,
        configured_weight=w,
        effective_weight=0.0,
        is_heuristic=False,
        status="UNKNOWN",
        basis=basis,
        explanation="Provenance metadata is UNKNOWN or UNAVAILABLE; omitted from trust logit rather than assuming poisoning.",
        flags=["PROVENANCE_UNKNOWN"],
    )


# ---------------------------------------------------------------------------
# Optional FilterRAG Supplementary Heuristic — Freq-Density (Separate from F1..F6)
# ---------------------------------------------------------------------------

def evaluate_freq_density_heuristic(
    query: str,
    doc: EvidenceDocument,
    config: MSDConfig,
    *,
    intermediate_answer: Optional[str] = None,
    answer_callable: Optional[Callable[[str, EvidenceDocument], str]] = None,
) -> SignalDetail:
    """Optional FilterRAG-inspired Freq-Density supplementary heuristic.

    Measures concentration of query-and-answer-related tokens inside a retrieved passage.
    Kept strictly separate from the 6 core signals and excluded from sigmoid(w · f(d) + b).
    Limitation: lexical concentration heuristic cannot detect subtle factual entity swaps and
    cannot serve as standalone proof of poisoning.
    """
    basis = (
        "FilterRAG-inspired Freq-Density heuristic (word concentration of query + intermediate answer tokens). "
        "Limitations: purely lexical overlap concentration; not standalone poisoning proof."
    )
    if not config.enable_freq_density:
        return SignalDetail(
            signal_id="SUPP_FREQ_DENSITY",
            signal_name="freq_density",
            available=False,
            value=None,
            raw_value=None,
            configured_weight=0.0,
            effective_weight=0.0,
            is_heuristic=True,
            status="UNAVAILABLE",
            basis=basis,
            explanation="Optional FilterRAG Freq-Density disabled by configuration (enable_freq_density=False).",
        )

    ans_txt = intermediate_answer
    if ans_txt is None and answer_callable is not None:
        try:
            ans_txt = answer_callable(query, doc)
        except Exception as exc:
            return SignalDetail(
                signal_id="SUPP_FREQ_DENSITY",
                signal_name="freq_density",
                available=False,
                value=None,
                raw_value=None,
                configured_weight=0.0,
                effective_weight=0.0,
                is_heuristic=True,
                status="UNAVAILABLE",
                basis=basis,
                explanation=f"Intermediate answer model unavailable for Freq-Density: {exc}",
            )

    if is_empty_text(doc.text) or is_empty_text(ans_txt):
        return SignalDetail(
            signal_id="SUPP_FREQ_DENSITY",
            signal_name="freq_density",
            available=False,
            value=None,
            raw_value=None,
            configured_weight=0.0,
            effective_weight=0.0,
            is_heuristic=True,
            status="UNAVAILABLE",
            basis=basis,
            explanation="Freq-Density unavailable: intermediate answer or document text missing.",
        )

    doc_tokens = tokenize_content_words(doc.text, include_negations=False)
    ref_tokens = set(tokenize_content_words(query, include_negations=False)) | set(
        tokenize_content_words(str(ans_txt), include_negations=False)
    )
    if not doc_tokens or not ref_tokens:
        return SignalDetail(
            signal_id="SUPP_FREQ_DENSITY",
            signal_name="freq_density",
            available=False,
            value=None,
            raw_value=None,
            configured_weight=0.0,
            effective_weight=0.0,
            is_heuristic=True,
            status="UNAVAILABLE",
            basis=basis,
            explanation="Insufficient content tokens to compute Freq-Density.",
        )

    hits = sum(1 for tok in doc_tokens if tok in ref_tokens)
    density = hits / len(doc_tokens)
    return SignalDetail(
        signal_id="SUPP_FREQ_DENSITY",
        signal_name="freq_density",
        available=True,
        value=round(min(1.0, density), 4),
        raw_value=round(density, 4),
        configured_weight=0.0,
        effective_weight=0.0,
        is_heuristic=True,
        status="AVAILABLE",
        basis=basis,
        explanation=f"freq_density={density:.4f} ({hits}/{len(doc_tokens)} passage content tokens align with query/answer).",
    )


__all__ = [
    "evaluate_perplexity_signal",
    "evaluate_embedding_norm_signal",
    "evaluate_query_match_signal",
    "evaluate_instruction_content_signal",
    "evaluate_consensus_deviation_signals",
    "evaluate_provenance_signal",
    "evaluate_freq_density_heuristic",
]
