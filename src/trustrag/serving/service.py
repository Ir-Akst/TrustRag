"""Thread-safe production runtime service for TrustRAG Phase 06."""

from __future__ import annotations

import json
import logging
try:
    import resource
except ImportError:
    resource = None  # type: ignore[assignment]
import threading
import time
import uuid
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
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
from trustrag.engine.schemas import EvidenceDocument, SRMBackendHealth
from trustrag.srm.client import SRMClient

LOGGER = logging.getLogger(__name__)


class ProductionQueryRequest(BaseModel):
    """Schema-validated incoming inference request."""

    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    query: str = Field(min_length=1, max_length=8192)
    top_k: int = Field(default=5, ge=1, le=20)
    request_timeout_seconds: float | None = Field(default=None, gt=0.0)


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
    initialized: bool = True
    shut_down: bool = False
    corpus_documents: int = Field(ge=0)
    adaptive_mode: str
    calibration_active: bool
    calibration_version: str | None = None
    srm_backend: str
    srm_health: SRMBackendHealth | None = None
    total_requests: int = Field(ge=0)
    blocked_requests: int = Field(ge=0)
    abstained_requests: int = Field(ge=0)
    fail_safe_fallbacks: int = Field(ge=0)
    error_requests: int = Field(default=0, ge=0)
    timeout_requests: int = Field(default=0, ge=0)
    peak_rss_mib: float | None = None


