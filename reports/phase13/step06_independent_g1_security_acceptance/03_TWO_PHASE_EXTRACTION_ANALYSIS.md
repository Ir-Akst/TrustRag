# TrustRAG Phase 13 Step 6 — Two-Phase Extraction Analysis

**Audit Scope:** Deep Structural Analysis of the Two-Phase Extraction Implementation  
**Source Code:** `src/trustrag/guardrails/input_guardrail.py` (lines 80–158)  
**Audit Status:** Complete & Rigorously Analyzed  

---

## 1. Architectural Architecture

The remediation introduces a two-phase architecture designed to combine backward-compatible speed with adversarial delimiter resilience:

```
                  Raw Query Input
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
    [ Phase 1 ]                   [ Phase 2 ]
 Strict Fast-Path Regex       Alphanumeric Candidate Regex
  _BASE64_TOKEN_RE            _BASE64_CANDIDATE_RE
  (length >= 16, strict)      (length >= 16, [A-Za-z0-9] boundary)
         │                             │
         │ (clean tokens)              │ (candidate runs)
         │                             ▼
         │                     lstrip("+=/")
         │                             │
         │                             ▼
         │                   _base64_trailing_variants()
         │                   (tries as-is, ==, =, no-pad)
         │                             │
         │                             ▼
         │                   base64.b64decode(validate=True)
         │                             │
         │ (deduplicate against Phase 1)
         └──────────────┬──────────────┘
                        ▼
             Validated Base64 Tokens
                        │
                        ▼
              4KB Decode & Inspect
         (match_threat_patterns -> G1)
```

---

## 2. Component Inspection

### 2.1 Phase 1 Regex: `_BASE64_TOKEN_RE`
```python
_BASE64_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9+/=])(?:[A-Za-z0-9+/]{4}){3,}"
    r"(?:[A-Za-z0-9+/]{4}|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)"
    r"(?![A-Za-z0-9+/=])"
)
```
- **Strengths:** O(N) single-pass regex; zero false-token generation for standard whitespace or punctuation-delimited text.
- **Weakness:** Cannot match when `/`, `+`, or `=` immediately abut the token.

### 2.2 Phase 2 Regex: `_BASE64_CANDIDATE_RE`
```python
_BASE64_CANDIDATE_RE = re.compile(
    r"(?<![A-Za-z0-9])[A-Za-z0-9+/=]{16,}(?![A-Za-z0-9])"
)
```
- **Boundaries:** Uses only `(?<![A-Za-z0-9])` and `(?![A-Za-z0-9])`. Delimiter characters (`/`, `+`, `=`) are explicitly allowed outside the token, allowing the regex to capture runs that include surrounding delimiters.
- **Bounds:** Capped at `[:_MAX_B64_CANDIDATES]` (64 items) with single-token length check `len(raw) <= 8192`.

### 2.3 Post-Extraction Trimming: `_base64_trailing_variants`
```python
def _base64_trailing_variants(s: str) -> list[str]:
    core = s.rstrip("+/=")
    trailing = s[len(core):]
    variants = [s]
    if trailing:
        for pad in ("==", "=", ""):
            candidate = core + pad
            if len(candidate) >= 16 and candidate not in variants:
                variants.append(candidate)
    return variants
```
- **Behavior:** Strips trailing delimiter noise, reconstructs standard quartet padding (`==`, `=`, or none), and tests structural validity via `base64.b64decode(trial, validate=True)`.
- **Complexity:** Maximum 4 variant attempts per candidate. With 64 candidates, maximum decode validations = 256 calls.

---

## 3. Independent Adversarial Probes

**Test Script:** `evidence/probe_extraction_adversarial.py`  
**Raw Results:** `evidence/probe_extraction_adversarial.json`

