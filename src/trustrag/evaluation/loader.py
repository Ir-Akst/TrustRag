"""Dataset loading and validation utilities for Phase 04 evaluation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from trustrag.data.schemas import (
    ClaimVerificationRecord,
    QueryRecord,
    SecurityRecord,
)
from trustrag.evaluation.schemas import ErrorRecord

SCHEMA_BY_BENCHMARK: dict[str, type[BaseModel]] = {
    "clean_rag": QueryRecord,
    "knowledge_poisoning": SecurityRecord,
    "adversarial_robustness": SecurityRecord,
    "hallucination": ClaimVerificationRecord,
    "custom_security": SecurityRecord,
}


@dataclass
class LoadedPartition:
    """Container for a loaded evaluation partition and its integrity metadata."""

    dataset_name: str
    split: str
    partition_path: Path
    manifest_checksum: str | None = None
    partition_sha256: str | None = None
    crlf_manifest_match: bool | None = None
    is_synthetic: bool = False
    records: list[Any] = field(default_factory=list)
    invalid_records: list[ErrorRecord] = field(default_factory=list)


def load_evaluation_partition(
    dataset_name: str,
    split: str = "test",
    *,
    dataset_dir: str | Path | None = None,
    file_path: str | Path | None = None,
    schema_cls: type[BaseModel] | None = None,
    limit: int | None = None,
) -> LoadedPartition:
    """Load and validate an evaluation partition while tracking invalid/corrupt records."""
    if file_path is not None:
        target_file = Path(file_path)
        base_dir = target_file.parent
    else:
        base_dir = Path(dataset_dir) if dataset_dir else Path("data/benchmarks") / dataset_name
        target_file = base_dir / f"{split}.jsonl"

    if not target_file.is_file():
        raise FileNotFoundError(f"Evaluation partition file not found: {target_file}")

    raw_bytes = target_file.read_bytes()
    partition_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    crlf_sha256 = hashlib.sha256(raw_bytes.replace(b"\n", b"\r\n")).hexdigest()

    manifest_path = base_dir / "manifest.json"
    manifest_checksum: str | None = None
    crlf_match: bool | None = None
    if manifest_path.is_file():
        manifest_bytes = manifest_path.read_bytes()
        manifest_checksum = hashlib.sha256(manifest_bytes).hexdigest()
        try:
            manifest_data = json.loads(manifest_bytes.decode("utf-8"))
            for entry in manifest_data.get("files", []):
                if entry.get("file_path") == target_file.name:
                    recorded = entry.get("sha256")
                    crlf_match = recorded in (partition_sha256, crlf_sha256)
                    break
        except Exception:
            crlf_match = None

    resolved_cls = schema_cls or SCHEMA_BY_BENCHMARK.get(dataset_name)
    records: list[Any] = []
    invalid_records: list[ErrorRecord] = []
    is_synthetic = dataset_name in {"knowledge_poisoning", "adversarial_robustness", "custom_security"}

    with target_file.open("r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except Exception as exc:
                invalid_records.append(
                    ErrorRecord(
                        sample_id=f"line_{line_no}",
                        error_type="JSONDecodeError",
                        message=str(exc),
                    )
                )
                continue

            if not isinstance(obj, dict):
                invalid_records.append(
                    ErrorRecord(
                        sample_id=f"line_{line_no}",
                        error_type="SchemaError",
                        message=f"Expected JSON object, got {type(obj).__name__}",
                    )
                )
                continue

            if isinstance(obj.get("metadata"), dict) and obj["metadata"].get("is_synthetic"):
                is_synthetic = True
            if isinstance(obj.get("provenance"), str) and "synthetic" in obj["provenance"].lower():
                is_synthetic = True

            if resolved_cls is not None:
                try:
                    rec = resolved_cls.model_validate(obj)
                except PydanticValidationError as exc:
                    sid = str(
                        obj.get("record_id")
                        or obj.get("query_id")
                        or obj.get("document_id")
                        or f"line_{line_no}"
                    )
                    invalid_records.append(
                        ErrorRecord(
                            sample_id=sid,
                            error_type="PydanticValidationError",
                            message=str(exc),
                        )
                    )
                    continue
                records.append(rec)
            else:
                records.append(obj)

            if limit is not None and len(records) >= limit:
                break

    return LoadedPartition(
        dataset_name=dataset_name,
        split=split,
        partition_path=target_file,
        manifest_checksum=manifest_checksum,
        partition_sha256=partition_sha256,
        crlf_manifest_match=crlf_match,
        is_synthetic=is_synthetic,
        records=records,
        invalid_records=invalid_records,
    )


__all__ = ["SCHEMA_BY_BENCHMARK", "LoadedPartition", "load_evaluation_partition"]
