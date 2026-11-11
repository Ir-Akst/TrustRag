"""Composable controller connecting Phase 05 adaptive calibration, thresholding, and drift awareness."""

from __future__ import annotations

import logging
import math
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from trustrag.adaptive.calibration import TrustCalibrator
from trustrag.adaptive.drift import DriftMonitor, TelemetryRecord
from trustrag.adaptive.policy_engine import AdaptationPolicyEngine
from trustrag.adaptive.schemas import (
    AdaptiveConfig,
    AdaptiveMode,
    DriftReport,
    ThresholdRecommendation,
)
from trustrag.adaptive.thresholding import ContextAwareThresholdSelector, extract_context_features
from trustrag.config import Settings, load_config
from trustrag.detection import MultiSignalDetector
from trustrag.engine.schemas import EvidenceDocument, G1Assessment, G2DocumentAssessment
from trustrag.guardrails import InputGuardrail
from trustrag.pipeline import TrustRAGPipeline
from trustrag.retrieval import TrustAwareRetriever

LOGGER = logging.getLogger(__name__)


@dataclass
class AdaptiveRunOutcome:
    """Detailed outcome of executing one query under static or adaptive defense."""

    variant_name: str
    query: str
    g1_assessment: G1Assessment
    threshold_recommendation: ThresholdRecommendation
    drift_report: DriftReport | None
    assessments: list[G2DocumentAssessment]
    retained_documents: list[EvidenceDocument]
    removed_documents: list[EvidenceDocument]
    abstained: bool
    blocked_by_guardrail: bool
    answer: str
    g3_verdict: str | None
    fail_safe_events: list[str] = field(default_factory=list)


