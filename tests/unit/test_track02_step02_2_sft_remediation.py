"""Unit tests for Track 2 Step 2.2: Objective-Specific SFT Dataset Remediation (sft_v2).

Verifies label preservation, NLI mapping rules, span offset exactness,
test-set quarantine, leakage remediation, and cryptographic checksums.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402
from pydantic import ValidationError  # noqa: E402
from tools.data_prep.prepare_sft_v2_remediated import (  # noqa: E402
    BinaryExampleRecord,
    NLIExampleRecord,
    SpanExampleRecord,
    compute_sha256,
    normalize_text_hash,
)

SFT_V2_DIR = REPO_ROOT / "data/processed/sft_v2"


# ==============================================================================
# 1. Binary Dataset Tests
# ==============================================================================

def test_binary_dataset_schema_and_counts() -> None:
    """Verify sft_v2/binary schema compliance, record counts, and distributions."""
    bin_dir = SFT_V2_DIR / "binary"
    train_path = bin_dir / "train.jsonl"
    val_path = bin_dir / "validation.jsonl"

    assert train_path.exists()
    assert val_path.exists()

    with open(train_path, encoding="utf-8") as f:
        train_recs = [json.loads(line) for line in f]
    with open(val_path, encoding="utf-8") as f:
        val_recs = [json.loads(line) for line in f]

    assert len(train_recs) == 26054
    assert len(val_recs) == 5984

    # Validate schema on samples
    for r in train_recs[:100] + val_recs[:100]:
        rec = BinaryExampleRecord.model_validate(r)
        assert rec.binary_label in ("FACTUAL", "HALLUCINATED")
        assert rec.source_dataset in ("ragtruth", "halueval")

    # Extra forbidden
    bad = train_recs[0].copy()
    bad["illegal_key"] = "forbidden"
    with pytest.raises(ValidationError):
        BinaryExampleRecord.model_validate(bad)


def test_binary_dataset_zero_document_leakage() -> None:
    """Verify zero document text leakage between train and val, and zero test leakage."""
    bin_dir = SFT_V2_DIR / "binary"
    with open(bin_dir / "train.jsonl", encoding="utf-8") as f:
        train_docs = set(normalize_text_hash(json.loads(line_str)["context_or_evidence"]) for line_str in f)
    with open(bin_dir / "validation.jsonl", encoding="utf-8") as f:
        val_docs = set(normalize_text_hash(json.loads(line_str)["context_or_evidence"]) for line_str in f)

    overlap = train_docs.intersection(val_docs)
    assert len(overlap) == 0, f"Found {len(overlap)} overlapping documents between train and val!"

    # Test set quarantine
    he_test_file = REPO_ROOT / "data/processed/halueval/test.jsonl"
    rt_test_file = REPO_ROOT / "data/processed/ragtruth/test.jsonl"
    with open(he_test_file, encoding="utf-8") as f:
        he_test_docs = set(normalize_text_hash(json.loads(line_str)["document"]) for line_str in f)
    with open(rt_test_file, encoding="utf-8") as f:
        rt_test_docs = set(normalize_text_hash(str(json.loads(line_str)["document"])) for line_str in f)

    test_docs = he_test_docs.union(rt_test_docs)
    assert len(train_docs.intersection(test_docs)) == 0, "Test document leaked into binary train!"
    assert len(val_docs.intersection(test_docs)) == 0, "Test document leaked into binary val!"


def test_binary_exclusion_manifest() -> None:
    """Verify exclusion manifest documents the 52 quarantined HaluEval records."""
    excl_path = SFT_V2_DIR / "binary/exclusion_manifest.json"
    assert excl_path.exists()
    with open(excl_path, encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["total_excluded_records"] == 52
    reasons = manifest["reasons_breakdown"]
    assert reasons["HALUEVAL_PASSAGE_LEAKAGE_WITH_CANONICAL_TEST_SET"] == 26
    assert reasons["HALUEVAL_PASSAGE_LEAKAGE_WITH_TRAIN_SPLIT"] == 26


# ==============================================================================
# 2. NLI Dataset Tests
# ==============================================================================

def test_nli_dataset_labels_and_mapping_rules() -> None:
    """Verify 3-way NLI labels strictly conform to human conflict and baseless info semantics."""
    nli_dir = SFT_V2_DIR / "nli"
    train_path = nli_dir / "train.jsonl"
    val_path = nli_dir / "validation.jsonl"

    assert train_path.exists()
    assert val_path.exists()

    with open(train_path, encoding="utf-8") as f:
        train_recs = [json.loads(line) for line in f]
    with open(val_path, encoding="utf-8") as f:
        val_recs = [json.loads(line) for line in f]

    assert len(train_recs) == 10815
    assert len(val_recs) == 2662

    for r in train_recs + val_recs:
        rec = NLIExampleRecord.model_validate(r)
        assert rec.nli_label in ("ENTAILMENT", "CONTRADICTION", "NEUTRAL")
        assert rec.source_dataset == "ragtruth"

        # Check mapping logic
        if rec.nli_label == "ENTAILMENT":
            assert rec.span_count == 0
            assert len(rec.conflict_types) == 0
        elif rec.nli_label == "CONTRADICTION":
            assert rec.span_count > 0
            assert any("Conflict" in ct for ct in rec.conflict_types)
            assert not any("Baseless" in ct for ct in rec.conflict_types)
        elif rec.nli_label == "NEUTRAL":
            assert rec.span_count > 0
            assert any("Baseless" in ct for ct in rec.conflict_types)
            assert not any("Conflict" in ct for ct in rec.conflict_types)


def test_nli_exclusions() -> None:
    """Verify HaluEval and mixed conflict/baseless RAGTruth cases are quarantined."""
    excl_path = SFT_V2_DIR / "nli/exclusion_manifest.json"
    assert excl_path.exists()
    with open(excl_path, encoding="utf-8") as f:
        manifest = json.load(f)

    reasons = manifest["reasons_breakdown"]
    assert reasons["HALUEVAL_EXCLUDED_LACKS_DEFENSIBLE_NLI_SUPERVISION"] == 1
    assert reasons["RAGTRUTH_MIXED_CONFLICT_AND_BASELESS_INFO"] == 1613


# ==============================================================================
# 3. Span-Level Dataset Tests
# ==============================================================================

def test_span_dataset_exact_character_offsets() -> None:
    """Verify candidate_response[start:end] == span.text for 100% of spans."""
    span_dir = SFT_V2_DIR / "spans"
    train_path = span_dir / "train.jsonl"
    val_path = span_dir / "validation.jsonl"

    with open(train_path, encoding="utf-8") as f:
        train_recs = [json.loads(line) for line in f]
    with open(val_path, encoding="utf-8") as f:
        val_recs = [json.loads(line) for line in f]

    assert len(train_recs) == 12072
    assert len(val_recs) == 3018

    total_spans_checked = 0
    for r in train_recs + val_recs:
        rec = SpanExampleRecord.model_validate(r)
        cand = rec.candidate_response
        for s in rec.hallucination_spans:
            total_spans_checked += 1
            assert cand[s.start:s.end] == s.text, f"Offset mismatch in {rec.example_id}: '{cand[s.start:s.end]}' != '{s.text}'"

    assert total_spans_checked == 12756, f"Expected 12,756 spans, checked {total_spans_checked}"


# ==============================================================================
# 4. G3 Supervision Gap & Checksum Integrity
# ==============================================================================

def test_g3_gap_specification_and_no_fabricated_records() -> None:
    """Verify zero five-outcome G3 training records are fabricated."""
    g3_dir = SFT_V2_DIR / "g3_readiness"
    manifest_path = g3_dir / "g3_readiness_manifest.json"
    assert manifest_path.exists()
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["readiness_verdict"] == "BLOCKED"
    assert data["fabricated_records"] == 0
    assert not (g3_dir / "train.jsonl").exists()
    assert not (g3_dir / "validation.jsonl").exists()


def test_sft_v2_all_checksums_pass() -> None:
    """Verify cryptographic checksums across all four sft_v2 directories."""
    for sub in ("binary", "nli", "spans", "g3_readiness"):
        sub_dir = SFT_V2_DIR / sub
        checksums_file = sub_dir / "checksums.sha256"
        assert checksums_file.exists(), f"Missing checksums.sha256 in {sub_dir}"

        with open(checksums_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                expected_sha, fname = line.split()
                actual_sha = compute_sha256(sub_dir / fname)
                assert actual_sha == expected_sha, f"SHA256 mismatch for {sub}/{fname}"
