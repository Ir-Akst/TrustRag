"""Client wrapper orchestrating SRM backend selection, timeout handling, fallback, and audit logging."""

from __future__ import annotations

from typing import Optional

from trustrag.config.engine_config import SRMConfig
from trustrag.config.settings import LLMProviderConfig
from trustrag.engine.schemas import SRMExecutionStatus, SRMRequest, SRMResponse
from trustrag.exceptions import ModelError, ProviderError
from trustrag.srm.backends import (
    BaseSRMBackend,
    DeterministicFallbackBackend,
    LocalOllamaBackend,
    OpenAICompatibleAPIBackend,
)
from trustrag.utils.logging import get_logger

LOGGER = get_logger(__name__)


class SRMClient:
    """HalluGuard-inspired Small Reasoning Model client with deterministic fallback."""

    def __init__(
        self,
        config: Optional[SRMConfig] = None,
        llm_config: Optional[LLMProviderConfig] = None,
        backend: Optional[BaseSRMBackend] = None,
    ) -> None:
        self.config = config or SRMConfig()
        self.llm_config = llm_config or LLMProviderConfig()
        self._fallback = DeterministicFallbackBackend(model_name=self.config.model_name)
        self._backend: BaseSRMBackend = backend or self._select_backend()

    def _select_backend(self) -> BaseSRMBackend:
        if not self.config.enabled or self.config.backend == "disabled":
            return self._fallback
        if self.config.backend == "local_ollama":
            return LocalOllamaBackend(self.config, self.llm_config)
        if self.config.backend == "openai_compatible":
            return OpenAICompatibleAPIBackend(self.config, self.llm_config)
        raise ProviderError(f"Unsupported SRM backend: '{self.config.backend}'")

    def _log_execution(self, response: SRMResponse) -> None:
        LOGGER.info(
            "SRM reasoning execution finished",
            extra={
                "model_name": response.model_name,
                "backend": response.backend_used,
                "execution_status": response.execution_status.value,
                "is_fallback": response.is_fallback,
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
        """Execute SRM reasoning with automatic timeout/unavailable handling and logging."""
        if not self.config.enabled or (self.config.backend == "disabled" and isinstance(self._backend, DeterministicFallbackBackend)):
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


__all__ = ["SRMClient"]

