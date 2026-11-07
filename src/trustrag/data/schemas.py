"""Normalized schema definitions for TrustRAG datasets.

All records are represented as Pydantic models with optional fields where the
source dataset does not provide a value. The ``content_hash`` field is a SHA‑256
hex digest of the ``text`` (or ``document``/``claim``) after normalisation and is
used for duplicate detection.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class DocumentRecord(BaseModel):
    document_id: str
    text: str
    source_dataset: str
    source_split: Optional[str] = None
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    license: Optional[str] = None
    provenance: Optional[str] = None
    content_hash: str = Field(default_factory=str)

    @validator("content_hash", pre=True, always=True)
    def compute_hash(cls, v: str, values: Dict[str, Any]) -> str:
        if v:
            return v
        text = values.get("text", "")
        return _hash_content(text)


class QueryRecord(BaseModel):
    query_id: str
    query: str
    source_dataset: str
    source_split: Optional[str] = None
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    relevant_document_ids: List[str] = Field(default_factory=list)
    answer: Optional[str] = None


class ClaimVerificationRecord(BaseModel):
    record_id: str
    document: str
    claim: str
    label: str
    justification: Optional[str] = None
    source_dataset: str
    source_split: Optional[str] = None
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SecurityRecord(BaseModel):
    record_id: str
    document: Optional[str] = None
    passage: Optional[str] = None
    attack_family: Optional[str] = None
    attack_subtype: Optional[str] = None
    clean_poison_label: Optional[str] = None
    trigger_metadata: Optional[Dict[str, Any]] = None
    target_query: Optional[str] = None
    provenance: Optional[str] = None
    source_dataset: str
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

