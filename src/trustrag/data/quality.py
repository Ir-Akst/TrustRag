"""Quality validation and metrics reporting for TrustRAG datasets.

Phase 02 Data Quality Validation computes:
- Total records acquired / inspected
- Valid records
- Invalid records
- Duplicate records (via SHA-256 content hashes)
- Empty / blank records
- Missing required fields
- Unknown labels
- Missing source IDs
- Unique documents count
- Unique queries count
- Unique claims count
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Union

from trustrag.data.preprocessing.cleaning import is_empty_text
from trustrag.data.schemas import (
    ClaimVerificationRecord,
    DocumentRecord,
    NormalizedRecord,
    QueryRecord,
    SecurityRecord,
    compute_content_hash,
)
from trustrag.data.taxonomy import (
    ALLOWED_CLAIM_LABELS,
    ALLOWED_SECURITY_LABELS,
)


@dataclass
class DatasetQualityReport:
    """Comprehensive dataset quality and integrity report."""

    dataset_name: str
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicate_records: int = 0
    empty_records: int = 0
    missing_required_fields: int = 0
    unknown_labels: int = 0
    missing_source_ids: int = 0
    unique_documents: int = 0
    unique_queries: int = 0
    unique_claims: int = 0
    error_samples: List[str] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        """True if there are zero invalid, empty, or unknown label errors."""
        return self.invalid_records == 0 and self.empty_records == 0 and self.unknown_labels == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        d = asdict(self)
        d["is_healthy"] = self.is_healthy
        d["valid_rate"] = round(self.valid_records / self.total_records, 4) if self.total_records else 0.0
        d["duplicate_rate"] = round(self.duplicate_records / self.total_records, 4) if self.total_records else 0.0
        return d

    def to_json(self, indent: int = 2) -> str:
        """Serialize report to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        """Format report as GitHub-flavored Markdown."""
        lines = [
            f"# Data Quality Report: {self.dataset_name}",
            "",
            "## Summary Metrics",
            f"- **Dataset:** `{self.dataset_name}`",
            f"- **Total Records Inspected:** {self.total_records}",
            f"- **Valid Records:** {self.valid_records} ({round(self.valid_records / self.total_records * 100, 2) if self.total_records else 0}%)",
            f"- **Invalid Records:** {self.invalid_records}",
            f"- **Empty Records:** {self.empty_records}",
            f"- **Duplicate Records:** {self.duplicate_records}",
            f"- **Missing Required Fields:** {self.missing_required_fields}",
            f"- **Unknown Labels:** {self.unknown_labels}",
            f"- **Missing Source IDs:** {self.missing_source_ids}",
            "",
            "## Cardinality Metrics",
            f"- **Unique Documents:** {self.unique_documents}",
            f"- **Unique Queries:** {self.unique_queries}",
            f"- **Unique Claims:** {self.unique_claims}",
            "",
            f"**Quality Status:** `{'HEALTHY (PASS)' if self.is_healthy else 'QUALITY ISSUES DETECTED'}`",
        ]
        if self.error_samples:
            lines.extend([
                "",
                "## Sample Validation Errors",
            ])
            for err in self.error_samples[:10]:
                lines.append(f"- {err}")
        return "\n".join(lines)


