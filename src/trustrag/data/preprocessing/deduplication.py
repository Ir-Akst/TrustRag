"""Deduplication utilities using cryptographic content hashes.

Provides exact duplicate detection and duplicate reporting for normalized records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


@dataclass
class DeduplicationReport:
    """Report detailing deduplication statistics and detected duplicate groups."""

    total_records: int = 0
    unique_records: int = 0
    duplicate_records: int = 0
    duplicates_by_hash: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def duplicate_ratio(self) -> float:
        """Ratio of duplicate records to total records."""
        if self.total_records == 0:
            return 0.0
        return self.duplicate_records / self.total_records

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to a dictionary."""
        return {
            "total_records": self.total_records,
            "unique_records": self.unique_records,
            "duplicate_records": self.duplicate_records,
            "duplicate_ratio": round(self.duplicate_ratio, 4),
            "duplicate_groups_count": len(self.duplicates_by_hash),
        }


class DuplicateDetector:
    """Stateful detector for identifying and reporting duplicate records by content hash."""

    def __init__(self) -> None:
        self._seen_hashes: Dict[str, str] = {}  # hash -> first seen record_id
        self._duplicates_by_hash: Dict[str, List[str]] = {}
        self._total_count = 0
        self._unique_count = 0
        self._duplicate_count = 0

    def check_and_add(self, record_id: str, content_hash: str) -> bool:
        """Check if content_hash has already been seen.

        Returns
        -------
        bool
            True if the record is unique (first time seen), False if it is a duplicate.
        """
        self._total_count += 1
        if not content_hash:
            # An empty hash cannot be reliably deduplicated, count as unique but warn
            self._unique_count += 1
            return True

        if content_hash in self._seen_hashes:
            self._duplicate_count += 1
            if content_hash not in self._duplicates_by_hash:
                self._duplicates_by_hash[content_hash] = [self._seen_hashes[content_hash]]
            self._duplicates_by_hash[content_hash].append(record_id)
            return False

        self._seen_hashes[content_hash] = record_id
        self._unique_count += 1
        return True

    def get_report(self) -> DeduplicationReport:
        """Return a snapshot report of duplicate statistics."""
        return DeduplicationReport(
            total_records=self._total_count,
            unique_records=self._unique_count,
            duplicate_records=self._duplicate_count,
            duplicates_by_hash=dict(self._duplicates_by_hash),
        )

    def reset(self) -> None:
        """Reset internal detector state."""
        self._seen_hashes.clear()
        self._duplicates_by_hash.clear()
        self._total_count = 0
        self._unique_count = 0
        self._duplicate_count = 0


__all__ = [
    "DeduplicationReport",
    "DuplicateDetector",
]

