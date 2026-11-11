"""Bounded, deterministic context-aware security thresholding for Phase 05 Step 3."""

from __future__ import annotations

import logging
import math
from collections.abc import Sequence

from trustrag.adaptive.schemas import (
    AdaptiveMode,
    ContextFeatures,
    ThresholdBounds,
    ThresholdRecommendation,
)
from trustrag.config import GuardrailsConfig, MSDConfig, RetrievalConfig
from trustrag.engine.schemas import EvidenceDocument, G1Assessment, G2DocumentAssessment

LOGGER = logging.getLogger(__name__)


def _classify_query_intent(query: str, g1_risk_score: float, g1_flagged: bool) -> str:
    """Classify benign query structure without inspecting retrieved documents."""
    if g1_flagged or g1_risk_score >= 0.35:
        return "suspicious"
    lowered = query.strip().lower()
    words = lowered.split()
    if any(tok in lowered for tok in ("ignore", "override", "system prompt", "bypass", "disregard")):
        return "instructional_ambiguous"
    if len(words) >= 12 or any(w in words for w in ("compare", "explain", "analyze", "contrast", "why", "how")):
        return "analytical"
    return "factual"


def extract_context_features(
    query: str,
    candidates: Sequence[EvidenceDocument],
    *,
    g1_assessment: G1Assessment | None = None,
    assessments: Sequence[G2DocumentAssessment] | None = None,
) -> ContextFeatures:
    """Extract safe structural context features for threshold selection.

    Critically, threshold features never read retrieved document text or injected instructions;
    only query traits, G1 status, source diversity, provenance tags, and aggregate signal counts are used.
    """
    n = len(candidates)
    g1_risk = float(g1_assessment.risk_score) if g1_assessment is not None else 0.0
    g1_flagged = bool(
        g1_assessment is not None and g1_assessment.decision.value in {"FLAG", "BLOCK"}
    )
    intent = _classify_query_intent(query, g1_risk, g1_flagged)

    unique_sources = {
        (d.source_id or "").strip().lower()
        for d in candidates
        if (d.source_id or "").strip() and (d.source_id or "").strip().lower() != "unknown"
    }
    evidence_diversity = (len(unique_sources) / n) if n > 0 else 0.0

    known_prov = sum(
        1
        for d in candidates
        if str(d.provenance or "").strip().lower() not in {"", "unknown", "none"}
    )
    provenance_coverage = (known_prov / n) if n > 0 else 0.0

    mean_avail_sig = 0.0
    conflict_ratio = 0.0
    uncertain_sec_ratio = 0.0
    if assessments:
        m = len(assessments)
        mean_avail_sig = sum(a.available_signals_count for a in assessments) / m
        conflict_ratio = sum(1 for a in assessments if a.conflict_detected) / m
        uncertain_sec_ratio = sum(
            1
            for a in assessments
            if a.decision.value in {"POISONED", "UNCERTAIN"}
            and (a.instruction_risk_score > 0.0 or a.trust_score < 0.60)
        ) / m

    return ContextFeatures(
        query_intent=intent,  # type: ignore[arg-type]
        query_word_count=len(query.split()),
        g1_risk_score=round(min(1.0, max(0.0, g1_risk)), 4),
        g1_flagged=g1_flagged,
        candidate_count=n,
        evidence_diversity=round(min(1.0, max(0.0, evidence_diversity)), 4),
        provenance_coverage=round(min(1.0, max(0.0, provenance_coverage)), 4),
        mean_available_signals=round(min(6.0, max(0.0, mean_avail_sig)), 4),
        conflict_ratio=round(min(1.0, max(0.0, conflict_ratio)), 4),
        security_uncertainty_ratio=round(min(1.0, max(0.0, uncertain_sec_ratio)), 4),
    )


