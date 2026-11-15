"""Track 1 Step 1: Unit tests for dataset acquisition, ingestion, integrity, and loaders."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from trustrag.data.acquisition.downloader import (
    DatasetArtifactEntry,
    DatasetDownloader,
    DatasetManifest,
    compute_file_sha256,
)
from trustrag.data.exceptions import AcquisitionError, ValidationError
from trustrag.data.loaders.halueval import HaluEvalAdapter
from trustrag.data.loaders.hotpotqa import HotpotQAAdapter
from trustrag.data.loaders.llm_aggrefact import LLMAggreFactAdapter
from trustrag.data.loaders.ms_marco import MSMarcoAdapter
from trustrag.data.loaders.ragtruth import RAGTruthAdapter
from trustrag.data.loaders.rsb import RSBAdapter
from trustrag.data.schemas import ClaimVerificationRecord, QueryRecord


# -----------------------------------------------------------------------------
# 1. Downloader and Manifest Unit Tests
# -----------------------------------------------------------------------------

def test_compute_file_sha256(tmp_path: Path) -> None:
    test_file = tmp_path / "sample.txt"
    test_file.write_text("TrustRAG Research Completion", encoding="utf-8")
    expected_hash = compute_file_sha256(test_file)
    assert len(expected_hash) == 64
    assert expected_hash == compute_file_sha256(test_file)


def test_dataset_manifest_roundtrip(tmp_path: Path) -> None:
    manifest = DatasetManifest(
        dataset_name="test_dataset",
        version="1.0.0",
        source_uri="https://example.com/data.json",
        license="MIT",
        status="DOWNLOADED",
        download_timestamp="2026-11-13T00:00:00Z",
        raw_artifacts=[
            DatasetArtifactEntry(
                file_name="data.json",
                relative_path="raw/data.json",
                file_size_bytes=1024,
                sha256="abc123def456",
                record_count=100,
            )
        ],
        metadata={"domain": "research"},
    )
    manifest_path = manifest.save(tmp_path)
    assert manifest_path.exists()

    loaded = DatasetManifest.load(tmp_path)
    assert loaded.dataset_name == "test_dataset"
    assert loaded.version == "1.0.0"
    assert len(loaded.raw_artifacts) == 1
    assert loaded.raw_artifacts[0].sha256 == "abc123def456"
    assert loaded.metadata["domain"] == "research"


def test_download_file_integrity_mismatch(tmp_path: Path) -> None:
    downloader = DatasetDownloader(raw_root=tmp_path / "raw", processed_root=tmp_path / "proc")
    mock_resp = MagicMock()
    mock_resp.read.side_effect = [b"corrupted data", b""]
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.headers = {"content-length": "14"}

    target_file = tmp_path / "raw" / "test.dat"
    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(ValidationError, match="SHA-256 checksum mismatch"):
            downloader.download_url(
                url="https://example.com/test.dat",
                dest_path=target_file,
                expected_sha256="0000000000000000000000000000000000000000000000000000000000000000",
            )


def test_download_file_resume_when_already_complete(tmp_path: Path) -> None:
    downloader = DatasetDownloader(raw_root=tmp_path / "raw", processed_root=tmp_path / "proc")
    target_file = tmp_path / "raw" / "valid.dat"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_bytes(b"valid canonical content")
    expected_hash = compute_file_sha256(target_file)

    with patch("urllib.request.urlopen") as mock_open:
        # If target file exists and sha256 matches, download_url should verify and return without downloading
        downloaded = downloader.download_url(
            url="https://example.com/valid.dat",
            dest_path=target_file,
            expected_sha256=expected_hash,
        )
        assert downloaded == target_file
        mock_open.assert_not_called()


# -----------------------------------------------------------------------------
# 2. Loader Verification with Local Data
# -----------------------------------------------------------------------------

def test_ragtruth_loader_loads_processed_or_raw(tmp_path: Path) -> None:
    local_file = tmp_path / "test.jsonl"
    sample_records = [
        {
            "record_id": "rt_01",
            "document": "Python is a programming language.",
            "claim": "Python is interpreted.",
            "label": "FACTUAL",
            "source_dataset": "ragtruth",
            "metadata": {"task": "qa"},
        },
        {
            "record_id": "rt_02",
            "document": "The Earth orbits the Sun.",
            "claim": "The Sun orbits the Earth.",
            "label": "HALLUCINATED",
            "source_dataset": "ragtruth",
            "metadata": {"task": "summary"},
        },
    ]
    with open(local_file, "w", encoding="utf-8") as f:
        for r in sample_records:
            f.write(json.dumps(r) + "\n")

    adapter = RAGTruthAdapter(
        split="test",
        local_path=local_file,
        offline=True,
    )
    records = list(adapter.process())
    assert len(records) == 2
    assert all(isinstance(r, ClaimVerificationRecord) for r in records)
    assert records[0].label == "FACTUAL"
    assert records[1].label == "HALLUCINATED"


def test_halueval_loader_splits_into_factual_and_hallucinated(tmp_path: Path) -> None:
    local_file = tmp_path / "qa_data.json"
    raw_items = [
        {
            "knowledge": "The speed of light is 300,000 km/s.",
            "question": "What is the speed of light?",
            "right_answer": "It is approximately 300,000 km/s.",
            "hallucinated_answer": "It is 100 km/h.",
        }
    ]
    local_file.write_text(json.dumps(raw_items), encoding="utf-8")

    adapter = HaluEvalAdapter(
        split="test",
        local_path=local_file,
        offline=True,
    )
    records = list(adapter.process())
    assert len(records) == 2
    labels = {r.label for r in records}
    assert labels == {"FACTUAL", "HALLUCINATED"}
    assert all(isinstance(r, ClaimVerificationRecord) for r in records)


def test_hotpotqa_loader_transforms_to_query_record(tmp_path: Path) -> None:
    local_file = tmp_path / "validation.jsonl"
    sample_item = {
        "id": "hp_sample_1",
        "question": "Where was Alan Turing born?",
        "answer": "London, England",
        "supporting_facts": {"title": ["Alan Turing", "London"]},
    }
    local_file.write_text(json.dumps(sample_item) + "\n", encoding="utf-8")

    adapter = HotpotQAAdapter(
        split="validation",
        local_path=local_file,
        offline=True,
    )
    records = list(adapter.process())
    assert len(records) == 1
    assert isinstance(records[0], QueryRecord)
    assert records[0].query_id == "hp_sample_1"
    assert records[0].answer == "London, England"
    assert "Alan Turing" in records[0].relevant_document_ids


def test_ms_marco_loader_transforms_to_query_record(tmp_path: Path) -> None:
    local_file = tmp_path / "validation.jsonl"
    sample_item = {
        "query_id": 999,
        "query": "what is photosynthesis",
        "answers": ["Photosynthesis is the process by which green plants make food."],
        "passages": {
            "passage_text": ["Passage 1 text", "Passage 2 text"],
            "is_selected": [1, 0],
        },
    }
    local_file.write_text(json.dumps(sample_item) + "\n", encoding="utf-8")

    adapter = MSMarcoAdapter(
        split="validation",
        local_path=local_file,
        offline=True,
    )
    records = list(adapter.process())
    assert len(records) == 1
    assert isinstance(records[0], QueryRecord)
    assert records[0].query_id == "999"
    assert records[0].query == "what is photosynthesis"
    assert "Photosynthesis" in (records[0].answer or "")
    assert len(records[0].relevant_document_ids) == 1


# -----------------------------------------------------------------------------
# 3. Gated / Blocked Dataset Failure Handling
# -----------------------------------------------------------------------------

def test_llm_aggrefact_blocked_handling_offline(tmp_path: Path) -> None:
    adapter = LLMAggreFactAdapter(
        split="test",
        cache_dir=tmp_path / "cache",
        offline=True,
    )
    with pytest.raises(AcquisitionError, match="unavailable in offline mode|ACCESS_BLOCKED|gated|token"):
        list(adapter.load_raw())


def test_rsb_blocked_handling_offline(tmp_path: Path) -> None:
    adapter = RSBAdapter(
        split="test",
        cache_dir=tmp_path / "cache",
        offline=True,
    )
    with pytest.raises(AcquisitionError, match="ACCESS_BLOCKED|arXiv:2505.18543|local"):
        list(adapter.load_raw())
