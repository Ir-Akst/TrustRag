"""Unit tests for dataset registry and adapter orchestration."""

import pytest

from trustrag.data.exceptions import AcquisitionError
from trustrag.data.registry import (
    get_adapter_class,
    get_dataset_metadata,
    list_datasets,
    load_dataset,
)


EXPECTED_DATASETS = [
    "natural_questions",
    "hotpotqa",
    "ms_marco",
    "squad",
    "boolq",
    "halueval",
    "ragtruth",
    "llm_aggrefact",
    "wice",
    "expertqa",
    "rsb",
    "custom_security",
    "fineweb",
]


def test_registry_contains_all_13_datasets():
    datasets = list_datasets()
    assert len(datasets) == 13
    for ds in EXPECTED_DATASETS:
        assert ds in datasets


def test_get_adapter_class_and_metadata():
    for ds in EXPECTED_DATASETS:
        adapter_cls = get_adapter_class(ds)
        assert adapter_cls is not None

        meta = get_dataset_metadata(ds)
        assert meta.name == ds
        assert meta.category in ["rag_qa", "hallucination", "security", "training_corpus"]
        assert meta.license is not None
        assert meta.source_uri is not None
        assert meta.access_type in ["open", "gated", "local_only", "pending_verification"]


def test_unknown_dataset_raises():
    with pytest.raises(AcquisitionError, match="not registered"):
        get_adapter_class("non_existent_dataset")

    with pytest.raises(AcquisitionError, match="not registered"):
        get_dataset_metadata("non_existent_dataset")

    with pytest.raises(AcquisitionError, match="not registered"):
        list(load_dataset("non_existent_dataset"))

