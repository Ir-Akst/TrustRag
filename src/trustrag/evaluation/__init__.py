"""TrustRAG Phase 04 evaluation infrastructure."""

from trustrag.evaluation.loader import (
    SCHEMA_BY_BENCHMARK,
    LoadedPartition,
    load_evaluation_partition,
)
from trustrag.evaluation.metrics import (
    bootstrap_confidence_interval,
    compute_binary_classification_metrics,
    compute_multiclass_metrics,
    mcnemar_test,
    paired_effect_comparison,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    summarize_distribution,
    wilson_confidence_interval,
)
from trustrag.evaluation.runner import EvaluationRunner
from trustrag.evaluation.schemas import (
    ErrorRecord,
    ExperimentConfig,
    ExperimentResult,
    SampleOutcome,
)

__all__ = [
    "SCHEMA_BY_BENCHMARK",
    "ErrorRecord",
    "EvaluationRunner",
    "ExperimentConfig",
    "ExperimentResult",
    "LoadedPartition",
    "SampleOutcome",
    "bootstrap_confidence_interval",
    "compute_binary_classification_metrics",
    "compute_multiclass_metrics",
    "load_evaluation_partition",
    "mcnemar_test",
    "paired_effect_comparison",
    "precision_at_k",
    "recall_at_k",
    "reciprocal_rank",
    "summarize_distribution",
    "wilson_confidence_interval",
]
