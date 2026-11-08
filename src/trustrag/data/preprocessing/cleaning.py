"""Text cleaning and normalization utilities for TrustRAG.

Provides safe normalization:
- Unicode normalization (NFKC)
- Whitespace collapse while preserving paragraph boundaries
- Safe text cleaning preserving punctuation, negation, and instructions
- Empty record detection
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Mapping, Union


def clean_text(text: str) -> str:
    """Safely clean a single string.

    Applies NFKC Unicode normalization, normalizes carriage returns, collapses
    excessive horizontal whitespace, and trims leading/trailing spaces.
    Crucially preserves punctuation, casing, negation, and instruction-like formatting.
    """
    if not isinstance(text, str):
        return text

    # Unicode NFKC normalization
    normalized = unicodedata.normalize("NFKC", text)

    # Normalize line breaks
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse consecutive horizontal whitespace (spaces/tabs) on each line
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.split("\n")]

    # Collapse consecutive empty lines to a single empty line (paragraph break)
    cleaned_lines: List[str] = []
    empty_count = 0
    for line in lines:
        if not line:
            empty_count += 1
            if empty_count <= 1:
                cleaned_lines.append("")
        else:
            empty_count = 0
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def normalize_whitespace_single_line(text: str) -> str:
    """Normalize text into a single line with collapsed whitespace."""
    if not isinstance(text, str):
        return text
    normalized = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", normalized).strip()


def is_empty_text(text: str | None) -> bool:
    """Check if a text string is empty or contains only whitespace."""
    if text is None:
        return True
    return len(text.strip()) == 0


def normalize_text(record: Union[Mapping[str, Any], str, List[Any]]) -> Any:
    """Recursively normalize text fields in a record, mapping, list, or string.

    Maintains backward compatibility with earlier Phase 00 interfaces while
    applying safe normalization.
    """
    if isinstance(record, str):
        return clean_text(record)
    if isinstance(record, dict):
        return {k: normalize_text(v) for k, v in record.items()}
    if isinstance(record, list):
        return [normalize_text(item) for item in record]
    return record


__all__ = [
    "clean_text",
    "normalize_whitespace_single_line",
    "is_empty_text",
    "normalize_text",
]
