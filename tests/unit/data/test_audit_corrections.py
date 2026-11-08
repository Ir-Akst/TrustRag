"""Tests for Phase 01 data integrity audit corrections.

Covers:
1. Official split preservation vs explicit custom splitting.
2. Group isolation (clean and poisoned variants, document-level grouping).
3. Cross-split duplicate content leakage detection.
4. Deterministic reproducibility with fixed seed.
5. Small dataset splitting (1, 2, 3 groups).
6. Missing group ID fallback to deterministic content hash.
7. Manifest consistency validation (checksums, file sizes, record counts).
8. Path portability (forward slashes, relative paths).
9. Training and evaluation dataset usage isolation.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from trustrag.data.exceptions import ManifestError, SplitError, UsageIsolationError
from trustrag.data.isolation import DatasetUsageCategory, DatasetUsageValidator
from trustrag.data.manifest import DatasetManifest, ManifestFileEntry, ManifestManager
from trustrag.data.schemas import QueryRecord, SecurityRecord, compute_content_hash
from trustrag.data.splitting import LeakageResistantSplitter, SplitConfig, SplitStatistics


def _make_query_record(qid: str, text: str, group_id: str | None = None) -> QueryRecord:
    content_hash = compute_content_hash(text)
    meta = {"source_doc_id": group_id} if group_id else {}
    return QueryRecord(
        query_id=qid,
        query=text,
        source_dataset="test_qa",
        source_split="train",
        source_id=qid,
        metadata=meta,
        content_hash=content_hash,
    )


def _make_security_record(
    rid: str,
    text: str,
    doc_id: str,
    label: str = "clean",
    family: str | None = None,
) -> SecurityRecord:
    content_hash = compute_content_hash(text)
    return SecurityRecord(
        record_id=rid,
        document=text,
        clean_poison_label=label,
        attack_family=family,
        source_dataset="test_sec",
        source_split="train",
        source_id=rid,
        metadata={"document_id": doc_id},
        content_hash=content_hash,
    )


class TestSplittingAndLeakageAudit:
    """Audit tests for splitting logic, leakage detection, and group isolation."""

    def test_official_split_preservation(self):
        """Official splits must be audited without repartitioning."""
        records = [_make_query_record(f"q_{i}", f"Query text {i}", f"doc_{i}") for i in range(20)]

        audit = LeakageResistantSplitter.audit_partitions({"validation": records}, split_type="official")
        assert audit.split_type == "official"
        assert audit.total_records == 20
        assert not audit.leakage_detected
        assert audit.group_overlap_train_val == 0

    def test_custom_splitting_explicit(self):
        """Custom 70/15/15 splitting is supported when explicitly requested."""
        config = SplitConfig(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, seed=42, group_key="source_doc_id")
        records = [_make_query_record(f"q_{i}", f"Query text {i}", f"doc_{i}") for i in range(100)]

        splits, audit = LeakageResistantSplitter.split(records, config=config)
        assert audit.split_type == "custom"
        assert len(splits["train"]) == 70
        assert len(splits["val"]) == 15
        assert len(splits["test"]) == 15
        assert not audit.leakage_detected
        assert audit.group_overlap_train_val == 0
        assert audit.group_overlap_train_test == 0
        assert audit.group_overlap_val_test == 0

    def test_group_isolation_clean_poison_pairs(self):
        """Clean and poisoned variants sharing the same document ID must remain in the same partition."""
        config = SplitConfig(seed=42, group_key="document_id")
        records = []
        for i in range(30):
            doc_id = f"doc_{i}"
            clean = _make_security_record(f"sec_{i}_clean", f"Clean text for doc {i}", doc_id, label="clean")
            poison = _make_security_record(
                f"sec_{i}_poison", f"Poisoned text for doc {i}", doc_id, label="poison", family="corpus_poisoning"
            )
            records.extend([clean, poison])

        splits, audit = LeakageResistantSplitter.split(records, config=config)
        assert not audit.leakage_detected

        train_groups = {LeakageResistantSplitter.extract_group_id(r, "document_id") for r in splits["train"]}
        val_groups = {LeakageResistantSplitter.extract_group_id(r, "document_id") for r in splits["val"]}
        test_groups = {LeakageResistantSplitter.extract_group_id(r, "document_id") for r in splits["test"]}

        assert train_groups.isdisjoint(val_groups)
        assert train_groups.isdisjoint(test_groups)
        assert val_groups.isdisjoint(test_groups)

    def test_duplicate_content_leakage_detection(self):
        """Detect duplicate content hashes across partitions."""
        # Partition 1 and Partition 2 contain records with identical text (and thus identical content_hash)
        rec1 = _make_query_record("q_1", "Exact duplicate text", "doc_A")
        rec2 = _make_query_record("q_2", "Exact duplicate text", "doc_B")

        # Manually create leaking partitions
        partitions = {
            "train": [rec1],
            "val": [rec2],
        }

        with pytest.raises(SplitError, match="Data leakage detected"):
            LeakageResistantSplitter.audit_partitions(partitions)

    def test_deterministic_reproducibility(self):
        """Splitting with seed 42 must produce identical partitions every time."""
        records = [_make_query_record(f"q_{i}", f"Question {i}", f"group_{i % 10}") for i in range(50)]
        config = SplitConfig(seed=42, group_key="source_doc_id")

        splits_a, _ = LeakageResistantSplitter.split(records, config=config)
        splits_b, _ = LeakageResistantSplitter.split(records, config=config)

        for split_name in ("train", "val", "test"):
            ids_a = [r.query_id for r in splits_a[split_name]]
            ids_b = [r.query_id for r in splits_b[split_name]]
            assert ids_a == ids_b

    def test_small_datasets_handling(self):
        """Handle 1, 2, or 3 groups safely without division by zero or index errors."""
        config = SplitConfig(seed=42)

        # 1 group
        rec_1 = [_make_query_record("q1", "text 1", "g1")]
        splits_1, audit_1 = LeakageResistantSplitter.split(rec_1, config=config)
        assert len(splits_1["train"]) == 1
        assert len(splits_1["val"]) == 0
        assert len(splits_1["test"]) == 0
        assert not audit_1.leakage_detected

        # 2 groups
        rec_2 = [_make_query_record("q1", "text 1", "g1"), _make_query_record("q2", "text 2", "g2")]
        splits_2, audit_2 = LeakageResistantSplitter.split(rec_2, config=config)
        assert len(splits_2["train"]) == 1
        assert len(splits_2["val"]) == 0
        assert len(splits_2["test"]) == 1
        assert not audit_2.leakage_detected

        # 3 groups
        rec_3 = [
            _make_query_record("q1", "text 1", "g1"),
            _make_query_record("q2", "text 2", "g2"),
            _make_query_record("q3", "text 3", "g3"),
        ]
        splits_3, audit_3 = LeakageResistantSplitter.split(rec_3, config=config)
        assert len(splits_3["train"]) == 1
        assert len(splits_3["val"]) == 1
        assert len(splits_3["test"]) == 1
        assert not audit_3.leakage_detected

    def test_missing_group_id_deterministic_fallback(self):
        """When group_id is missing, fallback to content_hash deterministically."""
        rec = _make_query_record("q1", "Some query without metadata group")
        # Clear source_id and query_id so fallback checks content_hash
        rec.source_id = ""
        rec.query_id = ""
        group_id_1 = LeakageResistantSplitter.extract_group_id(rec, group_key="nonexistent_field")
        group_id_2 = LeakageResistantSplitter.extract_group_id(rec, group_key="nonexistent_field")

        assert group_id_1 == group_id_2
        assert group_id_1.startswith("hash_")


class TestManifestPortabilityAndValidation:
    """Tests for manifest consistency validation and path portability."""

    def test_manifest_validation_success(self, tmp_path: Path):
        """Valid manifest pointing to existing files with correct checksums passes."""
        split_file = tmp_path / "train.jsonl"
        line1 = json.dumps({"query_id": "1", "query": "test 1"})
        line2 = json.dumps({"query_id": "2", "query": "test 2"})
        split_file.write_text(f"{line1}\n{line2}\n", encoding="utf-8")

        manager = ManifestManager()
        entry = manager.create_file_entry(split_file, "train", tmp_path, original_split="train")
        assert entry.file_path == "train.jsonl"
        assert "\\" not in entry.file_path
        assert entry.record_count == 2

        manifest = DatasetManifest(
            name="test_ds",
            version="1.0.0",
            source_identifier="test_ds",
            source_url="http://example.com",
            license="MIT",
            files=[entry],
        )

        is_valid, errors = manager.validate_manifest(manifest, tmp_path)
        assert is_valid is True
        assert errors == []

    def test_manifest_validation_missing_file(self, tmp_path: Path):
        """Manifest referencing a missing file raises ManifestError."""
        manager = ManifestManager()
        entry = ManifestFileEntry(
            split="train",
            file_path="missing_file.jsonl",
            format="jsonl",
            record_count=10,
            file_size_bytes=100,
            sha256="abc123",
        )
        manifest = DatasetManifest(
            name="test_ds",
            version="1.0.0",
            source_identifier="test_ds",
            source_url="http://example.com",
            license="MIT",
            files=[entry],
        )

        with pytest.raises(ManifestError, match="Referenced file not found on disk"):
            manager.validate_manifest(manifest, tmp_path, raise_on_error=True)

    def test_manifest_validation_checksum_mismatch(self, tmp_path: Path):
        """Manifest with a corrupted checksum raises ManifestError."""
        split_file = tmp_path / "train.jsonl"
        split_file.write_text("{}", encoding="utf-8")

        manager = ManifestManager()
        entry = manager.create_file_entry(split_file, "train", tmp_path)
        # Corrupt the sha256
        entry.sha256 = "0000000000000000000000000000000000000000000000000000000000000000"

        manifest = DatasetManifest(
            name="test_ds",
            version="1.0.0",
            source_identifier="test_ds",
            source_url="http://example.com",
            license="MIT",
            files=[entry],
        )

        with pytest.raises(ManifestError, match="SHA-256 checksum mismatch"):
            manager.validate_manifest(manifest, tmp_path, raise_on_error=True)

    def test_manifest_validation_record_count_mismatch(self, tmp_path: Path):
        """Manifest with mismatched record count raises ManifestError."""
        split_file = tmp_path / "train.jsonl"
        split_file.write_text('{"a": 1}\n{"b": 2}\n', encoding="utf-8")

        manager = ManifestManager()
        entry = manager.create_file_entry(split_file, "train", tmp_path)
        entry.record_count = 999  # deliberate discrepancy

        manifest = DatasetManifest(
            name="test_ds",
            version="1.0.0",
            source_identifier="test_ds",
            source_url="http://example.com",
            license="MIT",
            files=[entry],
        )

        with pytest.raises(ManifestError, match="Record count mismatch"):
            manager.validate_manifest(manifest, tmp_path, raise_on_error=True)

    def test_path_portability_forward_slashes(self, tmp_path: Path):
        """File paths in manifests must always use forward slashes and be relative."""
        sub_dir = tmp_path / "sub_split"
        sub_dir.mkdir()
        file_path = sub_dir / "data.jsonl"
        file_path.write_text('{"id": 1}\n', encoding="utf-8")

        manager = ManifestManager()
        entry = manager.create_file_entry(file_path, "train", tmp_path)
        assert entry.file_path == "sub_split/data.jsonl"
        assert "\\" not in entry.file_path
        assert not Path(entry.file_path).is_absolute()


class TestTrainingAndEvaluationIsolation:
    """Tests enforcing training vs evaluation isolation rules."""

    def test_allowed_training_dataset(self):
        """Permitted datasets can be validated for training workflows."""
        validator = DatasetUsageValidator()
        validator.validate_usage("natural_questions", DatasetUsageCategory.TRAINING)
        validator.validate_usage("squad", DatasetUsageCategory.TRAINING)
        validator.validate_usage("fineweb", DatasetUsageCategory.TRAINING_CORPUS)

    def test_llm_aggrefact_blocked_from_training(self):
        """LLM-AggreFact has non-derivative license terms and must be blocked from training."""
        validator = DatasetUsageValidator()
        with pytest.raises(UsageIsolationError, match="prohibited from training workflows"):
            validator.validate_usage("llm_aggrefact", DatasetUsageCategory.TRAINING)

        with pytest.raises(UsageIsolationError, match="prohibited from training workflows"):
            validator.validate_usage("llm_aggrefact", DatasetUsageCategory.TRAINING_CORPUS)

        # But it is permitted for evaluation
        validator.validate_usage("llm_aggrefact", DatasetUsageCategory.EVALUATION)

    def test_rsb_blocked_from_training(self):
        """RSB benchmark must be isolated to evaluation/security benchmark."""
        validator = DatasetUsageValidator()
        with pytest.raises(UsageIsolationError, match="prohibited from training workflows"):
            validator.validate_usage("rsb", DatasetUsageCategory.TRAINING)

        # Permitted for security benchmark
        validator.validate_usage("rsb", DatasetUsageCategory.SECURITY_BENCHMARK)
        validator.validate_usage("rsb", DatasetUsageCategory.EVALUATION)

    def test_fineweb_blocked_from_evaluation(self):
        """FineWeb is a training corpus only and must not be used as an evaluation benchmark."""
        validator = DatasetUsageValidator()
        with pytest.raises(UsageIsolationError, match="cannot be used in evaluation workflows"):
            validator.validate_usage("fineweb", DatasetUsageCategory.EVALUATION)

        with pytest.raises(UsageIsolationError, match="cannot be used in evaluation workflows"):
            validator.validate_usage("fineweb", DatasetUsageCategory.SECURITY_BENCHMARK)

        # Permitted for training corpus
        validator.validate_usage("fineweb", DatasetUsageCategory.TRAINING_CORPUS)
