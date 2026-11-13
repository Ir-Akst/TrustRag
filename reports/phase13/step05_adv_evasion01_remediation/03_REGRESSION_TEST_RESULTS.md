# Phase 13 Step 5 — Regression Test Results

## New Tests: `test_phase_13_step05_evasion01_remediation.py`

**Total: 43 passed, 0 failed**

### Category A: Alphabet-Colliding Delimiters (17 tests)

| Test | Delimiter Pattern | Payload | Result |
|------|------------------|---------|--------|
| `test_evasion_blocked[slash-wrap-sp]` | `/payload=/` | Single pad | PASS |
| `test_evasion_blocked[slash-wrap-dp]` | `/payload==/` | Double pad | PASS |
| `test_evasion_blocked[plus-wrap-sp]` | `+payload=+` | Single pad | PASS |
| `test_evasion_blocked[plus-wrap-dp]` | `+payload==+` | Double pad | PASS |
| `test_evasion_blocked[eq-wrap-sp]` | `=payload==` | Single pad | PASS |
| `test_evasion_blocked[eq-wrap-dp]` | `=payload===` | Double pad | PASS |
| `test_evasion_blocked[slash-prefix]` | `/payload= text` | Prefix only | PASS |
| `test_evasion_blocked[plus-prefix]` | `+payload= text` | Prefix only | PASS |
| `test_evasion_blocked[slash-suffix]` | `text payload=/` | Suffix only | PASS |
| `test_evasion_blocked[plus-suffix]` | `text payload=+` | Suffix only | PASS |
| `test_evasion_blocked[np-slash-wrap]` | `/payload/` | No pad | PASS |
| `test_evasion_blocked[multi-token]` | `/A=/ and +B==+` | Multi | PASS |
| `test_evasion_blocked[unicode-adjacent]` | `こんにちは/payload=/世界` | Unicode | PASS |
| `test_mixed_delimiters_blocked[mixed-slash-plus]` | `/payload=+` | Mixed | PASS |
| `test_mixed_delimiters_blocked[mixed-plus-slash]` | `+payload==/` | Mixed | PASS |
| `test_mixed_delimiters_blocked[triple-slash]` | `///payload=///` | Triple | PASS |
| `test_mixed_delimiters_blocked[triple-plus]` | `+++payload==+++` | Triple | PASS |

### Category B: Backward Compatibility (7 tests)

| Test | Delimiter | Result |
|------|-----------|--------|
| `test_clean_boundary_blocked[space-delimited-sp]` | Space | PASS |
| `test_clean_boundary_blocked[space-delimited-dp]` | Space | PASS |
| `test_clean_boundary_blocked[dot-delimited]` | Period | PASS |
| `test_clean_boundary_blocked[bracket-delimited]` | Brackets | PASS |
| `test_clean_boundary_blocked[beginning-of-input]` | BOL | PASS |
| `test_clean_boundary_blocked[end-of-input]` | EOL | PASS |
| `test_clean_boundary_blocked[newline-delimited]` | Newline | PASS |

### Category C: Token Extraction Unit Tests (7 tests)

All PASS — verifies extraction, deduplication, boundary enforcement, short token rejection.

### Category D: False-Positive Safety (8 tests)

All PASS — benign questions, SHA-256 hashes, UUIDs, URLs, emails, multilingual content.

### Category E: Resource Bounds (4 tests)

All PASS — large payloads, many candidates, invalid Base64, malformed UTF-8.

## Existing Tests

| Suite | Result |
|-------|--------|
| `test_phase_13_step03_base64_remediation.py` | **17/17 passed** |
| Full test suite (`pytest -W error -q`) | **497 passed, 2 deselected** |

