"""Thread-safe production runtime service for TrustRAG Phase 06."""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from trustrag.adaptive import (
    AdaptationPolicyEngine,
    AdaptiveConfig,
    AdaptiveDefenseController,
    AdaptiveMode,
    DriftMonitor,
    EvidenceQualityMonitor,
    TrustCalibrator,
)
from trustrag.config import Settings, load_config
from trustrag.engine.schemas import EvidenceDocument

LOGGER = logging.getLogger(__name__)


class ProductionQueryRequest(BaseModel):
    """Schema-validated incoming inference request."""

    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    query: str = Field(min_length=1, max_length=8192)
    top_k: int = Field(default=5, ge=1, le=20)


class ProductionQueryResponse(BaseModel):
    """Public-safe production response payload (quarantined content redacted)."""

    request_id: str
    status: Literal["OK", "ABSTAINED", "BLOCKED", "ERROR"]
    answer: str
    safe_to_display: bool
    abstained: bool
    blocked_by_guardrail: bool
    g1_decision: str
    g3_verdict: str | None = None
    retained_doc_ids: list[str] = Field(default_factory=list)
    latency_ms: float = Field(ge=0.0)
    adaptive_mode: str
    threshold_reasons: list[str] = Field(default_factory=list)
    fail_safe_events: list[str] = Field(default_factory=list)


class ServiceHealthStatus(BaseModel):
    """Structured liveness and readiness status report."""

    status: Literal["healthy", "degraded", "not_ready"]
    ready: bool
    corpus_documents: int = Field(ge=0)
    adaptive_mode: str
    calibration_active: bool
    calibration_version: str | None = None
    srm_backend: str
    total_requests: int = Field(ge=0)
    blocked_requests: int = Field(ge=0)
    abstained_requests: int = Field(ge=0)
    fail_safe_fallbacks: int = Field(ge=0)


