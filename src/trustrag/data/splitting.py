"""Leakage-resistant dataset splitting logic for TrustRAG.

Guarantees:
- Grouped splitting so related records (e.g. clean passages and their poisoned variants,
  or queries and referenced documents) never cross split boundaries.
- Exact content-hash overlap verification across train, validation, and test splits.
- Reproducible deterministic splitting via explicit random seed (default 42).
- Preservation of official splits unless custom splitting is explicitly requested.
- Partition auditing for cross-split duplicate content and group leakage.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from pydantic import BaseModel, Field, model_validator

from .exceptions import SplitError
from .schemas import (
    ClaimVerificationRecord,
    DocumentRecord,
    NormalizedRecord,
    QueryRecord,
    SecurityRecord,
)


class SplitConfig(BaseModel):
    """Configuration for custom dataset splitting."""

    train_ratio: float = Field(default=0.70, ge=0.0, le=1.0)
    val_ratio: float = Field(default=0.15, ge=0.0, le=1.0)
    test_ratio: float = Field(default=0.15, ge=0.0, le=1.0)
    seed: int = Field(default=42)
    group_key: Optional[str] = Field(
        default=None,
        description="Attribute or metadata key used to group records to prevent leakage",
    )

    @model_validator(mode="after")
    def validate_ratios(self) -> SplitConfig:
        total = round(self.train_ratio + self.val_ratio + self.test_ratio, 5)
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"Split ratios must sum to 1.0, got {total}")
        return self


@dataclass
class SplitStatistics:
    """Detailed audit report of split sizes, distributions, and leakage checks."""

    dataset_name: str
    total_records: int = 0
    train_count: int = 0
    val_count: int = 0
    test_count: int = 0
    num_groups: int = 0
    leakage_detected: bool = False
    group_overlap_train_val: int = 0
    group_overlap_train_test: int = 0
    group_overlap_val_test: int = 0
    hash_overlap_train_val: int = 0
    hash_overlap_train_test: int = 0
    hash_overlap_val_test: int = 0
    seed: int = 42
    split_type: str = "custom"  # "official" or "custom"

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary."""
        return {
            "dataset_name": self.dataset_name,
            "split_type": self.split_type,
            "total_records": self.total_records,
            "train_count": self.train_count,
            "val_count": self.val_count,
            "test_count": self.test_count,
            "train_ratio_actual": round(self.train_count / self.total_records, 4) if self.total_records else 0,
            "val_ratio_actual": round(self.val_count / self.total_records, 4) if self.total_records else 0,
            "test_ratio_actual": round(self.test_count / self.total_records, 4) if self.total_records else 0,
            "num_groups": self.num_groups,
            "leakage_detected": self.leakage_detected,
            "group_overlaps": {
                "train_val": self.group_overlap_train_val,
                "train_test": self.group_overlap_train_test,
                "val_test": self.group_overlap_val_test,
            },
            "content_hash_overlaps": {
                "train_val": self.hash_overlap_train_val,
                "train_test": self.hash_overlap_train_test,
                "val_test": self.hash_overlap_val_test,
            },
            "seed": self.seed,
        }


