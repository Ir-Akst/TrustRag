# Phase 13 Step 5 — Root Cause & Code Change

## Root Cause Analysis

### Original Regex (REM-01 Fix, Step 3)

```python
_BASE64_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9+/=])(?:[A-Za-z0-9+/]{4}){3,}"
    r"(?:[A-Za-z0-9+/]{4}|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)"
    r"(?![A-Za-z0-9+/=])"
)
```

The negative lookarounds `(?<![A-Za-z0-9+/=])` and `(?![A-Za-z0-9+/=])` include the characters `+`, `/`, `=`.

These characters serve dual roles:
- **Base64 alphabet:** `+` (value 62), `/` (value 63), `=` (padding)
- **Common delimiters:** `/` in file paths, `+` in math/search, `=` in key-value pairs

When an attacker wraps a Base64 payload in these characters (e.g., `/aWdub3Jl.../`), neither the lookbehind nor the lookahead allows a match boundary at that position.

### Why a Simple Fix Doesn't Work

Removing `+/=` from the lookaround character class causes **over-matching**:
- A lookahead `(?![A-Za-z0-9])` would allow matching at a position where the next char is `=`, potentially truncating valid padding.
- This creates false token boundaries within legitimate padded tokens.

### Solution: Two-Phase Extraction

```
Phase 1: _BASE64_TOKEN_RE       (strict, backward-compatible, fast path)
Phase 2: _BASE64_CANDIDATE_RE   (broad, alphanumeric-only boundaries)
         └→ lstrip("+/=")       (remove leading delimiter chars)
         └→ trailing variants   (test ==, =, no-pad options)  
         └→ b64decode(validate=True)  (structural validation)
         └→ deduplication       (skip if already found in Phase 1)
```

## Exact Code Change

### File: `src/trustrag/guardrails/input_guardrail.py`

**Added** (lines 86–158): `_BASE64_CANDIDATE_RE` regex, `_MAX_B64_CANDIDATES`, `_MAX_B64_TOKEN_LEN`, `_base64_trailing_variants()`, `_extract_base64_tokens()`

**Modified** (line 280): Changed extraction loop from `_BASE64_TOKEN_RE.findall(original_input)` to `_extract_base64_tokens(original_input)`

### New Regex

```python
_BASE64_CANDIDATE_RE = re.compile(
    r"(?<![A-Za-z0-9])[A-Za-z0-9+/=]{16,}(?![A-Za-z0-9])"
)
```

Only uses `[A-Za-z0-9]` (no `+/=`) in the lookarounds.

### Resource Bounds

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `_MAX_B64_CANDIDATES` | 64 | Max candidates extracted from input |
| `_MAX_B64_TOKEN_LEN` | 8192 | Max single candidate length |
| Decode ceiling | 4096 bytes | Pre-existing, preserved |
| Variant count | ≤4 per candidate | Fixed set: as-is, `==`, `=`, none |

Total worst-case decode attempts: 64 × 4 = 256 (bounded, no exponential behavior).

