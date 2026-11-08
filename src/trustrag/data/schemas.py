"""Normalized schema definitions for TrustRAG datasets.

All records are represented as Pydantic models with optional fields where the
source dataset does not provide a value. The ``content_hash`` field is a SHA-256
hex digest of the primary content after normalization and is used for duplicate
detection and leakage prevention.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, model_validator


def compute_content_hash(content: str) -> str:
    """Return SHA-256 hex digest of normalized content."""
    return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()


class DocumentRecord(BaseModel):
    """Normalized schema for document/passage records."""

    document_id: str
    text: str
    source_dataset: str
    source_split: Optional[str] = None
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    license: Optional[str] = None
    provenance: Optional[str] = None
    content_hash: str = Field(default_factory=str)

    @model_validator(mode="before")
    @classmethod
    def compute_hash(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("content_hash"):
                text = data.get("text", "")
                data["content_hash"] = compute_content_hash(text)
        return data


class QueryRecord(BaseModel):
    """Normalized schema for QA query records."""

    query_id: str
    query: str
    source_dataset: str
    source_split: Optional[str] = None
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    relevant_document_ids: List[str] = Field(default_factory=list)
    answer: Optional[str] = None
    content_hash: str = Field(default_factory=str)

    @model_validator(mode="before")
    @classmethod
    def compute_hash(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("content_hash"):
                query = data.get("query", "")
                data["content_hash"] = compute_content_hash(query)
        return data


class ClaimVerificationRecord(BaseModel):
    """Normalized schema for hallucination and claim-verification records."""

    record_id: str
    document: str
    claim: str
    label: str
    justification: Optional[str] = None
    source_dataset: str
    source_split: Optional[str] = None
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content_hash: str = Field(default_factory=str)

    @model_validator(mode="before")
    @classmethod
    def compute_hash(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("content_hash"):
                doc = data.get("document", "")
                claim = data.get("claim", "")
                combined = f"{doc}\n{claim}"
                data["content_hash"] = compute_content_hash(combined)
        return data


class SecurityRecord(BaseModel):
    """Normalized schema for security, poisoning, and attack evaluation records."""

    record_id: str
    document: Optional[str] = None
    passage: Optional[str] = None
    attack_family: Optional[str] = None
    attack_subtype: Optional[str] = None
    clean_poison_label: Optional[str] = None
    trigger_metadata: Optional[Dict[str, Any]] = None
    target_query: Optional[str] = None
    target_behavior: Optional[str] = None
    provenance: Optional[str] = None
    source_dataset: str
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content_hash: str = Field(default_factory=str)

    @model_validator(mode="before")
    @classmethod
    def compute_hash(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("content_hash"):
                target = data.get("passage") or data.get("document") or data.get("target_query") or ""
                data["content_hash"] = compute_content_hash(target)
        return data


NormalizedRecord = Union[DocumentRecord, QueryRecord, ClaimVerificationRecord, SecurityRecord]


__all__ = [
    "compute_content_hash",
    "DocumentRecord",
    "QueryRecord",
    "ClaimVerificationRecord",
    "SecurityRecord",
    "NormalizedRecord",
]