@dataclass
class AdaptiveDefenseController:
    """Non-intrusive Phase 05 orchestrator wrapping G1, G2 calibration, thresholding, and drift monitoring."""

    settings: Settings = field(default_factory=load_config)
    adaptive_config: AdaptiveConfig = field(default_factory=AdaptiveConfig)
    calibrator: TrustCalibrator | None = None
    drift_monitor: DriftMonitor | None = None
    policy_engine: AdaptationPolicyEngine | None = None
    variant_name: str = "static"
    failure_events: list[dict[str, str]] = field(default_factory=list)
    _cached_corpus_key: tuple[tuple[str, str], ...] | None = field(default=None, init=False, repr=False)
    _cached_base_retriever: TrustAwareRetriever | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.selector = ContextAwareThresholdSelector(
            guardrails_config=self.settings.guardrails,
            msd_config=self.settings.msd,
            retrieval_config=self.settings.retrieval,
            bounds=self.adaptive_config.threshold_bounds,
            mode=(
                AdaptiveMode.ENFORCED
                if self.adaptive_config.enable_context_thresholding and self.adaptive_config.mode != AdaptiveMode.DISABLED
                else AdaptiveMode.DISABLED
            ),
        )

    def _get_or_build_base_retriever(
        self,
        documents: Sequence[EvidenceDocument],
    ) -> TrustAwareRetriever:
        """Cache TF-IDF corpus index across identical document pools to avoid O(N) refits per query."""
        corpus_key = tuple((d.doc_id, d.content_hash) for d in documents)
        if self._cached_base_retriever is not None and self._cached_corpus_key == corpus_key:
            return self._cached_base_retriever
        base = TrustAwareRetriever(
            documents=list(documents),
            retrieval_config=self.settings.retrieval,
            msd_config=self.settings.msd,
        )
        self._cached_corpus_key = corpus_key
        self._cached_base_retriever = base
        return base

    @staticmethod
    def _clone_indexed_retriever(
        base: TrustAwareRetriever,
        *,
        retrieval_config: Any,
        msd_config: Any,
        detector: MultiSignalDetector,
    ) -> TrustAwareRetriever:
        """Create a query-isolated retriever sharing base's precomputed TF-IDF matrices."""
        clone = TrustAwareRetriever(
            documents=None,
            retrieval_config=retrieval_config,
            msd_config=msd_config,
            detector=detector,
        )
        clone._documents = base._documents
        clone._vectorizer = base._vectorizer
        clone._raw_vectorizer = base._raw_vectorizer
        clone._doc_matrix = base._doc_matrix
        clone._raw_doc_matrix = base._raw_doc_matrix
        return clone

    def _apply_drift_tightening(
        self,
        rec: ThresholdRecommendation,
        drift_rep: DriftReport | None,
    ) -> ThresholdRecommendation:
        """Apply strictly monotonic safety tightening (never weakening) on confirmed attack drift."""
        if (
            not self.adaptive_config.enable_drift_monitoring
            or drift_rep is None
            or drift_rep.classification != "suspected_attack_drift"
        ):
            return rec
        b = self.adaptive_config.threshold_bounds
        new_rec = rec.model_copy(deep=True)
        new_rec.g2_trust_threshold = round(min(b.g2_trust_max, max(new_rec.g2_trust_threshold, self.settings.msd.trust_threshold + 0.06)), 4)
        new_rec.g2_poison_threshold = round(min(b.g2_poison_max, max(new_rec.g2_poison_threshold, self.settings.msd.poison_threshold + 0.04)), 4)
        new_rec.g1_flag_threshold = round(max(b.g1_flag_min, min(new_rec.g1_flag_threshold, self.settings.guardrails.flag_threshold - 0.05)), 4)
        new_rec.g1_block_threshold = round(max(b.g1_block_min, min(new_rec.g1_block_threshold, self.settings.guardrails.block_threshold - 0.08)), 4)
        new_rec.removal_cap_ratio = round(min(b.removal_cap_ratio_max, max(new_rec.removal_cap_ratio, self.settings.retrieval.removal_cap_ratio + 0.15)), 4)
        new_rec.reason_codes = list(dict.fromkeys([*new_rec.reason_codes, f"DRIFT_TIGHTEN_{drift_rep.overall_severity.upper()}"]))
        new_rec.used_static_fallback = False
        return new_rec

    def _record_failure(self, code: str, detail: str, fail_safe_events: list[str]) -> None:
        fail_safe_events.append(code)
        self.failure_events.append({"code": code, "detail": detail})
        LOGGER.warning("Adaptive fail-safe triggered: %s (%s)", code, detail)
        if self.policy_engine is not None:
            self.policy_engine.rollback_to_static_baseline(reason=f"{code}: {detail}")

    def _validate_recommendation_or_fallback(
        self,
        rec: ThresholdRecommendation,
        fail_safe_events: list[str],
    ) -> ThresholdRecommendation:
        b = self.adaptive_config.threshold_bounds
        vals = (
            rec.g1_flag_threshold,
            rec.g1_block_threshold,
            rec.g2_trust_threshold,
            rec.g2_poison_threshold,
            rec.removal_cap_ratio,
        )
        invalid = (
            not all(math.isfinite(v) for v in vals)
            or rec.g1_flag_threshold >= rec.g1_block_threshold
            or rec.g2_poison_threshold >= rec.g2_trust_threshold
            or not (b.g1_flag_min <= rec.g1_flag_threshold <= b.g1_flag_max)
            or not (b.g1_block_min <= rec.g1_block_threshold <= b.g1_block_max)
            or not (b.g2_trust_min <= rec.g2_trust_threshold <= b.g2_trust_max)
            or not (b.g2_poison_min <= rec.g2_poison_threshold <= b.g2_poison_max)
            or not (b.removal_cap_ratio_min <= rec.removal_cap_ratio <= b.removal_cap_ratio_max)
            or rec.g1_flag_threshold > self.settings.guardrails.flag_threshold
            or rec.g1_block_threshold > self.settings.guardrails.block_threshold
            or rec.g2_poison_threshold < self.settings.msd.poison_threshold
            or rec.removal_cap_ratio < self.settings.retrieval.removal_cap_ratio
        )
        if invalid:
            self._record_failure(
                "FAIL_SAFE_INVALID_THRESHOLD_RECOMMENDATION",
                f"Rejected unsafe recommendation {vals}; restored static baseline",
                fail_safe_events,
            )
            return self.selector.static_recommendation("FAIL_SAFE_STATIC_RESTORED")
        return rec

    def evaluate_query(
        self,
        query: str,
        documents: Sequence[EvidenceDocument],
        *,
        top_k: int = 5,
    ) -> AdaptiveRunOutcome:
        """Execute G1 + Retrieval + G2 (optional calibration/context/drift) + Generator + G3 with fail-safe."""
        fail_safe_events: list[str] = []
        adapt_t0 = time.perf_counter()

        active_cal = (
            self.calibrator
            if (self.adaptive_config.mode != AdaptiveMode.DISABLED and self.adaptive_config.enable_calibration)
            else None
        )
        if active_cal is not None and not active_cal.is_active:
            self._record_failure(
                "FAIL_SAFE_CORRUPT_CALIBRATOR",
                "Calibrator inactive or checksum corrupted; reverting to static raw scores",
                fail_safe_events,
            )
            active_cal = None

        latest_drift: DriftReport | None = None
        if (
            self.adaptive_config.mode != AdaptiveMode.DISABLED
            and self.adaptive_config.enable_drift_monitoring
            and self.drift_monitor is not None
        ):
            try:
                latest_drift = self.drift_monitor.evaluate_window(f"{self.variant_name}-pre")
            except Exception as exc:
                self._record_failure("FAIL_SAFE_DRIFT_ERROR", str(exc), fail_safe_events)
                latest_drift = None

        base_rec = self.selector.static_recommendation("INITIAL_BASELINE")
        pre_rec = self._validate_recommendation_or_fallback(
            self._apply_drift_tightening(base_rec, latest_drift),
            fail_safe_events,
        )

        g1_cfg = self.settings.guardrails.model_copy(deep=True)
        g1_cfg.flag_threshold = pre_rec.g1_flag_threshold
        g1_cfg.block_threshold = pre_rec.g1_block_threshold
        g1_pre = InputGuardrail(config=g1_cfg).evaluate(query)

        base_retriever = self._get_or_build_base_retriever(documents)

        if (
            self.adaptive_config.mode != AdaptiveMode.DISABLED
            and self.adaptive_config.enable_context_thresholding
            and g1_pre.decision.value != "BLOCK"
        ):
            try:
                pre_ret = base_retriever.retrieve_trusted(g1_pre.normalized_input, top_k=top_k)
                cand_docs_for_ctx = list(pre_ret.trusted_documents) + list(pre_ret.removed_documents)
                ctx = extract_context_features(
                    query,
                    cand_docs_for_ctx or list(documents)[:top_k],
                    g1_assessment=g1_pre,
                    assessments=pre_ret.assessments,
                )
                rec = self.selector.select_thresholds(ctx)
            except Exception as exc:
                self._record_failure("FAIL_SAFE_THRESHOLD_SELECTOR_ERROR", str(exc), fail_safe_events)
                rec = base_rec
        else:
            rec = base_rec

        rec = self._validate_recommendation_or_fallback(
            self._apply_drift_tightening(rec, latest_drift),
            fail_safe_events,
        )

        # Enforce adaptation timeout budget: if exceeded, restore static baseline immediately
        adapt_elapsed = time.perf_counter() - adapt_t0
        if (
            self.adaptive_config.mode != AdaptiveMode.DISABLED
            and adapt_elapsed > self.adaptive_config.adaptation_timeout_seconds
        ):
            self._record_failure(
                "FAIL_SAFE_ADAPTATION_TIMEOUT",
                f"Adaptive selection exceeded {self.adaptive_config.adaptation_timeout_seconds:.4f}s ({adapt_elapsed:.4f}s)",
                fail_safe_events,
            )
            rec = self.selector.static_recommendation("FAIL_SAFE_TIMEOUT_STATIC")
            active_cal = None

        # Build adapted Settings snapshot (never mutates self.settings)
        adapted = self.settings.model_copy(deep=True)
        adapted.guardrails.flag_threshold = rec.g1_flag_threshold
        adapted.guardrails.block_threshold = rec.g1_block_threshold
        adapted.msd.trust_threshold = rec.g2_trust_threshold
        adapted.msd.poison_threshold = rec.g2_poison_threshold
        adapted.retrieval.removal_cap_ratio = rec.removal_cap_ratio
        adapted.retrieval.trust_weight = rec.trust_weight

        detector = MultiSignalDetector(config=adapted.msd, calibrator=active_cal)
        retriever = self._clone_indexed_retriever(
            base_retriever,
            retrieval_config=adapted.retrieval,
            msd_config=adapted.msd,
            detector=detector,
        )
        pipe = TrustRAGPipeline(settings=adapted, retriever=retriever)
        resp = pipe.run(query, top_k=top_k)

        diag = resp.get_diagnostics(authorized=True) if hasattr(resp, "get_diagnostics") else {}
        assessments = list(diag.get("raw_g2_assessments") or (resp.trust_report.g2_assessments if resp.trust_report else []))
        g3_verdict = (
            resp.trust_report.g3_verification.verdict.value
            if resp.trust_report and resp.trust_report.g3_verification and resp.trust_report.g3_verification.verdict
            else None
        )

        if self.drift_monitor is not None and assessments:
            try:
                self.drift_monitor.record_batch(
                    TelemetryRecord.from_pipeline_step(
                        assessments=assessments,
                        retained_docs=resp.evidence,
                        requested_top_k=top_k,
                        g3_report=resp.trust_report.g3_verification if resp.trust_report else None,
                    )
                )
            except Exception as exc:
                self._record_failure("FAIL_SAFE_TELEMETRY_RECORD_ERROR", str(exc), fail_safe_events)

        return AdaptiveRunOutcome(
            variant_name=self.variant_name,
            query=query,
            g1_assessment=resp.trust_report.g1_assessment,
            threshold_recommendation=rec,
            drift_report=latest_drift,
            assessments=assessments,
            retained_documents=list(resp.evidence),
            removed_documents=list(diag.get("quarantined_evidence", [])),
            abstained=resp.abstained,
            blocked_by_guardrail=resp.blocked_by_guardrail,
            answer=resp.answer,
            g3_verdict=g3_verdict,
            fail_safe_events=fail_safe_events,
        )


__all__ = [
    "AdaptiveDefenseController",
    "AdaptiveRunOutcome",
]
