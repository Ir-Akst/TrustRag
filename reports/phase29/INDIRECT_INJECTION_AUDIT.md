# Phase 29 — Indirect Prompt Injection Audit

---

## 1. Threat Model & Experimental Scope

Indirect prompt injection occurs when a user submits a benign query, but external knowledge documents fetched by the retriever contain adversarial instructions designed to hijack the generator's execution.

Because G1 only inspects the user query, **G1 provides 0.0% coverage against indirect prompt injection**. The defense must rely entirely on G2 (retrieval pruning) and G3 (output verification).

---

## 2. Empirical Results ($N=12$ Cases: 9 Attacks, 3 Controls)

| Metric | Measured Value | Wilson 95% Confidence Interval |
| :--- | :--- | :--- |
| **Total Test Cases** | 12 | - |
| **Adversarial Poisoned Injections** | 9 | - |
| **Benign Controls** | 3 | - |
| **G1 Query Interception Rate** | **0.00%** ($0 / 9$) | $[0.00\%, 30.79\%]$ |
| **G2 Pruning Rate on Malicious Passages** | **55.56%** ($5 / 9$) | $[26.66\%, 81.12\%]$ |
| **Attacks Reaching LLM Generator** | **44.44%** ($4 / 9$) | $[18.88\%, 73.34\%]$ |
| **Clean Control False Positive Rate** | **0.00%** ($0 / 3$) | $[0.00\%, 56.15\%]$ |

---

## 3. Failure Mode Analysis: Why Indirect Injections Bypass G2

1. **Semantic Alignment with Query**:
   When an attacker hides an injection inside a passage that otherwise directly answers the query (e.g. `INDIRECT_HID_01` on Nginx SSL configuration), the passage exhibits high semantic similarity to the query. G2's distance clustering considers the passage an in-distribution core document rather than an outlier.
2. **Disguised Documentation Pretexts**:
   Instructions formatted as developer notices or official system documentation (e.g. `INDIRECT_DOC_01`) exhibit normal lexical distributions and evade both keyword density and clustering filters.
3. **Implication for Manuscript Claims**:
   The manuscript must explicitly disclaim that TrustRAG prevents indirect prompt injection. G2 prunes crude poisoning outliers, but semantic indirect injections pass through to the generator in **$44.44\%$** of test cases.
