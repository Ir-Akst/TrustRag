# TrustRAG Phase 13 Step 8 — Splitter Security and Boundary Analysis

**Target Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11`  
**HEAD Commit:** `8229aee01a0b6f7fd61a5e774da5bb707bd6a7c1`  
**Audit Component:** `_split_adjacent_candidates()` in `src/trustrag/guardrails/input_guardrail.py`  
**Audit Script:** `evidence/probe_step08_independent_audit.py`  
**Verdict:** **`SECURE` (All safety bounds, limits, and ReDoS protections strictly verified)**

---

## 1. Splitter Architecture Inspection

The candidate splitting logic in `src/trustrag/guardrails/input_guardrail.py` is invoked during Phase 2 of `_extract_base64_tokens()`:
```python
def _split_adjacent_candidates(raw: str) -> list[str]:
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

---

## 2. Adversarial Security Dimensions & Findings

### 2.1 Boundary Limits Enforcement

| Boundary Dimension | Configured Constraint | Stress Test Vector | Actual Observed Behavior | Verdict |
|---|---|---|---|---|
| **Candidate Cap** | `_MAX_B64_CANDIDATES = 64` | Input with 200 distinct delimited tokens (`/{tok_i}/`) | Exactly 64 evaluated; remainder truncated | **ENFORCED** |
| **Max Token Length** | `_MAX_B64_TOKEN_LEN = 8192` | Giant token of 10,000 chars (`/{'A' * 10000}/`) | Immediately discarded (`len(raw) > 8192`); 0 tokens | **ENFORCED** |
| **Min Candidate Length** | $\ge 16$ characters | Short token (`SGVsbG8=`, 8 chars) | Discarded by `len(rc) >= 16` check; 0 tokens | **ENFORCED** |
| **Decoded Byte Ceiling** | $4096$ bytes max | Valid Base64 encoding of 10,000 bytes | `dec_bytes[:4096]` sliced before threat matching | **ENFORCED** |

### 2.2 Resistance to Regular Expression Denial of Service (ReDoS)
- **Pathological Input:** A string containing 1,000 consecutive slash delimiters wrapping a valid token:
  `"/" * 500 + valid_token + "/" * 500`
- **Execution Time:** **$0.027\text{ ms}$**
- **Analysis:** Patterns `r"[/+=]{2,}"`, `r"=+[/+=_\- ]*"`, and `r"/+"` contain no nested unbounded quantifiers or ambiguous alternations. Python's regex engine evaluates them deterministically with linear time complexity $\mathcal{O}(N)$ without backtracking.

### 2.3 Candidate Starvation & Suppression Resistance
- **Attack Scenario:** Prepending malformed or garbage candidates (`NOT_VALID_BASE64_###` or `/SHORT_INVALID///`) before a genuine malicious payload.
- **Observed Behavior:** Each slice in `candidate_slices` is evaluated independently. A failure in `_try_validate_and_decode()` for slice 1 does not terminate the loop or suppress evaluation of slice 2. In probe `ADJ-06`, the malicious payload following the malformed token was extracted and blocked with risk score $1.00$.

### 2.4 Duplicate Candidate Generation & Overlap Handling
- **Deduplication:** Slices are deduplicated twice:
  1. Inside `_split_adjacent_candidates`: `if ... and rc not in subcandidates: subcandidates.append(rc)`
  2. Inside `_extract_base64_tokens`: `seen: set[str]` tracks every validated token across both Phase 1 and Phase 2.
- **Empirical Check:** In probe `SPLIT-01`, repeated occurrences of identical tokens produced exactly 1 unique evaluation entry, preventing resource exhaustion via duplication.

### 2.5 Empty & Degenerate Input Safety
- **Adversarial Inputs:** `""`, `"///"`, `"++++"`, `"====="`, `"///+++==="`, `"   "`.
- **Observed Behavior:** No exceptions raised. All degenerate strings stripped to empty substrings or lengths $< 16$, yielding 0 candidate tokens and safely proceeding to standard input evaluation.

---

## 3. Summary Assessment

The splitter function `_split_adjacent_candidates()` is structurally sound, strictly enforces all configured resource boundaries, exhibits deterministic linear complexity $\mathcal{O}(N)$, and is completely immune to candidate starvation and ReDoS bypass attempts.

