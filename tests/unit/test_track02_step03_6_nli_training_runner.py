"""Unit and Integration Tests for Track 2, Step 3.6 NLI Training Runner.

Tests all runner modules WITHOUT running actual model training or allocating optimizer state:
- Dataset schema validation
- Label mapping & serialization
- Deterministic 3-class balanced sampling
- Leakage rejection & test-set access prohibition
- Active watchdog abort triggers (RAM, swap growth, swap free min, timeout)
- 3-class evaluation metric arithmetic & confusion matrix calculations
- Checkpoint protection and safety against overwriting pretrained or binary weights
- Authorization guard preventing unauthorized training execution
- Offline model instantiation and 3-class classification head verification
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from collections import Counter
from contextlib import contextmanager

try:
    import pytest
except ImportError:
    class MockPytest:
        @staticmethod
        @contextmanager
        def raises(expected_exc, match=None):
            try:
                yield
            except expected_exc as e:
                if match and not re.search(match, str(e)):
                    raise AssertionError(f"Pattern '{match}' does not match exception message: '{e}'")
                return
            except Exception as e:
                raise AssertionError(f"Expected {expected_exc.__name__}, got {type(e).__name__}: {e}")
            raise AssertionError(f"Expected exception {expected_exc.__name__} was not raised")

        @staticmethod
        def skip(reason):
            pass

    pytest = MockPytest()

from tools.training.train_nli_classifier import (
    MANDATORY_NLI_FIELDS,
    NLI_LABEL_MAP,
    ID_TO_NLI_LABEL,
    NLITrainingConfig,
    WatchdogMonitor,
    ResourceAbortError,
    SecurityViolationError,
    TimeoutAbortError,
    TrainingNotAuthorizedError,
    ClassStarvationError,
    validate_nli_record,
    serialize_nli_input,
    load_nli_dataset,
    check_class_starvation,
    evidence_preserving_tokenize,
    verify_split_isolation,
    compute_nli_metrics,
    save_checkpoint_atomic,
    prepare_nli_model,
    execute_training,
    parse_args,
)


# --- 1. Schema Validation Tests ---


def test_validate_nli_record_valid():
    valid_rec = {
        "example_id": "nli_001",
        "source_dataset": "ragtruth",
        "source_id": "doc_100",
        "split": "train",
        "premise": "The solar system contains eight planets.",
        "hypothesis": "Eight planets orbit the Sun.",
        "nli_label": "ENTAILMENT",
        "conflict_types": [],
        "span_count": 0,
        "source_provenance": "ragtruth_human_annotation",
    }
    validate_nli_record(valid_rec)


def test_validate_nli_record_missing_fields():
    invalid_rec = {
        "example_id": "nli_002",
        "source_dataset": "ragtruth",
        "split": "train",
    }
    with pytest.raises(ValueError, match="missing mandatory fields"):
        validate_nli_record(invalid_rec)


def test_validate_nli_record_invalid_label():
    rec = {
        "example_id": "nli_003",
        "source_dataset": "ragtruth",
        "source_id": "doc_100",
        "split": "train",
        "premise": "Context",
        "hypothesis": "Claim",
        "nli_label": "UNKNOWN_LABEL",
        "conflict_types": [],
        "span_count": 0,
        "source_provenance": "test",
    }
    with pytest.raises(ValueError, match="invalid label 'UNKNOWN_LABEL'"):
        validate_nli_record(rec)


def test_validate_nli_record_test_split_prohibited():
    rec = {
        "example_id": "nli_004",
        "source_dataset": "ragtruth",
        "source_id": "doc_100",
        "split": "test",
        "premise": "Context",
        "hypothesis": "Claim",
        "nli_label": "ENTAILMENT",
        "conflict_types": [],
        "span_count": 0,
        "source_provenance": "test",
    }
    with pytest.raises(SecurityViolationError, match="Access to test record prohibited"):
        validate_nli_record(rec)


def test_validate_nli_record_empty_premise():
    rec = {
        "example_id": "nli_005",
        "source_dataset": "ragtruth",
        "source_id": "doc_100",
        "split": "train",
        "premise": "   ",
        "hypothesis": "Claim",
        "nli_label": "ENTAILMENT",
        "conflict_types": [],
        "span_count": 0,
        "source_provenance": "test",
    }
    with pytest.raises(ValueError, match="empty premise"):
        validate_nli_record(rec)


def test_validate_nli_record_empty_hypothesis():
    rec = {
        "example_id": "nli_006",
        "source_dataset": "ragtruth",
        "source_id": "doc_100",
        "split": "train",
        "premise": "Context",
        "hypothesis": "   ",
        "nli_label": "ENTAILMENT",
        "conflict_types": [],
        "span_count": 0,
        "source_provenance": "test",
    }
    with pytest.raises(ValueError, match="empty hypothesis"):
        validate_nli_record(rec)


# --- 2. Serialization Tests ---


def test_serialize_nli_input():
    rec = {
        "premise": "  Context paragraph.  ",
        "hypothesis": "  Hypothesis statement.  ",
    }
    premise, hypothesis = serialize_nli_input(rec)
    assert premise == "Context paragraph."
    assert hypothesis == "Hypothesis statement."


# --- 3. Sampling and Dataset Loading Tests ---


def test_load_nli_dataset_class_balanced(tmp_path: Path):
    data_file = tmp_path / "nli_sample.jsonl"
    records = []
    for i in range(10):
        records.append({
            "example_id": f"ent_{i}", "source_dataset": "ragtruth", "source_id": f"d_{i}",
            "split": "train", "premise": f"P {i}", "hypothesis": f"H {i}",
            "nli_label": "ENTAILMENT", "conflict_types": [], "span_count": 0, "source_provenance": "t",
        })
        records.append({
            "example_id": f"con_{i}", "source_dataset": "ragtruth", "source_id": f"d_{i}",
            "split": "train", "premise": f"P {i}", "hypothesis": f"H {i}",
            "nli_label": "CONTRADICTION", "conflict_types": ["Evident Conflict"], "span_count": 1, "source_provenance": "t",
        })
        records.append({
            "example_id": f"neu_{i}", "source_dataset": "ragtruth", "source_id": f"d_{i}",
            "split": "train", "premise": f"P {i}", "hypothesis": f"H {i}",
            "nli_label": "NEUTRAL", "conflict_types": ["Evident Baseless Info"], "span_count": 1, "source_provenance": "t",
        })

    with open(data_file, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    loaded = load_nli_dataset(data_file, max_samples=6, strategy="stratified_class_balanced")
    assert len(loaded) == 6
    counts = Counter(r["nli_label"] for r in loaded)
    assert counts["ENTAILMENT"] == 2
    assert counts["CONTRADICTION"] == 2
    assert counts["NEUTRAL"] == 2


def test_load_nli_dataset_test_file_prohibited(tmp_path: Path):
    test_file = tmp_path / "nli_test.jsonl"
    test_file.touch()
    with pytest.raises(SecurityViolationError, match="Direct targeting of test set file is prohibited"):
        load_nli_dataset(test_file, max_samples=5)


# --- 4. Split Isolation Tests ---


def test_verify_split_isolation_clean():
    train_recs = [
        {"example_id": "t1", "premise": "Document Alpha text"},
        {"example_id": "t2", "premise": "Document Beta text"},
    ]
    val_recs = [
        {"example_id": "v1", "premise": "Document Gamma text"},
        {"example_id": "v2", "premise": "Document Delta text"},
    ]
    verify_split_isolation(train_recs, val_recs)


def test_verify_split_isolation_id_leakage():
    train_recs = [{"example_id": "shared_01", "premise": "P1"}]
    val_recs = [{"example_id": "shared_01", "premise": "P2"}]
    with pytest.raises(SecurityViolationError, match="Example ID leakage detected"):
        verify_split_isolation(train_recs, val_recs)


def test_verify_split_isolation_premise_leakage():
    train_recs = [{"example_id": "t1", "premise": "Identical document text."}]
    val_recs = [{"example_id": "v1", "premise": "Identical document text."}]
    with pytest.raises(SecurityViolationError, match="Document/premise leakage detected"):
        verify_split_isolation(train_recs, val_recs)


# --- 5. Metric Computation Tests ---


def test_compute_nli_metrics_perfect():
    y_true = [0, 1, 2, 0, 1, 2]
    y_pred = [0, 1, 2, 0, 1, 2]
    probs = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    metrics = compute_nli_metrics(y_true, y_pred, probs)
    assert metrics["accuracy"] == 1.0
    assert metrics["balanced_accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["per_class"]["ENTAILMENT"]["f1"] == 1.0
    assert metrics["per_class"]["CONTRADICTION"]["f1"] == 1.0
    assert metrics["per_class"]["NEUTRAL"]["f1"] == 1.0
    assert metrics["brier_score"] == 0.0
    assert metrics["ece_10bins"] == 0.0
    assert metrics["confusion_matrix"] == [[2, 0, 0], [0, 2, 0], [0, 0, 2]]


def test_compute_nli_metrics_imperfect():
    y_true = [0, 1, 2, 0]
    y_pred = [0, 2, 2, 0]  # 1 sample misclassified (1 -> 2)
    metrics = compute_nli_metrics(y_true, y_pred)
    assert metrics["accuracy"] == 0.75
    assert metrics["confusion_matrix"] == [[2, 0, 0], [0, 0, 1], [0, 0, 1]]


# --- 6. Watchdog Safety Tests ---


def test_watchdog_normal():
    telemetry = {
        "rss_mb": 1500.0,
        "available_ram_mb": 4000.0,
        "swap_total_mb": 6000.0,
        "swap_used_mb": 2000.0,
        "swap_free_mb": 4000.0,
    }
    wd = WatchdogMonitor(telemetry_fn=lambda: dict(telemetry))
    res = wd.check(step=1)
    assert res["rss_mb"] == 1500.0


def test_watchdog_abort_on_low_ram():
    state = {
        "rss_mb": 1500.0,
        "available_ram_mb": 4000.0,
        "swap_total_mb": 6000.0,
        "swap_used_mb": 2000.0,
        "swap_free_mb": 4000.0,
    }
    wd = WatchdogMonitor(ram_abort_threshold_mb=700.0, telemetry_fn=lambda: dict(state))
    wd.check(step=1)

    state["available_ram_mb"] = 650.0  # Drops below 700 MB
    with pytest.raises(ResourceAbortError, match="Available host RAM dropped"):
        wd.check(step=2)


def test_watchdog_abort_on_swap_growth():
    state = {
        "rss_mb": 1500.0,
        "available_ram_mb": 4000.0,
        "swap_total_mb": 6000.0,
        "swap_used_mb": 2000.0,
        "swap_free_mb": 4000.0,
    }
    wd = WatchdogMonitor(swap_growth_abort_mb=500.0, telemetry_fn=lambda: dict(state))
    wd.check(step=1)

    state["swap_used_mb"] = 2600.0  # +600 MB growth
    with pytest.raises(ResourceAbortError, match="Swap usage grew by 600.0 MB"):
        wd.check(step=2)


def test_watchdog_abort_on_timeout():
    state = {
        "rss_mb": 1500.0,
        "available_ram_mb": 4000.0,
        "swap_total_mb": 6000.0,
        "swap_used_mb": 2000.0,
        "swap_free_mb": 4000.0,
    }
    wd = WatchdogMonitor(max_duration_seconds=1.0, telemetry_fn=lambda: dict(state))
    wd.t_start = 0.0  # Force timeout
    with pytest.raises(TimeoutAbortError, match="exceeded hard cutoff"):
        wd.check(step=1)


# --- 7. Checkpoint Protection Tests ---


def test_save_checkpoint_atomic_protected_overwrite_rejection():
    mock_model = MagicMock()
    mock_tok = MagicMock()
    protected_binary = Path("/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000")
    with pytest.raises(SecurityViolationError, match="Attempted overwrite of protected path"):
        save_checkpoint_atomic(mock_model, mock_tok, protected_binary, meta={})


# --- 8. Execution Authorization Guard Tests ---


def test_execute_training_unauthorized_rejection():
    cfg = NLITrainingConfig(
        model_dir="/dummy/model",
        train_file="/dummy/train.jsonl",
        val_file="/dummy/val.jsonl",
        output_dir="/dummy/out",
        authorized=False,
    )
    with pytest.raises(TrainingNotAuthorizedError, match="NLI training execution is NOT authorized"):
        execute_training(cfg)


# --- 9. Model Architecture Preparation Test ---


def test_prepare_nli_model_architecture():
    try:
        import torch
        from transformers import AutoConfig
    except ImportError:
        pytest.skip("Torch/transformers not installed in current environment")
        return

    pretrained_path = "/home/aditya/rags/models/pretrained/deberta-v3-small"
    model, tokenizer = prepare_nli_model(pretrained_path, device="cpu")
    assert model.classifier.weight.shape == (3, 768)
    assert model.classifier.bias.shape == (3,)
    assert sum(p.numel() for p in model.parameters()) == 141897219
    for p in model.parameters():
        assert p.dtype == torch.float32


# --- 10. Remediation Step 3.10 Tests: Sampling, Starvation & Evidence Preservation ---


def test_deterministic_shuffling_reproducibility(tmp_path):
    p = tmp_path / "train.jsonl"
    lines = []
    for i in range(30):
        lbl = ["ENTAILMENT", "CONTRADICTION", "NEUTRAL"][i % 3]
        lines.append(json.dumps({
            "example_id": f"ex_{i}",
            "source_dataset": "ragtruth",
            "source_id": str(i),
            "split": "train",
            "premise": f"Premise {i}",
            "hypothesis": f"Hypothesis {i}",
            "nli_label": lbl,
            "conflict_types": [],
            "span_count": 0,
            "source_provenance": "ragtruth",
        }))
    p.write_text("\n".join(lines), encoding="utf-8")

    # Same seed -> exact identical sample ordering
    s1 = load_nli_dataset(p, 30, strategy="stratified_class_balanced", seed=42)
    s2 = load_nli_dataset(p, 30, strategy="stratified_class_balanced", seed=42)
    assert [r["example_id"] for r in s1] == [r["example_id"] for r in s2]

    # Different seed -> different sample ordering
    s3 = load_nli_dataset(p, 30, strategy="stratified_class_balanced", seed=123)
    assert [r["example_id"] for r in s1] != [r["example_id"] for r in s3]

    # All three classes present with exact quotas
    c_counts = Counter(r["nli_label"] for r in s1)
    assert c_counts["ENTAILMENT"] == 10
    assert c_counts["CONTRADICTION"] == 10
    assert c_counts["NEUTRAL"] == 10


def test_shuffled_order_breaks_sequential_tail(tmp_path):
    p = tmp_path / "train.jsonl"
    lines = []
    # 20 Entailment first, then 10 Contradiction, then 10 Neutral
    for i in range(20):
        lines.append(json.dumps({
            "example_id": f"e_{i}", "source_dataset": "ragtruth", "source_id": str(i), "split": "train",
            "premise": "P", "hypothesis": "H", "nli_label": "ENTAILMENT", "conflict_types": [], "span_count": 0, "source_provenance": "test"
        }))
    for i in range(10):
        lines.append(json.dumps({
            "example_id": f"c_{i}", "source_dataset": "ragtruth", "source_id": str(i), "split": "train",
            "premise": "P", "hypothesis": "H", "nli_label": "CONTRADICTION", "conflict_types": [], "span_count": 0, "source_provenance": "test"
        }))
    for i in range(10):
        lines.append(json.dumps({
            "example_id": f"n_{i}", "source_dataset": "ragtruth", "source_id": str(i), "split": "train",
            "premise": "P", "hypothesis": "H", "nli_label": "NEUTRAL", "conflict_types": [], "span_count": 0, "source_provenance": "test"
        }))
    p.write_text("\n".join(lines), encoding="utf-8")

    # Unshuffled: sequential order
    unshuffled = load_nli_dataset(p, 30, strategy="stratified_class_balanced", shuffle=False)
    unshuffled_labels = [r["nli_label"] for r in unshuffled]
    assert unshuffled_labels[:10] == ["ENTAILMENT"] * 10
    assert unshuffled_labels[-10:] == ["NEUTRAL"] * 10

    # Shuffled: labels are thoroughly mixed
    shuffled = load_nli_dataset(p, 30, strategy="stratified_class_balanced", seed=42, shuffle=True)
    shuffled_labels = [r["nli_label"] for r in shuffled]
    assert shuffled_labels != unshuffled_labels
    # Tail is not 100% single class
    assert len(set(shuffled_labels[-10:])) > 1


def test_class_starvation_detection_violation():
    # Construct sequence where ENTAILMENT is missing for 30 consecutive steps
    records = [{"nli_label": "CONTRADICTION"}] * 15 + [{"nli_label": "NEUTRAL"}] * 15
    with pytest.raises(ClassStarvationError, match="Class starvation violation: Class 'ENTAILMENT' absent for 30 consecutive steps"):
        check_class_starvation(records, max_starvation_threshold=25)


def test_class_starvation_clean_on_shuffled_sequence():
    records = []
    for i in range(300):
        lbl = ["ENTAILMENT", "CONTRADICTION", "NEUTRAL"][i % 3]
        records.append({"nli_label": lbl})
    res = check_class_starvation(records, max_starvation_threshold=25)
    assert res["status"] == "BALANCED_NO_STARVATION"
    assert res["max_consecutive_absences"]["ENTAILMENT"] <= 3


def test_evidence_preserving_tokenization_hypothesis_priority():
    # Mock tokenizer
    class MockTokenizer:
        cls_token_id = 1
        sep_token_id = 2

        def __call__(self, text, add_special_tokens=False):
            # 1 word ~ 1 token for mock
            words = text.split()
            return {"input_ids": [hash(w) % 1000 + 10 for w in words]}

    mock_tok = MockTokenizer()
    # Premise: 100 words. Hypothesis: 20 words.
    premise = " ".join([f"fact_{i}" for i in range(100)])
    hypothesis = " ".join([f"claim_{i}" for i in range(20)])

    res = evidence_preserving_tokenize(
        mock_tok,
        premise=premise,
        hypothesis=hypothesis,
        max_seq_len=60,
        min_premise_tokens=15,
    )
    meta = res["metadata"]
    assert meta["orig_hypothesis_tokens"] == 20
    assert meta["processed_hypothesis_tokens"] == 20
    assert meta["hypothesis_truncated"] is False
    assert meta["hypothesis_retention_rate"] == 1.0
    # Premise was truncated to fit remaining budget (60 - 3 - 20 = 37 tokens)
    assert meta["processed_premise_tokens"] == 37
    assert meta["premise_truncated"] is True


def test_evidence_preserving_tokenization_long_hypothesis_safeguard():
    class MockTokenizer:
        cls_token_id = 1
        sep_token_id = 2

        def __call__(self, text, add_special_tokens=False):
            words = text.split()
            return {"input_ids": [hash(w) % 1000 + 10 for w in words]}

    mock_tok = MockTokenizer()
    # Premise: 50 words. Hypothesis: 80 words. Total budget: 60.
    premise = " ".join([f"fact_{i}" for i in range(50)])
    hypothesis = " ".join([f"claim_{i}" for i in range(80)])

    res = evidence_preserving_tokenize(
        mock_tok,
        premise=premise,
        hypothesis=hypothesis,
        max_seq_len=60,
        min_premise_tokens=15,
    )
    meta = res["metadata"]
    # Guaranteed min_premise_tokens=15
    assert meta["processed_premise_tokens"] == 15
    # Hypothesis gets 60 - 3 - 15 = 42 tokens
    assert meta["processed_hypothesis_tokens"] == 42
    assert meta["hypothesis_truncated"] is True
    assert meta["processed_seq_len"] == 60


def test_save_checkpoint_atomic_protected_nli_pilot1000_overwrite_rejection():
    mock_model = MagicMock()
    mock_tok = MagicMock()
    protected_nli = Path("/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000")
    with pytest.raises(SecurityViolationError, match="Attempted overwrite of protected path"):
        save_checkpoint_atomic(mock_model, mock_tok, protected_nli, meta={})


# --- 7. Step 3.12 Evidence Retention & Multi-Chunk Premise Tests ---

from tools.training.nli_multi_chunk import (
    AggregationPolicy,
    ChunkAggregator,
    EvidenceSpanRetentionAuditor,
    MultiChunkNLIProcessor,
)


def test_evidence_span_retention_auditor_perfect_alignment():
    class MockOffsetTokenizer:
        def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
            # Tokenize by splitting spaces, each token is 5 chars
            words = text.split()
            ids = [i + 1 for i in range(len(words))]
            offsets = []
            curr = 0
            for w in words:
                start = text.find(w, curr)
                end = start + len(w)
                offsets.append((start, end))
                curr = end
            return {"input_ids": ids, "offset_mapping": offsets}

    tok = MockOffsetTokenizer()
    auditor = EvidenceSpanRetentionAuditor(tok)
    hypothesis = "The patient shows acute appendicitis symptoms."
    annotated_spans = [
        {"start": 18, "end": 36, "text": "acute appendicitis", "label_type": "Conflict"}
    ]

    # Full hypothesis kept (10 tokens available, hypothesis has 6 tokens)
    res = auditor.audit_record_spans(hypothesis, annotated_spans, kept_hypothesis_tokens=10)
    assert res["status"] == "MEASURED"
    assert res["total_spans"] == 1
    assert res["fully_preserved_spans"] == 1
    assert res["partially_preserved_spans"] == 0
    assert res["completely_lost_spans"] == 0
    assert res["span_retention_rate"] == 1.0
    assert res["token_retention_rate"] == 1.0


def test_evidence_span_retention_auditor_truncated_lost_and_partial():
    class MockOffsetTokenizer:
        def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
            words = text.split()
            ids = [i + 1 for i in range(len(words))]
            offsets = []
            curr = 0
            for w in words:
                start = text.find(w, curr)
                end = start + len(w)
                offsets.append((start, end))
                curr = end
            return {"input_ids": ids, "offset_mapping": offsets}

    tok = MockOffsetTokenizer()
    auditor = EvidenceSpanRetentionAuditor(tok)
    # words: The(0) patient(1) shows(2) acute(3) appendicitis(4) symptoms(5) definitely(6) today(7)
    hypothesis = "The patient shows acute appendicitis symptoms definitely today"
    annotated_spans = [
        {"start": 0, "end": 11, "text": "The patient", "label_type": "Conflict"},  # tokens 0, 1
        {"start": 18, "end": 36, "text": "acute appendicitis", "label_type": "Conflict"},  # tokens 3, 4
        {"start": 46, "end": 62, "text": "definitely today", "label_type": "Conflict"},  # tokens 6, 7
    ]

    # If only 4 tokens are kept (tokens 0, 1, 2, 3):
    # Span 1 (tokens 0, 1): fully kept (2/2) -> FULLY_PRESERVED
    # Span 2 (tokens 3, 4): partially kept (token 3 kept, 4 lost) -> PARTIALLY_PRESERVED
    # Span 3 (tokens 6, 7): completely lost (0/2) -> COMPLETELY_LOST
    res = auditor.audit_record_spans(hypothesis, annotated_spans, kept_hypothesis_tokens=4)
    assert res["status"] == "MEASURED"
    assert res["total_spans"] == 3
    assert res["fully_preserved_spans"] == 1
    assert res["partially_preserved_spans"] == 1
    assert res["completely_lost_spans"] == 1
    assert res["span_retention_rate"] == 1 / 3
    assert res["total_span_tokens"] == 6
    assert res["kept_span_tokens"] == 3
    assert res["token_retention_rate"] == 0.5


def test_evidence_span_retention_auditor_invalid_and_empty_spans():
    tok = MagicMock()
    auditor = EvidenceSpanRetentionAuditor(tok)
    empty_res = auditor.audit_record_spans("Hypothesis", [], kept_hypothesis_tokens=10)
    assert empty_res["status"] == "NOT_MEASURABLE"
    assert empty_res["total_spans"] == 0


def test_multi_chunk_processor_single_chunk_fit():
    class MockTok:
        def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
            words = text.split()
            ids = [i + 1 for i in range(len(words))]
            return {"input_ids": ids, "offset_mapping": [(0, 1)] * len(ids)}

    tok = MockTok()
    proc = MultiChunkNLIProcessor(tok, max_seq_len=128, chunk_overlap=16, min_premise_tokens=10)
    record = {
        "example_id": "test_ex_1",
        "premise": "Short premise text.",
        "hypothesis": "Short hypothesis.",
        "nli_label": "ENTAILMENT",
    }
    chunks = proc.process_example(record)
    assert len(chunks) == 1
    c0 = chunks[0]
    assert c0.metadata.example_id == "test_ex_1"
    assert c0.metadata.chunk_id == "test_ex_1_chunk_0"
    assert c0.metadata.chunk_index == 0
    assert c0.metadata.total_chunks == 1
    assert c0.metadata.is_terminal_chunk is True
    assert c0.metadata.hypothesis_truncated is False


def test_multi_chunk_processor_sliding_window_overlap():
    class MockTok:
        def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
            words = text.split()
            ids = [i + 1 for i in range(len(words))]
            offsets = []
            curr = 0
            for w in words:
                start = text.find(w, curr)
                end = start + len(w)
                offsets.append((start, end))
                curr = end
            return {"input_ids": ids, "offset_mapping": offsets}

    tok = MockTok()
    # Budget: max_seq_len=50, special=3, hyp=10 tokens -> premise budget = 37 tokens per chunk
    # Overlap = 10 tokens -> stride = 27 tokens
    proc = MultiChunkNLIProcessor(tok, max_seq_len=50, chunk_overlap=10, min_premise_tokens=10)
    premise_words = [f"word{i}" for i in range(80)]
    premise = " ".join(premise_words)
    hypothesis = " ".join([f"hyp{i}" for i in range(10)])

    record = {
        "example_id": "multi_ex_99",
        "premise": premise,
        "hypothesis": hypothesis,
        "nli_label": "CONTRADICTION",
    }
    chunks = proc.process_example(record)
    assert len(chunks) > 1
    # Check that every chunk preserves the full hypothesis
    for ch in chunks:
        assert ch.hypothesis_text == hypothesis
        assert ch.metadata.example_id == "multi_ex_99"
        assert ch.metadata.hypothesis_truncated is False
        assert ch.nli_label == "CONTRADICTION"

    # Verify sliding overlap between chunk 0 and chunk 1
    c0 = chunks[0]
    c1 = chunks[1]
    assert c0.metadata.chunk_id == "multi_ex_99_chunk_0"
    assert c1.metadata.chunk_id == "multi_ex_99_chunk_1"
    assert c1.metadata.premise_token_start < c0.metadata.premise_token_end
    # Overlap is exactly 10 tokens
    assert c0.metadata.premise_token_end - c1.metadata.premise_token_start == 10
    assert chunks[-1].metadata.is_terminal_chunk is True


def test_chunk_aggregator_contradiction_priority():
    aggregator = ChunkAggregator()
    chunk_preds = [
        {"chunk_id": "ex1_chunk_0", "predicted_label": "ENTAILMENT", "probs": [0.85, 0.05, 0.10]},
        {"chunk_id": "ex1_chunk_1", "predicted_label": "CONTRADICTION", "probs": [0.05, 0.90, 0.05]},
        {"chunk_id": "ex1_chunk_2", "predicted_label": "ENTAILMENT", "probs": [0.80, 0.10, 0.10]},
    ]
    # Under CONTRADICTION_PRIORITY, a single contradictory chunk falsifies the entire claim
    res = aggregator.aggregate("ex1", chunk_preds, policy=AggregationPolicy.CONTRADICTION_PRIORITY)
    assert res["example_id"] == "ex1"
    assert res["aggregated_label"] == "CONTRADICTION"
    assert res["confidence"] == 0.90
    assert res["conflicting_chunks_detected"] is True
    assert res["total_chunks"] == 3


def test_chunk_aggregator_insufficient_evidence_guard():
    aggregator = ChunkAggregator()
    # Low-confidence chunks where none exceeds 0.50 threshold
    chunk_preds = [
        {"chunk_id": "ex2_chunk_0", "predicted_label": "ENTAILMENT", "probs": [0.40, 0.30, 0.30]},
        {"chunk_id": "ex2_chunk_1", "predicted_label": "NEUTRAL", "probs": [0.35, 0.20, 0.45]},
    ]
    res = aggregator.aggregate(
        "ex2",
        chunk_preds,
        policy=AggregationPolicy.INSUFFICIENT_EVIDENCE_GUARD,
        uncertainty_threshold=0.50,
    )
    assert res["aggregated_label"] == "INSUFFICIENT_EVIDENCE"
    assert res["confidence"] == 0.45


def test_chunk_aggregator_average_probabilities():
    aggregator = ChunkAggregator()
    chunk_preds = [
        {"chunk_id": "ex3_chunk_0", "predicted_label": "ENTAILMENT", "probs": [0.70, 0.10, 0.20]},
        {"chunk_id": "ex3_chunk_1", "predicted_label": "ENTAILMENT", "probs": [0.80, 0.10, 0.10]},
    ]
    res = aggregator.aggregate("ex3", chunk_preds, policy=AggregationPolicy.AVERAGE_PROBABILITIES)
    assert res["aggregated_label"] == "ENTAILMENT"
    # Average probs: [0.75, 0.10, 0.15]
    assert res["aggregated_probs"] == [0.75, 0.10, 0.15]
    assert res["confidence"] == 0.75



# ════════════════════════════════════════════════════════════════════════════
# Step 3.15.2: CLI --max-duration-seconds Remediation Tests
# ════════════════════════════════════════════════════════════════════════════

def test_cli_max_duration_seconds_default():
    """Verify --max-duration-seconds defaults to 3600.0 when not specified."""
    args = parse_args(["--authorize-nli-training"])
    assert args.max_duration_seconds == 3600.0, (
        f"Expected default 3600.0, got {args.max_duration_seconds}"
    )


def test_cli_max_duration_seconds_explicit_36000():
    """Verify --max-duration-seconds 36000 parses to 36000.0."""
    args = parse_args(["--authorize-nli-training", "--max-duration-seconds", "36000"])
    assert args.max_duration_seconds == 36000.0, (
        f"Expected 36000.0, got {args.max_duration_seconds}"
    )


def test_cli_max_duration_seconds_reaches_config():
    """Verify parsed --max-duration-seconds value reaches NLITrainingConfig."""
    args = parse_args(["--authorize-nli-training", "--max-duration-seconds", "36000"])
    cfg = NLITrainingConfig(max_duration_seconds=args.max_duration_seconds)
    assert cfg.max_duration_seconds == 36000.0, (
        f"Config got {cfg.max_duration_seconds} instead of 36000.0"
    )


def test_cli_max_duration_seconds_rejects_zero():
    """Verify --max-duration-seconds 0 is rejected."""
    with pytest.raises(SystemExit):
        parse_args(["--max-duration-seconds", "0"])


def test_cli_max_duration_seconds_rejects_negative():
    """Verify --max-duration-seconds -100 is rejected."""
    with pytest.raises(SystemExit):
        parse_args(["--max-duration-seconds", "-100"])


def test_cli_max_duration_seconds_rejects_nan():
    """Verify --max-duration-seconds nan is rejected."""
    with pytest.raises(SystemExit):
        parse_args(["--max-duration-seconds", "nan"])


def test_cli_max_duration_seconds_rejects_inf():
    """Verify --max-duration-seconds inf is rejected."""
    with pytest.raises(SystemExit):
        parse_args(["--max-duration-seconds", "inf"])


def test_watchdog_timeout_still_functional_after_cli_addition():
    """Verify the existing WatchdogMonitor timeout behavior is unchanged after CLI changes."""
    mock_telemetry = lambda: {
        "rss_mb": 100.0,
        "available_ram_mb": 8000.0,
        "swap_total_mb": 4000.0,
        "swap_used_mb": 100.0,
        "swap_free_mb": 3900.0,
    }
    wd = WatchdogMonitor(
        max_duration_seconds=36000.0,
        telemetry_fn=mock_telemetry,
    )
    # Normal check should pass
    result = wd.check(step=1)
    assert "elapsed_seconds" in result

    # Now test with a very short timeout
    wd2 = WatchdogMonitor(
        max_duration_seconds=0.001,
        telemetry_fn=mock_telemetry,
    )
    import time
    time.sleep(0.01)
    with pytest.raises(TimeoutAbortError):
        wd2.check(step=1)


def test_authorization_gate_unchanged_after_cli_addition():
    """Verify the authorization gate still works after adding --max-duration-seconds."""
    cfg = NLITrainingConfig(authorized=False, max_duration_seconds=36000.0)
    with pytest.raises(TrainingNotAuthorizedError):
        execute_training(config=cfg)
