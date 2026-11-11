"""Pydantic schemas for TrustRAG Phase 04 standardized evaluation and benchmarking."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class ExperimentConfig(BaseModel):
    """Standardized configuration for a reproducible TrustRAG evaluation experiment."""

    experiment_name: str
    dataset_name: str
    split: str = "test"
    dataset_dir: str | None = None
    model_name: str = "tfidf-heuristic-extractive"
    backend: str = "local_deterministic"
    random_seed: int = 42
    top_k: int = 5
    limit: int | None = None
    is_synthetic: bool = False
    parameters: dict[str, Any] = Field(default_factory=dict)

    def deterministic_id(self) -> str:
        """Compute a deterministic short identifier from the experiment config."""
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10]
        return f"{self.experiment_name}_{self.dataset_name}_{self.split}_{digest}"


class SampleOutcome(BaseModel):
    """Per-example execution outcome preserving failures and latency."""

    sample_id: str
    status: str  # "success", "failed", "skipped", "invalid"
    latency_ms: float = 0.0
    prediction: Any = None
    ground_truth: Any = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class ErrorRecord(BaseModel):
    """Recorded execution or validation error."""

    sample_id: str
    error_type: str
    message: str


class ExperimentResult(BaseModel):
    """Full traceable record of an executed evaluation experiment."""

    experiment_id: str
    experiment_name: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat().replace("+00:00", "Z")
    )
    dataset: str
    split: str
    dataset_path: str
    dataset_manifest_checksum: str | None = None
    partition_file_sha256: str | None = None
    is_synthetic: bool = False
    model: str
    backend: str
    configuration: dict[str, Any] = Field(default_factory=dict)
    random_seed: int = 42
    total_examples: int = 0
    successful_examples: int = 0
    failed_examples: int = 0
    skipped_examples: int = 0
    invalid_examples: int = 0
    metrics: dict[str, Any] = Field(default_factory=dict)
    execution_time_seconds: float = 0.0
    errors: list[ErrorRecord] = Field(default_factory=list)
    sample_outcomes: list[SampleOutcome] = Field(default_factory=list)


__all__ = [
    "ErrorRecord",
    "ExperimentConfig",
    "ExperimentResult",
    "SampleOutcome",
]
