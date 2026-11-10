# src/trustrag/exceptions/__init__.py
"""Exception hierarchy for TrustRAG.

All custom exceptions inherit from :class:`TrustRAGError`.
"""

class TrustRAGError(Exception):
    """Base class for all TrustRAG exceptions."""
    pass

class ConfigurationError(TrustRAGError, ValueError):
    """Raised when configuration loading or validation fails."""
    pass

class DatasetError(TrustRAGError):
    """Raised for dataset‑related issues."""
    pass

class RetrievalError(TrustRAGError):
    """Raised for retrieval‑related errors."""
    pass

class ModelError(TrustRAGError):
    """Raised for model loading or inference errors."""
    pass

class ProviderError(TrustRAGError):
    """Raised when an LLM provider integration fails."""
    pass

class DetectionError(TrustRAGError):
    """Raised for multi‑signal detection problems."""
    pass

class GuardrailError(TrustRAGError):
    """Raised for input guardrail failures."""
    pass

class EvaluationError(TrustRAGError):
    """Raised for evaluation‑related errors."""
    pass

__all__ = [
    "TrustRAGError",
    "ConfigurationError",
    "DatasetError",
    "RetrievalError",
    "ModelError",
    "ProviderError",
    "DetectionError",
    "GuardrailError",
    "EvaluationError",
]

