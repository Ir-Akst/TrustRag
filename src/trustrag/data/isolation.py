"""Dataset usage categorization and isolation controls for TrustRAG.

Enforces strict compliance with dataset licensing and usage boundaries:
- Prevents evaluation-only benchmarks (e.g. LLM-AggreFact, RSB) from leaking into training workflows.
- Prevents training corpora (e.g. FineWeb) from being used as evaluation benchmarks.
- Validates workflow usage against verified dataset permissions.
"""

from __future__ import annotations

from enum import Enum
from typing import Set, Union

from .exceptions import UsageIsolationError, ValidationError


class DatasetUsageCategory(str, Enum):
    """Explicit workflow usage categories for TrustRAG datasets."""

    TRAINING = "TRAINING"
    VALIDATION = "VALIDATION"
    EVALUATION = "EVALUATION"
    TRAINING_CORPUS = "TRAINING_CORPUS"
    SECURITY_BENCHMARK = "SECURITY_BENCHMARK"


# Categories that involve model training, fine-tuning, or synthetic prompt injection
TRAINING_USAGE_CATEGORIES: Set[DatasetUsageCategory] = {
    DatasetUsageCategory.TRAINING,
    DatasetUsageCategory.TRAINING_CORPUS,
}

# Categories for benchmarking, evaluation, and guardrail validation
EVALUATION_USAGE_CATEGORIES: Set[DatasetUsageCategory] = {
    DatasetUsageCategory.VALIDATION,
    DatasetUsageCategory.EVALUATION,
    DatasetUsageCategory.SECURITY_BENCHMARK,
}


class DatasetUsageValidator:
    """Enforces training and evaluation isolation rules."""

    @classmethod
    def validate_usage(
        cls,
        dataset_or_metadata: Union[DatasetMetadata, str],
        requested_usage: Union[DatasetUsageCategory, str],
    ) -> None:
        """Validate whether a dataset is permitted for the requested workflow usage.

        Raises
        ------
        UsageIsolationError
            If the requested usage violates dataset licensing, terms of use, or category constraints.
        ValidationError
            If the requested usage category is unrecognized.
        """
        if isinstance(dataset_or_metadata, str):
            from .registry import get_dataset_metadata
            try:
                metadata = get_dataset_metadata(dataset_or_metadata.lower())
            except Exception:
                # Minimal mock metadata for unknown or ad-hoc strings
                metadata = DatasetMetadata(
                    name=dataset_or_metadata,
                    category="unknown",
                    permitted_for_training=True,
                    permitted_for_evaluation=True,
                )
        else:
            metadata = dataset_or_metadata

        if isinstance(requested_usage, str):
            try:
                usage = DatasetUsageCategory(requested_usage.upper())
            except ValueError:
                raise ValidationError(
                    f"Unknown dataset usage category '{requested_usage}'. "
                    f"Allowed: {[c.value for c in DatasetUsageCategory]}"
                )
        else:
            usage = requested_usage

        # 1. Enforce Training Prohibition
        if usage in TRAINING_USAGE_CATEGORIES:
            if not metadata.permitted_for_training:
                reason = metadata.known_limitations or "Dataset terms explicitly prohibit training."
                raise UsageIsolationError(
                    f"PROHIBITED WORKFLOW: Dataset '{metadata.name}' is prohibited from training workflows "
                    f"({usage.value}). License/Terms restriction: {reason}"
                )

        # 2. Enforce Evaluation Prohibition
        if usage in EVALUATION_USAGE_CATEGORIES:
            if not metadata.permitted_for_evaluation:
                raise UsageIsolationError(
                    f"PROHIBITED WORKFLOW: Dataset '{metadata.name}' cannot be used in "
                    f"evaluation workflows ({usage.value}). It is designated as a {metadata.category}."
                )

        # 3. FineWeb specific guard: must remain training corpus only
        if metadata.name.lower() == "fineweb":
            if usage in EVALUATION_USAGE_CATEGORIES:
                raise UsageIsolationError(
                    "PROHIBITED WORKFLOW: FineWeb is exclusively a pre-training corpus source "
                    "and must not be used as an evaluation benchmark."
                )

        # 4. LLM-AggreFact specific guard: strictly evaluation only
        if metadata.name.lower() == "llm_aggrefact" and usage in TRAINING_USAGE_CATEGORIES:
            raise UsageIsolationError(
                "LICENSE VIOLATION: LLM-AggreFact (CC-BY-ND-4.0) strictly prohibits use "
                "in pretraining or fine-tuning any NLP models. It is prohibited from training workflows."
            )

        # 5. RSB specific guard: security evaluation benchmark only
        if metadata.name.lower() == "rsb" and usage in TRAINING_USAGE_CATEGORIES:
            raise UsageIsolationError(
                "PROHIBITED WORKFLOW: RSB is a security attack evaluation benchmark and "
                "is prohibited from training workflows."
            )


__all__ = [
    "DatasetUsageCategory",
    "TRAINING_USAGE_CATEGORIES",
    "EVALUATION_USAGE_CATEGORIES",
    "DatasetUsageValidator",
]
