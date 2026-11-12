"""Small Reasoning Model (SRM) integration inspired by HalluGuard."""

from .backends import (
    BaseSRMBackend,
    DeterministicFallbackBackend,
    LocalOllamaBackend,
    OpenAICompatibleAPIBackend,
)
from .client import SRMClient
from .hf_local import HuggingFaceLocalSRMBackend
from .registry import BackendBuilder, SRMBackendRegistry

__all__ = [
    "BackendBuilder",
    "BaseSRMBackend",
    "DeterministicFallbackBackend",
    "HuggingFaceLocalSRMBackend",
    "LocalOllamaBackend",
    "OpenAICompatibleAPIBackend",
    "SRMBackendRegistry",
    "SRMClient",
]
