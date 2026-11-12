"""Dataset inventory, SHA-256 provenance, and split integrity auditing for Phase 10."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from trustrag.evaluation.external_benchmarks import (
    EXTERNAL_RESEARCH_BENCHMARKS,
    run_all_external_benchmarks,
)


class DatasetFileAudit(BaseModel):
    """SHA-256 and record count for one local dataset file."""

    path: str
    split: str
    record_count: int
    sha256: str
    size_bytes: int


class DatasetInventoryItem(BaseModel):
    """Complete provenance and availability record for one dataset."""

    dataset_name: str
    scope: Literal["external_target", "local_benchmark", "local_smoke_fixture"]
    official_name: str
    source_uri: str
    license: str
    access_type: str
    permitted_for_training: bool
    permitted_for_evaluation: bool
    status: Literal["AVAILABLE", "PARTIALLY_READY", "BLOCKED"]
    canonical_target_count: int | None = None
    total_local_records: int = 0
    files: list[DatasetFileAudit] = Field(default_factory=list)
    notes: str = ""


class Phase10DatasetInventory(BaseModel):
    """Full Phase 10 dataset inventory report."""

    offline: bool = True
    seed: int = 42
    items: list[DatasetInventoryItem] = Field(default_factory=list)


def _sha256_and_lines(path: Path) -> tuple[str, int, int]:
    h = hashlib.sha256()
    raw = path.read_bytes()
    h.update(raw)
    if path.suffix.lower() == ".jsonl":
        lines = sum(1 for line in raw.decode("utf-8", errors="replace").splitlines() if line.strip())
    elif path.suffix.lower() == ".json":
        try:
            obj = json.loads(raw.decode("utf-8"))
            lines = len(obj) if isinstance(obj, list) else 1
        except Exception:
            lines = 0
    else:
        lines = 0
    return h.hexdigest(), lines, len(raw)


def build_dataset_inventory(repo_root: str | Path = ".") -> Phase10DatasetInventory:
    """Audit all external benchmark targets and local datasets without network calls."""
    root = Path(repo_root).resolve()
    raw_dir = root / "data" / "raw"
    proc_dir = root / "data" / "processed"
    backup_dir = root / "data" / "benchmarks_backup"

    items: list[DatasetInventoryItem] = []

    # 1. External research benchmarks (via Phase 08 external_benchmarks harness)
    ext_report = run_all_external_benchmarks(
        raw_base_dir=raw_dir,
        processed_base_dir=proc_dir,
        seed=42,
        min_research_records=100,
    )
    ext_map = {r.dataset_name: r for r in ext_report.results}
    for name in EXTERNAL_RESEARCH_BENCHMARKS:
        res = ext_map[name]
        files: list[DatasetFileAudit] = []
        for p_str in res.integrity.local_file_paths:
            p = Path(p_str)
            if p.exists():
                digest, cnt, sz = _sha256_and_lines(p)
                files.append(
                    DatasetFileAudit(
                        path=str(p.relative_to(root)) if p.is_relative_to(root) else str(p),
                        split=p.stem,
                        record_count=cnt,
                        sha256=digest,
                        size_bytes=sz,
                    )
                )
        status: Literal["AVAILABLE", "PARTIALLY_READY", "BLOCKED"] = (
            "PARTIALLY_READY"
            if res.status == "PARTIALLY_READY"
            else ("AVAILABLE" if res.status == "COMPLETED" else "BLOCKED")
        )
        items.append(
            DatasetInventoryItem(
                dataset_name=name,
                scope="external_target",
                official_name=name,
                source_uri=res.integrity.source_uri,
                license=res.integrity.license,
                access_type=res.integrity.access_type,
                permitted_for_training=res.integrity.permitted_for_training,
                permitted_for_evaluation=res.integrity.permitted_for_evaluation,
                status=status,
                canonical_target_count=res.integrity.canonical_target_count,
                total_local_records=sum(f.record_count for f in files),
                files=files,
                notes=res.reason,
            )
        )

    # 2. Local processed & smoke corpora (BoolQ, WiCE, ExpertQA)
    local_specs: list[tuple[str, Literal["local_benchmark", "local_smoke_fixture"], str, str, Path, str]] = [
        (
            "boolq",
            "local_benchmark",
            "google/boolq",
            "CC-BY-SA-3.0",
            proc_dir / "boolq" / "custom_splits",
            "100 records partitioned 70/15/15 (custom_train/val/test)",
        ),
        (
            "wice_smoke",
            "local_smoke_fixture",
            "https://github.com/ryokamoi/wice",
            "MIT",
            raw_dir / "wice",
            "Local smoke fixture only (4 records)",
        ),
        (
            "expertqa_smoke",
            "local_smoke_fixture",
            "https://github.com/chaitanyamalaviya/ExpertQA",
            "Apache-2.0 / Academic",
            raw_dir / "expertqa",
            "Local smoke fixture only (4 records)",
        ),
    ]
    for name, scope, uri, lic, folder, notes in local_specs:
        files = []
        if folder.exists():
            for f in sorted(folder.glob("*.jsonl")):
                digest, cnt, sz = _sha256_and_lines(f)
                files.append(
                    DatasetFileAudit(
                        path=str(f.relative_to(root)),
                        split=f.stem.replace("custom_", ""),
                        record_count=cnt,
                        sha256=digest,
                        size_bytes=sz,
                    )
                )
        items.append(
            DatasetInventoryItem(
                dataset_name=name,
                scope=scope,
                official_name=name,
                source_uri=uri,
                license=lic,
                access_type="local",
                permitted_for_training=True,
                permitted_for_evaluation=True,
                status="AVAILABLE" if files else "BLOCKED",
                total_local_records=sum(f.record_count for f in files),
                files=files,
                notes=notes,
            )
        )

    # 3. Local TrustRAG benchmark suites (data/benchmarks_backup)
    for ds_name in ("adversarial_robustness", "clean_rag", "hallucination", "knowledge_poisoning"):
        ds_dir = backup_dir / ds_name
        files = []
        for split in ("train", "val", "test"):
            f = ds_dir / f"{split}.jsonl"
            if f.exists():
                digest, cnt, sz = _sha256_and_lines(f)
                files.append(
                    DatasetFileAudit(
                        path=str(f.relative_to(root)),
                        split=split,
                        record_count=cnt,
                        sha256=digest,
                        size_bytes=sz,
                    )
                )
        items.append(
            DatasetInventoryItem(
                dataset_name=ds_name,
                scope="local_benchmark",
                official_name=f"TrustRAG/{ds_name}",
                source_uri="local://data/benchmarks_backup",
                license="Internal / Derived",
                access_type="local",
                permitted_for_training=True,
                permitted_for_evaluation=True,
                status="AVAILABLE" if files else "BLOCKED",
                total_local_records=sum(f.record_count for f in files),
                files=files,
                notes="Internal benchmark backup splits; clean_rag/hallucination/knowledge_poisoning/adversarial_robustness",
            )
        )

    return Phase10DatasetInventory(offline=True, seed=42, items=items)
