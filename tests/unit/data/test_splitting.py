"""Unit tests for leakage-resistant dataset splitting and leakage audits."""

import pytest

from trustrag.data.exceptions import SplitError
from trustrag.data.schemas import DocumentRecord, SecurityRecord
from trustrag.data.splitting import (
    LeakageResistantSplitter,
    SplitConfig,
    SplitStatistics,
)


def test_split_reproducibility():
    records = [
        DocumentRecord(document_id=f"doc_{i}", text=f"Document text number {i}", source_dataset="test")
        for i in range(20)
    ]

    config_1 = SplitConfig(seed=42)
    splits_1, stats_1 = LeakageResistantSplitter.split(records, config=config_1)

    config_2 = SplitConfig(seed=42)
    splits_2, stats_2 = LeakageResistantSplitter.split(records, config=config_2)

    # Identical seed must produce identical record order
    ids_train_1 = [r.document_id for r in splits_1["train"]]
    ids_train_2 = [r.document_id for r in splits_2["train"]]
    assert ids_train_1 == ids_train_2

    # Different seed should produce different partition
    config_diff = SplitConfig(seed=999)
    splits_diff, _ = LeakageResistantSplitter.split(records, config=config_diff)
    ids_train_diff = [r.document_id for r in splits_diff["train"]]
    assert ids_train_1 != ids_train_diff


def test_grouped_splitting_prevents_leakage():
    # Create 5 groups of records (each group has 2 records sharing source_id)
    records = []
    for g in range(10):
        # Clean passage
        records.append(
            SecurityRecord(
                record_id=f"sec_clean_{g}",
                passage=f"Clean text for group {g}",
                clean_poison_label="CLEAN",
                source_id=f"group_{g}",
                source_dataset="custom_security",
            )
        )
        # Poisoned passage for same group
        records.append(
            SecurityRecord(
                record_id=f"sec_poison_{g}",
                passage=f"Poisoned text for group {g}",
                clean_poison_label="POISONED",
                source_id=f"group_{g}",
                source_dataset="custom_security",
            )
        )

    config = SplitConfig(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, seed=42)
    splits, stats = LeakageResistantSplitter.split(records, config=config, dataset_name="custom_security")

    assert stats.leakage_detected is False
    assert stats.group_overlap_train_val == 0
    assert stats.group_overlap_train_test == 0
    assert stats.group_overlap_val_test == 0

    # Verify that clean and poisoned variants of group_g are in the SAME split
    train_ids = {r.record_id for r in splits["train"]}
    val_ids = {r.record_id for r in splits["val"]}
    test_ids = {r.record_id for r in splits["test"]}

    for g in range(10):
        clean_id = f"sec_clean_{g}"
        poison_id = f"sec_poison_{g}"

        clean_in_train = clean_id in train_ids
        poison_in_train = poison_id in train_ids
        assert clean_in_train == poison_in_train, f"Group {g} clean/poison split across train boundary!"

        clean_in_val = clean_id in val_ids
        poison_in_val = poison_id in val_ids
        assert clean_in_val == poison_in_val, f"Group {g} clean/poison split across val boundary!"

        clean_in_test = clean_id in test_ids
        poison_in_test = poison_id in test_ids
        assert clean_in_test == poison_in_test, f"Group {g} clean/poison split across test boundary!"


def test_split_ratios_validation():
    with pytest.raises(ValueError, match="must sum to 1.0"):
        SplitConfig(train_ratio=0.8, val_ratio=0.3, test_ratio=0.1)


def test_empty_split_handling():
    splits, stats = LeakageResistantSplitter.split([])
    assert len(splits["train"]) == 0
    assert stats.total_records == 0

