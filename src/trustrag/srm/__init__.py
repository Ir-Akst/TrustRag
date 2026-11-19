"""Small Reasoning Model (SRM) integration inspired by HalluGuard."""

from .backends import (
    BaseSRMBackend,
    DeterministicFallbackBackend,
    LocalOllamaBackend,
    OpenAICompatibleAPIBackend,
)
from .client import SRMClient
from .hf_local import HuggingFaceLocalSRMBackend
from .neural_nli import NeuralNLISRMBackend
from .registry import BackendBuilder, SRMBackendRegistry

__all__ = [
    "BackendBuilder",
    "BaseSRMBackend",
    "DeterministicFallbackBackend",
    "HuggingFaceLocalSRMBackend",
    "LocalOllamaBackend",
    "NeuralNLISRMBackend",
    "OpenAICompatibleAPIBackend",
    "SRMBackendRegistry",
    "SRMClient",
]
