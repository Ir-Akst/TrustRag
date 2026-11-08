"""Pydantic configuration models for TrustRAG datasets.

Loads settings from ``configs/datasets.yaml`` and supports environment overrides.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field, model_validator


class PreprocessingConfig(BaseModel):
    """Preprocessing and text cleaning settings."""

    unicode_normalization: str = Field(default="NFKC")
    collapse_whitespace: bool = Field(default=True)
    preserve_punctuation: bool = Field(default=True)
    deduplicate: bool = Field(default=True)


class SplittingConfig(BaseModel):
    """Dataset splitting parameters."""

    train_ratio: float = Field(default=0.70, ge=0.0, le=1.0)
    val_ratio: float = Field(default=0.15, ge=0.0, le=1.0)
    test_ratio: float = Field(default=0.15, ge=0.0, le=1.0)
    seed: int = Field(default=42)
    group_key: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def validate_ratios(self) -> SplittingConfig:
        total = round(self.train_ratio + self.val_ratio + self.test_ratio, 5)
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"Splitting ratios must sum to 1.0, got {total}")
        return self


class DatasetEntryConfig(BaseModel):
    """Configuration for a specific dataset."""

    name: str
    enabled: bool = Field(default=True)
    source_uri: str
    split: str = Field(default="train")
    limit: Optional[int] = Field(default=None)
    smoke_test_limit: int = Field(default=100)
    config_name: Optional[str] = Field(default=None)
    local_path: Optional[str] = Field(default=None)
    offline: bool = Field(default=False)
    description: Optional[str] = Field(default=None)


class DatasetRootConfig(BaseModel):
    """Top-level dataset configuration tree."""

    smoke_test: bool = Field(default=False, description="Enable smoke test mode with small limits")
    default_cache_dir: str = Field(default="data/raw")
    default_output_dir: str = Field(default="data/processed")
    manifest_dir: str = Field(default="data/manifests")
    offline_mode: bool = Field(default=False)
    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig)
    splitting: SplittingConfig = Field(default_factory=SplittingConfig)
    datasets: Dict[str, DatasetEntryConfig] = Field(default_factory=dict)

    @classmethod
    def load_from_yaml(cls, path: Optional[Union[str, Path]] = None) -> DatasetRootConfig:
        """Load dataset configuration from YAML file."""
        if path is None:
            # Default lookup
            candidate = Path(__file__).resolve().parents[3] / "configs" / "datasets.yaml"
            if not candidate.is_file():
                candidate = Path("configs/datasets.yaml")
            path = candidate

        path_obj = Path(path)
        if not path_obj.is_file():
            return cls()

        with path_obj.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # If data is nested under 'dataset', extract it
        if "dataset" in data and isinstance(data["dataset"], dict):
            data = data["dataset"]

        return cls.model_validate(data)

    def get_effective_limit(self, dataset_name: str) -> Optional[int]:
        """Return the effective record limit for a dataset, respecting smoke_test mode."""
        entry = self.datasets.get(dataset_name)
        if not entry:
            return 100 if self.smoke_test else None
        if self.smoke_test:
            return entry.smoke_test_limit
        return entry.limit


__all__ = [
    "PreprocessingConfig",
    "SplittingConfig",
    "DatasetEntryConfig",
    "DatasetRootConfig",
]

