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
    """Top-level application configuration.

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


from .dataset_config import DatasetRootConfig


class SectionConfig(BaseModel):
    """Generic section configuration placeholder."""
    pass


class Settings(BaseSettings):
    """Root settings combining all configuration sections.

    Precedence (highest to lowest):
    1. Explicit data passed to __init__
    2. Environment variables prefixed with ``TRUSTRAG_``.
    3. Values from ``configs/base.yaml`` and ``configs/datasets.yaml``.
    4. Model defaults.
    """

    model_config = SettingsConfigDict(env_prefix="TRUSTRAG_", env_nested_delimiter="_")

    app: ApplicationConfig = Field(default_factory=ApplicationConfig)
    llm: LLMProviderConfig = Field(default_factory=LLMProviderConfig)
    dataset: DatasetRootConfig = Field(default_factory=DatasetRootConfig)
    retrieval: SectionConfig = Field(default_factory=SectionConfig)
    generation: SectionConfig = Field(default_factory=SectionConfig)
    msd: SectionConfig = Field(default_factory=SectionConfig)
    guardrails: SectionConfig = Field(default_factory=SectionConfig)
    experiments: SectionConfig = Field(default_factory=SectionConfig)

    @classmethod
    def _load_yaml(cls) -> Dict[str, Any]:
        config_path = Path(__file__).resolve().parents[3] / "configs" / "base.yaml"
        if not config_path.is_file():
            # Try alternate lookup
            config_path = Path(__file__).resolve().parents[2] / "configs" / "base.yaml"
        data: Dict[str, Any] = {}
        if config_path.is_file():
            with config_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        # Load datasets.yaml if available
        ds_path = config_path.parent / "datasets.yaml"
        if ds_path.is_file():
            with ds_path.open("r", encoding="utf-8") as f:
                ds_data = yaml.safe_load(f) or {}
                if "dataset" in ds_data:
                    data["dataset"] = ds_data["dataset"]
                else:
                    data["dataset"] = ds_data
        return data

    def __init__(self, **data: Any):
        yaml_data = self._load_yaml()
        merged: Dict[str, Any] = {}
        for section in ("app", "llm", "dataset", "retrieval", "generation", "msd", "guardrails", "experiments"):
            if section in yaml_data and isinstance(yaml_data[section], dict):
                merged[section] = dict(yaml_data[section])

        # Environment variable overrides (TRUSTRAG_<SECTION>_<FIELD>)
        prefix = "TRUSTRAG_"
        for k, v in os.environ.items():
            if k.startswith(prefix):
                rest = k[len(prefix):]
                parts = rest.split("_", 1)
                if len(parts) == 2:
                    section = parts[0].lower()
                    field_name = parts[1].lower()
                    if section in ("app", "llm", "dataset", "retrieval", "generation", "msd", "guardrails", "experiments"):
                        if section not in merged:
                            merged[section] = {}
                        merged[section][field_name] = v

        # Explicit overrides take highest precedence
        for k, v in data.items():
            if isinstance(v, dict) and k in merged and isinstance(merged[k], dict):
                merged[k].update(v)
            else:
                merged[k] = v

        super().__init__(**merged)

    def dict(self, *args, **kwargs):  # pragma: no cover – convenience wrapper
        return super().model_dump(*args, **kwargs)


def load_config(**overrides: Any) -> Settings:
    """Load configuration settings with optional overrides."""
    return Settings(**overrides)
