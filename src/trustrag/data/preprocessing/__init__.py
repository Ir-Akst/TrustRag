"""Preprocessing package for TrustRAG.

Provides text cleaning, Unicode normalization, safe whitespace handling,
empty record detection, and content-hash-based deduplication.
"""

from .cleaning import (
    clean_text,
    is_empty_text,
    normalize_text,
    normalize_whitespace_single_line,
)
from .deduplication import DeduplicationReport, DuplicateDetector

__all__ = [
    "clean_text",
    "is_empty_text",
    "normalize_text",
    "normalize_whitespace_single_line",
    "DuplicateDetector",
    "DeduplicationReport",
]

