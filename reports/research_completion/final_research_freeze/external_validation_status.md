# TrustRAG — External Benchmark Validation Status & Generalization Reality Audit

**Auditor:** Senior ML Evaluation Auditor & Research Specialist  
**Date:** 2026-11-19T01:48:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Dedicated Branch:** `phase-17-20-final-release`  
**Target Architecture:** TrustRAG G3 Hybrid Verifier (Frozen DeBERTa-v3-small + Heuristics)  
**Deliverables Directory:** `reports/research_completion/final_research_freeze/`  

---

## 1. Executive Summary & Mandatory Distinction

A foundational duty of this independent audit is to enforce strict scientific demarcations:
> **Synthetic benchmark success does not constitute real-world external validation.**

While TrustRAG achieved an audited **$100.0\%$ Attack Defense Rate** on its internal synthetic benchmark (where attacks followed structured numerical, unit, and antonym templates), live evaluation against independent external benchmarks reveals clear generalization boundaries.

```
+---------------------------------------------------------------------------------------------------+
|                                 The Generalization Reality Gap                                    |
+---------------------------------------------------------------------------------------------------+
|  Internal Synthetic Benchmark:   100.0% ADR  |   0.0% Clean FPR  |  F1 = 1.0000 (Structured)     |
|  RAGTruth (ACL 2024 LLM Text):    66.0% ADR  |  46.0% Clean FPR  |  F1 = 0.6226 (Narrative QA)   |
|  HaluEval (EMNLP 2023 QA):        89.0% ADR  |  98.0% Clean FPR  |  F1 = 0.6202 (Entity QA)      |
|  RSB (arXiv:2505.18543):         BLOCKED     |  No local cache   |  Network sandbox isolation    |
|  PoisonedRAG (USENIX 2025):      BLOCKED     |  No local cache   |  Network sandbox isolation    |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Status of Academic Poisoning Benchmarks (RSB & PoisonedRAG)

In strict accordance with research integrity rules:
> *"Never claim external benchmark validation if the benchmark was not actually downloaded and evaluated. If a benchmark cannot be accessed, classify it as BLOCKED and continue with other permitted tasks. Do not substitute synthetic data and call it external validation."*

### 2.1 RAG Security Benchmark (RSB, arXiv:2505.18543)
- **Status:** **`BLOCKED`**
- **Forensic Verification:** Exhaustive search across `/home/aditya/rags/` and local disk revealed zero pre-cached RSB splits.
- **Acquisition Barrier:** No canonical public unauthenticated download URL exists; academic repository requires authenticated external git clone.
- **Safety Restriction:** Remote network downloads and scraping are prohibited by execution sandbox constraints. No synthetic data was substituted.

### 2.2 PoisonedRAG (USENIX Security 2025)
- **Status:** **`BLOCKED`**
- **Forensic Verification:** Zero PoisonedRAG evaluation files or embeddings exist on local storage.
- **Acquisition Barrier:** Requires external repository cloning from GitHub / Google Drive.
- **Safety Restriction:** Remote network downloads are strictly disabled. Marked formally as `BLOCKED`.

---

## 3. Empirical Evaluation on Accessible Public Benchmarks

Independent validation was successfully and legitimately executed on the two pre-staged public research benchmarks: **RAGTruth** (ACL 2024) and **HaluEval** (EMNLP 2023).

### 3.1 Quantitative Results Summary

| External Benchmark | Ground Truth Task | $N$ | Defense Rate (ADR) | Leakage Rate (ASR) | Clean False Positive Rate (FPR) | Precision | Recall | $F_1$ Score | P50 Latency |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **RAGTruth (ACL 2024)** | Real LLM Summaries / QA | 200 | **66.00%** | 34.00% | **46.00%** | 0.5893 | 0.6600 | **0.6226** | 184.22 ms |
| **HaluEval (EMNLP 2023)**| Entity Fragment QA | 200 | **89.00%** | 11.00% | **98.00%** | 0.4759 | 0.8900 | **0.6202** | 68.45 ms |

---

## 4. In-Depth Forensic Audit of High Clean False Positive Rates

### 4.1 HaluEval Clean FPR of 98.0%: The Propositional Entity Dilemma
- **Root Cause Mechanism:**
  - Natural Language Inference (NLI) cross-attention models are trained to evaluate sentence-level propositional entailment: `premise` $\implies$ `hypothesis`.
  - HaluEval answers frequently consist of detached noun phrases or isolated entity names (e.g., Question: *"Who starred in Westworld?"* $\implies$ Answer: `"Luke Hemsworth"`).
  - When evaluating premise: *"Luke Hemsworth is an Australian actor who starred in Westworld..."* paired with hypothesis: `"Luke Hemsworth"`, the NLI model cannot establish a truth-conditional propositional entailment.
  - DeBERTa predicts **`NEUTRAL`** ($p_{\text{neu}} \ge 0.85$).
  - Because TrustRAG's default conservative verification policy treats ungrounded neutral claims as insufficient evidence (`unsupported_flag = True`), clean single-entity answers are systematically rejected.
- **Audit Verdict:** The $98\%$ FPR on HaluEval is a structural consequence of applying sentence-level NLI to detached entity-level answers. It is not an implementation bug, but a fundamental domain mismatch.

### 4.2 RAGTruth Clean FPR of 46.0%: Narrative Subordination & Over-Quarantining
- **Root Cause Mechanism:**
  - RAGTruth evaluates open-domain summaries produced by GPT-3.5, GPT-4, and Llama-2-70B across news articles and business profiles.
  - Human summaries naturally incorporate subordinate clauses, introductory transitions, or implied context (e.g., *"Speaking to reporters on Tuesday, the senator announced..."* where the source text mentions the announcement but omits the phrase *"speaking to reporters on Tuesday"*).
  - The strict G3 verifier analyzes each clause independently. When minor background details are omitted from the retrieved snippet, G3 assigns an insufficient support flag.
  - Consequently, **$46.0\%$ of completely factual, safe human summaries are falsely quarantined**.
- **Audit Verdict:** While strict verification protects against subtle factual poisoning, it imposes a severe utility penalty on rich, multi-clause narrative text.

---

## 5. Synthesis & Audit Conclusion

1. **Synthetic vs. Real-World Dichotomy:** TrustRAG's $100\%$ defense score is an artifact of benchmark-targeted engineering on structured factual mutations. Against open-domain natural language hallucinations generated by commercial LLMs, performance stabilizes at an $F_1$ score of $\sim 0.62$.
2. **Operational Constraint:** TrustRAG is highly suited for structured enterprise knowledge bases (medical formulations, financial parameters, technical specifications), but cannot be deployed as an autonomous filter for open-domain narrative generation without human-in-the-loop oversight.

