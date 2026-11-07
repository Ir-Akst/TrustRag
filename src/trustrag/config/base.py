# src/trustrag/config/base.py
"""Base configuration models for TrustRAG.

Provides Pydantic Settings models that load defaults from ``configs/base.yaml``
and allow overrides via environment variables. Additional configuration sections
(e.g., ``DatasetConfig``, ``RetrievalConfig``) can be added later.
"""

from .base import Settings  # Re-export for convenience

