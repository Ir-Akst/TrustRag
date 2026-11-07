# src/trustrag/config/__init__.py
"""Configuration package for TrustRAG.

Provides a function to load the full configuration hierarchy from YAML files
and environment variables using Pydantic Settings.
"""

from .settings import Settings, load_config

__all__ = ["Settings", "load_config"]

