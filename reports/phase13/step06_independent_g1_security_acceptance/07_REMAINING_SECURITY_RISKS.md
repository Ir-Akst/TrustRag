# TrustRAG Phase 13 Step 6 — Remaining Security Risks

**Audit Scope:** Comprehensive Risk Register of Open, Residual, and Out-of-Scope Security Risks Post-Remediation  
**Status:** Documented for Production Hardening & Future Phases  

---

## 1. Closed Vulnerabilities Register

| Vulnerability ID | Description | Remediation Phase | Audit Verdict |
|---|---|---|---|
| **REM-01** | G1 padded Base64 regex `\b` stripping equals padding | Phase 13 Step 3 | **CLOSED & VERIFIED** |
| **ADV-EVASION-01** | Alphabet-colliding delimiters (`/`, `+`, `=`) bypass | Phase 13 Step 5 | **CLOSED & VERIFIED** |

---

## 2. Residual & Open Security Risks

### RISK-01: URL-Safe Base64 Encodings (RFC 4648 §5)
- **Severity:** Medium
- **Description:** RFC 4648 §5 specifies an alternative "URL-safe" Base64 alphabet replacing `+` with `-` and `/` with `_`.
- **Observed Behavior:**
  - Neither `_BASE64_TOKEN_RE` nor `_BASE64_CANDIDATE_RE` includes `-` or `_` in their character classes.
  - When a URL-safe Base64 token contains `-` or `_` at intervals shorter than 16 characters (e.g. `Pj5pZ25vcmU-PmFsbD4-cHJldj4-aW5zdA==`), the token is fragmented into pieces smaller than 16 characters.
  - The fragmented pieces are rejected by the length threshold (`< 16`), allowing the payload to bypass inspection.
- **Recommended Remediation:** In a future phase, either:
  1. Add a parallel extraction regex recognizing `[A-Za-z0-9\-_=]{16,}` followed by URL-safe decoding (`base64.urlsafe_b64decode`).
  2. Normalize `-` to `+` and `_` to `/` in candidate tokens prior to standard decoding.
- **Current Status:** Documented architectural limitation. Out of scope for Step 5 remediation.

---

### RISK-02: Glued Multi-Token Delimiter Merging
- **Severity:** Low
- **Description:** When two separate Base64-encoded payloads are concatenated using delimiter characters without whitespace (e.g., `/{PAYLOAD_A}///{PAYLOAD_B}/`):
  - Because `/` is in the candidate character set `[A-Za-z0-9+/=]`, `_BASE64_CANDIDATE_RE` extracts the entire string as a single candidate.
  - The merged string is not valid Base64 as a whole, so structural validation fails, and neither payload is inspected.
- **Workaround / Defense-in-Depth:**
  - Attackers rarely chain two separate Base64 prompt injections with slashes without spaces, as prompt injection typically requires a single contiguous directive.
  - If whitespace separates them (`/{PAYLOAD_A}/ /{PAYLOAD_B}/`), both are extracted and blocked.
- **Current Status:** Accepted residual risk.

---

### RISK-03: Alphanumeric Letter-Glued Delimiters
- **Severity:** Low
- **Description:** If an attacker directly attaches an ASCII alphanumeric letter to a delimiter without spaces (e.g. `word+PAYLOAD+word` or `o+PAYLOAD+caf`):
  - Because `word` is alphanumeric, the lookbehind/lookahead `(?<![A-Za-z0-9])` applies before `word`, including it in the candidate string.
  - `_extract_base64_tokens` currently only strips leading `+/=` (`candidate.lstrip('+/=')`), so it cannot strip `word`.
  - Non-ASCII Unicode (e.g. `Русский+PAYLOAD+текст` or `こんにちは+PAYLOAD+世界`) does NOT suffer from this issue and is correctly blocked.
- **Recommended Remediation:** If required in the future, implement a sliding window search within long candidates to identify quartet-aligned Base64 substrings.
- **Current Status:** Accepted residual risk.

---

### RISK-04: Nested Multi-Layer Encodings
- **Severity:** Low
- **Description:** If an attacker applies Base64 encoding twice (Base64 of Base64):
  - G1 decodes the outer Base64 token to obtain the inner Base64 string.
  - G1 scans the decoded text against `SHARED_THREAT_PATTERNS`.
  - Because the inner text is itself Base64 (and does not match English threat keywords), G1 does not detect it, and does not recursively decode a second time.
- **Risk Assessment:** Recursive decoding without depth limits introduces DoS risks (zip bomb/decode bomb attacks). A single decode layer is standard practice for input guardrails.
- **Current Status:** Accepted design choice.

---

### RISK-05: Non-Base64 Obfuscation Schemes
- **Severity:** Low
- **Description:** Obfuscation schemes outside standard Base64 (e.g. Base32, Base85, Hex-encoded strings, ROT13, Leetspeak, Morse code) are not decoded by G1.
- **Risk Assessment:** TrustRAG relies on downstream layers (retriever cosine similarity, G2 Multi-Signal Detector, and generator grounding) to handle non-executable obfuscated queries.
- **Current Status:** Out of scope for G1 Base64 guardrail.

---

## 3. Summary of Risk Status

The critical security vulnerability ADV-EVASION-01 is **fully resolved** for all standard delimiter evasions. The remaining risks identified above are edge cases or alternative encoding schemes suitable for future defense-in-depth enhancements.

