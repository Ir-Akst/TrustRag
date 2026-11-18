"""Unit and Integration Tests for Track 2, Step 3.4.1 Binary Training Runner.

Tests all runner modules WITHOUT running actual model training or allocating optimizer state:
- Dataset schema validation
- Label mapping & serialization
- Deterministic sampling (source-stratified & sequential)
- Leakage rejection & test-set access prohibition
- Active watchdog abort triggers (RAM, swap growth, swap free min, timeout)
- Evaluation metric arithmetic & confusion matrix calculations
- Atomic checkpoint creation and safety against overwriting pretrained weights
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.training.train_binary_classifier import (
    LABEL_MAP,
    MANDATORY_FIELDS,
    REVERSE_LABEL_MAP,
    ResourceAbortError,
    SecurityViolationError,
    TimeoutAbortError,
    TrainingConfig,
    WatchdogMonitor,
    compute_binary_metrics,
    load_binary_dataset,
    save_checkpoint_atomic,
    serialize_binary_input,
    validate_dataset_record,
    verify_split_isolation,
)


# --- 1. Schema Validation Tests ---


def test_validate_dataset_record_valid():
    valid_rec = {
        "example_id": "bin_001",
        "question_or_claim": "Is this factual?",
        "context_or_evidence": "Evidence context here.",
        "candidate_response": "Yes it is.",
        "binary_label": "FACTUAL",
    }
    validate_dataset_record(valid_rec)  # should not raise


def test_validate_dataset_record_missing_field():
    invalid_rec = {
        "example_id": "bin_002",
        "question_or_claim": "Question only",
        "context_or_evidence": "Context only",
        # missing candidate_response
        "binary_label": "FACTUAL",
    }
    with pytest.raises(ValueError, match="missing mandatory fields"):
        validate_dataset_record(invalid_rec)


def test_validate_dataset_record_invalid_label():
    invalid_rec = {
        "example_id": "bin_003",
        "question_or_claim": "Question",
        "context_or_evidence": "Context",
        "candidate_response": "Response",
        "binary_label": "NEUTRAL",  # Invalid for binary
    }
    with pytest.raises(ValueError, match="invalid label 'NEUTRAL'"):
        validate_dataset_record(invalid_rec)


def test_validate_dataset_record_rejects_test_split():
    test_rec = {
        "example_id": "bin_004",
        "question_or_claim": "Question",
        "context_or_evidence": "Context",
        "candidate_response": "Response",
        "binary_label": "FACTUAL",
        "split": "test",
    }
    with pytest.raises(SecurityViolationError, match="Access to test record prohibited"):
        validate_dataset_record(test_rec)


# --- 2. Input Serialization & Label Mapping Tests ---


def test_label_mapping():
    assert LABEL_MAP["FACTUAL"] == 0
    assert LABEL_MAP["HALLUCINATED"] == 1
    assert REVERSE_LABEL_MAP[0] == "FACTUAL"
    assert REVERSE_LABEL_MAP[1] == "HALLUCINATED"


def test_serialize_binary_input():
    rec = {
        "question_or_claim": "Did X happen?",
        "context_or_evidence": "X happened in 1999.",
        "candidate_response": "Yes, in 1999.",
    }
    text_a, text_b = serialize_binary_input(rec)
    assert text_a == "Did X happen? X happened in 1999."
    assert text_b == "Yes, in 1999."
    # Ensure premise/hypothesis keys are not required
    assert "premise" not in rec
    assert "hypothesis" not in rec


# --- 3. Deterministic Sampling Tests ---


@pytest.fixture
def dummy_dataset_file(tmp_path):
    file_path = tmp_path / "train_dummy.jsonl"
    records = []
    # 10 halueval (5 FACTUAL, 5 HALLUCINATED)
    for i in range(5):
        records.append({
            "example_id": f"halu_f_{i}",
            "question_or_claim": f"Q {i}",
            "context_or_evidence": f"C {i}",
            "candidate_response": f"R {i}",
            "binary_label": "FACTUAL",
            "source_dataset": "halueval",
        })
        records.append({
            "example_id": f"halu_h_{i}",
            "question_or_claim": f"Q {i}",
            "context_or_evidence": f"C {i}",
            "candidate_response": f"R {i}",
            "binary_label": "HALLUCINATED",
            "source_dataset": "halueval",
        })
    # 10 ragtruth (5 FACTUAL, 5 HALLUCINATED)
    for i in range(5):
        records.append({
            "example_id": f"rag_f_{i}",
            "question_or_claim": f"Q {i}",
            "context_or_evidence": f"C {i}",
            "candidate_response": f"R {i}",
            "binary_label": "FACTUAL",
            "source_dataset": "ragtruth",
        })
        records.append({
            "example_id": f"rag_h_{i}",
            "question_or_claim": f"Q {i}",
            "context_or_evidence": f"C {i}",
            "candidate_response": f"R {i}",
            "binary_label": "HALLUCINATED",
            "source_dataset": "ragtruth",
        })

    with open(file_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return file_path


def test_stratified_sampling(dummy_dataset_file):
    subset = load_binary_dataset(dummy_dataset_file, max_samples=8, strategy="stratified_source_balanced")
    assert len(subset) == 8

    halu_records = [r for r in subset if r["source_dataset"] == "halueval"]
    rag_records = [r for r in subset if r["source_dataset"] == "ragtruth"]
    assert len(halu_records) == 4
    assert len(rag_records) == 4

    factuals = [r for r in subset if r["binary_label"] == "FACTUAL"]
    hallucinated = [r for r in subset if r["binary_label"] == "HALLUCINATED"]
    assert len(factuals) == 4
    assert len(hallucinated) == 4


def test_sequential_sampling(dummy_dataset_file):
    subset = load_binary_dataset(dummy_dataset_file, max_samples=4, strategy="sequential")
    assert len(subset) == 4
    assert [r["example_id"] for r in subset] == ["halu_f_0", "halu_h_0", "halu_f_1", "halu_h_1"]


def test_load_dataset_rejects_test_file(tmp_path):
    test_file = tmp_path / "test_set.jsonl"
    test_file.touch()
    with pytest.raises(SecurityViolationError, match="prohibited"):
        load_binary_dataset(test_file, max_samples=10)


# --- 4. Split Isolation and Leakage Rejection ---


def test_verify_split_isolation_clean():
    train = [{"example_id": "tr_1"}, {"example_id": "tr_2"}]
    val = [{"example_id": "val_1"}, {"example_id": "val_2"}]
    verify_split_isolation(train, val)  # should not raise


def test_verify_split_isolation_leakage():
    train = [{"example_id": "shared_01"}, {"example_id": "tr_2"}]
    val = [{"example_id": "shared_01"}, {"example_id": "val_2"}]
    with pytest.raises(SecurityViolationError, match="DATA LEAKAGE"):
        verify_split_isolation(train, val)


# --- 5. Active Watchdog Safeguard Tests ---


def test_watchdog_normal_operation():
    mock_telemetry = {
        "rss_mb": 500.0,
        "available_ram_mb": 4000.0,
        "swap_total_mb": 6000.0,
        "swap_used_mb": 2000.0,
        "swap_free_mb": 4000.0,
    }
    watchdog = WatchdogMonitor(
        ram_abort_threshold_mb=700.0,
        swap_growth_abort_mb=500.0,
        swap_free_min_mb=1000.0,
        max_duration_seconds=1800.0,
        telemetry_fn=lambda: dict(mock_telemetry),
    )
    res = watchdog.check(step=1)
    assert res["available_ram_mb"] == 4000.0
    assert res["swap_growth_mb"] == 0.0


def test_watchdog_abort_on_low_ram():
    mock_telemetry = {
        "rss_mb": 2500.0,
        "available_ram_mb": 650.0,  # Below 700 MB
        "swap_total_mb": 6000.0,
        "swap_used_mb": 2000.0,
        "swap_free_mb": 4000.0,
    }
    watchdog = WatchdogMonitor(
        ram_abort_threshold_mb=700.0,
        swap_growth_abort_mb=500.0,
        swap_free_min_mb=1000.0,
        max_duration_seconds=1800.0,
        telemetry_fn=lambda: dict(mock_telemetry),
    )
    with pytest.raises(ResourceAbortError, match="Available host RAM dropped to 650.0 MB"):
        watchdog.check(step=10)


def test_watchdog_abort_on_swap_growth():
    initial_telemetry = {
        "rss_mb": 1000.0,
        "available_ram_mb": 3000.0,
        "swap_total_mb": 6000.0,
        "swap_used_mb": 2000.0,
        "swap_free_mb": 4000.0,
    }
    state = dict(initial_telemetry)
    watchdog = WatchdogMonitor(
        ram_abort_threshold_mb=700.0,
        swap_growth_abort_mb=500.0,
        swap_free_min_mb=1000.0,
        max_duration_seconds=1800.0,
        telemetry_fn=lambda: state,
    )
    # Simulate swap growth of 600 MB
    state["swap_used_mb"] = 2600.0
    with pytest.raises(ResourceAbortError, match="Swap usage grew by 600.0 MB"):
        watchdog.check(step=15)


def test_watchdog_abort_on_low_free_swap():
    mock_telemetry = {
        "rss_mb": 1000.0,
        "available_ram_mb": 3000.0,
        "swap_total_mb": 6000.0,
        "swap_used_mb": 5100.0,
        "swap_free_mb": 900.0,  # Below 1000 MB min
    }
    watchdog = WatchdogMonitor(
        ram_abort_threshold_mb=700.0,
        swap_growth_abort_mb=500.0,
        swap_free_min_mb=1000.0,
        max_duration_seconds=1800.0,
        telemetry_fn=lambda: dict(mock_telemetry),
    )
    with pytest.raises(ResourceAbortError, match="Free swap dropped to 900.0 MB"):
        watchdog.check(step=20)


def test_watchdog_abort_on_timeout():
    mock_telemetry = {
        "rss_mb": 1000.0,
        "available_ram_mb": 3000.0,
        "swap_total_mb": 6000.0,
        "swap_used_mb": 2000.0,
        "swap_free_mb": 4000.0,
    }
    watchdog = WatchdogMonitor(
        ram_abort_threshold_mb=700.0,
        swap_growth_abort_mb=500.0,
        swap_free_min_mb=1000.0,
        max_duration_seconds=0.01,  # extremely short timeout
        telemetry_fn=lambda: dict(mock_telemetry),
    )
    import time

    time.sleep(0.02)
    with pytest.raises(TimeoutAbortError, match="exceeded hard cutoff"):
        watchdog.check(step=25)


# --- 6. Metric Calculations & Confusion Matrix Tests ---


def test_compute_binary_metrics_perfect():
    # 5 Factual (0), 5 Hallucinated (1) - 100% correct
    y_true = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    y_pred = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    m = compute_binary_metrics(y_true, y_pred, loss=0.1)
    assert m["accuracy"] == 1.0
    assert m["balanced_accuracy"] == 1.0
    assert m["macro_f1"] == 1.0
    assert m["confusion_matrix"] == {
        "true_positives": 5,
        "true_negatives": 5,
        "false_positives": 0,
        "false_negatives": 0,
    }


def test_compute_binary_metrics_imperfect():
    # TP=3, FN=2 (true 1s: 5)
    # TN=4, FP=1 (true 0s: 5)
    y_true = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    y_pred = [1, 1, 1, 0, 0, 0, 0, 0, 0, 1]
    m = compute_binary_metrics(y_true, y_pred, loss=0.5)
    assert m["accuracy"] == 0.7
    # Sensitivity = 3/5 = 0.6, Specificity = 4/5 = 0.8 -> Balanced Acc = 0.7
    assert m["balanced_accuracy"] == pytest.approx(0.7)
    assert m["confusion_matrix"]["true_positives"] == 3
    assert m["confusion_matrix"]["true_negatives"] == 4
    assert m["confusion_matrix"]["false_positives"] == 1
    assert m["confusion_matrix"]["false_negatives"] == 2


# --- 7. Atomic Checkpoint & Directory Protection Tests ---


def test_save_checkpoint_atomic_success(tmp_path):
    output_dir = tmp_path / "trained_model"
    pretrained_dir = tmp_path / "pretrained_model"
    pretrained_dir.mkdir()

    mock_model = MagicMock()
    mock_tokenizer = MagicMock()

    saved_path = save_checkpoint_atomic(
        model=mock_model,
        tokenizer=mock_tokenizer,
        output_dir=output_dir,
        step=1000,
        metrics={"acc": 0.85},
        pretrained_model_dir=pretrained_dir,
    )

    assert saved_path == output_dir.resolve()
    assert output_dir.exists()
    assert (output_dir / "training_meta.json").exists()
    mock_model.save_pretrained.assert_called_once()
    mock_tokenizer.save_pretrained.assert_called_once()


def test_save_checkpoint_rejects_overwriting_pretrained(tmp_path):
    pretrained_dir = tmp_path / "pretrained_model"
    pretrained_dir.mkdir()

    mock_model = MagicMock()
    mock_tokenizer = MagicMock()

    with pytest.raises(SecurityViolationError, match="cannot overwrite pretrained model directory"):
        save_checkpoint_atomic(
            model=mock_model,
            tokenizer=mock_tokenizer,
            output_dir=pretrained_dir,  # Attempting to overwrite pretrained
            step=1000,
            metrics={},
            pretrained_model_dir=pretrained_dir,
        )

