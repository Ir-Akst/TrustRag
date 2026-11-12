"""Pluggable SRM backend registry separating backend instantiation from SRMClient."""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

from trustrag.config.engine_config import SRMConfig
from trustrag.config.settings import LLMProviderConfig
from trustrag.exceptions import ProviderError
from trustrag.srm.backends import (
    BaseSRMBackend,
    DeterministicFallbackBackend,
    LocalOllamaBackend,
    OpenAICompatibleAPIBackend,
)
from trustrag.srm.hf_local import HuggingFaceLocalSRMBackend

BackendBuilder = Callable[[SRMConfig, LLMProviderConfig], BaseSRMBackend]


class SRMBackendRegistry:
    """Thread-safe factory registry for HalluGuard-inspired SRM backends."""

    _builders: ClassVar[dict[str, BackendBuilder]] = {
        "disabled": lambda srm_cfg, _llm_cfg: DeterministicFallbackBackend(model_name=srm_cfg.model_name),
        "local_ollama": lambda srm_cfg, llm_cfg: LocalOllamaBackend(srm_cfg, llm_cfg),
        "openai_compatible": lambda srm_cfg, llm_cfg: OpenAICompatibleAPIBackend(srm_cfg, llm_cfg),
        "hf_local": lambda srm_cfg, llm_cfg: HuggingFaceLocalSRMBackend(srm_cfg, llm_cfg),
    }

    @classmethod
    def register(cls, name: str, builder: BackendBuilder) -> None:
        """Register or override a named SRM backend factory."""
        key = name.strip().lower()
        if not key:
            raise ProviderError("SRM backend name must be non-empty.")
        cls._builders[key] = builder

    @classmethod
    def list_backends(cls) -> list[str]:
        """Return registered SRM backend names."""
        return sorted(cls._builders.keys())

    @classmethod
    def create(
        cls,
        srm_config: SRMConfig,
        llm_config: LLMProviderConfig | None = None,
    ) -> BaseSRMBackend:
        """Instantiate an SRM backend strictly from explicit configuration."""
        if not srm_config.enabled or srm_config.backend == "disabled":
            return DeterministicFallbackBackend(model_name=srm_config.model_name)
        key = srm_config.backend.strip().lower()
        builder = cls._builders.get(key)
        if builder is None:
            raise ProviderError(
                f"Unsupported SRM backend '{srm_config.backend}'. Registered: {cls.list_backends()}"
            )
        return builder(srm_config, llm_config or LLMProviderConfig())


__all__ = ["BackendBuilder", "SRMBackendRegistry"]
