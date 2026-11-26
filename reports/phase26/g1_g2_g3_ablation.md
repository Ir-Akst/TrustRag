# TrustRAG Phase 26: G1 / G2 / G3 Layer Ablation Study

**Evaluation Date:** 2026-11-24  
**Evaluator:** Principal ML Systems Architect & Security Researcher  
**Ablation Cohort:** 100 Adversarial Samples & 100 Benign Control Samples  

---

## 1. Experimental Design

To isolate the individual contribution of each defensive tier in TrustRAG, identical evaluation cohorts were processed through 5 controlled configurations:

1. **Config 1 — Baseline RAG (No Defense):** Standard retrieval and generation with zero guardrails.
2. **Config 2 — G1 Input Guardrail Only:** Pre-retrieval query screening active; document filtering disabled.
3. **Config 3 — G2 Document MSD Only:** Query screening disabled; candidate document filtering active.
4. **Config 4 — G1 + G2 Defense:** Both input guardrail and document multi-signal detection active.
5. **Config 5 — Full TrustRAG (G1 + G2 + G3):** Complete defense-in-depth pipeline active.

---

## 2. Controlled Ablation Results Table

| Configuration | Adversarial Blocked ($TP$) | ADR (%) | Wilson 95% CI (ADR) | Benign Allowed ($TN$) | Clean Delivery (%) | Strict FPR (%) | Total Exec Time | Avg Latency |
|---|---|---|---|---|---|---|---|---|
| **1. Baseline RAG** | 0 / 100 | **0.00%** | [0.00%, 3.70%] | 100 / 100 | **100.00%** | 0.00% | 0.01 ms | 0.000 ms |
| **2. G1 Only** | 48 / 100 | **48.00%** | [38.46%, 57.68%] | 100 / 100 | **100.00%** | 0.00% | 38.79 ms | 0.194 ms |
| **3. G2 Only** | 0 / 100 | **0.00%** | [0.00%, 3.70%] | 100 / 100 | **100.00%** | 0.00% | 0.02 ms | 0.000 ms |
| **4. G1 + G2** | 48 / 100 | **48.00%** | [38.46%, 57.68%] | 100 / 100 | **100.00%** | 0.00% | 38.70 ms | 0.193 ms |
| **5. Full TrustRAG** | 48 / 100 | **48.00%** | [38.46%, 57.68%] | 100 / 100 | **100.00%** | 0.00% | 38.88 ms | 0.194 ms |

---

## 3. Layer Insights & Trade-Off Analysis

1. **Independent Role of G1:**
   In query-focused adversarial suites, G1 is the primary defensive barrier. Without G1 (Configs 1 and 3), the Attack Detection Rate drops to **0.00%**, leaving the language model completely vulnerable to direct prompt injections, jailbreaks, and command exfiltrations.
2. **Independent Role of G2:**
   G2 MSD specifically targets retrieved candidate documents rather than raw user queries. As demonstrated in Task 5's retrieval poisoning evaluation, G2 provides 100% detection of poisoned documents injected into context, but does not intercept user queries.
3. **Latency Footprint:**
   Activating the G1 deterministic filter adds less than **0.20 ms** of latency per request on CPU, demonstrating that defense-in-depth adds essentially negligible computational overhead compared to downstream neural retrieval or generation.
