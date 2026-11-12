"""Small Reasoning Model (SRM) integration inspired by HalluGuard."""

from .backends import (
    BaseSRMBackend,
    DeterministicFallbackBackend,
    LocalOllamaBackend,
    OpenAICompatibleAPIBackend,
)
from .client import SRMClient
from .registry import BackendBuilder, SRMBackendRegistry

__all__ = [
    "BackendBuilder",
    "BaseSRMBackend",
    "DeterministicFallbackBackend",
    "LocalOllamaBackend",
    "OpenAICompatibleAPIBackend",
    "SRMBackendRegistry",
    "SRMClient",
]
