"""Validation and quality-assurance checks for TrustRAG datasets.

Provides record-level and dataset-level validation:
- Schema conformity checks
- Empty/blank field detection
- Malformed record reporting
- Content hash integrity checks
- Label validity enforcement
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Type

from pydantic import BaseModel

from .exceptions import ValidationError
from .preprocessing.cleaning import is_empty_text
from .schemas import (
    ClaimVerificationRecord,
    DocumentRecord,
    NormalizedRecord,
    QueryRecord,
    SecurityRecord,
    compute_content_hash,
)

# Standardized labels for claim verification and security
ALLOWED_CLAIM_LABELS: Set[str] = {
    "SUPPORTED",
    "CONTRADICTED",
    "NOT_ENOUGH_EVIDENCE",
    "REFUTED",
    "NOT_ENOUGH_INFO",
    "HALLUCINATED",
    "FACTUAL",
    "TRUE",
    "FALSE",
}

ALLOWED_SECURITY_LABELS: Set[str] = {
    "CLEAN",
    "POISONED",
    "UNCERTAIN",
    "ATTACK",
    "BENIGN",
}


@dataclass
class ValidationReport:
    """Comprehensive report summarizing dataset record validation results."""

    dataset_name: str
    total_checked: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    empty_count: int = 0
    hash_mismatch_count: int = 0
    label_error_count: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """True if there are zero invalid or empty records."""
        return self.invalid_count == 0 and self.empty_count == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "dataset_name": self.dataset_name,
            "total_checked": self.total_checked,
            "valid_count": self.valid_count,
            "invalid_count": self.invalid_count,
            "empty_count": self.empty_count,
            "hash_mismatch_count": self.hash_mismatch_count,
            "label_error_count": self.label_error_count,
            "is_valid": self.is_valid,
            "sample_errors": self.errors[:10],
        }


class RecordValidator:
    """Validator for inspecting normalized records and generating quality reports."""

    def __init__(self, dataset_name: str = "dataset") -> None:
        self.report = ValidationReport(dataset_name=dataset_name)

    def validate(self, record: Any) -> bool:
        """Validate a single record. Updates internal ValidationReport and returns True if valid."""
        self.report.total_checked += 1

        if not isinstance(record, (DocumentRecord, QueryRecord, ClaimVerificationRecord, SecurityRecord)):
            self.report.invalid_count += 1
            self._log_error(f"Record {type(record)} is not a recognized TrustRAG record model")
            return False

        # 1. Check for empty primary content
        if isinstance(record, DocumentRecord):
            if is_empty_text(record.text):
                self.report.empty_count += 1
                self.report.invalid_count += 1
                self._log_error(f"DocumentRecord {record.document_id} has empty text")
                return False
            expected_hash = compute_content_hash(record.text)
            if record.content_hash != expected_hash:
                self.report.hash_mismatch_count += 1

        elif isinstance(record, QueryRecord):
            if is_empty_text(record.query):
                self.report.empty_count += 1
                self.report.invalid_count += 1
                self._log_error(f"QueryRecord {record.query_id} has empty query")
                return False
            expected_hash = compute_content_hash(record.query)
            if record.content_hash != expected_hash:
                self.report.hash_mismatch_count += 1

        elif isinstance(record, ClaimVerificationRecord):
            if is_empty_text(record.document) or is_empty_text(record.claim):
                self.report.empty_count += 1
                self.report.invalid_count += 1
                self._log_error(f"ClaimVerificationRecord {record.record_id} has empty document or claim")
                return False
            if record.label.upper() not in ALLOWED_CLAIM_LABELS:
                self.report.label_error_count += 1
                self.report.invalid_count += 1
                self._log_error(
                    f"ClaimVerificationRecord {record.record_id} has unknown label '{record.label}'. "
                    f"Allowed: {sorted(ALLOWED_CLAIM_LABELS)}"
                )
                return False

        elif isinstance(record, SecurityRecord):
            target = record.passage or record.document or record.target_query
            if is_empty_text(target):
                self.report.empty_count += 1
                self.report.invalid_count += 1
                self._log_error(f"SecurityRecord {record.record_id} has no target content (passage/document/query)")
                return False
            if record.clean_poison_label is not None:
                if record.clean_poison_label.upper() not in ALLOWED_SECURITY_LABELS:
                    self.report.label_error_count += 1
                    self.report.invalid_count += 1
                    self._log_error(
                        f"SecurityRecord {record.record_id} has invalid label '{record.clean_poison_label}'. "
                        f"Allowed: {sorted(ALLOWED_SECURITY_LABELS)}"
                    )
                    return False

        self.report.valid_count += 1
        return True

    def _log_error(self, message: str) -> None:
        if len(self.report.errors) < 100:
            self.report.errors.append(message)

    def get_report(self) -> ValidationReport:
        """Return the collected validation report."""
        return self.report


__all__ = [
    "ALLOWED_CLAIM_LABELS",
    "ALLOWED_SECURITY_LABELS",
    "ValidationReport",
    "RecordValidator",
]