class TrustRAGService:
    """Concurrency-safe serving facade around AdaptiveDefenseController and TrustRAG."""

    def __init__(
        self,
        documents: Sequence[EvidenceDocument],
        *,
        settings: Settings | None = None,
        adaptive_config: AdaptiveConfig | None = None,
        calibrator_path: str | Path | None = None,
        srm_client: SRMClient | None = None,
        default_timeout_seconds: float | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self.settings = (settings or load_config()).model_copy(deep=True)
        self.adaptive_config = (
            adaptive_config.model_copy(deep=True)
            if adaptive_config is not None
            else AdaptiveConfig(mode=AdaptiveMode.DISABLED)
        )
        self.default_timeout_seconds = default_timeout_seconds
        self._srm_client = srm_client or SRMClient(
            config=self.settings.srm,
            llm_config=self.settings.llm,
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

        self._initialized = True
        self._shut_down = False
        self._total_requests = 0
        self._blocked_requests = 0
        self._abstained_requests = 0
        self._fail_safe_fallbacks = 0
        self._error_requests = 0
        self._timeout_requests = 0

    def initialize(self) -> ServiceHealthStatus:
        """Explicitly initialize backend resources and transition service to ready state."""
        with self._lock:
            self._srm_client.initialize()
            self._shut_down = False
            self._initialized = True
            return self.health()

    def shutdown(self) -> None:
        """Gracefully release SRM backend resources and reject subsequent inference requests."""
        with self._lock:
            self._shut_down = True
            self._initialized = False
            self._srm_client.shutdown()

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

    def _error_response(
        self,
        req: ProductionQueryRequest,
        *,
        start_time: float,
        g1_decision: str,
        answer: str,
        fail_safe_event: str,
    ) -> ProductionQueryResponse:
        return ProductionQueryResponse(
            request_id=req.request_id,
            status="ERROR",
            answer=answer,
            safe_to_display=False,
            abstained=True,
            blocked_by_guardrail=False,
            g1_decision=g1_decision,
            g3_verdict=None,
            retained_doc_ids=[],
            latency_ms=round((time.perf_counter() - start_time) * 1000.0, 4),
            adaptive_mode=self.adaptive_config.mode.value,
            threshold_reasons=[],
            fail_safe_events=[fail_safe_event],
        )

    def _execute_query_locked(self, req: ProductionQueryRequest) -> Any:
        with self._lock:
            if self._shut_down:
                raise RuntimeError("SERVICE_SHUTDOWN")
            return self._controller.evaluate_query(
                req.query,
                self._documents,
                top_k=req.top_k,
            )

    def handle_query(self, request: ProductionQueryRequest | dict[str, Any]) -> ProductionQueryResponse:
        """Execute validated inference request with timeout enforcement and failure isolation."""
        req = (
            request
            if isinstance(request, ProductionQueryRequest)
            else ProductionQueryRequest.model_validate(request)
        )
        t0 = time.perf_counter()

        with self._lock:
            self._total_requests += 1
            if self._shut_down:
                self._error_requests += 1
                self._abstained_requests += 1
                return self._error_response(
                    req,
                    start_time=t0,
                    g1_decision="SERVICE_SHUTDOWN",
                    answer="Service has shut down and cannot process requests.",
                    fail_safe_event="SERVICE_SHUTDOWN",
                )

        effective_timeout = (
            req.request_timeout_seconds
            if req.request_timeout_seconds is not None
            else self.default_timeout_seconds
        )

        outcome: Any = None
        if effective_timeout is not None:
            pool = ThreadPoolExecutor(max_workers=1)
            future = pool.submit(self._execute_query_locked, req)
            try:
                outcome = future.result(timeout=effective_timeout)
            except FuturesTimeoutError:
                with self._lock:
                    self._timeout_requests += 1
                    self._error_requests += 1
                    self._abstained_requests += 1
                    self._fail_safe_fallbacks += 1
                return self._error_response(
                    req,
                    start_time=t0,
                    g1_decision="TIMEOUT",
                    answer="Request timed out safely prior to answer release.",
                    fail_safe_event="REQUEST_TIMEOUT",
                )
            except Exception as exc:
                LOGGER.warning("TrustRAGService request failed safely: %s", exc)
                with self._lock:
                    self._error_requests += 1
                    self._abstained_requests += 1
                    self._fail_safe_fallbacks += 1
                return self._error_response(
                    req,
                    start_time=t0,
                    g1_decision="ERROR",
                    answer="Internal service error: abstaining safely.",
                    fail_safe_event=f"INTERNAL_ERROR:{type(exc).__name__}",
                )
            finally:
                pool.shutdown(wait=False, cancel_futures=True)
        else:
            try:
                outcome = self._execute_query_locked(req)
            except Exception as exc:
                LOGGER.warning("TrustRAGService request failed safely: %s", exc)
                with self._lock:
                    self._error_requests += 1
                    self._abstained_requests += 1
                    self._fail_safe_fallbacks += 1
                return self._error_response(
                    req,
                    start_time=t0,
                    g1_decision="ERROR",
                    answer="Internal service error: abstaining safely.",
                    fail_safe_event=f"INTERNAL_ERROR:{type(exc).__name__}",
                )

        with self._lock:
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
        """Return structured liveness, readiness, SRM health, memory, and request counters."""
        with self._lock:
            srm_health = self._srm_client.health_check()
            ready = (not self._shut_down) and self._initialized and (len(self._documents) > 0)
            cal_ok = bool(self._calibrator is not None and self._calibrator.is_active)
            cal_ver = (
                self._calibrator.artifact.version
                if self._calibrator is not None and self._calibrator.artifact is not None
                else None
            )
            srm_degraded = (
                self.settings.srm.enabled
                and self.settings.srm.backend != "disabled"
                and not srm_health.available
            )
            state: Literal["healthy", "degraded", "not_ready"] = (
                "not_ready"
                if not ready
                else ("degraded" if (self._fail_safe_fallbacks > 0 or srm_degraded) else "healthy")
            )
            try:
                peak_rss_mib = (
                    round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 3)
                    if resource is not None
                    else None
                )
            except Exception:
                peak_rss_mib = None
            return ServiceHealthStatus(
                status=state,
                ready=ready,
                initialized=self._initialized,
                shut_down=self._shut_down,
                corpus_documents=len(self._documents),
                adaptive_mode=self.adaptive_config.mode.value,
                calibration_active=cal_ok,
                calibration_version=cal_ver,
                srm_backend=self.settings.srm.backend,
                srm_health=srm_health,
                total_requests=self._total_requests,
                blocked_requests=self._blocked_requests,
                abstained_requests=self._abstained_requests,
                fail_safe_fallbacks=self._fail_safe_fallbacks,
                error_requests=self._error_requests,
                timeout_requests=self._timeout_requests,
                peak_rss_mib=peak_rss_mib,
            )


__all__ = [
    "ProductionQueryRequest",
    "ProductionQueryResponse",
    "ServiceHealthStatus",
    "TrustRAGService",
]

