"""Local file dataset importer for TrustRAG.

Supports streaming or reading records from:
- JSON (.json)
- JSON Lines (.jsonl)
- CSV (.csv)
- Parquet (.parquet)
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Union

from trustrag.data.exceptions import AcquisitionError


class LocalFileImporter:
    """Importer for reading local files of various tabular and document formats."""

    @classmethod
    def read_records(
        cls,
        file_path: Union[str, Path],
        limit: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Read and yield raw dictionary records from a local file.

        Parameters
        ----------
        file_path: str | Path
            Path to the local data file.
        limit: int | None
            Maximum number of records to read.

        Yields
        ------
        Dict[str, Any]
            Parsed record dictionary.
        """
        path = Path(file_path)
        if not path.is_file():
            raise AcquisitionError(f"Local dataset file not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".jsonl":
            yield from cls._read_jsonl(path, limit=limit)
        elif suffix == ".json":
            yield from cls._read_json(path, limit=limit)
        elif suffix == ".csv":
            yield from cls._read_csv(path, limit=limit)
        elif suffix == ".parquet":
            yield from cls._read_parquet(path, limit=limit)
        else:
            raise AcquisitionError(
                f"Unsupported file format '{suffix}' for {path}. "
                "Supported formats: .json, .jsonl, .csv, .parquet"
            )

    @classmethod
    def _read_jsonl(cls, path: Path, limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        count = 0
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if isinstance(record, dict):
                        yield record
                        count += 1
                        if limit is not None and count >= limit:
                            return
                except json.JSONDecodeError as e:
                    raise AcquisitionError(f"Malformed JSON on line {line_no} of {path}: {e}")

    @classmethod
    def _read_json(cls, path: Path, limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise AcquisitionError(f"Failed to read JSON file {path}: {e}")

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Check for common container keys
            for key in ("data", "records", "items", "rows", "passages", "queries"):
                if key in data and isinstance(data[key], list):
                    items = data[key]
                    break
            else:
                items = [data]
        else:
            raise AcquisitionError(f"Unexpected JSON root structure in {path}: {type(data)}")

        for count, item in enumerate(items):
            if limit is not None and count >= limit:
                break
            if isinstance(item, dict):
                yield item

    @classmethod
    def _read_csv(cls, path: Path, limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        try:
            with path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for count, row in enumerate(reader):
                    if limit is not None and count >= limit:
                        break
                    yield dict(row)
        except Exception as e:
            raise AcquisitionError(f"Failed to read CSV file {path}: {e}")

    @classmethod
    def _read_parquet(cls, path: Path, limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        try:
            import pyarrow.parquet as pq

            parquet_file = pq.ParquetFile(path)
            count = 0
            for batch in parquet_file.iter_batches():
                records = batch.to_pylist()
                for rec in records:
                    yield rec
                    count += 1
                    if limit is not None and count >= limit:
                        return
        except ImportError:
            # Fallback to pandas
            try:
                import pandas as pd

                df = pd.read_parquet(path)
                for count, row in df.iterrows():
                    if limit is not None and count >= limit:
                        break
                    yield row.to_dict()
            except Exception as e:
                raise AcquisitionError(f"Failed to read Parquet file {path}: {e}")
        except Exception as e:
            raise AcquisitionError(f"Error reading Parquet {path}: {e}")


__all__ = ["LocalFileImporter"]

