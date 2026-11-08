"""Storage and persistence utilities for processed TrustRAG datasets.

Supports saving and loading normalized records in JSONL and Parquet formats
with atomic writes and SHA-256 checksum computation.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Type, Union

from pydantic import BaseModel

from .exceptions import StorageError
from .schemas import (
    ClaimVerificationRecord,
    DocumentRecord,
    NormalizedRecord,
    QueryRecord,
    SecurityRecord,
)

SCHEMA_MAPPING: Dict[str, Type[BaseModel]] = {
    "DocumentRecord": DocumentRecord,
    "QueryRecord": QueryRecord,
    "ClaimVerificationRecord": ClaimVerificationRecord,
    "SecurityRecord": SecurityRecord,
}


def compute_file_sha256(path: Union[str, Path]) -> str:
    """Compute the SHA-256 checksum of a file on disk."""
    hasher = hashlib.sha256()
    with Path(path).open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class DatasetStorage:
    """Handles atomic serialization and deserialization of processed datasets."""

    @classmethod
    def save_jsonl(
        cls,
        records: Sequence[Union[BaseModel, Dict[str, Any]]],
        output_path: Union[str, Path],
    ) -> Dict[str, Any]:
        """Save records to a JSONL file atomically.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing file_path, record_count, file_size_bytes, and sha256_checksum.
        """
        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = dest.with_suffix(dest.suffix + ".tmp")

        count = 0
        try:
            with tmp_path.open("w", encoding="utf-8") as f:
                for rec in records:
                    if isinstance(rec, BaseModel):
                        data = rec.model_dump()
                    elif isinstance(rec, dict):
                        data = rec
                    else:
                        raise StorageError(f"Cannot serialize item of type {type(rec)}")
                    f.write(json.dumps(data, ensure_ascii=False) + "\n")
                    count += 1
                f.flush()
                os.fsync(f.fileno())

            # Atomic replace
            tmp_path.replace(dest)
        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink()
            raise StorageError(f"Failed to save JSONL dataset to {dest}: {e}")

        checksum = compute_file_sha256(dest)
        size_bytes = dest.stat().st_size
        return {
            "file_path": str(dest.resolve()),
            "format": "jsonl",
            "record_count": count,
            "file_size_bytes": size_bytes,
            "sha256": checksum,
        }

    @classmethod
    def load_jsonl(
        cls,
        file_path: Union[str, Path],
        record_type: Optional[Type[NormalizedRecord]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[Union[NormalizedRecord, Dict[str, Any]]]:
        """Load records from a JSONL file."""
        path = Path(file_path)
        if not path.is_file():
            raise StorageError(f"File not found: {path}")

        count = 0
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception as e:
                    raise StorageError(f"Corrupt line {line_no} in {path}: {e}")

                if record_type is not None:
                    try:
                        record = record_type.model_validate(data)
                        yield record
                    except Exception as e:
                        raise StorageError(f"Validation failed for record on line {line_no}: {e}")
                else:
                    yield data

                count += 1
                if limit is not None and count >= limit:
                    break

    @classmethod
    def save_parquet(
        cls,
        records: Sequence[Union[BaseModel, Dict[str, Any]]],
        output_path: Union[str, Path],
    ) -> Dict[str, Any]:
        """Save records to a Parquet file atomically."""
        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = dest.with_suffix(dest.suffix + ".tmp")

        try:
            import pyarrow as pa
            import pyarrow.parquet as pq

            dict_records = []
            for rec in records:
                item = rec.model_dump() if isinstance(rec, BaseModel) else dict(rec)
                for dict_key in ("metadata", "trigger_metadata"):
                    if dict_key in item and isinstance(item[dict_key], dict):
                        item[dict_key] = json.dumps(item[dict_key])
                dict_records.append(item)

            table = pa.Table.from_pylist(dict_records)
            pq.write_table(table, tmp_path)
            tmp_path.replace(dest)
        except Exception as e:
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception:
                pass
            raise StorageError(f"Failed to save Parquet dataset to {dest}: {e}")

        checksum = compute_file_sha256(dest)
        size_bytes = dest.stat().st_size
        return {
            "file_path": str(dest.resolve()),
            "format": "parquet",
            "record_count": len(records),
            "file_size_bytes": size_bytes,
            "sha256": checksum,
        }


__all__ = [
    "SCHEMA_MAPPING",
    "compute_file_sha256",
    "DatasetStorage",
]
