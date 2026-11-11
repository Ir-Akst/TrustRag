"""Dataset manifest and dataset card generation utilities for TrustRAG.

Maintains machine-readable manifests (manifest.json) recording provenance, licensing,
versions, split sizes, file checksums, and dataset cards (README.md).
Enforces path portability (relative, POSIX-style paths) and manifest consistency validation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field

from .base import DatasetMetadata, ProcessingStats
from .exceptions import ManifestError
from .splitting import SplitStatistics
from .storage import compute_file_sha256


class ManifestFileEntry(BaseModel):
    """Metadata describing a persisted dataset partition file."""

    split: str
    original_split: Optional[str] = None
    processed_split: Optional[str] = None
    split_type: str = "official"  # "official" or "custom"
    file_path: str  # Must be portable relative path with forward slashes
    format: str = "jsonl"  # "jsonl" or "parquet"
    record_count: int
    file_size_bytes: int
    sha256: str


class DatasetManifest(BaseModel):
    """Machine-readable manifest recording complete provenance and metadata for a processed dataset."""

    name: str
    version: str = "1.0.0"
    schema_version: str = "1.0.0"
    preprocessing_version: str = "1.0.0"
    source_identifier: str
    source_url: str
    source_revision: Optional[str] = None
    license: str
    access_conditions: str = "open"
    retrieval_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    config_name: Optional[str] = None
    split_type: str = "official"  # "official", "custom", or "mixed"
    splits_included: List[str] = Field(default_factory=list)
    split_seed: Optional[int] = 42
    split_sizes: Dict[str, int] = Field(default_factory=dict)
    raw_records_count: int = 0
    processed_records_count: int = 0
    valid_records_count: int = 0
    invalid_records_count: int = 0
    duplicate_records_count: int = 0
    empty_records_count: int = 0
    record_type: str = "DocumentRecord"
    files: List[ManifestFileEntry] = Field(default_factory=list)
    known_limitations: Optional[str] = None
    intended_use: str = "Research evaluation and defense benchmarking"
    usage_category: str = "EVALUATION"
    permitted_for_training: bool = True
    permitted_for_evaluation: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_json(self, indent: int = 2) -> str:
        """Serialize manifest to JSON string."""
        return self.model_dump_json(indent=indent)


class ManifestManager:
    """Manager for generating, writing, reading, and validating dataset manifests."""

    @classmethod
    def _normalize_relative_path(cls, path_str: str, base_dir: Optional[Path] = None) -> str:
        """Convert a path to a portable, forward-slash relative path."""
        p = Path(path_str)
        if base_dir:
            try:
                p = p.resolve().relative_to(base_dir.resolve())
            except (ValueError, RuntimeError):
                # If not inside base_dir, just use basename or relative posix
                p = Path(p.name)
        return p.as_posix()

    @classmethod
    def create_file_entry(
        cls,
        file_path: Union[str, Path],
        split: str,
        base_dir: Optional[Union[str, Path]] = None,
        original_split: Optional[str] = None,
        processed_split: Optional[str] = None,
        split_type: str = "official",
        record_count: Optional[int] = None,
    ) -> ManifestFileEntry:
        """Create a validated ManifestFileEntry from an existing or planned file."""
        from .storage import compute_file_sha256

        p = Path(file_path)
        base_p = Path(base_dir) if base_dir else None
        portable_path = cls._normalize_relative_path(str(p), base_p)
        sha256 = compute_file_sha256(p) if p.is_file() else ""
        file_size = p.stat().st_size if p.is_file() else 0
        if record_count is None and p.is_file():
            if p.suffix == ".jsonl":
                with p.open("r", encoding="utf-8") as fh:
                    record_count = sum(1 for line in fh if line.strip())
            else:
                record_count = 0
        return ManifestFileEntry(
            split=split,
            original_split=original_split or split,
            processed_split=processed_split or split,
            split_type=split_type,
            file_path=portable_path,
            format="parquet" if p.suffix == ".parquet" else "jsonl",
            record_count=record_count or 0,
            file_size_bytes=file_size,
            sha256=sha256,
        )

    @classmethod
    def create_manifest(
        cls,
        metadata: DatasetMetadata,
        stats: Optional[ProcessingStats] = None,
        split_stats: Optional[SplitStatistics] = None,
        files: Optional[List[Dict[str, Any]]] = None,
        config_name: Optional[str] = None,
        base_dir: Optional[Union[str, Path]] = None,
        source_revision: Optional[str] = None,
        split_type: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> DatasetManifest:
        """Create a portable DatasetManifest instance."""
        file_entries: List[ManifestFileEntry] = []
        splits_included: List[str] = []
        split_sizes: Dict[str, int] = {}
        base_path = Path(base_dir) if base_dir else None

        determined_split_type = split_type or (split_stats.split_type if split_stats else "official")

        if files:
            for f in files:
                split_name = f.get("split", "all")
                portable_path = cls._normalize_relative_path(str(f.get("file_path", "")), base_path)
                entry = ManifestFileEntry(
                    split=split_name,
                    original_split=f.get("original_split", split_name),
                    processed_split=f.get("processed_split", split_name),
                    split_type=f.get("split_type", determined_split_type),
                    file_path=portable_path,
                    format=f.get("format", "jsonl"),
                    record_count=f.get("record_count", 0),
                    file_size_bytes=f.get("file_size_bytes", 0),
                    sha256=f.get("sha256", ""),
                )
                file_entries.append(entry)
                splits_included.append(split_name)
                split_sizes[split_name] = entry.record_count

        if split_stats:
            split_sizes = {
                "train": split_stats.train_count,
                "val": split_stats.val_count,
                "test": split_stats.test_count,
            }
            splits_included = list(split_sizes.keys())

        total_processed = sum(e.record_count for e in file_entries) if file_entries else (stats.processed_records if stats else 0)

        # Derive appropriate usage category
        if not metadata.permitted_for_training and metadata.permitted_for_evaluation:
            usage_cat = "EVALUATION"
        elif metadata.category == "training_corpus":
            usage_cat = "TRAINING_CORPUS"
        elif metadata.category == "security":
            usage_cat = "SECURITY_BENCHMARK"
        elif metadata.permitted_for_training and metadata.permitted_for_evaluation:
            usage_cat = "TRAINING" if determined_split_type == "official" else "VALIDATION"
        else:
            usage_cat = "EVALUATION"

        return DatasetManifest(
            name=metadata.name,
            source_identifier=metadata.name,
            source_url=metadata.source_uri,
            source_revision=source_revision,
            license=metadata.license,
            access_conditions=metadata.access_type,
            config_name=config_name or metadata.default_config,
            split_type=determined_split_type,
            splits_included=splits_included,
            split_seed=split_stats.seed if split_stats else 42,
            split_sizes=split_sizes,
            raw_records_count=stats.raw_records if stats else total_processed,
            processed_records_count=stats.processed_records if stats else total_processed,
            valid_records_count=stats.valid_records if stats else total_processed,
            invalid_records_count=stats.invalid_records if stats else 0,
            duplicate_records_count=stats.duplicate_records if stats else 0,
            empty_records_count=stats.empty_records if stats else 0,
            record_type=metadata.record_type,
            files=file_entries,
            known_limitations=metadata.known_limitations,
            intended_use=metadata.intended_use,
            usage_category=usage_cat,
            permitted_for_training=metadata.permitted_for_training,
            permitted_for_evaluation=metadata.permitted_for_evaluation,
            metadata=extra_metadata or {},
        )

    @classmethod
    def save_manifest(
        cls,
        manifest: DatasetManifest,
        output_dir: Union[str, Path],
    ) -> Path:
        """Save manifest to manifest.json in the specified output directory.

        Guarantees that all recorded file paths are stored as portable paths relative to output_dir.
        """
        dir_path = Path(output_dir)
        dir_path.mkdir(parents=True, exist_ok=True)
        manifest_path = dir_path / "manifest.json"

        # Ensure file paths in manifest are relative
        for entry in manifest.files:
            entry.file_path = cls._normalize_relative_path(entry.file_path, dir_path)

        try:
            with manifest_path.open("w", encoding="utf-8") as f:
                f.write(manifest.to_json(indent=2))
        except Exception as e:
            raise ManifestError(f"Failed to write manifest to {manifest_path}: {e}")

        return manifest_path

    @classmethod
    def load_manifest(cls, manifest_path: Union[str, Path]) -> DatasetManifest:
        """Load and validate manifest from manifest.json."""
        path = Path(manifest_path)
        if not path.is_file():
            raise ManifestError(f"Manifest file not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return DatasetManifest.model_validate(data)
        except Exception as e:
            raise ManifestError(f"Failed to load manifest from {path}: {e}")

    @classmethod
    def validate_manifest(
        cls,
        manifest: DatasetManifest,
        base_dir: Union[str, Path],
        raise_on_error: bool = False,
    ) -> Tuple[bool, List[str]]:
        """Validate consistency of manifest against actual files on disk.

        Checks:
        1. All referenced partition files exist on disk.
        2. Actual file size matches recorded `file_size_bytes`.
        3. Actual SHA-256 checksum matches recorded `sha256`.
        4. Actual record count matches recorded `record_count`.
        5. File paths do not contain machine-specific absolute path prefixes.

        Returns
        -------
        Tuple[bool, List[str]]
            Tuple of (is_valid, error_messages).
        """
        base = Path(base_dir)
        errors: List[str] = []

        if not manifest.files:
            errors.append("Manifest contains zero file entries.")

        for entry in manifest.files:
            # Check for non-portable absolute paths
            if "\\" in entry.file_path or entry.file_path.startswith("/") or ":" in entry.file_path:
                errors.append(f"Non-portable file path detected in manifest: '{entry.file_path}'")

            target_file = base / entry.file_path
            if not target_file.is_file():
                errors.append(f"Referenced file not found on disk: {target_file}")
                continue

            # Verify size
            actual_size = target_file.stat().st_size
            if actual_size != entry.file_size_bytes:
                errors.append(
                    f"File size mismatch for {entry.file_path}: recorded {entry.file_size_bytes}, "
                    f"actual {actual_size}"
                )

            # Verify checksum
            actual_hash = compute_file_sha256(target_file)
            if actual_hash != entry.sha256:
                errors.append(
                    f"SHA-256 checksum mismatch for {entry.file_path}: recorded {entry.sha256}, "
                    f"actual {actual_hash}"
                )

            # Verify line count for JSONL
            if entry.format == "jsonl":
                with target_file.open("r", encoding="utf-8") as f:
                    actual_count = sum(1 for line in f if line.strip())
                if actual_count != entry.record_count:
                    errors.append(
                        f"Record count mismatch for {entry.file_path}: recorded {entry.record_count}, "
                        f"actual {actual_count}"
                    )

        is_valid = len(errors) == 0
        if not is_valid and raise_on_error:
            raise ManifestError(f"Manifest consistency validation failed for '{manifest.name}': " + "; ".join(errors))

        return is_valid, errors

    @classmethod
    def generate_dataset_card(
        cls,
        manifest: DatasetManifest,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> str:
        """Generate GitHub-style Markdown dataset card documenting provenance, licenses, and usage."""
        lines = [
            f"# Dataset Card: {manifest.name}",
            "",
            "## Summary",
            f"- **Dataset Name:** `{manifest.name}`",
            f"- **Schema Record Type:** `{manifest.record_type}`",
            f"- **Source Identifier / URL:** {manifest.source_url}",
            f"- **Source Revision:** `{manifest.source_revision or 'Unspecified'}`",
            f"- **License:** `{manifest.license}`",
            f"- **Access Conditions:** `{manifest.access_conditions}`",
            f"- **Workflow Usage Category:** `{manifest.usage_category}`",
            f"- **Split Type:** `{manifest.split_type}`",
            f"- **Retrieval Date:** {manifest.retrieval_date}",
            f"- **Schema Version:** `{manifest.schema_version}`",
            f"- **Preprocessing Version:** `{manifest.preprocessing_version}`",
            "",
            "## Intended Use & Permissions",
            f"- {manifest.intended_use}",
            f"- **Permitted for Training:** {'Yes' if manifest.permitted_for_training else 'NO (STRICTLY PROHIBITED)'}",
            f"- **Permitted for Evaluation:** {'Yes' if manifest.permitted_for_evaluation else 'No'}",
            "",
            "## Records and Split Statistics",
            f"- **Raw Records:** {manifest.raw_records_count}",
            f"- **Processed Records:** {manifest.processed_records_count}",
            f"- **Valid Records:** {manifest.valid_records_count}",
            f"- **Duplicate Records:** {manifest.duplicate_records_count}",
            f"- **Empty / Invalid Records:** {manifest.invalid_records_count + manifest.empty_records_count}",
            f"- **Split Seed:** {manifest.split_seed}",
            "",
            "### Partition Sizes",
        ]

        if manifest.split_sizes:
            for split_name, size in manifest.split_sizes.items():
                lines.append(f"- **{split_name}:** {size} records")
        else:
            lines.append("- *(No split statistics provided)*")

        lines.extend([
            "",
            "## Files and Checksums",
        ])

        if manifest.files:
            lines.append("| Split | Split Type | Format | Records | Size (Bytes) | Relative Path | SHA-256 Checksum |")
            lines.append("|---|---|---|---:|---:|---|---|")
            for entry in manifest.files:
                lines.append(
                    f"| {entry.split} | {entry.split_type} | {entry.format} | {entry.record_count} | "
                    f"{entry.file_size_bytes} | `{entry.file_path}` | `{entry.sha256[:16]}...` |"
                )
        else:
            lines.append("- *(No partition files recorded)*")

        lines.extend([
            "",
            "## Known Biases and Limitations",
            manifest.known_limitations or "None documented.",
            "",
            "## Preprocessing Pipeline",
            "1. Safe NFKC Unicode normalization.",
            "2. Safe horizontal whitespace collapse preserving paragraph boundaries, punctuation, and negation.",
            "3. Empty record filtering.",
            "4. SHA-256 content-hash generation and exact duplicate elimination.",
            "5. Leakage-resistant grouped train/val/test splitting with zero group and hash overlaps.",
        ])

        card_text = "\n".join(lines) + "\n"

        if output_dir:
            card_path = Path(output_dir) / "README.md"
            try:
                card_path.parent.mkdir(parents=True, exist_ok=True)
                with card_path.open("w", encoding="utf-8") as f:
                    f.write(card_text)
            except Exception as e:
                raise ManifestError(f"Failed to write dataset card to {card_path}: {e}")

        return card_text


__all__ = [
    "ManifestFileEntry",
    "DatasetManifest",
    "ManifestManager",
]
