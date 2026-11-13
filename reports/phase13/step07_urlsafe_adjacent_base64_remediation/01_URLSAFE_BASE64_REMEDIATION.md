# TrustRAG Phase 13 Step 7 — Remediation A: URL-Safe Base64

**Remediation Target:** RFC 4648 §5 URL-Safe Base64 Evasion Vector  
**Implementation Source:** `src/trustrag/guardrails/input_guardrail.py`  
**Test Suite:** `tests/unit/test_phase_13_step07_urlsafe_adjacent_remediation.py`  
**Status:** Complete & Verified  

---

## 1. Problem Statement & Root Cause

RFC 4648 §5 defines URL-safe Base64 by substituting character 62 (`+` $\to$ `-`) and character 63 (`/` $\to$ `_`), with padding (`=`) optionally omitted.

In Phase 13 Step 6:
- The candidate extraction regex `_BASE64_CANDIDATE_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9+/=]{16,}(?![A-Za-z0-9])")` only recognized standard characters.
- Hyphens (`-`) and underscores (`_`) acted as candidate boundaries, breaking URL-safe payloads into fragments. If fragments were $< 16$ characters, they were omitted; even if $\ge 16$ characters, individual fragments failed to decode the full injection phrase.
- Furthermore, Python's `base64.b64decode` with `validate=False` corrupts or rejects tokens containing `-` and `_`.

---

## 2. Technical Remediation Design

### 2.1 Expanded Candidate Extraction
`_BASE64_CANDIDATE_RE` was updated to incorporate `-` and `_`:
```python
_BASE64_CANDIDATE_RE = re.compile(
    r"(?<![A-Za-z0-9])[A-Za-z0-9+/_\-=]{16,}(?![A-Za-z0-9])"
)
```

### 2.2 Strict Encoding Disambiguation & Validation
In `_try_validate_and_decode(candidate: str)`:
```python
has_std = ("+" in candidate) or ("/" in candidate)
has_url = ("-" in candidate) or ("_" in candidate)

# Strictly reject mixed standard and URL-safe characters within a single token
if has_std and has_url:
    return False, b"", ""

if has_url:
    # URL-safe Base64: normalize to standard alphabet
    normalized = candidate.replace("-", "+").replace("_", "/")
    pad_len = (-len(normalized)) % 4
    normalized_padded = normalized + ("=" * pad_len) if pad_len else normalized
    try:
        dec = base64.b64decode(normalized_padded, validate=True)
        return True, dec, candidate
    except Exception:
        return False, b"", ""
```

### 2.3 Universal Safe Decoding
In `_decode_b64_token(token: str) -> bytes`:
```python
def _decode_b64_token(token: str) -> bytes:
    if "-" in token or "_" in token:
        normalized = token.replace("-", "+").replace("_", "/")
        pad_len = (-len(normalized)) % 4
        if pad_len in (1, 2, 3):
            normalized += "=" * pad_len
        return base64.b64decode(normalized, validate=False)
    pad_len = (-len(token)) % 4
    if pad_len in (1, 2, 3):
        token = token + ("=" * pad_len)
    return base64.b64decode(token, validate=False)
```

---

## 3. Mathematical Proof on UTF-8 Character Boundaries

A critical safety property was established:
**Can a legitimate UTF-8 string ever encode to a Base64 token whose first character is `+`, `/`, `-`, or `_`?**

- In UTF-8, valid leading bytes are `0x00`..`0x7F` (ASCII) or `0xC2`..`0xF4` (multibyte code points).
- The highest possible first 6 bits of any valid UTF-8 byte is `0xF4 >> 2` = 61 (`9`).
- Characters 62 and 63 (`+`, `/`, `-`, `_`) require the initial byte to be $\ge \text{0xF8}$, which is strictly forbidden in UTF-8.
- **Theorem:** Any leading `+`, `/`, `-`, `_`, or `=` preceding an encoded UTF-8 text string is mathematically guaranteed to be a delimiter or noise, NEVER content.
- Therefore, `stripped = cand.lstrip("+/=_ -")` is 100% loss-free for any text-based prompt injection payload.

---

## 4. Verification Results

| Test ID | Input Structure | Payload Alphabet | Decision | Score | Verdict |
|---|---|---|---|---|---|
| `URL-01` | `Execute: {URL_1}` | Padded with `-` | **BLOCK** | 1.00 | **PASS** |
| `URL-02` | `Execute: {URL_1_UNPAD}` | Unpadded with `-` | **BLOCK** | 1.00 | **PASS** |
| `URL-03` | `Execute: {URL_2}` | Padded with `_` | **BLOCK** | 1.00 | **PASS** |
| `URL-04` | `Execute: {URL_2_UNPAD}` | Unpadded with `_` | **BLOCK** | 0.90 | **PASS** |
| `URL-05` | `Execute: {URL_3}` | Padded with both `-` and `_` | **BLOCK** | 1.00 | **PASS** |
| `URL-06` | `Execute: {URL_3_UNPAD}` | Unpadded with both `-` and `_`| **BLOCK** | 1.00 | **PASS** |
| `URL-07` | `/{URL_1}/` | Slash-wrapped URL-safe | **BLOCK** | 1.00 | **PASS** |
| `URL-08` | `+{URL_2}+` | Plus-wrapped URL-safe | **BLOCK** | 1.00 | **PASS** |
| `URL-09` | `-{URL_3}-` | Dash-wrapped URL-safe | **BLOCK** | 1.00 | **PASS** |
| `URL-10` | `_{URL_1_UNPAD}_` | Underscore-wrapped URL-safe | **BLOCK** | 1.00 | **PASS** |
| `URL-11` | `={URL_2}=` | Equals-wrapped URL-safe | **BLOCK** | 1.00 | **PASS** |
| `URL-12` | `Process {URL_3_UNPAD} now` | Embedded in prose sentence | **BLOCK** | 1.00 | **PASS** |

**Conclusion:** Remediation A is fully verified. URL-safe Base64 attacks are reliably captured and inspected.

