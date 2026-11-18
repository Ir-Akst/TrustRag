"""Unit tests for Track 2 Step 2: Evidence-Grounded SFT Data Preparation.

Verifies schema compliance, deterministic generation, split isolation (zero source leakage),
test-set quarantine, retrieval benchmark exclusion, and target provenance.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.data_prep.prepare_sft_dataset import SFTExampleRecord, compute_sha256  # noqa: E402

SFT_V1_DIR = REPO_ROOT / "data/processed/sft_v1"


@pytest.fixture(scope="module")
def train_records():
    train_path = SFT_V1_DIR / "train.jsonl"
    assert train_path.exists(), "train.jsonl does not exist"
    records = []
    with open(train_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


@pytest.fixture(scope="module")
def val_records():
    val_path = SFT_V1_DIR / "validation.jsonl"
    assert val_path.exists(), "validation.jsonl does not exist"
    records = []
    with open(val_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


@pytest.fixture(scope="module")
def manifest():
    manifest_path = SFT_V1_DIR / "dataset_manifest.json"
    assert manifest_path.exists(), "dataset_manifest.json does not exist"
    with open(manifest_path, encoding="utf-8") as f:
        return json.load(f)


def test_sft_record_schema_validation(train_records, val_records):
    """Verify all records conform strictly to SFTExampleRecord schema."""
    # Test a sample of records from both splits for speed & thoroughness
    sample = train_records[:200] + train_records[-200:] + val_records[:200] + val_records[-200:]
    for r in sample:
        rec = SFTExampleRecord.model_validate(r)
        assert rec.example_id.startswith("sft_")
        assert rec.source_dataset in ("ragtruth", "halueval")
        assert rec.ground_truth_label in ("FACTUAL", "HALLUCINATED")
        assert rec.split in ("train", "validation")
        assert len(rec.context_or_evidence) > 0
        assert len(rec.candidate_response) > 0
        assert len(rec.target) > 0
        assert len(rec.target_provenance) > 0


def test_sft_schema_rejects_extra_fields():
    """Verify extra fields are strictly forbidden by Pydantic."""
    bad_record = {
        "example_id": "sft_bad_1",
        "source_dataset": "ragtruth",
        "source_id": "sid_1",
        "split": "train",
        "question_or_claim": "test claim",
        "context_or_evidence": "test doc",
        "candidate_response": "test resp",
        "ground_truth_label": "FACTUAL",
        "target": '{"verdict": "SUPPORTED"}',
        "target_provenance": "test",
        "unauthorized_field": "illegal",
    }
    with pytest.raises(ValidationError):
        SFTExampleRecord.model_validate(bad_record)


def test_record_counts_and_distributions(train_records, val_records, manifest):
    """Verify total record counts and split partitions match specification."""
    assert len(train_records) == 26072, f"Expected 26,072 train records, got {len(train_records)}"
    assert len(val_records) == 6018, f"Expected 6,018 val records, got {len(val_records)}"

    # Check manifest alignment
    assert manifest["splits"]["train"]["records"] == 26072
    assert manifest["splits"]["validation"]["records"] == 6018

    # Source dataset representation
    train_sources = [r["source_dataset"] for r in train_records]
    assert train_sources.count("ragtruth") == 12072
    assert train_sources.count("halueval") == 14000

    val_sources = [r["source_dataset"] for r in val_records]
    assert val_sources.count("ragtruth") == 3018
    assert val_sources.count("halueval") == 3000


def test_zero_leakage_between_train_and_val(train_records, val_records):
    """Verify zero overlap of source_ids between train and validation splits."""
    train_sids: set[str] = set(r["source_id"] for r in train_records)
    val_sids: set[str] = set(r["source_id"] for r in val_records)

    overlap = train_sids.intersection(val_sids)
    assert len(overlap) == 0, f"Found source_id leakage between train and val: {len(overlap)} overlapping IDs"


def test_zero_leakage_with_test_splits(train_records, val_records):
    """Verify quarantined benchmark test splits have zero overlap with sft_v1 train and val."""
    rt_test_file = REPO_ROOT / "data/processed/ragtruth/test.jsonl"
    he_test_file = REPO_ROOT / "data/processed/halueval/test.jsonl"

    assert rt_test_file.exists()
    assert he_test_file.exists()

    with open(rt_test_file, encoding="utf-8") as f:
        rt_test_sids = set(json.loads(line)["source_id"] for line in f)
        rt_test_rids = set(json.loads(line)["record_id"] for line in f)

    with open(he_test_file, encoding="utf-8") as f:
        he_test_sids = set(json.loads(line)["source_id"] for line in f)
        he_test_rids = set(json.loads(line)["record_id"] for line in f)

    all_sft_sids = set(r["source_id"] for r in train_records + val_records)

    # Check source ID leakage
    rt_sid_leakage = all_sft_sids.intersection(rt_test_sids)
    assert len(rt_sid_leakage) == 0, f"RAGTruth test source_id leaked into sft_v1: {rt_sid_leakage}"

    he_sid_leakage = all_sft_sids.intersection(he_test_sids)
    assert len(he_sid_leakage) == 0, f"HaluEval test source_id leaked into sft_v1: {he_sid_leakage}"

    # Check raw record ID presence
    for r in train_records + val_records:
        raw_id = r["example_id"].split("_")[-1]
        assert raw_id not in rt_test_rids, f"RAGTruth test record {raw_id} found in SFT dataset"
        assert raw_id not in he_test_rids, f"HaluEval test record {raw_id} found in SFT dataset"


def test_retrieval_benchmarks_quarantined(train_records, val_records):
    """Verify HotpotQA and MS MARCO retrieval records are strictly excluded from SFT."""
    for r in train_records + val_records:
        assert r["source_dataset"] in ("ragtruth", "halueval")
        assert "hotpotqa" not in r["example_id"]
        assert "ms_marco" not in r["example_id"]
        assert "msmarco" not in r["example_id"]


def test_provenance_and_target_validity(train_records, val_records):
    """Verify target strings are valid JSON and provenance explicitly traceable."""
    sample = train_records[:50] + val_records[:50]
    for r in sample:
        # Target must parse as valid JSON
        target_obj = json.loads(r["target"])
        assert "verdict" in target_obj
        assert target_obj["verdict"] in ("SUPPORTED", "CONTRADICTED")

        # Provenance must be documented
        assert len(r["target_provenance"]) > 10
        if r["source_dataset"] == "ragtruth":
            assert "ragtruth_original_annotations" in r["target_provenance"]
        elif r["source_dataset"] == "halueval":
            assert "halueval_qa_original_annotations" in r["target_provenance"]


def test_checksum_file_integrity():
    """Verify checksums.sha256 in sft_v1 accurately matches all artifacts."""
    checksums_file = SFT_V1_DIR / "checksums.sha256"
    assert checksums_file.exists()

    with open(checksums_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            expected_hash, fname = line.split()
            actual_hash = compute_sha256(SFT_V1_DIR / fname)
            assert actual_hash == expected_hash, f"SHA-256 mismatch for {fname}"