class DatasetQualityAuditor:
    """Auditor for computing full quality metrics across a sequence of records or file."""

    # Recognized valid labels across schemas
    VALID_CLAIM_LABELS: Set[str] = {
        "SUPPORTED", "CONTRADICTED", "NOT_ENOUGH_EVIDENCE",
        "REFUTED", "HALLUCINATED", "FACTUAL", "TRUE", "FALSE", "NOT_ENOUGH_INFO",
    }
    VALID_SECURITY_LABELS: Set[str] = {
        "clean", "poison", "poisoned", "attack", "benign", "uncertain",
    }

    @classmethod
    def audit_records(
        cls,
        records: Iterator[Any] | List[Any],
        dataset_name: str = "dataset",
    ) -> DatasetQualityReport:
        """Audit an iterable of records and compute quality metrics."""
        report = DatasetQualityReport(dataset_name=dataset_name)

        seen_hashes: Set[str] = set()
        seen_documents: Set[str] = set()
        seen_queries: Set[str] = set()
        seen_claims: Set[str] = set()

        for idx, item in enumerate(records, start=1):
            report.total_records += 1
            has_error = False

            rec = item
            if isinstance(rec, dict):
                # Infer and validate into normalized Pydantic model
                parsed = None
                if "attack_family" in rec or "clean_poison_label" in rec:
                    try:
                        parsed = SecurityRecord.model_validate(rec)
                    except Exception:
                        pass
                elif "claim" in rec and "label" in rec:
                    try:
                        parsed = ClaimVerificationRecord.model_validate(rec)
                    except Exception:
                        pass
                elif "query" in rec and "query_id" in rec:
                    try:
                        parsed = QueryRecord.model_validate(rec)
                    except Exception:
                        pass
                elif "text" in rec and "document_id" in rec:
                    try:
                        parsed = DocumentRecord.model_validate(rec)
                    except Exception:
                        pass

                if parsed is None:
                    for model_cls in (SecurityRecord, ClaimVerificationRecord, QueryRecord, DocumentRecord):
                        try:
                            parsed = model_cls.model_validate(rec)
                            break
                        except Exception:
                            continue

                if parsed is not None:
                    rec = parsed

            # Check if valid schema type
            if not isinstance(rec, (DocumentRecord, QueryRecord, ClaimVerificationRecord, SecurityRecord)):
                report.invalid_records += 1
                report.missing_required_fields += 1
                if len(report.error_samples) < 10:
                    report.error_samples.append(f"Record {idx}: unrecognized model type {type(item)}")
                continue

            # 1. Check Source ID
            if not rec.source_id or not str(rec.source_id).strip():
                report.missing_source_ids += 1

            # 2. Duplicate Detection via content_hash
            chash = rec.content_hash or ""
            if chash:
                if chash in seen_hashes:
                    report.duplicate_records += 1
                else:
                    seen_hashes.add(chash)

            # 3. Type-specific field checks
            if isinstance(rec, DocumentRecord):
                if is_empty_text(rec.text):
                    report.empty_records += 1
                    has_error = True
                if not rec.document_id:
                    report.missing_required_fields += 1
                    has_error = True
                if rec.text:
                    seen_documents.add(compute_content_hash(rec.text))

            elif isinstance(rec, QueryRecord):
                if is_empty_text(rec.query):
                    report.empty_records += 1
                    has_error = True
                if not rec.query_id:
                    report.missing_required_fields += 1
                    has_error = True
                if rec.query:
                    seen_queries.add(compute_content_hash(rec.query))

            elif isinstance(rec, ClaimVerificationRecord):
                if is_empty_text(rec.claim) or is_empty_text(rec.document):
                    report.empty_records += 1
                    has_error = True
                if not rec.record_id:
                    report.missing_required_fields += 1
                    has_error = True
                if rec.label.upper() not in cls.VALID_CLAIM_LABELS:
                    report.unknown_labels += 1
                    has_error = True
                    if len(report.error_samples) < 10:
                        report.error_samples.append(f"Record {idx}: unknown claim label '{rec.label}'")
                if rec.document:
                    seen_documents.add(compute_content_hash(rec.document))
                if rec.claim:
                    seen_claims.add(compute_content_hash(rec.claim))

            elif isinstance(rec, SecurityRecord):
                target_text = rec.passage or rec.document or ""
                if is_empty_text(target_text):
                    report.empty_records += 1
                    has_error = True
                if not rec.record_id:
                    report.missing_required_fields += 1
                    has_error = True
                if rec.clean_poison_label:
                    if str(rec.clean_poison_label).strip().lower() not in cls.VALID_SECURITY_LABELS:
                        report.unknown_labels += 1
                        has_error = True
                        if len(report.error_samples) < 10:
                            report.error_samples.append(
                                f"Record {idx}: unknown security label '{rec.clean_poison_label}'"
                            )
                else:
                    report.missing_required_fields += 1
                    has_error = True
                if target_text:
                    seen_documents.add(compute_content_hash(target_text))
                if rec.target_query:
                    seen_queries.add(compute_content_hash(rec.target_query))

            if has_error:
                report.invalid_records += 1
            else:
                report.valid_records += 1

        report.unique_documents = len(seen_documents)
        report.unique_queries = len(seen_queries)
        report.unique_claims = len(seen_claims)
        return report

    @classmethod
    def audit_file(cls, file_path: Union[str, Path], dataset_name: Optional[str] = None) -> DatasetQualityReport:
        """Audit records from a JSONL file on disk."""
        from trustrag.data.storage import DatasetStorage

        p = Path(file_path)
        name = dataset_name or p.stem
        records = list(DatasetStorage.load_jsonl(p))
        return cls.audit_records(records, dataset_name=name)


__all__ = [
    "DatasetQualityReport",
    "DatasetQualityAuditor",
]
