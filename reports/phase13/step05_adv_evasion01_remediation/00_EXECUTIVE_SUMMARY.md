# Phase 13 Step 5 — ADV-EVASION-01 Executive Summary

**Date:** 2026-11-13  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11`  
**HEAD:** `8229aee01a0b6f7fd61a5e774da5bb707bd6a7c1`  

## Vulnerability

**ADV-EVASION-01 — G1 Alphabet-Colliding Delimiter Bypass**

Base64-encoded prompt injection payloads bypass G1 detection when enclosed by characters from the Base64 alphabet (`/`, `+`, `=`).

Discovered by the independent Phase 13 Step 4 security audit.

## Root Cause

The `_BASE64_TOKEN_RE` regex uses `[A-Za-z0-9+/=]` in both negative lookarounds. When `+`, `/`, or `=` appear as delimiters around a payload, the regex fails to match because the lookaround character class includes these same characters.

## Fix

Two-phase Base64 token extraction:

| Phase | Regex | Boundaries | Purpose |
|-------|-------|-----------|---------|
| 1 (original) | `_BASE64_TOKEN_RE` | Includes `+/=` | Backward-compatible fast path |
| 2 (new) | `_BASE64_CANDIDATE_RE` | Alphanumeric only | Catches alphabet-colliding delimiters |

Phase 2 strips leading delimiter chars, generates trailing-padding variants, and validates with `base64.b64decode(validate=True)`. De-duplicated against Phase 1 results.

## Before / After

| Metric | Before | After |
|--------|--------|-------|
| Evasion attacks bypassed | **13/13** | **0/13** |
| Controls blocked | 3/3 | 3/3 |
| False positives | 0 | 0 |
| New regression tests | — | **43 passed** |
| Step 3 tests | 17/17 | 17/17 |
| Step 4 adversarial probes | 17/17 | 17/17 |
| Full test suite | 454 passed | **497 passed**, 2 deselected |
| Spec validation gates | 13/13 | 13/13 |

## Files Modified

1. `src/trustrag/guardrails/input_guardrail.py` — Added `_BASE64_CANDIDATE_RE`, `_base64_trailing_variants()`, `_extract_base64_tokens()`; updated extraction loop.

## Files Added

1. `tests/unit/test_phase_13_step05_evasion01_remediation.py` — 43 regression tests.

## Verdict

**FIX_VERIFIED** — ADV-EVASION-01 is closed. Zero regressions. Zero false positives.

## Remaining Risks

1. URL-safe Base64 (RFC 4648 §5, `-` and `_`) is NOT extracted.
2. Nested Base64 is detected to one level only.
3. Fragmented Base64 across multiple parameters is not reassembled.

