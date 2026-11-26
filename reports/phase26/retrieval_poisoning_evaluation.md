# TrustRAG Phase 26: Retrieval Poisoning & Removal Cap Evaluation Report

**Evaluation Date:** 2026-11-24  
**Evaluator:** Principal ML Security Researcher & RAG Robustness Specialist  
**Target:** G2 Multi-Signal Detector (MSD) & Context Filtering Subsystem  

---

## 1. Scope & Objective

RAG pipelines are vulnerable to poisoned retrieved documents (e.g., indirect prompt injection or false consensus attacks). G2 MSD evaluates retrieved candidates across 6 signals (F1..F6) and prunes poisoned passages before context assembly.

However, to avoid context starvation, TrustRAG enforces a **Removal Cap ($C_r = 0.50$)**, meaning G2 can prune at most 50% of the candidate set. In Phase 26, we evaluated G2 across varying poisoning ratios ($0\%$ to $80\%$) to test the structural boundaries of this defense.

---

## 2. Empirical Poisoning Results

| Scenario | Total Candidates | Injected Poison Docs | Poison Ratio | G2 Detected Poisoned | Pruned Documents | Residual Poison in Context | Removal Cap Triggered | Detection Rate | Clean Rejection Rate |
|---|---|---|---|---|---|---|---|---|---|
| **Clean Baseline** | 5 | 0 | 0.0% | 0 | 0 | **0** | No | 100.0% | 0.0% |
| **Single Poisoned** | 5 | 1 | 20.0% | 1 | 1 | **0** | No | 100.0% | 0.0% |
| **Multi Poisoned (40%)** | 5 | 2 | 40.0% | 2 | 2 | **0** | No | 100.0% | 33.3% |
| **Sybil Majority (60%)** | 5 | 3 | 60.0% | 3 | 2 | **1** | **YES** | 100.0% | 50.0% |
| **Sybil Flooding (80%)** | 5 | 4 | 80.0% | 4 | 2 | **2** | **YES** | 100.0% | 100.0% |

---

## 3. Critical Architectural Finding: The Sybil Frontier Limitation

1. **Perfect Detection, Incomplete Removal:**
   In all scenarios, G2 MSD correctly identified 100% of the poisoned documents (`detection_rate_pct = 100.0%`) via Signal F4 (`system_override_tag`, `answer_manipulation_directive`).
2. **The Removal Cap Bottleneck:**
   When the fraction of poisoned documents exceeds $50\%$ (e.g., in the 60% and 80% Sybil scenarios), the removal cap ($C_r = 0.50 \implies \lfloor 5 \times 0.50 \rfloor = 2$) actively halts further pruning to preserve retrieval context. As a direct result:
   - In the 60% scenario, 1 poisoned passage **leaks directly into the LLM context**.
   - In the 80% scenario, 2 poisoned passages **leak directly into the LLM context**.
3. **Publication Significance:**
   This is a fundamental structural trade-off: **Availability vs. Robustness**. TrustRAG chooses to prevent denial-of-service (empty context) at the cost of allowing residual poisoned passages when an attacker achieves retrieval majority. This structural frontier is an essential research contribution that must be explicitly analyzed in the paper.
