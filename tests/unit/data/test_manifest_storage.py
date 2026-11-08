"""Unit tests for dataset storage, atomic writes, checksum computation, and manifests."""

import json
from pathlib import Path
import pytest

from trustrag.data.base import DatasetMetadata, ProcessingStats
from trustrag.data.manifest import DatasetManifest, ManifestManager
from trustrag.data.schemas import DocumentRecord
from trustrag.data.splitting import SplitStatistics
from trustrag.data.storage import DatasetStorage, compute_file_sha256


def test_storage_jsonl_atomic_save_and_load(tmp_path: Path):
    records = [
        DocumentRecord(document_id=f"doc_{i}", text=f"Text content {i}", source_dataset="test")
        for i in range(5)
    ]
    out_file = tmp_path / "processed" / "train.jsonl"
    res = DatasetStorage.save_jsonl(records, out_file)

    assert out_file.exists()
    assert res["record_count"] == 5
    assert len(res["sha256"]) == 64
    assert res["sha256"] == compute_file_sha256(out_file)

    # Load back as DocumentRecord models
    loaded = list(DatasetStorage.load_jsonl(out_file, record_type=DocumentRecord))
    assert len(loaded) == 5
    assert loaded[0].document_id == "doc_0"
    assert loaded[0].text == "Text content 0"


def test_storage_parquet(tmp_path: Path):
    pytest.importorskip("pyarrow")
    records = [
        DocumentRecord(document_id=f"doc_{i}", text=f"Parquet text {i}", source_dataset="test")
        for i in range(3)
    ]
    out_file = tmp_path / "train.parquet"
    res = DatasetStorage.save_parquet(records, out_file)

    assert out_file.exists()
    assert res["record_count"] == 3
    assert res["format"] == "parquet"


def test_manifest_generation_and_serialization(tmp_path: Path):
    meta = DatasetMetadata(
        name="test_dataset",
        category="rag_qa",
        description="Test dataset for manifest generation",
        source_uri="https://example.com/data",
        license="MIT",
        access_type="open",
        record_type="DocumentRecord",
        permitted_for_training=True,
        permitted_for_evaluation=True,
    )

    stats = ProcessingStats(
        raw_records=100,
        processed_records=100,
        valid_records=95,
        invalid_records=2,
        duplicate_records=3,
    )

    split_stats = SplitStatistics(
        dataset_name="test_dataset",
        total_records=95,
        train_count=65,
        val_count=15,
        test_count=15,
        seed=42,
    )

    files = [
        {
            "split": "train",
            "file_path": str(tmp_path / "train.jsonl"),
            "format": "jsonl",
            "record_count": 65,
            "file_size_bytes": 1024,
            "sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        }
    ]

    manifest = ManifestManager.create_manifest(
        metadata=meta,
        stats=stats,
        split_stats=split_stats,
        files=files,
    )

    assert manifest.name == "test_dataset"
    assert manifest.license == "MIT"
    assert manifest.valid_records_count == 95
    assert manifest.split_sizes["train"] == 65

    # Save manifest
    manifest_path = ManifestManager.save_manifest(manifest, tmp_path)
    assert manifest_path.exists()

    # Load back
    loaded_manifest = ManifestManager.load_manifest(manifest_path)
    assert loaded_manifest.name == "test_dataset"
    assert loaded_manifest.files[0].record_count == 65

    # Generate dataset card
    card_md = ManifestManager.generate_dataset_card(loaded_manifest, tmp_path)
    assert "# Dataset Card: test_dataset" in card_md
    assert "- **License:** `MIT`" in card_md
    assert "abcdef1234567890..." in card_md
    assert (tmp_path / "README.md").exists()
