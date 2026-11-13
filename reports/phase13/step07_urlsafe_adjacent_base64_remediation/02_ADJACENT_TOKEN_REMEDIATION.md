# TrustRAG Phase 13 Step 7 — Remediation B: Adjacent Slash-Separated Base64 Tokens

**Remediation Target:** Adjacent Slash-Separated Base64 Evasion Vector (`/{A}///{B}/`)  
**Implementation Source:** `src/trustrag/guardrails/input_guardrail.py`  
**Test Suite:** `tests/unit/test_phase_13_step07_urlsafe_adjacent_remediation.py`  
**Status:** Complete & Verified  

---

## 1. Problem Statement & Root Cause

In Phase 13 Step 6, an independent adversarial probe discovered that chaining multiple Base64 tokens separated by repeated slashes bypassed inspection:
```
Query: /{PAYLOAD_A}///{PAYLOAD_B}/
Result: ALLOW (risk_score = 0.00, G1_CLEAN)
```

### Why Did This Happen?
1. The `/` character is both a valid Base64 alphabet character and a common path/wrapper delimiter.
2. `_BASE64_CANDIDATE_RE` consumed the entire sequence `/{PAYLOAD_A}///{PAYLOAD_B}/` as a single candidate string.
3. The guardrail attempted to validate the concatenated string `{PAYLOAD_A}///{PAYLOAD_B}` as ONE Base64 token.
4. Because the combined string violated RFC 4648 formatting (e.g. intermediate padding `=` or misaligned quartet bit boundaries), `base64.b64decode(validate=True)` threw an exception.
5. As a consequence, BOTH valid payloads `{PAYLOAD_A}` and `{PAYLOAD_B}` were discarded!

---

## 2. Technical Remediation Design

### 2.1 Bounded Candidate Disaggregation
A candidate decomposition function `_split_adjacent_candidates(raw: str)` was implemented to extract independent sub-candidates without quadratic or unrestricted scanning:

```python
def _split_adjacent_candidates(raw: str) -> list[str]:
    """Extract sub-candidates when multiple tokens are glued by delimiters (/+, ++, ==, etc.)."""
    subcandidates = [raw]
    # 1. Delimiter runs of 2+ chars: //+, +++, ===, etc.
    runs = re.split(r"[/+=]{2,}", raw)
    if len(runs) > 1:
        for r in runs:
            rc = r.strip("/+=_- ")
            if len(rc) >= 16 and rc not in subcandidates:
                subcandidates.append(rc)
    # 2. '=' padding in the middle of string (e.g. {A}={B} or {A}=={B})
    if "=" in raw[:-2]:
        eq_parts = re.split(r"=+[/+=_\- ]*", raw)
        if len(eq_parts) > 1:
            for ep in eq_parts:
                epc = ep.strip("/+=_- ")
                if len(epc) >= 16 and epc not in subcandidates:
                    subcandidates.append(epc)
    # 3. Single-slash split if multiple parts exist
    if "/" in raw:
        slash_parts = re.split(r"/+", raw)
        if len(slash_parts) > 1:
            for sp in slash_parts:
                spc = sp.strip("/+=_- ")
                if len(spc) >= 16 and spc not in subcandidates:
                    subcandidates.append(spc)
    return subcandidates
```

### 2.2 Preservation of Legitimate Internal Slashes
A critical requirement was preserving legitimate standard Base64 payloads containing internal slashes (e.g. `Pz8/IEhlbGxvID8/PyBXb3JsZCA/Pz8gdGVzdCA/Pz8=` which decodes to `??? Hello ??? World ??? test ???`).
- The candidate string is always tested **as a whole first** (`subcandidates = [raw, ...]`).
- If the candidate validates as a single token, it is extracted as the unified payload.
- Sub-candidates are only extracted if their length is $\ge 16$. In the case of benign text with internal `/`, the fragments between slashes are typically short words ($< 16$ chars) that are automatically skipped.

---

## 3. Verification Results

| Test ID | Input Structure | Scenario Description | Decision | Score | Verdict |
|---|---|---|---|---|---|
| `ADJ-01` | `/{STD_4}///{STD_2}/` | Triple slash-separated | **BLOCK** | 1.00 | **PASS** |
| `ADJ-02` | `/{STD_4}//{STD_2}/` | Double slash-separated | **BLOCK** | 1.00 | **PASS** |
| `ADJ-03` | `{STD_4}/{STD_2}` | Single slash-separated (padded) | **BLOCK** | 1.00 | **PASS** |
| `ADJ-04` | `{STD_4_UNPAD}/{STD_2}` | Single slash-separated (unpadded) | **BLOCK** | 1.00 | **PASS** |
| `ADJ-05` | `+{STD_4}+++{STD_2}+` | Plus-separated adjacent | **BLOCK** | 1.00 | **PASS** |
| `ADJ-06` | `={STD_4}==={STD_2}=` | Equals-separated adjacent | **BLOCK** | 1.00 | **PASS** |
| `ADJ-07` | `/{STD_4}///{URL_3}/` | Mixed standard and URL-safe | **BLOCK** | 1.00 | **PASS** |
| `ADJ-08` | `/{URL_1}///{URL_2}/` | Adjacent URL-safe tokens | **BLOCK** | 1.00 | **PASS** |
| `ADJ-09` | `/{STD_4}///{STD_2}///{URL_3}/` | Three chained distinct tokens | **BLOCK** | 1.00 | **PASS** |
| `ADJ-10` | `////{STD_4}////{STD_2}////` | Leading and trailing repeated slashes | **BLOCK** | 1.00 | **PASS** |
| `ADJ-11` | `/short///{STD_4}/` | Malformed candidate first, then valid | **BLOCK** | 0.90 | **PASS** |
| `ADJ-12` | `/{STD_4}///invalid???noise/` | Valid candidate first, then malformed | **BLOCK** | 0.90 | **PASS** |

**Conclusion:** Remediation B is fully verified. Adjacent slash-separated tokens are reliably disaggregated, validated independently, and blocked.

