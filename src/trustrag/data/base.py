"""Base dataset adapter and common interfaces for TrustRAG.

Provides the foundational :class:`BaseAdapter` class, metadata definitions,
and validation/transformation hooks for all dataset loaders.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Type, Union

from pydantic import BaseModel

from .exceptions import AcquisitionError, DataError, ValidationError
from .preprocessing.cleaning import clean_text, is_empty_text
from .preprocessing.deduplication import DeduplicationReport, DuplicateDetector
from .schemas import (
    ClaimVerificationRecord,
    DocumentRecord,
    QueryRecord,
    SecurityRecord,
)

logger = logging.getLogger(__name__)


@dataclass
class DatasetMetadata:
    """Metadata describing a dataset's origin, license, access terms, and schema."""

    name: str
    category: str  # "rag_qa", "hallucination", "security", "training_corpus"
    description: str
    source_uri: str
    license: str
    access_type: str  # "open", "gated", "local_only", "pending_verification"
    record_type: str  # "DocumentRecord", "QueryRecord", "ClaimVerificationRecord", "SecurityRecord"
    paper_reference: Optional[str] = None
    known_limitations: Optional[str] = None
    default_config: Optional[str] = None
    default_splits: List[str] = field(default_factory=lambda: ["train", "validation", "test"])
    intended_use: str = "Research evaluation and defense benchmarking"
    permitted_for_training: bool = True
    permitted_for_evaluation: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "source_uri": self.source_uri,
            "license": self.license,
            "access_type": self.access_type,
            "record_type": self.record_type,
            "paper_reference": self.paper_reference,
            "known_limitations": self.known_limitations,
            "default_config": self.default_config,
            "default_splits": self.default_splits,
            "intended_use": self.intended_use,
            "permitted_for_training": self.permitted_for_training,
            "permitted_for_evaluation": self.permitted_for_evaluation,
        }


@dataclass
class ProcessingStats:
    """Statistics captured during dataset loading and transformation."""

    raw_records: int = 0
    processed_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicate_records: int = 0
    empty_records: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "raw_records": self.raw_records,
            "processed_records": self.processed_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "duplicate_records": self.duplicate_records,
            "empty_records": self.empty_records,
            "error_sample": self.errors[:10],
        }


NormalizedRecord = Union[DocumentRecord, QueryRecord, ClaimVerificationRecord, SecurityRecord]


class BaseAdapter(ABC):
    """Abstract base class for all TrustRAG dataset adapters.

    Subclasses implement dataset-specific acquisition, raw loading, and
    transformation into one of TrustRAG's normalized record schemas.
    """

    metadata: DatasetMetadata

    def __init__(
        self,
        *,
        split: str = "train",
        limit: Optional[int] = None,
        cache_dir: Optional[Union[str, Path]] = None,
        offline: bool = False,
        config_name: Optional[str] = None,
    ) -> None:
        self.split = split
        self.limit = limit
        self.offline = offline
        self.config_name = config_name or getattr(self.metadata, "default_config", None)
        self.cache_dir = Path(cache_dir) if cache_dir else Path("data/raw") / self.metadata.name
        self.stats = ProcessingStats()
        self.deduplicator = DuplicateDetector()

    @abstractmethod
    def acquire(self) -> Any:
        """Acquire raw dataset files or verify local availability.

        Raises
        ------
        AcquisitionError
            If network download fails, dataset is missing in offline mode, or
            manual access agreement is required.
        """
        pass

    @abstractmethod
    def load_raw(self) -> Iterator[Dict[str, Any]]:
        """Yield raw records from the acquired dataset."""
        pass

    @abstractmethod
    def transform(self, raw_item: Dict[str, Any]) -> Iterator[NormalizedRecord]:
        """Transform a single raw item into one or more normalized record models."""
        pass

    def validate_record(self, record: NormalizedRecord) -> bool:
        """Validate a normalized record for completeness and quality."""
        if isinstance(record, DocumentRecord):
            if is_empty_text(record.text):
                self.stats.empty_records += 1
                return False
        elif isinstance(record, QueryRecord):
            if is_empty_text(record.query):
                self.stats.empty_records += 1
                return False
        elif isinstance(record, ClaimVerificationRecord):
            if is_empty_text(record.claim) or is_empty_text(record.document):
                self.stats.empty_records += 1
                return False
        elif isinstance(record, SecurityRecord):
            target = record.passage or record.document or record.target_query
            if is_empty_text(target):
                self.stats.empty_records += 1
                return False
        return True

    def process(
        self,
        *,
        deduplicate: bool = True,
        clean: bool = True,
    ) -> Iterator[NormalizedRecord]:
        """Execute the loading pipeline: load_raw -> transform -> clean -> validate -> deduplicate.

        Parameters
        ----------
        deduplicate: bool
            Whether to drop duplicate records using content hash.
        clean: bool
            Whether to apply safe text cleaning and whitespace normalization.

        Yields
        ------
        NormalizedRecord
            Normalized, validated records conforming to schema up to `self.limit`.
        """
        self.stats = ProcessingStats()
        self.deduplicator.reset()

        count = 0
        raw_iter = self.load_raw()

        for raw_item in raw_iter:
            self.stats.raw_records += 1
            try:
                records = list(self.transform(raw_item))
            except Exception as e:
                self.stats.invalid_records += 1
                err_msg = f"Transform error on raw item {self.stats.raw_records}: {str(e)}"
                if len(self.stats.errors) < 100:
                    self.stats.errors.append(err_msg)
                logger.warning(err_msg)
                continue

            for record in records:
                self.stats.processed_records += 1

                # Clean text if requested
                if clean:
                    if isinstance(record, DocumentRecord):
                        record.text = clean_text(record.text)
                    elif isinstance(record, QueryRecord):
                        record.query = clean_text(record.query)
                        if record.answer:
                            record.answer = clean_text(record.answer)
                    elif isinstance(record, ClaimVerificationRecord):
                        record.document = clean_text(record.document)
                        record.claim = clean_text(record.claim)
                        if record.justification:
                            record.justification = clean_text(record.justification)
                    elif isinstance(record, SecurityRecord):
                        if record.passage:
                            record.passage = clean_text(record.passage)
                        if record.document:
                            record.document = clean_text(record.document)
                        if record.target_query:
                            record.target_query = clean_text(record.target_query)

                # Quality / completeness validation
                if not self.validate_record(record):
                    self.stats.invalid_records += 1
                    continue

                # Deduplication check
                record_id = getattr(record, "record_id", None) or getattr(record, "document_id", None) or getattr(record, "query_id", "")
                content_hash = getattr(record, "content_hash", "")
                if deduplicate and not self.deduplicator.check_and_add(record_id, content_hash):
                    self.stats.duplicate_records += 1
                    continue

                self.stats.valid_records += 1
                yield record
                count += 1

                if self.limit is not None and count >= self.limit:
                    return

    def get_stats(self) -> ProcessingStats:
        """Return processing statistics for the most recent run."""
        return self.stats

    def get_deduplication_report(self) -> DeduplicationReport:
        """Return deduplication report."""
        return self.deduplicator.get_report()


__all__ = [
    "DatasetMetadata",
    "ProcessingStats",
    "NormalizedRecord",
    "BaseAdapter",
]

