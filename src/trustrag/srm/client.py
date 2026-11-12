"""Client wrapper orchestrating SRM backend selection, lifecycle, timeout handling, fallback, and audit logging."""

from __future__ import annotations

from collections.abc import Sequence

from trustrag.config.engine_config import SRMConfig
from trustrag.config.settings import LLMProviderConfig
from trustrag.engine.schemas import (
    SRMBackendHealth,
    SRMClaimJudgment,
    SRMExecutionStatus,
    SRMRequest,
    SRMResponse,
)
from trustrag.exceptions import ModelError, ProviderError
from trustrag.srm.backends import (
    BaseSRMBackend,
    DeterministicFallbackBackend,
)
from trustrag.srm.registry import SRMBackendRegistry
from trustrag.utils.logging import get_logger

LOGGER = get_logger(__name__)


class SRMClient:
    """HalluGuard-inspired Small Reasoning Model client with explicit fallback & lifecycle controls."""

    def __init__(
        self,
        config: SRMConfig | None = None,
        llm_config: LLMProviderConfig | None = None,
        backend: BaseSRMBackend | None = None,
    ) -> None:
        self.config = config or SRMConfig()
        self.llm_config = llm_config or LLMProviderConfig()
        self._fallback = DeterministicFallbackBackend(model_name=self.config.model_name)
        self._backend: BaseSRMBackend = backend or self._select_backend()

    def _select_backend(self) -> BaseSRMBackend:
        return SRMBackendRegistry.create(self.config, self.llm_config)

    @property
    def backend(self) -> BaseSRMBackend:
        """Expose active backend instance for inspection or resource management."""
        return self._backend

    def initialize(self) -> SRMBackendHealth:
        """Explicitly initialize the selected SRM backend and report health status."""
        self._backend.initialize()
        return self.health_check()

    def shutdown(self) -> None:
        """Gracefully unload or release active SRM backend resources."""
        self._backend.shutdown()

    def health_check(self) -> SRMBackendHealth:
        """Return explicit backend health report (never hides fallback status)."""
        if not self.config.enabled or (
            self.config.backend == "disabled" and isinstance(self._backend, DeterministicFallbackBackend)
        ):
            return self._fallback.health_check()
        return self._backend.health_check()

    def _log_execution(self, response: SRMResponse) -> None:
        LOGGER.info(
            "SRM reasoning execution finished",
            extra={
                "model_name": response.model_name,
                "backend": response.backend_used,
                "execution_status": response.execution_status.value,
                "is_fallback": response.is_fallback,
                "inference_mode": response.inference_mode,
                "srm_config": {
                    "enabled": self.config.enabled,
                    "configured_backend": self.config.backend,
                    "timeout_seconds": self.config.timeout_seconds,
                    "temperature": self.config.temperature,
                    "fallback_on_error": self.config.fallback_on_error,
                },
            },
        )

    def reason(self, request: SRMRequest) -> SRMResponse:
        """Execute SRM reasoning with explicit fallback control and structured audit logging."""
        if not self.config.enabled or (
            self.config.backend == "disabled" and isinstance(self._backend, DeterministicFallbackBackend)
        ):
            resp = self._fallback.invoke(
                request,
                status=SRMExecutionStatus.DISABLED,
                error_detail="SRM remote/local model backend disabled; deterministic fallback executed.",
            )
            self._log_execution(resp)
            return resp

        if isinstance(self._backend, DeterministicFallbackBackend):
            resp = self._backend.invoke(request, status=SRMExecutionStatus.FALLBACK)
            self._log_execution(resp)
            return resp

        try:
            resp = self._backend.invoke(request)
            self._log_execution(resp)
            return resp
        except TimeoutError as exc:
            if not self.config.fallback_on_error:
                raise
            resp = self._fallback.invoke(
                request,
                status=SRMExecutionStatus.TIMEOUT,
                error_detail=str(exc),
            )
            self._log_execution(resp)
            return resp
        except (ProviderError, ModelError, Exception) as exc:
            if not self.config.fallback_on_error:
                raise
            resp = self._fallback.invoke(
                request,
                status=SRMExecutionStatus.UNAVAILABLE,
                error_detail=str(exc),
            )
            self._log_execution(resp)
            return resp

    def reason_batch(self, requests: Sequence[SRMRequest]) -> list[SRMResponse]:
        """Execute bounded-batch reasoning across requests using configured batch_size."""
        max_bs = max(1, self.config.batch_size)
        out: list[SRMResponse] = []
        for idx in range(0, len(requests), max_bs):
            for req in requests[idx : idx + max_bs]:
                out.append(self.reason(req))
        return out

    def verify_claims(self, request: SRMRequest) -> list[SRMClaimJudgment]:
        """Verify claim judgments for a structured request."""
        return self.reason(request).claim_judgments

    def classify_evidence(
        self,
        query: str,
        evidence_passages: Sequence[dict[str, str]],
        candidate_answer: str,
    ) -> SRMResponse:
        """Execute evidence-grounded classification blind to upstream G3 rule hints."""
        return self.reason(
            SRMRequest(
                query=query,
                candidate_answer=candidate_answer,
                evidence_passages=list(evidence_passages),
                blind_to_g3_heuristics=True,
            )
        )


__all__ = ["SRMClient"]
