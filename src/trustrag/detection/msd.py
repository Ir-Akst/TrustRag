"""G2: Multi-Signal Detector (MSD) for TrustRAG Phase 03, Step 3.

Evaluates every retrieved document across six core research-aligned signals:
- F1: perplexity (Perplexity Anomaly — optional backend, never fabricated)
- F2: embedding_norm (Embedding-Norm Anomaly — actual vector L2 norms only)
- F3: query_match (Semantic Query Match — cosine similarity, raw value preserved)
- F4: instruction_content (Suspicious Instruction Content — RAG injection vs benign imperatives)
- F5: consensus_deviation (Consensus Deviation — cross-document semantic & factual outliers)
- F6: provenance (Provenance Prior — configurable priors & metadata traceability; UNKNOWN when absent)

Plus optional FilterRAG supplementary heuristic (`freq_density`) strictly separate from core scoring.

Computes normalized trust score via:
    trust_score(d) = sigmoid(w_eff · f(d) + b)
where available signal values s_i in [0, 1] are mapped to centered features f_i = 2*s_i - 1 in [-1, 1].
Missing signals contribute zero log-odds (f_i = 0) and NEVER amplify the remaining signal weights;
under the default 'coverage_attenuated' policy, observed weights are scaled by the observed
weight ratio r_A = available_weight / total_configured_weight <= 1.0 so missingness shrinks
posterior confidence toward the neutral prior rather than inflating it.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from trustrag.config.engine_config import MSDConfig
from trustrag.data.preprocessing.cleaning import is_empty_text
from trustrag.data.taxonomy import DocumentSecurityLabel
from trustrag.detection.signals import (
    evaluate_consensus_deviation_signals,
    evaluate_embedding_norm_signal,
    evaluate_freq_density_heuristic,
    evaluate_instruction_content_signal,
    evaluate_perplexity_signal,
    evaluate_provenance_signal,
    evaluate_query_match_signal,
)
from trustrag.engine.schemas import EvidenceDocument, G2DocumentAssessment, SignalDetail
from trustrag.utils.logging import get_logger

LOGGER = get_logger(__name__)


def _sigmoid(x: float) -> float:
    """Numerically stable logistic sigmoid bounded strictly in (0, 1)."""
    clamped = max(-40.0, min(40.0, float(x)))
    return 1.0 / (1.0 + math.exp(-clamped))


class MultiSignalDetector:
    """G2 Multi-Signal Detector (MSD) implementing 6-signal trust assessment and CLEAN/POISONED/UNCERTAIN classification."""

    def __init__(
        self,
        config: Optional[MSDConfig] = None,
        *,
        perplexity_callable: Optional[Callable[[str], float]] = None,
        embedding_callable: Optional[Callable[[Sequence[str]], Sequence[np.ndarray]]] = None,
        answer_callable: Optional[Callable[[str, EvidenceDocument], str]] = None,
        calibrator: Optional[Any] = None,
    ) -> None:
        self.config = config or MSDConfig()
        self.perplexity_callable = perplexity_callable
        self.embedding_callable = embedding_callable
        self.answer_callable = answer_callable
        self.calibrator = calibrator

    def _resolve_doc_embeddings(
        self,
        candidates: Sequence[EvidenceDocument],
        provided_embeddings: Optional[Sequence[Optional[np.ndarray]]],
    ) -> List[Optional[np.ndarray]]:
        """Resolve real document vectors from explicit embeddings, callable backend, or TF-IDF."""
        n = len(candidates)
        if provided_embeddings is not None:
            if len(provided_embeddings) != n:
                raise ValueError("doc_embeddings length must match candidates length")
            return [np.asarray(v, dtype=float) if v is not None else None for v in provided_embeddings]

        if self.config.embedding_backend == "disabled":
            return [None] * n

        if self.config.embedding_backend == "callable" and self.embedding_callable is not None:
            texts = [d.text if not is_empty_text(d.text) else "" for d in candidates]
            try:
                vecs = list(self.embedding_callable(texts))
                return [
                    np.asarray(vecs[i], dtype=float) if i < len(vecs) and vecs[i] is not None and not is_empty_text(candidates[i].text) else None
                    for i in range(n)
                ]
            except Exception as exc:
                LOGGER.warning("Embedding callable failed; marking embeddings unavailable", extra={"error": str(exc)})
                return [None] * n

        if self.config.embedding_backend in {"tfidf_raw", "tfidf_sublinear"}:
            non_empty = [i for i, d in enumerate(candidates) if not is_empty_text(d.text)]
            if len(non_empty) < 2:
                return [None] * n
            try:
                use_sublinear = self.config.embedding_backend == "tfidf_sublinear"
                # Compute actual unnormalized TF-IDF document vectors so norms represent real term-IDF energy
                vec = TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 2),
                    norm=None,
                    sublinear_tf=use_sublinear,
                    token_pattern=r"(?u)\b[a-zA-Z0-9][a-zA-Z0-9\-]*\b",
                )
                mat = vec.fit_transform([candidates[i].text for i in non_empty])
                resolved: List[Optional[np.ndarray]] = [None] * n
                for row_idx, orig_i in enumerate(non_empty):
                    arr = mat[row_idx].toarray().ravel()
                    if use_sublinear:
                        tok_count = max(1, len(candidates[orig_i].text.split()))
                        arr = arr / math.sqrt(float(tok_count))
                    resolved[orig_i] = arr
                return resolved
            except ValueError:
                return [None] * n

        return [None] * n

    def _compute_standalone_similarities(
        self,
        query: str,
        candidates: Sequence[EvidenceDocument],
        provided_scores: Optional[Sequence[Optional[float]]],
    ) -> List[Optional[float]]:
        """Use provided retrieval similarities or compute TF-IDF cosine when text exists."""
        n = len(candidates)
        if provided_scores is not None:
            if len(provided_scores) != n:
                raise ValueError("relevance_scores length must match candidates length")
            return [float(s) if s is not None else None for s in provided_scores]

        if is_empty_text(query) or self.config.embedding_backend == "disabled":
            return [None] * n

        from trustrag.engine.text_utils import compute_tfidf_similarities

        unique_texts: list[str] = []
        sig_to_uidx: dict[str, int] = {}
        doc_to_uidx: list[int] = []
        for d in candidates:
            sig = " ".join(d.text.strip().lower().split())
            if sig not in sig_to_uidx:
                sig_to_uidx[sig] = len(unique_texts)
                unique_texts.append(d.text)
            doc_to_uidx.append(sig_to_uidx[sig])
        unique_sims = compute_tfidf_similarities(query, unique_texts)
        return [
            None if is_empty_text(candidates[i].text) else float(unique_sims[doc_to_uidx[i]])
            for i in range(n)
        ]

    def assess_candidates(
        self,
        query: str,
        candidates: Sequence[EvidenceDocument],
        relevance_scores: Optional[Sequence[Optional[float]]] = None,
        *,
        doc_embeddings: Optional[Sequence[Optional[np.ndarray]]] = None,
        raw_perplexities: Optional[Sequence[Optional[float]]] = None,
        intermediate_answers: Optional[Sequence[Optional[str]]] = None,
        original_ranks: Optional[Sequence[int]] = None,
        trust_weight: float = 0.45,
    ) -> List[G2DocumentAssessment]:
        """Assess all candidate documents jointly across F1..F6 and emit structured G2 assessments."""
        if not candidates:
            return []

        n = len(candidates)
        if not self.config.enabled:
            rel_list = self._compute_standalone_similarities(query, candidates, relevance_scores)
            orig_ranks = list(original_ranks) if original_ranks is not None else list(range(1, n + 1))
            disabled_assessments: List[G2DocumentAssessment] = []
            for doc, orig_score, orig_rank in zip(candidates, rel_list, orig_ranks, strict=False):
                base_rel = round(float(orig_score), 4) if orig_score is not None else None
                disabled_assessments.append(
                    G2DocumentAssessment(
                        document_id=doc.doc_id,
                        source_id=doc.source_id,
                        provenance=doc.provenance,
                        metadata=dict(doc.metadata),
                        trust_score=1.0,
                        decision=DocumentSecurityLabel.CLEAN,
                        signals={},
                        supplementary_heuristics={},
                        available_signals_count=0,
                        available_weight_ratio=0.0,
                        missing_signal_policy=self.config.missing_signal_policy,
                        config_snapshot={"enabled": False},
                        reason_codes=["G2_DISABLED"],
                        original_retrieval_score=base_rel,
                        adjusted_retrieval_score=base_rel,
                        original_rank=orig_rank,
                        conflict_detected=False,
                        conflicting_doc_ids=[],
                        instruction_risk_score=0.0,
                        content_hash=doc.content_hash,
                    )
                )
            return disabled_assessments

        rel_list = self._compute_standalone_similarities(query, candidates, relevance_scores)
        vecs = self._resolve_doc_embeddings(candidates, doc_embeddings)
        ppl_list = list(raw_perplexities) if raw_perplexities is not None else [None] * n
        ans_list = list(intermediate_answers) if intermediate_answers is not None else [None] * n
        orig_ranks = list(original_ranks) if original_ranks is not None else list(range(1, n + 1))

        peer_norms = [
            float(np.linalg.norm(v))
            for v in vecs
            if v is not None and v.size > 0 and math.isfinite(float(np.linalg.norm(v))) and float(np.linalg.norm(v)) > 0.0
        ]

        # F5 requires joint comparison across candidate pool
        consensus_map = evaluate_consensus_deviation_signals(candidates, vecs, self.config)
        majority_consensus_peers = sum(
            1
            for sig, _ in consensus_map.values()
            if sig.available and sig.value is not None and float(sig.value) >= 0.70
        )

        total_configured_weight = (
            self.config.weight_perplexity
            + self.config.weight_embedding_norm
            + self.config.weight_query_match
            + self.config.weight_instruction_content
            + self.config.weight_consensus_deviation
            + self.config.weight_provenance
        )

        config_snapshot = {
            "enabled": self.config.enabled,
            "missing_signal_policy": self.config.missing_signal_policy,
            "embedding_norm_reference_policy": self.config.embedding_norm_reference_policy,
            "trust_threshold": self.config.trust_threshold,
            "poison_threshold": self.config.poison_threshold,
            "instruction_poison_threshold": self.config.instruction_poison_threshold,
            "bias": self.config.bias,
            "weights": {
                "perplexity": self.config.weight_perplexity,
                "embedding_norm": self.config.weight_embedding_norm,
                "query_match": self.config.weight_query_match,
                "instruction_content": self.config.weight_instruction_content,
                "consensus_deviation": self.config.weight_consensus_deviation,
                "provenance": self.config.weight_provenance,
            },
        }

        assessments: List[G2DocumentAssessment] = []

        for idx, doc in enumerate(candidates):
            orig_score = rel_list[idx]
            orig_rank = orig_ranks[idx]

            if not self.config.enabled:
                assessments.append(
                    G2DocumentAssessment(
                        document_id=doc.doc_id,
                        source_id=doc.source_id,
                        provenance=doc.provenance,
                        metadata=dict(doc.metadata),
                        trust_score=round(_sigmoid(self.config.bias), 4),
                        decision=DocumentSecurityLabel.UNCERTAIN,
                        signals={},
                        available_signals_count=0,
                        missing_signal_policy=self.config.missing_signal_policy,
                        config_snapshot=config_snapshot,
                        reason_codes=["G2_DISABLED"],
                        original_retrieval_score=orig_score,
                        adjusted_retrieval_score=orig_score,
                        original_rank=orig_rank,
                        content_hash=doc.content_hash,
                    )
                )
                continue

            # Evaluate 6 core signals
            sig_f1 = evaluate_perplexity_signal(
                doc,
                self.config,
                perplexity_callable=self.perplexity_callable,
                raw_perplexity=ppl_list[idx],
            )
            sig_f2 = evaluate_embedding_norm_signal(vecs[idx], peer_norms, self.config)
            sig_f3 = evaluate_query_match_signal(query, doc, orig_score, self.config)
            sig_f4, inst_risk = evaluate_instruction_content_signal(doc, self.config)
            sig_f5, conflicting_ids = consensus_map[doc.doc_id]
            sig_f6 = evaluate_provenance_signal(doc, self.config)

            signals_dict: Dict[str, SignalDetail] = {
                "perplexity": sig_f1,
                "embedding_norm": sig_f2,
                "query_match": sig_f3,
                "instruction_content": sig_f4,
                "consensus_deviation": sig_f5,
                "provenance": sig_f6,
            }

            # Optional FilterRAG supplementary heuristic (excluded from core scoring)
            supp_dict: Dict[str, SignalDetail] = {}
            if self.config.enable_freq_density:
                supp_dict["freq_density"] = evaluate_freq_density_heuristic(
                    query,
                    doc,
                    self.config,
                    intermediate_answer=ans_list[idx],
                    answer_callable=self.answer_callable,
                )

            available_list = [s for s in signals_dict.values() if s.available and s.value is not None]
            available_weight = sum(s.configured_weight for s in available_list)
            weight_ratio = available_weight / total_configured_weight if total_configured_weight > 0 else 0.0

            insufficient_signals = (
                is_empty_text(doc.text)
                or len(available_list) < self.config.min_available_signals
                or weight_ratio < self.config.min_available_weight_ratio
                or (self.config.missing_signal_policy == "strict_uncertain_on_missing" and len(available_list) < 6)
            )

            # Non-amplifying missing-signal scoring: missing signals contribute 0 log-odds
            # and never scale up the weights of the remaining signals.
            if available_weight > 0.0 and total_configured_weight > 0.0:
                if self.config.missing_signal_policy == "zero_log_odds":
                    confidence_scale = 1.0
                else:
                    # 'coverage_attenuated' (and non-amplifying base for 'strict_uncertain_on_missing'):
                    # Attenuates log-odds proportionally to observed weight coverage r_A <= 1.0
                    # so sparse signals pull confidence honestly toward the prior instead of amplifying it.
                    confidence_scale = min(1.0, weight_ratio)
                logit = float(self.config.bias)
                minority_outlier_attenuated = False
                for s in signals_dict.values():
                    if s.available and s.value is not None:
                        eff_w = s.configured_weight * confidence_scale
                        if (
                            self.config.enable_minority_outlier_attenuation
                            and s.signal_id == "F5"
                            and "MINORITY_OUTLIER" in s.flags
                            and float(s.value) <= 0.25
                            and majority_consensus_peers >= self.config.minority_outlier_majority_peers_min
                        ):
                            eff_w *= self.config.minority_outlier_consensus_multiplier
                            minority_outlier_attenuated = True
                        s.effective_weight = round(eff_w, 4)
                        centered_f = 2.0 * float(s.value) - 1.0  # Maps [0, 1] -> [-1, +1]
                        logit += eff_w * centered_f
                    else:
                        s.effective_weight = 0.0
                trust_score = round(_sigmoid(logit), 4)
            else:
                minority_outlier_attenuated = False
                for s in signals_dict.values():
                    s.effective_weight = 0.0
                trust_score = round(_sigmoid(self.config.bias), 4)

            doc_config_snapshot: Dict[str, Any] = dict(config_snapshot)
            doc_config_snapshot["raw_trust_score"] = trust_score
            if self.calibrator is not None and not insufficient_signals:
                cal_score, cal_fallback = self.calibrator.calibrate_score(trust_score)
                art = getattr(self.calibrator, "artifact", None)
                doc_config_snapshot["calibration_active"] = bool(not cal_fallback and getattr(self.calibrator, "is_active", False))
                doc_config_snapshot["calibration_fallback"] = bool(cal_fallback)
                doc_config_snapshot["calibration_version"] = getattr(art, "version", None) if art is not None else None
                doc_config_snapshot["calibrated_trust_score"] = cal_score
                trust_score = cal_score

            reason_codes: List[str] = []
            for s in signals_dict.values():
                reason_codes.extend(s.flags)
            if minority_outlier_attenuated:
                reason_codes.append("G2_MINORITY_OUTLIER_ATTENUATED")

            conflict_detected = bool(conflicting_ids)

            # Classification Decision: CLEAN / POISONED / UNCERTAIN
            if is_empty_text(doc.text):
                decision = DocumentSecurityLabel.UNCERTAIN
                reason_codes.append("G2_EMPTY_DOCUMENT")
            elif insufficient_signals:
                decision = DocumentSecurityLabel.UNCERTAIN
                reason_codes.append("G2_INSUFFICIENT_SIGNALS")
            elif inst_risk >= self.config.instruction_poison_threshold:
                decision = DocumentSecurityLabel.POISONED
                reason_codes.append("G2_SUSPICIOUS_INSTRUCTION")
            elif trust_score < self.config.poison_threshold:
                # Guard: conflict or missing provenance alone must not force POISONED
                has_perplexity_spike = sig_f1.available and sig_f1.value is not None and sig_f1.value < 0.30
                has_norm_spike = sig_f2.available and sig_f2.value is not None and sig_f2.value < 0.30
                if conflict_detected and inst_risk < self.config.instruction_flag_threshold and not (has_perplexity_spike or has_norm_spike):
                    decision = DocumentSecurityLabel.UNCERTAIN
                    reason_codes.append("G2_CONFLICT_REQUIRES_VERIFICATION")
                else:
                    decision = DocumentSecurityLabel.POISONED
                    reason_codes.append("G2_LOW_TRUST_SCORE")
            elif conflict_detected or inst_risk >= self.config.instruction_flag_threshold or trust_score < self.config.trust_threshold:
                decision = DocumentSecurityLabel.UNCERTAIN
                if conflict_detected:
                    reason_codes.append("G2_CONFLICT_DETECTED")
                else:
                    reason_codes.append("G2_MEDIUM_TRUST_UNCERTAIN")
            else:
                decision = DocumentSecurityLabel.CLEAN
                reason_codes.append("G2_CLEAN")

            base_rel = float(orig_score) if orig_score is not None else 0.5
            tier_factor = (
                1.0
                if decision == DocumentSecurityLabel.CLEAN
                else (0.65 if decision == DocumentSecurityLabel.UNCERTAIN else 0.20)
            )
            adjusted_score = round(
                tier_factor * ((1.0 - trust_weight) * base_rel + trust_weight * trust_score),
                4,
            )

            assessments.append(
                G2DocumentAssessment(
                    document_id=doc.doc_id,
                    source_id=doc.source_id,
                    provenance=doc.provenance,
                    metadata=dict(doc.metadata),
                    trust_score=trust_score,
                    decision=decision,
                    signals=signals_dict,
                    supplementary_heuristics=supp_dict,
                    available_signals_count=len(available_list),
                    available_weight_ratio=round(weight_ratio, 4),
                    missing_signal_policy=self.config.missing_signal_policy,
                    config_snapshot=doc_config_snapshot,
                    reason_codes=list(dict.fromkeys(reason_codes)),
                    original_retrieval_score=round(float(orig_score), 4) if orig_score is not None else None,
                    adjusted_retrieval_score=adjusted_score,
                    original_rank=orig_rank,
                    conflict_detected=conflict_detected,
                    conflicting_doc_ids=conflicting_ids,
                    instruction_risk_score=inst_risk,
                    content_hash=doc.content_hash,
                )
            )

        LOGGER.info(
            "G2 Multi-Signal assessment completed",
            extra={
                "candidate_count": len(assessments),
                "clean_count": sum(1 for a in assessments if a.decision == DocumentSecurityLabel.CLEAN),
                "uncertain_count": sum(1 for a in assessments if a.decision == DocumentSecurityLabel.UNCERTAIN),
                "poisoned_count": sum(1 for a in assessments if a.decision == DocumentSecurityLabel.POISONED),
            },
        )
        return assessments

    def assess_document(
        self,
        query: str,
        doc: EvidenceDocument,
        relevance_score: Optional[float] = 0.5,
        *,
        embedding: Optional[np.ndarray] = None,
        raw_perplexity: Optional[float] = None,
    ) -> G2DocumentAssessment:
        """Convenience wrapper assessing a single document."""
        return self.assess_candidates(
            query,
            [doc],
            [relevance_score] if relevance_score is not None else None,
            doc_embeddings=[embedding] if embedding is not None else None,
            raw_perplexities=[raw_perplexity] if raw_perplexity is not None else None,
        )[0]


__all__ = ["MultiSignalDetector"]
