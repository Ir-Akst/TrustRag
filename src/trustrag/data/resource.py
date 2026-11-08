"""Storage estimation, disk-space checks, and resource management for TrustRAG.

Phase 02 Resource Management:
- Checks disk space before large acquisitions.
- Estimates dataset storage requirements.
- Reports disk usage across raw, processed, and benchmark tiers.
- Formats human-readable sizes.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from trustrag.data.exceptions import StorageError


def format_bytes(num_bytes: int) -> str:
    """Format bytes into human-readable string (KB, MB, GB)."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


@dataclass
class StorageTierReport:
    """Report detailing storage usage for a directory tier."""

    name: str
    path: str
    total_bytes: int = 0
    file_count: int = 0
    jsonl_count: int = 0
    parquet_count: int = 0

    @property
    def human_size(self) -> str:
        return format_bytes(self.total_bytes)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "total_bytes": self.total_bytes,
            "human_size": self.human_size,
            "file_count": self.file_count,
            "jsonl_count": self.jsonl_count,
            "parquet_count": self.parquet_count,
        }


class ResourceManager:
    """Utility class for checking disk space and inspecting repository storage tiers."""

    SAFETY_MARGIN_BYTES = 50 * 1024 * 1024  # 50 MB safety margin

    @classmethod
    def get_disk_free_bytes(cls, path: Union[str, Path] = ".") -> int:
        """Return free disk space in bytes for the volume hosting path."""
        p = Path(path).resolve()
        try:
            usage = shutil.disk_usage(p)
            return usage.free
        except Exception:
            # Fallback if shutil.disk_usage fails
            return 10 * 1024 * 1024 * 1024  # Assume 10GB if undetectable

    @classmethod
    def check_disk_space(
        cls,
        estimated_bytes: int,
        target_path: Union[str, Path] = "data",
        raise_on_insufficient: bool = True,
    ) -> bool:
        """Check if target disk volume has enough space for estimated bytes plus safety margin.

        Raises
        ------
        StorageError
            If free disk space is less than estimated_bytes + SAFETY_MARGIN_BYTES.
        """
        free_bytes = cls.get_disk_free_bytes(target_path)
        required = estimated_bytes + cls.SAFETY_MARGIN_BYTES
        if free_bytes < required:
            msg = (
                f"Insufficient disk space on target volume! Required: {format_bytes(required)} "
                f"(including {format_bytes(cls.SAFETY_MARGIN_BYTES)} margin), but only "
                f"{format_bytes(free_bytes)} free."
            )
            if raise_on_insufficient:
                raise StorageError(msg)
            return False
        return True

    @classmethod
    def estimate_dataset_storage(
        cls,
        record_count: int,
        avg_record_bytes: int = 1024,
    ) -> int:
        """Estimate required bytes for a dataset partition based on record count."""
        return record_count * avg_record_bytes

    @classmethod
    def inspect_directory_tier(cls, name: str, dir_path: Union[str, Path]) -> StorageTierReport:
        """Inspect storage metrics for a specific directory."""
        p = Path(dir_path)
        report = StorageTierReport(name=name, path=p.as_posix())
        if not p.exists():
            return report

        for root, _, files in os.walk(p):
            for f in files:
                fpath = Path(root) / f
                try:
                    size = fpath.stat().st_size
                    report.total_bytes += size
                    report.file_count += 1
                    if f.endswith(".jsonl"):
                        report.jsonl_count += 1
                    elif f.endswith(".parquet"):
                        report.parquet_count += 1
                except (OSError, PermissionError):
                    continue
        return report

    @classmethod
    def report_repository_storage(cls, base_dir: Union[str, Path] = "data") -> Dict[str, Any]:
        """Generate a complete repository storage breakdown across raw, processed, and benchmarks."""
        base = Path(base_dir)
        raw_report = cls.inspect_directory_tier("raw", base / "raw")
        proc_report = cls.inspect_directory_tier("processed", base / "processed")
        bench_report = cls.inspect_directory_tier("benchmarks", base / "benchmarks")

        total_bytes = raw_report.total_bytes + proc_report.total_bytes + bench_report.total_bytes
        total_files = raw_report.file_count + proc_report.file_count + bench_report.file_count
        free_bytes = cls.get_disk_free_bytes(base)

        return {
            "total_bytes": total_bytes,
            "total_human_size": format_bytes(total_bytes),
            "total_files": total_files,
            "disk_free_bytes": free_bytes,
            "disk_free_human": format_bytes(free_bytes),
            "tiers": {
                "raw": raw_report.to_dict(),
                "processed": proc_report.to_dict(),
                "benchmarks": bench_report.to_dict(),
            },
        }


__all__ = [
    "format_bytes",
    "StorageTierReport",
    "ResourceManager",
]