class ContextAwareThresholdSelector:
    """Deterministic, bounded threshold selector with fail-safe static fallback."""

    def __init__(
        self,
        *,
        guardrails_config: GuardrailsConfig | None = None,
        msd_config: MSDConfig | None = None,
        retrieval_config: RetrievalConfig | None = None,
        bounds: ThresholdBounds | None = None,
        mode: AdaptiveMode = AdaptiveMode.ENFORCED,
    ) -> None:
        self.guardrails = guardrails_config or GuardrailsConfig()
        self.msd = msd_config or MSDConfig()
        self.retrieval = retrieval_config or RetrievalConfig()
        self.bounds = bounds or ThresholdBounds()
        self.mode = mode
        self.audit_log: list[ThresholdRecommendation] = []

    def static_recommendation(self, reason: str = "STATIC_DEFAULT_FALLBACK") -> ThresholdRecommendation:
        """Return unmodified static baseline thresholds."""
        return ThresholdRecommendation(
            g1_flag_threshold=self.guardrails.flag_threshold,
            g1_block_threshold=self.guardrails.block_threshold,
            g2_trust_threshold=self.msd.trust_threshold,
            g2_poison_threshold=self.msd.poison_threshold,
            removal_cap_ratio=self.retrieval.removal_cap_ratio,
            trust_weight=self.retrieval.trust_weight,
            used_static_fallback=True,
            reason_codes=[reason],
            context_snapshot={},
        )

    def select_thresholds(
        self,
        context: ContextFeatures | None,
    ) -> ThresholdRecommendation:
        """Select bounded deterministic G1/G2/retrieval thresholds from safe context."""
        if self.mode == AdaptiveMode.DISABLED or context is None or context.candidate_count == 0:
            rec = self.static_recommendation(
                "ADAPTIVE_MODE_DISABLED" if self.mode == AdaptiveMode.DISABLED else "STATIC_NO_CANDIDATE_FALLBACK"
            )
            self.audit_log.append(rec)
            return rec

        b = self.bounds
        base_g1_flag = self.guardrails.flag_threshold
        base_g1_block = self.guardrails.block_threshold
        base_g2_trust = self.msd.trust_threshold
        base_g2_poison = self.msd.poison_threshold
        base_cap = self.retrieval.removal_cap_ratio
        base_tw = self.retrieval.trust_weight

        g1_flag = base_g1_flag
        g1_block = base_g1_block
        g2_trust = base_g2_trust
        g2_poison = base_g2_poison
        cap_ratio = base_cap
        trust_w = base_tw
        reasons: list[str] = []

        # Strict invariant: G1 risk, instructional ambiguity, or elevated retrieval conflict/security uncertainty
        # may ONLY tighten security thresholds (never relax).
        if context.g1_flagged or context.query_intent in {"suspicious", "instructional_ambiguous"}:
            g1_flag -= 0.06
            g1_block -= 0.10
            g2_trust += 0.08
            g2_poison += 0.05
            cap_ratio += 0.15
            trust_w = min(b.trust_weight_max, base_tw + 0.10)
            reasons.append("CTX_TIGHTEN_SUSPICIOUS_QUERY")
        elif context.security_uncertainty_ratio >= 0.25 or context.conflict_ratio >= 0.25:
            g2_trust += 0.04
            g2_poison += 0.02
            cap_ratio += 0.10
            if context.security_uncertainty_ratio == 0.0:
                # Topical conflict with zero instruction/low-trust anomalies: limit trust penalty on rank
                trust_w = max(b.trust_weight_min, 0.20)
            else:
                trust_w = min(b.trust_weight_max, base_tw + 0.05)
            reasons.append("CTX_TIGHTEN_EVIDENCE_CONFLICT_OR_RISK")
        elif context.provenance_coverage < 0.20 and context.candidate_count >= 5:
            g2_trust += 0.02
            if context.security_uncertainty_ratio == 0.0:
                trust_w = max(b.trust_weight_min, 0.20)
            reasons.append("CTX_TIGHTEN_LOW_PROVENANCE_POOL")
        elif (
            context.query_intent in {"factual", "analytical"}
            and not context.g1_flagged
            and context.g1_risk_score == 0.0
            and context.security_uncertainty_ratio == 0.0
            and context.conflict_ratio == 0.0
            and context.candidate_count >= 3
            and (context.provenance_coverage >= 0.50 or context.evidence_diversity >= 0.60)
        ):
            # Benign high-diversity clean context: reduce borderline G2 UNCERTAIN margin mildly
            # and reduce clean-pool reranking distortion while keeping poison/G1/removal cap frozen.
            g2_trust -= 0.05
            trust_w = max(b.trust_weight_min, 0.20)
            reasons.append("CTX_STABILIZE_CLEAN_DIVERSE_POOL")
        else:
            if context.security_uncertainty_ratio == 0.0 and context.g1_risk_score == 0.0:
                trust_w = max(b.trust_weight_min, 0.20)
            reasons.append("CTX_NOMINAL_STATIC")

        # Hard clamping: security floors ensure zero weakening of poison detection, G1 blocking, or removal cap
        g1_flag = round(min(min(base_g1_flag, b.g1_flag_max), max(b.g1_flag_min, g1_flag)), 4)
        g1_block = round(min(min(base_g1_block, b.g1_block_max), max(b.g1_block_min, g1_block)), 4)
        g2_trust = round(min(b.g2_trust_max, max(b.g2_trust_min, g2_trust)), 4)
        g2_poison = round(min(b.g2_poison_max, max(max(base_g2_poison, b.g2_poison_min), g2_poison)), 4)
        cap_ratio = round(min(b.removal_cap_ratio_max, max(max(base_cap, b.removal_cap_ratio_min), cap_ratio)), 4)
        trust_w = round(min(b.trust_weight_max, max(b.trust_weight_min, trust_w)), 4)

        values = (g1_flag, g1_block, g2_trust, g2_poison, cap_ratio, trust_w)
        if (
            not all(math.isfinite(v) for v in values)
            or g2_poison >= g2_trust
            or g1_flag >= g1_block
        ):
            rec = self.static_recommendation("CTX_INVARIANT_VIOLATION_FALLBACK")
            self.audit_log.append(rec)
            return rec

        rec = ThresholdRecommendation(
            g1_flag_threshold=g1_flag,
            g1_block_threshold=g1_block,
            g2_trust_threshold=g2_trust,
            g2_poison_threshold=g2_poison,
            removal_cap_ratio=cap_ratio,
            trust_weight=trust_w,
            used_static_fallback=False,
            reason_codes=reasons,
            context_snapshot=context.model_dump(),
        )
        self.audit_log.append(rec)
        LOGGER.info(
            "Context-aware thresholds selected",
            extra={
                "reasons": reasons,
                "g2_trust": g2_trust,
                "g2_poison": g2_poison,
                "g1_flag": g1_flag,
                "g1_block": g1_block,
                "removal_cap_ratio": cap_ratio,
            },
        )
        return rec


__all__ = [
    "ContextAwareThresholdSelector",
    "extract_context_features",
]
