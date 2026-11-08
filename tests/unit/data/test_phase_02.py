"""Unit test suite for TrustRAG Phase 02: Dataset Acquisition & Security Benchmark Construction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List
import pytest

from trustrag.data.acquisition.manager import AcquisitionManager, PRIORITY_TIERS, CONFIGURED_TARGETS
from trustrag.data.benchmarks.builder import BenchmarkBuilder, BENCHMARK_CATEGORIES
from trustrag.data.benchmarks.security_generator import (
    PROVENANCE_STRING,
    generate_security_benchmark_pairs,
)
from trustrag.data.cli import main
from trustrag.data.exceptions import AcquisitionError, StorageError, ValidationError
from trustrag.data.quality import DatasetQualityAuditor, DatasetQualityReport
from trustrag.data.resource import ResourceManager, format_bytes
from trustrag.data.schemas import (
    ClaimVerificationRecord,
    DocumentRecord,
    QueryRecord,
    SecurityRecord,
    compute_content_hash,
)
from trustrag.data.taxonomy import (
    ALLOWED_ATTACK_FAMILIES,
    ALLOWED_CLAIM_LABELS,
    ALLOWED_SECURITY_LABELS,
    AttackFamily,
    ClaimVerificationLabel,
    DocumentSecurityLabel,
    normalize_attack_family,
    normalize_claim_label,
    normalize_security_label,
)


class TestTaxonomyAndStandardization:
    """Validate canonical taxonomy mappings and label rejection."""

    def test_claim_label_mappings(self):
        # Supported mappings
        assert normalize_claim_label("supported")[0] == ClaimVerificationLabel.SUPPORTED
        assert normalize_claim_label("factual")[0] == ClaimVerificationLabel.SUPPORTED
        assert normalize_claim_label("entailment")[0] == ClaimVerificationLabel.SUPPORTED

        # Contradicted mappings
        assert normalize_claim_label("refuted")[0] == ClaimVerificationLabel.CONTRADICTED
        assert normalize_claim_label("hallucinated")[0] == ClaimVerificationLabel.CONTRADICTED
        assert normalize_claim_label("contradiction")[0] == ClaimVerificationLabel.CONTRADICTED

        # Not enough evidence mappings
        assert normalize_claim_label("not_enough_info")[0] == ClaimVerificationLabel.NOT_ENOUGH_EVIDENCE
        assert normalize_claim_label("nei")[0] == ClaimVerificationLabel.NOT_ENOUGH_EVIDENCE
        assert normalize_claim_label("ambiguous")[0] == ClaimVerificationLabel.NOT_ENOUGH_EVIDENCE

    def test_unknown_claim_label_raises(self):
        with pytest.raises(ValidationError):
            normalize_claim_label("unrecognized_label_xyz")

    def test_security_label_mappings(self):
        assert normalize_security_label("clean")[0] == DocumentSecurityLabel.CLEAN
        assert normalize_security_label("benign")[0] == DocumentSecurityLabel.CLEAN
        assert normalize_security_label("poisoned")[0] == DocumentSecurityLabel.POISONED
        assert normalize_security_label("attack")[0] == DocumentSecurityLabel.POISONED
        assert normalize_security_label("uncertain")[0] == DocumentSecurityLabel.UNCERTAIN

    def test_unknown_security_label_raises(self):
        with pytest.raises(ValidationError):
            normalize_security_label("dangerous_unknown")

    def test_attack_family_mappings(self):
        assert normalize_attack_family("knowledge_poisoning")[0] == AttackFamily.KNOWLEDGE_POISONING
        assert normalize_attack_family("prompt_injection")[0] == AttackFamily.PROMPT_INJECTION
        assert normalize_attack_family("trigger_dos")[0] == AttackFamily.TRIGGER_DOS
        assert normalize_attack_family("conflicting_evidence")[0] == AttackFamily.CONFLICTING_EVIDENCE
        assert normalize_attack_family("malicious_instruction")[0] == AttackFamily.MALICIOUS_INSTRUCTION
        assert normalize_attack_family("benign_instruction_like")[0] == AttackFamily.BENIGN_INSTRUCTION_LIKE

    def test_unknown_attack_family_raises(self):
        with pytest.raises(ValidationError):
            normalize_attack_family("trojan_horse_exploit")


class TestSecurityBenchmarkGenerator:
    """Validate 1,000 paired security document generation and properties."""

    def test_generator_structure_and_counts(self):
        clean_recs, poison_recs = generate_security_benchmark_pairs(num_pairs=50, seed=42)
        assert len(clean_recs) == 50
        assert len(poison_recs) == 50

        for c, p in zip(clean_recs, poison_recs):
            # 1. Clean document properties
            assert c.clean_poison_label == "clean"
            assert c.source_dataset == "custom_security"
            assert PROVENANCE_STRING in (c.provenance or "")
            assert c.content_hash != ""

            # 2. Poisoned document properties
            assert p.clean_poison_label == "poisoned"
            assert p.attack_family in ALLOWED_ATTACK_FAMILIES
            assert p.attack_subtype is not None
            assert p.target_query is not None
            assert p.target_behavior is not None
            assert PROVENANCE_STRING in (p.provenance or "")

            # 3. Grouped split linkage: clean and poison MUST share source_id
            assert c.source_id == p.source_id

    def test_generator_seed_reproducibility(self):
        c1, p1 = generate_security_benchmark_pairs(num_pairs=20, seed=123)
        c2, p2 = generate_security_benchmark_pairs(num_pairs=20, seed=123)

        assert [r.record_id for r in c1] == [r.record_id for r in c2]
        assert [r.content_hash for r in p1] == [r.content_hash for r in p2]


class TestResourceManagerAndStorage:
    """Validate storage estimation and disk space checks."""

    def test_format_bytes(self):
        assert format_bytes(500) == "500.00 B"
        assert format_bytes(1024) == "1.00 KB"
        assert format_bytes(1024 * 1024 * 5) == "5.00 MB"
        assert format_bytes(1024 * 1024 * 1024 * 2) == "2.00 GB"

    def test_estimate_dataset_storage(self):
        est_100 = ResourceManager.estimate_dataset_storage(100)
        est_1000 = ResourceManager.estimate_dataset_storage(1000)
        assert est_100 > 0
        assert est_1000 > est_100

    def test_check_disk_space_sufficient(self, tmp_path):
        # 1 KB should easily pass
        assert ResourceManager.check_disk_space(1024, target_path=tmp_path) is True

    def test_check_disk_space_exceeded_raises(self, tmp_path):
        # Impossibly large requirement (10 Petabytes) must raise StorageError
        huge_bytes = 10 * 1024 * 1024 * 1024 * 1024 * 1024
        with pytest.raises(StorageError):
            ResourceManager.check_disk_space(huge_bytes, target_path=tmp_path)

    def test_report_repository_storage(self, tmp_path):
        report = ResourceManager.report_repository_storage(base_dir=tmp_path)
        assert "total_bytes" in report
        assert "tiers" in report
        assert "raw" in report["tiers"]
        assert "processed" in report["tiers"]
        assert "benchmarks" in report["tiers"]


class TestQualityAuditor:
    """Validate dataset quality metrics and report generation."""

    def test_quality_auditor_healthy_records(self):
        records = [
            DocumentRecord(
                document_id="doc_1",
                text="The speed of light in vacuum is approximately 299,792,458 meters per second.",
                source_dataset="sample",
                source_split="train",
                source_id="src_1",
            ),
            QueryRecord(
                query_id="q_1",
                query="What is the speed of light?",
                source_dataset="sample",
                source_split="train",
                source_id="src_1",
                relevant_document_ids=["doc_1"],
            ),
            ClaimVerificationRecord(
                record_id="c_1",
                document="Water boils at 100 degrees Celsius at sea level.",
                claim="Water boils at 100 C under standard atmospheric pressure.",
                label="SUPPORTED",
                source_dataset="sample",
                source_id="src_2",
            ),
        ]
        quality = DatasetQualityAuditor.audit_records(records, dataset_name="healthy_test")
        assert quality.is_healthy is True
        assert quality.total_records == 3
        assert quality.valid_records == 3
        assert quality.invalid_records == 0
        assert quality.duplicate_records == 0
        assert quality.unknown_labels == 0

    def test_quality_auditor_detects_duplicates(self):
        text = "Identical document text for duplicate testing."
        rec1 = DocumentRecord(document_id="d1", text=text, source_dataset="t", source_id="s1")
        rec2 = DocumentRecord(document_id="d2", text=text, source_dataset="t", source_id="s2")

        quality = DatasetQualityAuditor.audit_records([rec1, rec2], dataset_name="dup_test")
        assert quality.total_records == 2
        assert quality.duplicate_records == 1

    def test_quality_auditor_detects_unknown_label(self):
        rec = ClaimVerificationRecord(
            record_id="c_err",
            document="Valid doc",
            claim="Valid claim",
            label="COMPLETELY_INVALID_LABEL",
            source_dataset="t",
            source_id="s1",
        )
        quality = DatasetQualityAuditor.audit_records([rec], dataset_name="label_test")
        assert quality.is_healthy is False
        assert quality.unknown_labels == 1
        assert quality.invalid_records == 1

    def test_quality_report_formatting(self):
        rep = DatasetQualityReport(dataset_name="demo", total_records=10, valid_records=10)
        d = rep.to_dict()
        assert d["is_healthy"] is True
        assert d["valid_rate"] == 1.0

        j_str = rep.to_json()
        assert "valid_rate" in j_str

        md = rep.to_markdown()
        assert "# Data Quality Report: demo" in md


class TestAcquisitionManager:
    """Validate acquisition tier priorities, storage pre-checks, and audit logging."""

    def test_fineweb_acquisition_blocked(self, tmp_path):
        mgr = AcquisitionManager(raw_base_dir=tmp_path / "raw")
        with pytest.raises(AcquisitionError, match="FineWeb"):
            mgr.acquire("fineweb")

    def test_rsb_acquisition_blocked_without_local_path(self, tmp_path):
        mgr = AcquisitionManager(raw_base_dir=tmp_path / "raw")
        with pytest.raises(AcquisitionError, match="RSB"):
            mgr.acquire("rsb")

    def test_acquire_custom_security_with_audit_log(self, tmp_path):
        raw_dir = tmp_path / "raw"
        audit_file = raw_dir / "audit.jsonl"
        mgr = AcquisitionManager(raw_base_dir=raw_dir, audit_log_path=audit_file)

        records, entry = mgr.acquire("custom_security", limit=20, smoke_test=True)
        assert len(records) == 20
        assert entry.status == "SUCCESS"
        assert Path(entry.raw_file_path).is_file()
        assert audit_file.is_file()

        # Verify audit log entry contents
        log_lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(log_lines) == 1
        data = json.loads(log_lines[0])
        assert data["dataset_name"] == "custom_security"
        assert data["records_acquired"] == 20
        assert "raw_file_sha256" in data

    def test_get_acquisition_status(self, tmp_path):
        mgr = AcquisitionManager(raw_base_dir=tmp_path / "raw", processed_base_dir=tmp_path / "processed")
        statuses = mgr.get_acquisition_status()
        assert len(statuses) == 13
        ds_names = {s["dataset_name"] for s in statuses}
        assert "ragtruth" in ds_names
        assert "boolq" in ds_names


class TestBenchmarkBuilder:
    """Validate construction of the 4 benchmark categories under data/benchmarks/."""

    def test_build_all_four_categories(self, tmp_path):
        builder = BenchmarkBuilder(output_root=tmp_path / "benchmarks")

        # 1. Clean RAG
        res_a = builder.build_clean_rag(limit=30)
        assert res_a["category"] == "clean_rag"
        assert res_a["total_records"] == 30
        assert res_a["quality_status"] == "HEALTHY"
        assert res_a["leakage_detected"] is False
        assert (tmp_path / "benchmarks" / "clean_rag" / "manifest.json").is_file()

        # 2. Knowledge Poisoning
        res_b = builder.build_knowledge_poisoning(num_pairs=20)
        assert res_b["category"] == "knowledge_poisoning"
        assert res_b["quality_status"] == "HEALTHY"
        assert res_b["leakage_detected"] is False
        assert (tmp_path / "benchmarks" / "knowledge_poisoning" / "manifest.json").is_file()

        # 3. Hallucination Detection
        res_c = builder.build_hallucination(limit_per_source=15)
        assert res_c["category"] == "hallucination"
        assert res_c["quality_status"] == "HEALTHY"
        assert res_c["leakage_detected"] is False
        assert (tmp_path / "benchmarks" / "hallucination" / "manifest.json").is_file()

        # 4. Adversarial Robustness
        res_d = builder.build_adversarial_robustness(num_pairs=20)
        assert res_d["category"] == "adversarial_robustness"
        assert res_d["quality_status"] == "HEALTHY"
        assert res_d["leakage_detected"] is False
        assert (tmp_path / "benchmarks" / "adversarial_robustness" / "manifest.json").is_file()


class TestPhase02CLIIntegration:
    """Validate CLI execution for Phase 02 subcommands."""

    def test_cli_storage(self, capsys):
        code = main(["storage"])
        assert code == 0
        captured = capsys.readouterr()
        assert "TrustRAG Repository Storage Breakdown" in captured.out
        assert "Dataset Acquisition & Processing Status" in captured.out

    def test_cli_benchmark_build_and_audit(self, tmp_path, capsys):
        out_dir = str(tmp_path / "benchmarks" / "knowledge_poisoning")

        # Build knowledge_poisoning benchmark
        build_code = main([
            "benchmark",
            "build",
            "--category",
            "knowledge_poisoning",
            "--limit",
            "30",
            "--output-dir",
            out_dir,
        ])
        assert build_code == 0

        # Audit built benchmark
        audit_code = main([
            "benchmark",
            "audit",
            "--category",
            "knowledge_poisoning",
            "--output-dir",
            out_dir,
        ])
        assert audit_code == 0
        captured = capsys.readouterr()
        assert "Leakage Detected:  NO (PASS)" in captured.out
        assert "Quality Health:    HEALTHY (PASS)" in captured.out
