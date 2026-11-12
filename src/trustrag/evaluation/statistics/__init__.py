"""Statistical validation helpers for TrustRAG Phase 10."""

from trustrag.evaluation.statistics.validation import (
    StatisticalComparison,
    compare_paired_outcomes,
    holm_bonferroni,
    mcnemar_test,
    paired_bootstrap_ci,
    paired_cohens_d,
    wilson_confidence_interval,
)

__all__ = [
    "StatisticalComparison",
    "compare_paired_outcomes",
    "holm_bonferroni",
    "mcnemar_test",
    "paired_bootstrap_ci",
    "paired_cohens_d",
    "wilson_confidence_interval",
]
