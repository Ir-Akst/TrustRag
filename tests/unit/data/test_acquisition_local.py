"""Unit tests for local file importing (.json, .jsonl, .csv, .parquet)."""

import csv
import json
from pathlib import Path
import pytest

from trustrag.data.acquisition.local import LocalFileImporter
from trustrag.data.exceptions import AcquisitionError


def test_read_jsonl(tmp_path: Path):
    file_path = tmp_path / "data.jsonl"
    lines = [
        {"id": "1", "text": "First"},
        {"id": "2", "text": "Second"},
        {"id": "3", "text": "Third"},
    ]
    with file_path.open("w", encoding="utf-8") as f:
        for item in lines:
            f.write(json.dumps(item) + "\n")

    # Read all
    records = list(LocalFileImporter.read_records(file_path))
    assert len(records) == 3
    assert records[0]["text"] == "First"

    # Read with limit
    limited = list(LocalFileImporter.read_records(file_path, limit=2))
    assert len(limited) == 2


def test_read_json_array(tmp_path: Path):
    file_path = tmp_path / "data.json"
    items = [{"id": "10", "query": "Q1"}, {"id": "20", "query": "Q2"}]
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(items, f)

    records = list(LocalFileImporter.read_records(file_path))
    assert len(records) == 2
    assert records[1]["query"] == "Q2"


def test_read_json_nested_dict(tmp_path: Path):
    file_path = tmp_path / "data.json"
    data = {"passages": [{"pid": "p1", "text": "Hello"}, {"pid": "p2", "text": "World"}]}
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f)

    records = list(LocalFileImporter.read_records(file_path))
    assert len(records) == 2
    assert records[0]["text"] == "Hello"


def test_read_csv(tmp_path: Path):
    file_path = tmp_path / "data.csv"
    with file_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "question", "answer"])
        writer.writeheader()
        writer.writerow({"id": "c1", "question": "Why?", "answer": "Because."})
        writer.writerow({"id": "c2", "question": "When?", "answer": "Now."})

    records = list(LocalFileImporter.read_records(file_path))
    assert len(records) == 2
    assert records[0]["question"] == "Why?"


def test_read_parquet(tmp_path: Path):
    pytest.importorskip("pyarrow")
    import pyarrow as pa
    import pyarrow.parquet as pq

    file_path = tmp_path / "data.parquet"
    data = [{"doc_id": "d1", "content": "PyArrow Parquet Content"}]
    table = pa.Table.from_pylist(data)
    pq.write_table(table, file_path)

    records = list(LocalFileImporter.read_records(file_path))
    assert len(records) == 1
    assert records[0]["content"] == "PyArrow Parquet Content"


def test_missing_file_raises(tmp_path: Path):
    with pytest.raises(AcquisitionError, match="not found"):
        list(LocalFileImporter.read_records(tmp_path / "non_existent.jsonl"))


def test_unsupported_format_raises(tmp_path: Path):
    bad_file = tmp_path / "test.txt"
    bad_file.write_text("plain text", encoding="utf-8")

    with pytest.raises(AcquisitionError, match="Unsupported file format"):
        list(LocalFileImporter.read_records(bad_file))


def test_malformed_jsonl_raises(tmp_path: Path):
    bad_jsonl = tmp_path / "corrupt.jsonl"
    bad_jsonl.write_text("{\"valid\": 1}\n{not json\n", encoding="utf-8")

    with pytest.raises(AcquisitionError, match="Malformed JSON"):
        list(LocalFileImporter.read_records(bad_jsonl))