class TrustRAGService:
    """Concurrency-safe serving facade around AdaptiveDefenseController and TrustRAG."""

    def __init__(
        self,
        documents: Sequence[EvidenceDocument],
        *,
        settings: Settings | None = None,
        adaptive_config: AdaptiveConfig | None = None,
        calibrator_path: str | Path | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self.settings = (settings or load_config()).model_copy(deep=True)
        self.adaptive_config = (
            adaptive_config.model_copy(deep=True)
            if adaptive_config is not None
            else AdaptiveConfig(mode=AdaptiveMode.DISABLED)
        )
        self._documents = list(documents)
        self._calibrator: TrustCalibrator | None = None
        if calibrator_path is not None:
            try:
                self._calibrator = TrustCalibrator.load_json(calibrator_path)
            except Exception as exc:
                LOGGER.warning("Calibrator load failed safely; falling back to uncalibrated: %s", exc)
                self._calibrator = None

        self._drift_monitor = (
            DriftMonitor(
                window_size=self.adaptive_config.drift_window_size,
                min_samples=self.adaptive_config.drift_min_samples,
            )
            if self.adaptive_config.enable_drift_monitoring
            else None
        )
        self._feedback_monitor = (
            EvidenceQualityMonitor() if self.adaptive_config.enable_feedback_monitoring else None
        )
        self._policy_engine = (
            AdaptationPolicyEngine(
                baseline_settings=self.settings,
                bounds=self.adaptive_config.threshold_bounds,
                min_monitoring_confidence=self.adaptive_config.min_monitoring_confidence,
                calibration_version=(
                    self._calibrator.artifact.version
                    if self._calibrator and self._calibrator.artifact
                    else None
                ),
            )
            if self.adaptive_config.enable_policy_engine
            else None
        )
        self._controller = AdaptiveDefenseController(
            settings=self.settings,
            adaptive_config=self.adaptive_config,
            calibrator=self._calibrator,
            drift_monitor=self._drift_monitor,
            policy_engine=self._policy_engine,
            variant_name="service",
        )
        # Warm retriever TF-IDF index cleanly at startup
        if self._documents:
            self._controller._get_or_build_base_retriever(self._documents)

        self._total_requests = 0
        self._blocked_requests = 0
        self._abstained_requests = 0
        self._fail_safe_fallbacks = 0

    @classmethod
    def from_jsonl(
        cls,
        file_path: str | Path,
        *,
        limit: int = 200,
        adaptive: bool = False,
        calibrator_path: str | Path | None = None,
        settings: Settings | None = None,
    ) -> TrustRAGService:
        """Load indexed evidence corpus from JSONL safely."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Corpus JSONL file not found: {path}")
        docs: list[EvidenceDocument] = []
        with path.open("r", encoding="utf-8") as fh:
            for idx, line in enumerate(fh):
                if limit and len(docs) >= limit:
                    break
                if not line.strip():
                    continue
                rec = json.loads(line)
                doc = EvidenceDocument.from_record(rec, idx=idx)
                if doc is not None:
                    docs.append(doc)
        acfg = (
            AdaptiveConfig(
                mode=AdaptiveMode.ENFORCED,
                enable_calibration=calibrator_path is not None,
                enable_context_thresholding=True,
                enable_drift_monitoring=True,
                enable_feedback_monitoring=True,
                enable_policy_engine=True,
            )
            if adaptive
            else AdaptiveConfig(mode=AdaptiveMode.DISABLED)
        )
        return cls(
            docs,
            settings=settings,
            adaptive_config=acfg,
            calibrator_path=calibrator_path,
        )

    def handle_query(self, request: ProductionQueryRequest | dict[str, Any]) -> ProductionQueryResponse:
        """Execute validated inference request under thread-safe lock with strict public sanitization."""
        req = (
            request
            if isinstance(request, ProductionQueryRequest)
            else ProductionQueryRequest.model_validate(request)
        )
        t0 = time.perf_counter()
        with self._lock:
            outcome = self._controller.evaluate_query(
                req.query,
                self._documents,
                top_k=req.top_k,
            )
            self._total_requests += 1
            if outcome.blocked_by_guardrail:
                self._blocked_requests += 1
            if outcome.abstained:
                self._abstained_requests += 1
            if outcome.fail_safe_events:
                self._fail_safe_fallbacks += 1

        lat_ms = round((time.perf_counter() - t0) * 1000.0, 4)
        status: Literal["OK", "ABSTAINED", "BLOCKED"] = (
            "BLOCKED"
            if outcome.blocked_by_guardrail
            else ("ABSTAINED" if outcome.abstained else "OK")
        )
        return ProductionQueryResponse(
            request_id=req.request_id,
            status=status,
            answer=outcome.answer,
            safe_to_display=(not outcome.blocked_by_guardrail),
            abstained=outcome.abstained,
            blocked_by_guardrail=outcome.blocked_by_guardrail,
            g1_decision=outcome.g1_assessment.decision.value,
            g3_verdict=outcome.g3_verdict,
            retained_doc_ids=[d.doc_id for d in outcome.retained_documents],
            latency_ms=lat_ms,
            adaptive_mode=self.adaptive_config.mode.value,
            threshold_reasons=list(outcome.threshold_recommendation.reason_codes),
            fail_safe_events=list(outcome.fail_safe_events),
        )

    def health(self) -> ServiceHealthStatus:
        """Return structured liveness, readiness, calibration integrity, and counters."""
        with self._lock:
            ready = len(self._documents) > 0
            cal_ok = bool(self._calibrator is not None and self._calibrator.is_active)
            cal_ver = (
                self._calibrator.artifact.version
                if self._calibrator is not None and self._calibrator.artifact is not None
                else None
            )
            state: Literal["healthy", "degraded", "not_ready"] = (
                "not_ready"
                if not ready
                else ("degraded" if self._fail_safe_fallbacks > 0 else "healthy")
            )
            return ServiceHealthStatus(
                status=state,
                ready=ready,
                corpus_documents=len(self._documents),
                adaptive_mode=self.adaptive_config.mode.value,
                calibration_active=cal_ok,
                calibration_version=cal_ver,
                srm_backend=self.settings.srm.backend,
                total_requests=self._total_requests,
                blocked_requests=self._blocked_requests,
                abstained_requests=self._abstained_requests,
                fail_safe_fallbacks=self._fail_safe_fallbacks,
            )


__all__ = [
    "ProductionQueryRequest",
    "ProductionQueryResponse",
    "ServiceHealthStatus",
    "TrustRAGService",
]

