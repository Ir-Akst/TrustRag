"""Small Reasoning Model (SRM) integration inspired by HalluGuard."""

from .backends import (
    BaseSRMBackend,
    DeterministicFallbackBackend,
    LocalOllamaBackend,
    OpenAICompatibleAPIBackend,
)
from .client import SRMClient

__all__ = [
    "BaseSRMBackend",
    "LocalOllamaBackend",
    "OpenAICompatibleAPIBackend",
    "DeterministicFallbackBackend",
    "SRMClient",
]

