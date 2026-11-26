# TrustRAG Phase 42 — Controlled Research Experiments Final Report

**Branch:** `phase-42-controlled-research-experiments`  
**Parent Commit (Phase 41):** `3b1f1e5fc0192f3c63eca6072a1d0b6fb2d91e79`  
**Phase 40.1 Commit:** `4818a7ce075adf961e062862a04cb21c095ea7c2`  
**Release Anchor:** `531bff32745ede1bd1b38609cc6daf653d3eff24` (`trustrag-v1.0.0-rc1`)  
**Frozen Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` (8/8 SHA-256 `OK`)  
**Production Code Modified:** None (`src/` untouched)  
**Final Verdict:** **PARTIALLY COMPLETE — LIMITED GAPS REMAIN**

---

## 1. Executive Summary

Phase 42 executed three controlled research experiments (`seed=42`, Peak RSS: 2347.28 MB) to complete TrustRAG's empirical evidence base without modifying production code:

1. **Five-Arm Controlled Component Ablation:** Demonstrated the causal necessity of every layer — removing `G1 Semantic` drops G1 ADR from **96.67% $\rightarrow$ 36.67%**; removing `GeneratorBoundaryEnforcer` raises boundary leakage from **0.00% $\rightarrow$ 100.00%**; removing `MultilingualSemanticDefense` drops multilingual ADR from **97.22% $\rightarrow$ 66.67%**; removing `G3 Verifier` raises unsupported leakage from **0.00% $\rightarrow$ 100.00%** and drops contradiction recall **100.00% $\rightarrow$ 0.00%**.
2. **External Baseline Benchmarking on Public Non-Cycled Datasets:**
   - On **RAGTruth (`test.jsonl`, $N=200$)**, `TrustRAG G3` reduced hallucination leakage to **3.00%** ($3/100$, vs 100% Vanilla RAG and 16.00% Lexical Overlap) with **82.35% precision**, at a conservative **14.00% factual recall** ($14/100$) on multi-sentence summaries.
   - On **HaluEval (`test.jsonl`, $N=200$)**, `TrustRAG G3` achieved **10.00% factual recall** and **24.00% hallucination leakage** because HaluEval QA answers are typically 1–3 words and filtered by `extract_atomic_claims` (`len < 3 words`).
   - On **Prompt-Injection Security ($N=250$ G1 + $N=140$ FW)**, `TrustRAG Full` (**96.67% G1 ADR, 0.00% boundary leakage**) outperformed `Heuristic/Regex-Only` (30.00% G1 ADR, 100.00% boundary leakage), `Spotlighting-Only` (0.00% ADR, 100.00% leakage), and `Vanilla RAG`.
3. **Quoted Malicious Content FPR Study ($N=120$):** Isolated the exact root cause of benign FPs across security education (**0.00% FPR**), quoted attacks (**40.00% FPR**), incident reports (**80.00% FPR**), and threat-intel briefs (**60.00% FPR**).