class LeakageResistantSplitter:
    """Splitter enforcing strict isolation between train, validation, and test sets."""

    @staticmethod
    def extract_group_id(record: NormalizedRecord, group_key: Optional[str] = None) -> str:
        """Extract a stable grouping key from a record.

        Falls back deterministically to content_hash if no explicit group or record ID exists,
        guaranteeing reproducibility across process runs.
        """
        if group_key:
            if hasattr(record, group_key):
                val = getattr(record, group_key)
                if val:
                    return str(val).strip()
            metadata = getattr(record, "metadata", {})
            if isinstance(metadata, dict) and group_key in metadata:
                val = metadata[group_key]
                if val:
                    return str(val).strip()

        # Heuristic based on record type
        if isinstance(record, SecurityRecord):
            # Group by source_id (parent doc), trigger metadata, or provenance
            gid = record.source_id or record.provenance or record.record_id
            if gid and gid.strip():
                return gid.strip()
        elif isinstance(record, ClaimVerificationRecord):
            gid = record.source_id or record.document[:64]
            if gid and gid.strip():
                return gid.strip()
        elif isinstance(record, QueryRecord):
            if record.relevant_document_ids and record.relevant_document_ids[0].strip():
                return record.relevant_document_ids[0].strip()
            gid = record.source_id or record.query_id
            if gid and gid.strip():
                return gid.strip()
        elif isinstance(record, DocumentRecord):
            gid = record.source_id or record.document_id
            if gid and gid.strip():
                return gid.strip()

        # Deterministic fallback when group IDs are missing
        rec_id = getattr(record, "record_id", None) or getattr(record, "document_id", None) or getattr(record, "query_id", None)
        if rec_id and str(rec_id).strip():
            return str(rec_id).strip()

        content_hash = getattr(record, "content_hash", None)
        if content_hash and content_hash.strip():
            return f"hash_{content_hash[:16]}"

        # Absolute fallback: hash of string representation
        return hashlib.sha256(repr(record).encode("utf-8")).hexdigest()[:16]

    @classmethod
    def audit_partitions(
        cls,
        partitions: Dict[str, Sequence[NormalizedRecord]],
        dataset_name: str = "dataset",
        group_key: Optional[str] = None,
        split_type: str = "official",
        raise_on_leakage: bool = True,
    ) -> SplitStatistics:
        """Audit existing dataset partitions (official or custom) for cross-split leakage.

        Parameters
        ----------
        partitions: Dict[str, Sequence[NormalizedRecord]]
            Mapping of partition names (e.g. 'train', 'validation', 'test') to records.
        dataset_name: str
            Name of dataset being audited.
        group_key: str | None
            Key used for group extraction.
        split_type: str
            Whether partitions represent 'official' or 'custom' splits.
        raise_on_leakage: bool
            Whether to raise SplitError if leakage is found.

        Returns
        -------
        SplitStatistics
            Comprehensive leakage audit statistics.
        """
        train_records = partitions.get("train", [])
        val_records = partitions.get("val", []) or partitions.get("validation", [])
        test_records = partitions.get("test", [])

        total = sum(len(p) for p in partitions.values())

        # Extract groups
        all_gids = set()
        for p_recs in partitions.values():
            for r in p_recs:
                all_gids.add(cls.extract_group_id(r, group_key))

        train_gids = {cls.extract_group_id(r, group_key) for r in train_records}
        val_gids = {cls.extract_group_id(r, group_key) for r in val_records}
        test_gids = {cls.extract_group_id(r, group_key) for r in test_records}

        train_hashes = {getattr(r, "content_hash", "") for r in train_records if getattr(r, "content_hash", "")}
        val_hashes = {getattr(r, "content_hash", "") for r in val_records if getattr(r, "content_hash", "")}
        test_hashes = {getattr(r, "content_hash", "") for r in test_records if getattr(r, "content_hash", "")}

        stats = SplitStatistics(
            dataset_name=dataset_name,
            total_records=total,
            train_count=len(train_records),
            val_count=len(val_records),
            test_count=len(test_records),
            num_groups=len(all_gids),
            split_type=split_type,
            group_overlap_train_val=len(train_gids & val_gids),
            group_overlap_train_test=len(train_gids & test_gids),
            group_overlap_val_test=len(val_gids & test_gids),
            hash_overlap_train_val=len(train_hashes & val_hashes),
            hash_overlap_train_test=len(train_hashes & test_hashes),
            hash_overlap_val_test=len(val_hashes & test_hashes),
        )

        has_group_leak = (
            stats.group_overlap_train_val > 0
            or stats.group_overlap_train_test > 0
            or stats.group_overlap_val_test > 0
        )
        has_hash_leak = (
            stats.hash_overlap_train_val > 0
            or stats.hash_overlap_train_test > 0
            or stats.hash_overlap_val_test > 0
        )

        if has_group_leak or has_hash_leak:
            stats.leakage_detected = True
            if raise_on_leakage:
                raise SplitError(
                    f"Data leakage detected in {split_type} partitions for '{dataset_name}'! "
                    f"Group overlaps: train-val={stats.group_overlap_train_val}, "
                    f"train-test={stats.group_overlap_train_test}, val-test={stats.group_overlap_val_test}. "
                    f"Content hash overlaps: train-val={stats.hash_overlap_train_val}, "
                    f"train-test={stats.hash_overlap_train_test}, val-test={stats.hash_overlap_val_test}."
                )

        return stats

    @classmethod
    def split(
        cls,
        records: Sequence[NormalizedRecord],
        config: Optional[SplitConfig] = None,
        dataset_name: str = "dataset",
    ) -> Tuple[Dict[str, List[NormalizedRecord]], SplitStatistics]:
        """Perform custom leakage-resistant grouped splitting (e.g. 70/15/15).

        Should only be invoked when explicitly requested or when a dataset has no official splits.
        """
        if config is None:
            config = SplitConfig()

        if not records:
            empty_stats = SplitStatistics(dataset_name=dataset_name, seed=config.seed, split_type="custom")
            return {"train": [], "val": [], "test": []}, empty_stats

        # 1. Group records by group ID
        groups: Dict[str, List[NormalizedRecord]] = {}
        for rec in records:
            gid = cls.extract_group_id(rec, config.group_key)
            groups.setdefault(gid, []).append(rec)

        group_keys = sorted(groups.keys())
        rng = random.Random(config.seed)
        rng.shuffle(group_keys)

        total_groups = len(group_keys)

        # Handle small dataset edge cases gracefully
        if total_groups == 1:
            train_groups = set(group_keys)
            val_groups = set()
            test_groups = set()
        elif total_groups == 2:
            train_groups = {group_keys[0]}
            val_groups = set()
            test_groups = {group_keys[1]}
        else:
            n_train = int(total_groups * config.train_ratio)
            n_val = int(total_groups * config.val_ratio)

            # Ensure every requested split with ratio > 0 gets at least 1 group if total_groups >= 3
            if config.train_ratio > 0 and n_train == 0:
                n_train = 1
            if config.val_ratio > 0 and n_val == 0:
                n_val = 1
            if n_train + n_val >= total_groups:
                n_train = max(1, total_groups - 2)
                n_val = 1

            train_groups = set(group_keys[:n_train])
            val_groups = set(group_keys[n_train : n_train + n_val])
            test_groups = set(group_keys[n_train + n_val :])

        # Assign records
        train_records: List[NormalizedRecord] = []
        val_records: List[NormalizedRecord] = []
        test_records: List[NormalizedRecord] = []

        for gid, rec_list in groups.items():
            if gid in train_groups:
                train_records.extend(rec_list)
            elif gid in val_groups:
                val_records.extend(rec_list)
            else:
                test_records.extend(rec_list)

        splits_dict = {
            "train": train_records,
            "val": val_records,
            "test": test_records,
        }

        # Run complete audit
        stats = cls.audit_partitions(
            splits_dict,
            dataset_name=dataset_name,
            group_key=config.group_key,
            split_type="custom",
            raise_on_leakage=True,
        )
        stats.seed = config.seed
        return splits_dict, stats


__all__ = [
    "SplitConfig",
    "SplitStatistics",
    "LeakageResistantSplitter",
]