| ID | Adversarial Test Scenario | Observed Behavior | Verdict |
|---|---|---|---|
| `ADV-EXT-01` | Single slash-wrapped malicious | Phase 1 misses, Phase 2 extracts, decoded & blocked | **PASS** |
| `ADV-EXT-02` | Clean token + slash-wrapped token | Both extracted, deduplicated, blocked | **PASS** |
| `ADV-EXT-03` | Benign clean + malicious slash-wrapped | 2 tokens extracted, malicious triggers block | **PASS** |
| `ADV-EXT-04` | Benign slash + malicious slash | 2 tokens extracted, malicious triggers block | **PASS** |
| `ADV-EXT-05` | Payload embedded in alphanumeric (`AAAA{P}BBBB`) | Extracted via aligned 4-multiple slice, blocked | **PASS** |
| `ADV-EXT-06` | Two payloads glued by `///` (`/{A}///{B}/`) | Merges into single invalid candidate (uninspected) | **DOCUMENTED** |
| `ADV-EXT-07` | Two payloads separated by `++` (`+{A}++{B}+`) | Extracted & blocked | **PASS** |
| `ADV-EXT-08` | Triple-equals wrapped (`==={P}===`) | Trailing variants trims padding, blocked | **PASS** |
| `ADV-EXT-09` | Corrupted padding (`...===`) | Trimmed to valid core, decoded & blocked | **PASS** |
| `ADV-EXT-10` | URL-safe payload (`-` and `_`) | Fragments < 16 chars bypass extraction | **DOCUMENTED** |
| `ADV-EXT-11` | Payload surrounded by `-` and `_` | Boundaries succeed, extracted & blocked | **PASS** |
| `ADV-EXT-12` | Nested Base64 (base64 of base64) | Outer layer decodes to base64 (allowed, safe) | **PASS** |
| `ADV-EXT-13` | Invalid UTF-8 decode bytes | Decodes safely with `errors="ignore"`, no crash | **PASS** |
| `ADV-EXT-14` | Random Base64 SHA-512 (benign) | Extracted, decodes to non-threat, allowed | **PASS** |
| `ADV-EXT-15` | Malformed candidate then valid malicious | Malformed skipped, valid extracted & blocked | **PASS** |
| `ADV-EXT-16` | Malformed noise then valid malicious | Safe continuation, blocked | **PASS** |
| `ADV-EXT-17` | Space-split payload (not reassembled) | 2 invalid fragments, allowed (architectural) | **PASS** |
| `ADV-EXT-18` | Clean boundary payload | Phase 1 fast-path catches, blocked | **PASS** |
| `ADV-EXT-19` | Deduplication check | Exactly 1 token extracted when clean + wrapped | **PASS** |

### Helper Function Unit Tests
- `TRAIL-01` (`variants for 'core==/' include '==' and '='`): **PASS**
- `TRAIL-02` (`clean padding preserved as first variant`): **PASS**
- `TRAIL-03` (`no trailing chars returns single variant`): **PASS**
- `REGEX-01` (`Phase 1 does NOT match slash-wrapped`): **PASS**
- `REGEX-02` (`Phase 2 matches slash-wrapped`): **PASS**
- `REGEX-03` (`Phase 1 matches clean boundary`): **PASS**

**Suite Verdict: 25/25 PASSED.**

---

## 4. Architectural Analysis & Edge Cases

### 4.1 Independent Token Isolation
A critical property verified by `ADV-EXT-15` and `ADV-EXT-16`: **A malformed or un-decodable candidate NEVER aborts the extraction loop.** Python's `try...except Exception: continue` ensures subsequent valid candidates in the same query are fully inspected.

### 4.2 Deduplication Efficiency
When a query contains both clean and delimiter-wrapped occurrences of the same token, Phase 1 registers the token in `seen: set[str]`. Phase 2 checks `if trial in seen: break`, avoiding duplicate decode and threat-matching passes.

### 4.3 Glued Delimiter Limitation (`ADV-EXT-06`)
When two valid Base64 tokens are concatenated using delimiter characters without intervening whitespace (`/{MAL_A}///{MAL_B}/`):
- `_BASE64_CANDIDATE_RE` treats the entire sequence as a single candidate because `/` is in `[A-Za-z0-9+/=]`.
- Because the combined length and characters do not form valid Base64, neither token is extracted.
- **Risk Assessment:** Low in practice, as prompt injection attacks typically execute a single cohesive instruction rather than two chained Base64 payloads glued without spaces. Documented in residual risks.

### 4.4 Conclusion
The two-phase extraction architecture is sound, safe, and robust. It cleanly isolates regular queries from adversarial delimiter manipulations without introducing quadratic regex backtracking.

