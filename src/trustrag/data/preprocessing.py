"""Utilities for preprocessing raw text records.

- Unicode normalization (NFKC)
- Whitespace collapse
- Stripping leading/trailing spaces
"""

import unicodedata
import re
from typing import Mapping, Dict, Any


def normalize_text(record: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a copy of *record* with all string fields normalised.

    The function walks the mapping recursively; if a value is a ``str`` it is
    normalised using NFKC, collapsed whitespace, and stripped. Non‑string values
    are left unchanged.
    """

    def _norm(value: Any) -> Any:
        if isinstance(value, str):
            # NFKC Unicode normalisation
            v = unicodedata.normalize("NFKC", value)
            # Collapse any sequence of whitespace characters to a single space
            v = re.sub(r"\s+", " ", v)
            return v.strip()
        if isinstance(value, dict):
            return {k: _norm(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_norm(v) for v in value]
        return value

    return {k: _norm(v) for k, v in record.items()}

