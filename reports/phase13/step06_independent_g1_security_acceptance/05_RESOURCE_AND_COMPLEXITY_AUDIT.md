# TrustRAG Phase 13 Step 6 — Resource & Complexity Audit

**Audit Scope:** Independent Resource, Latency, Memory, and Complexity Audit  
**Implementation Source:** `src/trustrag/guardrails/input_guardrail.py`  
**Audit Status:** Complete & Verified  

---

## 1. Complexity & Resource Bounds Audit

Adversarial inputs designed to exhaust CPU or memory via regex catastrophic backtracking, unbounded candidate generation, or memory leaks were tested against the implementation.

### 1.1 Declared Architecture Bounds

| Constant / Bound | Value | Purpose | Audit Verdict |
|---|---|---|---|
| `_MAX_B64_CANDIDATES` | 64 | Maximum number of candidates extracted per query | **ENFORCED & BOUNDED** |
| `_MAX_B64_TOKEN_LEN` | 8192 | Maximum character length of any single candidate | **ENFORCED & BOUNDED** |
| Decode Ceiling | 4096 bytes | Truncates decoded byte stream before UTF-8 decoding | **ENFORCED & BOUNDED** |
| Trailing Variants | ≤ 4 attempts | Fixed set of padding trials per candidate (`as-is`, `==`, `=`, none) | **ENFORCED & BOUNDED** |
| Max Input Length | 4096 chars | `GuardrailsConfig().max_input_length` threshold | **ENFORCED & BOUNDED** |

### 1.2 Worst-Case Mathematical Bound
For any query (regardless of input size or adversarial crafting):
$$\text{Max Decodes per Query} = \min(N, 64) \times 4 = 256 \text{ decode operations}$$
$$\text{Max Decoded Memory per Token} = 4096 \text{ bytes (4 KB)}$$
$$\text{Max Decoded Working Set} = 64 \times 4 \text{ KB} = 256 \text{ KB}$$

Because both regexes are strictly deterministic linear scans without nested quantifiers, worst-case extraction complexity is **$O(L)$** where $L$ is the query string length.

---

## 2. Empirical Benchmark Results

**Test Script:** `evidence/probe_resource_complexity.py`  
**Raw Results:** `evidence/probe_resource_complexity.json`

| Check ID | Stress Test Scenario | Measured Value | Threshold | Result |
|---|---|---|---|---|
| `RES-01` | Candidate Count Limit Constant | 64 | $\le 128$ | **PASS** |
| `RES-02` | Max Token Length Constant | 8192 | $\le 16384$ | **PASS** |
| `RES-03` | Normal-length input (< 200 chars) | 0.11 ms | $< 5.0$ ms | **PASS** |
| `RES-04` | Input near 4096 boundary (3984 chars) | 0.82 ms | $< 10.0$ ms | **PASS** |
| `RES-05` | Input over max length (5084 chars) | Flagged / Blocked | Safe failure | **PASS** |
| `RES-06` | Mass candidate injection (200 tokens) | Extracted: 1 token (dedup) | $\le 64$ tokens | **PASS** |
| `RES-07` | Large payload within bounds (8000 chars)| Extracted safely | No crash | **PASS** |
| `RES-08` | Oversized payload (13,336 chars) | 0 tokens (skipped) | Skipped $> 8192$ | **PASS** |
| `RES-09` | 1,000 Base64-looking fragments | 11.2 ms | $< 500$ ms | **PASS** |
| `RES-10` | Payload buried in 20 `+` delimiters | Extracted in 0.12 ms | $< 5.0$ ms | **PASS** |
| `RES-11` | Excessive padding (6 `=` signs) | Trimmed & safe | No crash | **PASS** |
| `RES-12` | 3 distinct malicious payloads in 1 query | 3 tokens extracted (0.28 ms) | All blocked | **PASS** |
| `RES-13` | 100-iteration benchmark (malicious query)| P50: 0.11 ms, P95: 0.18 ms | P95 $< 10.0$ ms | **PASS** |
| `RES-14` | 100-iteration benchmark (benign query) | P50: 0.05 ms, P95: 0.09 ms | P95 $< 5.0$ ms | **PASS** |
| `RES-15` | Memory leak audit (200 evaluations) | $\Delta = +0.00$ KB | $< 5000$ KB | **PASS** |
| `RES-16` | Adversarial worst-case (70 junk tokens) | 2.14 ms | $< 100$ ms | **PASS** |

**Summary: 16/16 (100%) Resource Checks PASSED.**

---

## 3. Latency Profile

Across 100 repeated evaluations of delimiter-wrapped injection queries:
- **Minimum Latency:** 0.098 ms
- **P50 (Median):** 0.112 ms
- **P95:** 0.184 ms
- **P99:** 0.321 ms
- **Maximum:** 0.445 ms
- **Mean:** 0.126 ms

The overhead of Phase 2 candidate extraction and structural validation is **$< 0.07$ ms** compared to the baseline benign evaluation (0.05 ms), representing negligible overhead in production RAG inference pipelines.

---

## 4. Memory Stability & Leak Audit

Using Python `tracemalloc`, heap allocations were tracked across 200 consecutive evaluations of adversarial Base64 queries:
- **Baseline Heap Allocation:** 28.4 MB
- **Final Heap Allocation (after 200 evals):** 28.4 MB
- **Net Allocated Difference:** **0.00 KB**

No uncollected memory references, regex cache blowups, or string accumulation leaks were observed.

---

## 5. Audit Conclusion

The remediation satisfies all resource, complexity, latency, and memory safety requirements. Catastrophic backtracking is structurally impossible due to linear character class lookarounds, and decoding work is strictly bounded to a maximum of 256 attempts per query.

