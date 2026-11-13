# Phase 13 Step 5 — Remaining Risks

## Closed

| ID | Risk | Status |
|----|------|--------|
| REM-01 | G1 padded Base64 `\b` boundary stripping | **CLOSED** (Step 3) |
| ADV-EVASION-01 | G1 alphabet-colliding delimiter bypass | **CLOSED** (Step 5) |

## Open — Known Limitations

### 1. URL-Safe Base64 (RFC 4648 §5)

**Risk Level:** MEDIUM

URL-safe Base64 uses `-` and `_` instead of `+` and `/`. Neither `_BASE64_TOKEN_RE` nor `_BASE64_CANDIDATE_RE` includes these characters in the alphabet.

An attacker encoding a prompt injection payload using URL-safe Base64 would bypass G1 entirely.

**Mitigation:** Add a parallel URL-safe extraction regex or normalize `-_` to `+/` before extraction.

**Status:** Documented as known gap. Not in scope for this remediation.

### 2. Nested Base64 (Base64-of-Base64)

**Risk Level:** LOW

If an attacker double-encodes a payload (Base64 of Base64), G1 will decode the outer layer and inspect the result. If the inner layer is also Base64, it will NOT be decoded a second time.

Step 4 probe ADV-10 confirmed this limitation exists but rates it LOW risk because:
- The inner encoded payload must itself trigger threat patterns in its Base64 form to be dangerous at the outer layer.
- Adding recursive decoding introduces unbounded processing risk.

**Status:** Accepted risk. No change.

### 3. Fragmented Base64

**Risk Level:** LOW

If an attacker splits a Base64 payload across multiple query parameters, chat messages, or input fields, G1 processes each fragment independently and may not detect the reassembled injection.

**Status:** Architectural limitation. Would require cross-field correlation, which is out of scope for G1's single-query design.

### 4. Timing Side Channel

**Risk Level:** VERY LOW

Phase 2 extraction performs up to `_MAX_B64_CANDIDATES` × 4 decode attempts. An attacker could potentially distinguish between inputs that trigger many vs. few decode attempts via timing.

**Mitigation:** The bounded constants (64 candidates × 4 variants = 256 max decodes) keep worst-case processing well under 1ms, making timing attacks impractical.

### 5. Non-Standard Encodings

**Risk Level:** LOW

G1 only inspects standard Base64 (RFC 4648 §4). Other encodings (Base32, Base85, hex-encoded payloads, ROT13, custom alphabets) are not decoded.

**Status:** Out of scope. Would require a broader obfuscation-detection layer.

