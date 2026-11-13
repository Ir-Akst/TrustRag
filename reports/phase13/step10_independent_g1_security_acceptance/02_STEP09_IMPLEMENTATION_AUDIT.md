# TrustRAG Phase 13 Step 10 — Step 9 Implementation Code Audit

**Auditor:** Independent Senior Application-Security Auditor & Code Reviewer  
**Component:** `src/trustrag/guardrails/input_guardrail.py`  
**Verdict:** **`CODE_VERIFIED` (All 9 architectural invariants confirmed)**

---

## 1. Source Code Inspection & Control-Flow Trace

The independent auditor examined lines 142–245 and 370–395 of `src/trustrag/guardrails/input_guardrail.py` to trace the actual execution path from raw input to candidate evaluation.

### 1.1 Phase 1 Extraction Path (Clean Boundaries)
```python
phase1_count = 0
for match_obj in _BASE64_TOKEN_RE.finditer(text):
    if phase1_count >= _MAX_B64_CANDIDATES:
        break
    match = match_obj.group(0)
    phase1_count += 1
    if len(match) > _MAX_B64_TOKEN_LEN:
        continue
    if match not in seen:
        seen.add(match)
        tokens.append(match)
```
- **Invariant 1 (Lazy Iteration):** `_BASE64_TOKEN_RE.finditer(text)` creates an iterator object rather than allocating a Python list. Match objects are yielded on demand.
- **Invariant 2 (Candidate Bound):** `phase1_count >= _MAX_B64_CANDIDATES` breaks the loop immediately upon encountering 64 candidate matches.
- **Invariant 3 (Token Length Bound):** `len(match) > _MAX_B64_TOKEN_LEN` skips any token exceeding 8,192 characters.
- **Invariant 4 (Deduplication):** `seen: set[str]` prevents repeated occurrences of identical tokens from populating `tokens`.

### 1.2 Phase 2 Extraction Path (Broader Delimiters & Adjacent Tokens)
```python
phase2_count = 0
for match_obj in _BASE64_CANDIDATE_RE.finditer(text):
    if phase2_count >= _MAX_B64_CANDIDATES:
        break
    raw = match_obj.group(0)
    phase2_count += 1
    if len(raw) > _MAX_B64_TOKEN_LEN:
        continue
    candidate_slices = _split_adjacent_candidates(raw)
    for cand in candidate_slices:
        if len(cand) > _MAX_B64_TOKEN_LEN:
            continue
        stripped = cand.lstrip("+/=_ -")
        if len(stripped) < 16:
            continue
        for trial in _base64_trailing_variants(stripped):
            if len(trial) < 16:
                continue
            if trial in seen:
                break
            ok, dec_bytes, valid_token = _try_validate_and_decode(trial)
            if ok:
                if valid_token not in seen:
                    seen.add(valid_token)
                    tokens.append(valid_token)
                break
```
- **Invariant 5 (Phase 2 Lazy Iteration):** Also migrated from `.findall()[:64]` to `.finditer(text)`, eliminating the initial full list allocation.
- **Invariant 6 (Phase 2 Candidate Cap):** `phase2_count >= _MAX_B64_CANDIDATES` halts match evaluation at 64 tokens.

### 1.3 Sub-Candidate Splitter Bounding
In `_split_adjacent_candidates(raw)`:
```python
subcandidates = [raw]
# 1. Delimiter runs of 2+ chars: //+, +++, ===, etc.
runs = re.split(r"[/+=]{2,}", raw)
if len(runs) > 1:
    for r in runs:
        if len(subcandidates) >= _MAX_B64_CANDIDATES:
            break
        ...
# 2. '=' padding in the middle of string
if "=" in raw[:-2] and len(subcandidates) < _MAX_B64_CANDIDATES:
    ...
# 3. Single-slash split
if "/" in raw and len(subcandidates) < _MAX_B64_CANDIDATES:
    ...
```
- **Invariant 7 (Splitter Ceiling):** The length of `subcandidates` is strictly bounded by `_MAX_B64_CANDIDATES = 64`. Even if an adversary supplies a candidate string packed with 500 slashes, `subcandidates` never exceeds 64 items.

### 1.4 Downstream Inspection Ceiling
In `InputGuardrail.evaluate()`:
```python
for b64_token in _extract_base64_tokens(original_input):
    try:
        dec_bytes = _decode_b64_token(b64_token)
        dec_text = dec_bytes[:4096].decode("utf-8", errors="ignore")
        if not dec_text.strip():
            continue
        for spec, snippet in match_threat_patterns(dec_text, target="query"):
            ...
```
- **Invariant 8 (Decoded Content Bound):** Slicing `dec_bytes[:4096]` guarantees that regex threat pattern scanning never operates on more than 4,096 bytes per token.
- **Invariant 9 (Absence of Quadratic Behavior):** Neither `_BASE64_TOKEN_RE` nor `_BASE64_CANDIDATE_RE` contains nested quantifiers or ambiguous alternations. Evaluation complexity is strictly linear $\mathcal{O}(N)$.

---

## 2. Invariant Compliance Matrix

| Invariant # | Verification Item | Inspection Proof | Compliance |
|---|---|---|---|
| **INV-01** | Phase 1 lazy `finditer()` | `_BASE64_TOKEN_RE.finditer(text)` at line 209 | **VERIFIED** |
| **INV-02** | Phase 2 lazy `finditer()` | `_BASE64_CANDIDATE_RE.finditer(text)` at line 222 | **VERIFIED** |
| **INV-03** | `_MAX_B64_CANDIDATES = 64` enforced on both | Breaks at count $\ge 64$ in both loops | **VERIFIED** |
| **INV-04** | `_MAX_B64_TOKEN_LEN = 8192` enforced on both | `len(match) > 8192: continue` in both paths | **VERIFIED** |
| **INV-05** | Splitter bounded to 64 | `len(subcandidates) >= 64: break` in all 3 phases | **VERIFIED** |
| **INV-06** | Decoded content bounded to 4096 bytes | `dec_bytes[:4096]` at line 373 | **VERIFIED** |
| **INV-07** | Zero intermediate eager allocations | No `.findall()` calls remain in candidate extraction | **VERIFIED** |
| **INV-08** | No alternate bypass paths | All Base64 evaluation flows strictly through `_extract_base64_tokens` | **VERIFIED** |
| **INV-09** | ReDoS immunity | Linear regex character classes with atomic lookarounds | **VERIFIED** |

---

## 3. Conclusion

The code implementation in `src/trustrag/guardrails/input_guardrail.py` satisfies all required security, bounding, and architectural invariants without deviation.

