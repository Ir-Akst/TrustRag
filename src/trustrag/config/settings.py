# src/trustrag/config/settings.py
"""Configuration models for TrustRAG.

This module defines a hierarchical configuration using Pydantic Settings. The base
configuration loads defaults from ``configs/base.yaml`` and allows overrides via
environment variables. Individual sections (e.g., ``DatasetConfig``) can be
extended later.
"""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationConfig(BaseModel):
    """Top‑level application configuration.

    Attributes:
        env: Runtime environment (development, staging, production).
        log_level: Logging verbosity.
        random_seed: Seed for reproducibility.
    """

    env: str = Field(default="development", description="Runtime environment")
    log_level: str = Field(default="INFO", description="Logging level")
    random_seed: int = Field(default=42, description="Global random seed")


class LLMProviderConfig(BaseModel):
    """Configuration for LLM providers (API keys, endpoints, defaults)."""

    default_provider: str = Field(default="openai", description="Default LLM provider")
    default_model: str | None = Field(default=None, description="Default model name")
    openai_api_key: str | None = Field(default=None)
    gemini_api_key: str | None = Field(default=None)
    anthropic_api_key: str | None = Field(default=None)
    local_provider: str = Field(default="ollama")
    local_base_url: str = Field(default="http://localhost:11434")


class Settings(BaseSettings):
    """Root settings combining all configuration sections.

    Precedence (highest to lowest):
    1. Environment variables prefixed with ``TRUSTRAG_``.
    2. Values from ``configs/base.yaml``.
    3. Model defaults.
    """

    model_config = SettingsConfigDict(env_prefix="TRUSTRAG_")

    app: ApplicationConfig = Field(default_factory=ApplicationConfig)
    llm: LLMProviderConfig = Field(default_factory=LLMProviderConfig)

    @classmethod
    def _load_yaml(cls) -> Dict[str, Any]:
        config_path = Path(__file__).resolve().parents[2] / "configs" / "base.yaml"
        if not config_path.is_file():
            return {}
        with config_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def __init__(self, **data: Any):
        yaml_data = self._load_yaml()
        merged: Dict[str, Any] = {"app": yaml_data.get("app", {}), "llm": yaml_data.get("llm", {})}
        merged.update(data)
        super().__init__(**merged)

    def dict(self, *args, **kwargs):  # pragma: no cover – convenience wrapper
        return super().model_dump(*args, **kwargs)

