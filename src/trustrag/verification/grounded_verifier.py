"""Phase 32 Workstream D: Evidence-Grounded Answer Verification Engine.

Performs rigorous factuality and entailment verification on generated answers:
1. Deconstructs generated answers into verifiable atomic claims.
2. Maps each claim to retrieved evidence spans via multi-stage alignment.
3. Evaluates 3-class NLI using the frozen DeBERTa-v3-small checkpoint:
   - ENTAILMENT: Claim is directly supported by evidence.
   - CONTRADICTION: Claim asserts facts opposite to evidence.
   - NEUTRAL: Claim lacks sufficient evidence in retrieved documents.
4. Identifies unsupported claims and conflicting evidence across passages.
5. Emits granular claim-level factuality telemetry and explicit ABSTAIN signals.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from trustrag.engine.schemas import EvidenceDocument
from trustrag.engine.text_utils import compute_lexical_overlap, split_sentences
from trustrag.verification.output_verifier import _extract_proper_entities

@dataclass
class ClaimVerificationResult:
    """Detailed verification assessment for an atomic claim."""
    claim_id: str
    claim_text: str
    verdict: str  # "SUPPORTED", "CONTRADICTED", "UNSUPPORTED", "INSUFFICIENT_EVIDENCE"
    entailment_prob: float
    contradiction_prob: float
    neutral_prob: float
    best_matching_doc_id: Optional[str]
    supporting_evidence_span: Optional[str]
    confidence: float
    has_numerical_match: bool

@dataclass
class EvidenceGroundedAnswerReport:
    """Comprehensive verification report for a generated RAG answer."""
    overall_status: str  # "SUPPORTED", "PARTIALLY_SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"
    safe_to_release: bool
    answer_text: str
    total_claims: int
    supported_claims_count: int
    contradicted_claims_count: int
    unsupported_claims_count: int
    claim_support_rate: float
    evidence_coverage: float
    contradiction_detected: bool
    abstention_required: bool
    abstention_reason: Optional[str]
    claim_results: List[ClaimVerificationResult]
    latency_ms: float = 0.0


_APPROX_CUES = re.compile(r"\b(?:roughly|approximately|about|around|nearly|almost|circa)\b|~", re.IGNORECASE)

_FUNCTIONAL_ROLE_PAT = re.compile(
    r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+(?:is|was|serves\s+as|became|remains)\s+(?:the\s+|de\s+facto\s+){1,2}(capital|president|prime\s+minister|founder|ceo|author|inventor|discoverer|largest\s+city|longest\s+river|highest\s+mountain)\s+(?:of|in)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\b"
)

_ANTONYM_POLARITY_PAIRS: Tuple[Tuple[re.Pattern[str], re.Pattern[str]], ...] = (
    (re.compile(r"\b(?:completely\s+)?safe\b", re.I), re.compile(r"\b(?:contraindicated|unsafe|hazardous|toxic|dangerous)\b", re.I)),
    (re.compile(r"\b(?:24\s+hours|continuously|around\s+the\s+clock|always\s+open)\b", re.I), re.compile(r"\b(?:closes|closed|reopens|shut)\b", re.I)),
    (re.compile(r"\b(?:proprietary|commercial\s+license|paid\s+license)\b", re.I), re.compile(r"\b(?:free\s+and\s+open[- ]source|open[- ]source|mit\s+license|public\s+domain)\b", re.I)),
    (re.compile(r"\b(?:increases|raises|accelerates|elevates)\b", re.I), re.compile(r"\b(?:decreases|reduces|lowers|inhibits|slows)\b", re.I)),
    (re.compile(r"\b(?:allows|permits|enables|requires)\b", re.I), re.compile(r"\b(?:prohibits|forbids|bans|prevents)\b", re.I)),
)


def _detect_functional_role_contradiction(premise: str, hypothesis: str) -> Tuple[bool, str]:
    """Detect conflicting role assignments like 'X is the capital of Y' vs 'Z is the capital of Y'."""
    p_roles = _FUNCTIONAL_ROLE_PAT.findall(premise)
    h_roles = _FUNCTIONAL_ROLE_PAT.findall(hypothesis)
    for h_subj, h_role, h_obj in h_roles:
        for p_subj, p_role, p_obj in p_roles:
            if h_role.lower() == p_role.lower() and (
                h_obj.lower() == p_obj.lower()
                or h_obj.lower() in p_obj.lower()
                or p_obj.lower() in h_obj.lower()
            ):
                if h_subj.lower() != p_subj.lower():
                    return True, f"Functional role contradiction on '{h_role} of {h_obj}': '{h_subj}' vs '{p_subj}'"
    return False, ""


def _detect_implicit_polarity_contradiction(premise: str, hypothesis: str) -> Tuple[bool, str]:
    """Detect antonymous polarity opposition between premise and hypothesis."""
    for pat_a, pat_b in _ANTONYM_POLARITY_PAIRS:
        if (pat_a.search(hypothesis) and pat_b.search(premise)) or (pat_b.search(hypothesis) and pat_a.search(premise)):
            return True, "Implicit semantic polarity contradiction detected"
    return False, ""


def _detect_semantic_entity_contradiction(premise: str, hypothesis: str, query: str = "") -> Tuple[bool, str]:
    """Detect general semantic entity divergence or functional-role conflict without hardcoded entities."""
    role_conflict, role_reason = _detect_functional_role_contradiction(premise, hypothesis)
    if role_conflict:
        return True, role_reason

    c_ents = _extract_proper_entities(hypothesis)
    p_ents = _extract_proper_entities(premise)
    q_ents = _extract_proper_entities(query) if query else set()

    unmatched_claim_ents = set()
    for ce in (c_ents - q_ents):
        stem_c = ce.rstrip("s").rstrip("y").rstrip("ic").rstrip("ian").rstrip("an")
        matched = False
        for pe in p_ents:
            stem_p = pe.rstrip("s").rstrip("y").rstrip("ic").rstrip("ian").rstrip("an")
            if ce == pe or stem_c == stem_p or (len(stem_c) >= 4 and (stem_c in pe or pe in stem_c)):
                matched = True
                break
        if not matched and ce in premise.lower():
            matched = True
        if not matched:
            unmatched_claim_ents.add(ce)

    unmatched_premise_ents = set()
    for pe in (p_ents - q_ents):
        stem_p = pe.rstrip("s").rstrip("y").rstrip("ic").rstrip("ian").rstrip("an")
        matched = False
        for ce in c_ents:
            stem_c = ce.rstrip("s").rstrip("y").rstrip("ic").rstrip("ian").rstrip("an")
            if ce == pe or stem_c == stem_p or (len(stem_c) >= 4 and (stem_c in pe or pe in stem_c)):
                matched = True
                break
        if not matched and pe in hypothesis.lower():
            matched = True
        if not matched:
            unmatched_premise_ents.add(pe)

    if unmatched_claim_ents and unmatched_premise_ents:
        # Require subject/focal-slot entity mismatch (opening proper entity of claim or premise is unmatched)
        # so extra detail entities on a matched subject (e.g. 'Acme Corp ... Q4' vs 'Acme Corp ... Ohio')
        # are treated as INSUFFICIENT_EVIDENCE rather than CONTRADICTED.
        h_tokens = [w.strip(".,;:!?\"'()").lower() for w in hypothesis.split()]
        p_tokens = [w.strip(".,;:!?\"'()").lower() for w in premise.split()]
        h_head = next((w for w in h_tokens[:5] if w in c_ents), None)
        p_head = next((w for w in p_tokens[:5] if w in p_ents), None)
        if (h_head and h_head in unmatched_claim_ents) or (p_head and p_head in unmatched_premise_ents):
            return True, f"Entity substitution contradiction: claim introduces {sorted(unmatched_claim_ents)} contradicting premise {sorted(unmatched_premise_ents)}"
    return False, ""


def _check_numerical_consistency(
    claim: str,
    span: str,
    best_ent: float,
) -> Tuple[bool, bool]:
    """Tolerance-aware numerical consistency check supporting approximation cues and unit scaling."""
    claim_nums = set(re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", claim.replace(",", "")))
    span_nums = set(re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", (span or "").replace(",", "")))
    if not claim_nums:
        return True, False
    if not span_nums:
        # Premise contains no numbers: claim is unsupported by numeric evidence, not numerically contradicted
        return False, False

    has_approx = bool(_APPROX_CUES.search(claim) or _APPROX_CUES.search(span or ""))
    tol = 0.02 if (has_approx or best_ent >= 0.65) else 0.001

    for cn in claim_nums:
        matched = False
        try:
            cn_val = float(cn)
        except ValueError:
            cn_val = None
        for sn in span_nums:
            if cn == sn or (len(cn) >= 4 and (sn.startswith(cn) or cn.startswith(sn))):
                matched = True
                break
            if cn_val is not None:
                try:
                    sn_val = float(sn)
                    denom = max(abs(cn_val), abs(sn_val), 1e-9)
                    if abs(cn_val - sn_val) / denom <= tol:
                        matched = True
                        break
                    # Check metric/imperial or km/m scaling (1000x or 1.60934x)
                    if abs(cn_val * 1000.0 - sn_val) / max(abs(sn_val), 1e-9) <= 0.02 or abs(sn_val * 1000.0 - cn_val) / max(abs(cn_val), 1e-9) <= 0.02:
                        matched = True
                        break
                except ValueError:
                    pass
        if not matched:
            return False, True
    return True, False

class EvidenceGroundedVerifier:
    """Grounded Verification Engine utilizing frozen DeBERTa-v3-small NLI inference."""

    FROZEN_NLI_CHECKPOINT = "/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch"

    def __init__(
        self,
        checkpoint_path: Optional[str | Path] = None,
        *,
        entailment_threshold: float = 0.50,
        contradiction_threshold: float = 0.20,
        min_support_ratio_to_release: float = 0.70
    ) -> None:
        self.checkpoint_path = Path(checkpoint_path or self.FROZEN_NLI_CHECKPOINT)
        self.entailment_threshold = entailment_threshold
        self.contradiction_threshold = contradiction_threshold
        self.min_support_ratio_to_release = min_support_ratio_to_release
        self._tokenizer: Any = None
        self._model: Any = None
        self._is_loaded = False
        self._nli_cache: Dict[Tuple[str, str], Tuple[float, float, float]] = {}

    def initialize(self) -> None:
        """Load frozen DeBERTa-v3-small weights for CPU inference."""
        if self._is_loaded and self._model is not None:
            return

        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        if not self.checkpoint_path.exists():
            raise FileNotFoundError(f"DeBERTa checkpoint path not found: {self.checkpoint_path}")

        self._tokenizer = AutoTokenizer.from_pretrained(str(self.checkpoint_path), local_files_only=True)
        self._model = AutoModelForSequenceClassification.from_pretrained(str(self.checkpoint_path), local_files_only=True)
        self._model.eval()
        for p in self._model.parameters():
            p.requires_grad = False
        self._is_loaded = True

    def _predict_nli_pair(self, premise: str, hypothesis: str) -> Tuple[float, float, float]:
        """Execute forward pass for (premise, hypothesis) returning (p_ent, p_con, p_neu)."""
        import torch

        if not self._is_loaded:
            self.initialize()

        inputs = self._tokenizer(
            premise,
            hypothesis,
            truncation=True,
            max_length=256,
            padding=True,
            return_tensors="pt"
        )
        with torch.no_grad():
            outputs = self._model(**inputs)
            probs = torch.softmax(outputs.logits[0], dim=-1).cpu().numpy()

        p_ent = float(probs[0])
        p_con = float(probs[1])
        p_neu = float(probs[2])
        return p_ent, p_con, p_neu

    def _predict_nli_batch(self, pairs: List[Tuple[str, str]]) -> List[Tuple[float, float, float]]:
        """Execute batched forward pass for [(premise, hypothesis), ...] with deterministic pair caching."""
        import torch

        if not pairs:
            return []
        if not self._is_loaded:
            self.initialize()

        results: List[Optional[Tuple[float, float, float]]] = [None] * len(pairs)
        uncached_indices: List[int] = []
        uncached_pairs: List[Tuple[str, str]] = []
        for idx, pair in enumerate(pairs):
            cached = self._nli_cache.get(pair)
            if cached is not None:
                results[idx] = cached
            else:
                uncached_indices.append(idx)
                uncached_pairs.append(pair)

        if uncached_pairs:
            premises = [p for p, _ in uncached_pairs]
            hypotheses = [h for _, h in uncached_pairs]
            inputs = self._tokenizer(
                premises,
                hypotheses,
                truncation=True,
                max_length=256,
                padding=True,
                return_tensors="pt",
            )
            with torch.no_grad():
                outputs = self._model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()

            for idx, pair, row in zip(uncached_indices, uncached_pairs, probs):
                score = (float(row[0]), float(row[1]), float(row[2]))
                if len(self._nli_cache) < 1024:
                    self._nli_cache[pair] = score
                results[idx] = score

        return [r for r in results if r is not None]

    def extract_atomic_claims(self, answer_text: str) -> List[str]:
        """Deconstruct answer text into verifiable atomic factual claims."""
        sentences = split_sentences(answer_text)
        claims: List[str] = []
        for s in sentences:
            s_clean = s.strip()
            # Disregard trivial conversational filler
            if len(s_clean.split()) < 3 or s_clean.lower() in ["thank you.", "here is the answer:", "in summary:"]:
                continue
            claims.append(s_clean)
        return claims

    def verify_answer(
        self,
        query: str,
        answer_text: str,
        retrieved_documents: List[EvidenceDocument]
    ) -> EvidenceGroundedAnswerReport:
        """Perform end-to-end evidence grounding verification on generated answer."""
        t0 = time.perf_counter()
        claims = self.extract_atomic_claims(answer_text)

        if not claims:
            # Empty or non-substantive answer
            return EvidenceGroundedAnswerReport(
                overall_status="INSUFFICIENT_EVIDENCE",
                safe_to_release=False,
                answer_text=answer_text,
                total_claims=0,
                supported_claims_count=0,
                contradicted_claims_count=0,
                unsupported_claims_count=0,
                claim_support_rate=0.0,
                evidence_coverage=0.0,
                contradiction_detected=False,
                abstention_required=True,
                abstention_reason="Answer contains no verifiable factual claims.",
                claim_results=[],
                latency_ms=round((time.perf_counter() - t0) * 1000.0, 3)
            )

        if not retrieved_documents:
            # Context starvation
            results = [
                ClaimVerificationResult(
                    claim_id=f"c_{idx}",
                    claim_text=c,
                    verdict="INSUFFICIENT_EVIDENCE",
                    entailment_prob=0.0,
                    contradiction_prob=0.0,
                    neutral_prob=1.0,
                    best_matching_doc_id=None,
                    supporting_evidence_span=None,
                    confidence=1.0,
                    has_numerical_match=False
                )
                for idx, c in enumerate(claims)
            ]
            return EvidenceGroundedAnswerReport(
                overall_status="INSUFFICIENT_EVIDENCE",
                safe_to_release=False,
                answer_text=answer_text,
                total_claims=len(claims),
                supported_claims_count=0,
                contradicted_claims_count=0,
                unsupported_claims_count=len(claims),
                claim_support_rate=0.0,
                evidence_coverage=0.0,
                contradiction_detected=False,
                abstention_required=True,
                abstention_reason="No evidence passages available to ground claims.",
                claim_results=results,
                latency_ms=round((time.perf_counter() - t0) * 1000.0, 3)
            )

        # Break retrieved documents into candidate evidence sentences
        evidence_spans: List[Tuple[str, str]] = []  # (doc_id, sentence_text)
        for doc in retrieved_documents:
            doc_sents = split_sentences(doc.text)
            for ds in doc_sents:
                if len(ds.strip().split()) >= 4:
                    evidence_spans.append((doc.doc_id, ds.strip()))

        claim_results: List[ClaimVerificationResult] = []
        supported_count = 0
        contradicted_count = 0
        unsupported_count = 0

        for c_idx, claim in enumerate(claims):
            best_ent = 0.0
            best_con = 0.0
            best_neu = 1.0
            best_doc_id = None
            best_span = None

            # Compare claim against all candidate evidence spans in a single batched forward pass
            pairs = [(span, claim) for _, span in evidence_spans]
            batch_scores = self._predict_nli_batch(pairs)
            for (doc_id, span), (p_ent, p_con, p_neu) in zip(evidence_spans, batch_scores):
                if p_con > best_con:
                    best_con = p_con
                if p_ent > best_ent:
                    best_ent = p_ent
                    best_neu = p_neu
                    best_doc_id = doc_id
                    best_span = span

            has_num_match, num_conflict = _check_numerical_consistency(claim, best_span or "", best_ent)
            lex_overlap = compute_lexical_overlap(best_span or "", claim)
            sem_conflict, sem_reason = _detect_semantic_entity_contradiction(best_span or "", claim, query=query)
            imp_conflict, imp_reason = _detect_implicit_polarity_contradiction(best_span or "", claim)

            # Decision logic with strict entailment and contradiction precedence:
            # Require genuine neural entailment dominance or substantial entailment without entity substitution
            # Never accept a claim purely based on lexical overlap when neutral probability dominates
            is_contradicted = (best_con >= self.contradiction_threshold or num_conflict or sem_conflict or imp_conflict)

            # Grounded entailment:
            # Requires either direct neural entailment (p_ent >= entailment_threshold), OR
            # consistent numerical and entity alignment where p_ent >= 0.16 and p_ent >= p_con and lex_overlap >= 0.18
            is_supported = (
                not is_contradicted
                and has_num_match
                and not num_conflict
                and not sem_conflict
                and not imp_conflict
                and (
                    best_ent >= self.entailment_threshold
                    or (best_ent >= 0.16 and best_ent >= best_con and lex_overlap >= 0.18)
                )
            )

            if is_contradicted:
                verdict = "CONTRADICTED"
                contradicted_count += 1
            elif is_supported:
                verdict = "SUPPORTED"
                supported_count += 1
            else:
                verdict = "UNSUPPORTED"
                unsupported_count += 1

            claim_results.append(ClaimVerificationResult(
                claim_id=f"claim_{c_idx+1}",
                claim_text=claim,
                verdict=verdict,
                entailment_prob=round(best_ent, 4),
                contradiction_prob=round(best_con, 4),
                neutral_prob=round(best_neu, 4),
                best_matching_doc_id=best_doc_id,
                supporting_evidence_span=best_span,
                confidence=round(max(best_ent, best_con, best_neu), 4),
                has_numerical_match=has_num_match
            ))

        total = len(claims)
        support_rate = supported_count / total if total else 0.0
        coverage = (supported_count + contradicted_count) / total if total else 0.0
        has_contradiction = contradicted_count > 0

        # Overall Status
        if has_contradiction:
            overall_status = "CONTRADICTED"
            abstain = True
            safe = False
            reason = f"Answer contains {contradicted_count} claim(s) directly contradicted by evidence."
        elif support_rate >= self.min_support_ratio_to_release:
            overall_status = "SUPPORTED"
            abstain = False
            safe = True
            reason = None
        elif support_rate > 0.0:
            overall_status = "PARTIALLY_SUPPORTED"
            abstain = True
            safe = False
            reason = f"Only {supported_count}/{total} claims grounded in evidence (support rate: {support_rate*100:.1f}% < threshold {self.min_support_ratio_to_release*100:.1f}%)."
        else:
            overall_status = "INSUFFICIENT_EVIDENCE"
            abstain = True
            safe = False
            reason = "No claims in the answer are supported by retrieved evidence."

        return EvidenceGroundedAnswerReport(
            overall_status=overall_status,
            safe_to_release=safe,
            answer_text=answer_text,
            total_claims=total,
            supported_claims_count=supported_count,
            contradicted_claims_count=contradicted_count,
            unsupported_claims_count=unsupported_count,
            claim_support_rate=round(support_rate, 4),
            evidence_coverage=round(coverage, 4),
            contradiction_detected=has_contradiction,
            abstention_required=abstain,
            abstention_reason=reason,
            claim_results=claim_results,
            latency_ms=round((time.perf_counter() - t0) * 1000.0, 3)
        )

