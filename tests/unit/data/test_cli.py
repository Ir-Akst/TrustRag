"""Unit tests for the TrustRAG Dataset Engineering CLI."""

import json
from pathlib import Path

from trustrag.data.cli import main


def test_cli_list(capsys):
    ret = main(["list"])
    assert ret == 0
    out, _ = capsys.readouterr()
    assert "natural_questions" in out
    assert "ragtruth" in out
    assert "rsb" in out
    assert "fineweb" in out


def test_cli_inspect(capsys):
    ret = main(["inspect", "boolq"])
    assert ret == 0
    out, _ = capsys.readouterr()
    assert "Dataset Metadata: boolq" in out
    assert "google/boolq" in out
    assert "CC-BY-SA-3.0" in out


def test_cli_import_and_validate(tmp_path: Path, capsys):
    # Create test local file
    data_file = tmp_path / "custom_data.jsonl"
    lines = [
        {"id": "c1", "question": "Is earth round?", "passage": "Earth is round.", "answer": True, "title": "Earth"},
        {"id": "c2", "question": "Can dogs talk?", "passage": "Dogs bark.", "answer": False, "title": "Dog"},
    ]
    with data_file.open("w", encoding="utf-8") as f:
        for item in lines:
            f.write(json.dumps(item) + "\n")

    out_file = tmp_path / "imported.jsonl"
    ret_import = main(["import", "boolq", str(data_file), "--output", str(out_file)])
    assert ret_import == 0
    assert out_file.exists()

    # Validate the imported file
    ret_val = main(["validate", str(out_file), "--dataset", "boolq"])
    assert ret_val == 0
    out, _ = capsys.readouterr()
    assert "Status:                  PASS" in out


def test_cli_split_stats(tmp_path: Path, capsys):
    # Create test records for custom_security
    data_file = tmp_path / "sec.jsonl"
    records = []
    for i in range(10):
        records.append({
            "record_id": f"s_{i}",
            "passage": f"Security passage {i}",
            "clean_poison_label": "clean" if i % 2 == 0 else "poisoned",
            "source_id": f"group_{i // 2}",
        })
    with data_file.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    ret_split = main(["split-stats", "custom_security", "--local-path", str(data_file), "--seed", "42"])
    assert ret_split == 0
    out, _ = capsys.readouterr()
    assert "Leakage Detected:        NO (PASS)" in out


def test_cli_manifest(tmp_path: Path, capsys):
    proc_dir = tmp_path / "processed" / "boolq"
    proc_dir.mkdir(parents=True)
    partition_file = proc_dir / "train.jsonl"
    with partition_file.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"query_id": "1", "query": "q", "source_dataset": "boolq"}) + "\n")

    ret_man = main(["manifest", "boolq", "--dir", str(proc_dir)])
    assert ret_man == 0
    assert (proc_dir / "manifest.json").exists()
    assert (proc_dir / "README.md").exists()

