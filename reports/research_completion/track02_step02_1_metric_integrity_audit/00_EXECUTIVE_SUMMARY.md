# TrustRAG — Track 1, Step 2.1: Independent Benchmark Metric Integrity Audit
## 00. Executive Summary

### 1. Audit Target & Authority
- **Repository Under Audit:** `/home/aditya/rags/TrustRag-phase11`
- **Branch:** `phase-11`
- **Commit HEAD:** `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`
- **Protected Phase 10 Baseline:** `/home/aditya/rags/TrustRag` (HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, Untouched)
- **Audit Mandate:** Perform an independent, read-only metric integrity audit of the Track 1 Step 2 benchmark evaluation results before accepting them as research baselines.
- **Audit Date:** 2026-11-13T22:45:00+05:30
- **Final Audit Verdict:** **`CONDITIONALLY_VERIFIED`**

---

### 2. High-Level Audit Findings

1. **Prediction Integrity (100% Census):**
   - RAGTruth: 2,700 / 2,700 records verified. Zero missing, zero duplicate, zero extra IDs.
   - HaluEval: 3,000 / 3,000 records verified. Zero missing, zero duplicate, zero extra IDs.
   - HotpotQA: 7,405 / 7,405 validation queries evaluated with zero data leakage.
   - MS MARCO: 9,706 / 10,047 queries evaluated; 341 unannotated queries verified as all-zero relevance in v1.1 ground truth.

2. **Resolution of Reported Discrepancies:**
   - **RAGTruth 436 "Unexplained" Records:** Exactly identified as **`PARTIALLY_SUPPORTED`** (436 records: 363 on Factual, 73 on Hallucinated). The Step 2 evaluation script omitted `PARTIALLY_SUPPORTED` from both the decisive coverage numerator and the abstention numerator, creating an apparent 436-record gap.
   - **HaluEval 19 "Unexplained" Records:** Exactly identified as **`PARTIALLY_SUPPORTED`** (19 records, all on Hallucinated ground truth). Omitted similarly from decisive and abstention numerators.
   - When properly accounted for, 100.00% of records in both benchmarks reconcile with zero unexplained items.

3. **Root Cause of Threshold Invariance:**
   - The Step 2 script attempted to configure `strict_g3` using `VerificationConfig(evidence_threshold=0.70, claim_threshold=0.75)`.
   - In the Pydantic-based `VerificationConfig`, these two field names do not exist (the actual parameter is `min_support_coverage`, default `0.65`). Pydantic silently ignored the extra keyword arguments.
   - Consequently, `default_g3` and `strict_g3` ran with **100% identical configuration parameters**, explaining why 0 records changed verdict between the two runs.

4. **Independent Reproducibility (100% Determinism):**
   - An independent full rerun in `/tmp/track02_reproducibility_test` produced **100.0% exact match** on all verdicts, scores, labels, and confusion matrix cells across all 15,111 evaluated records and queries. Minor textual diffs occurred solely from Python set-iteration ordering in explanation strings.

---

### 3. Metric Reconciliation Summary Table

| Benchmark | Total Records | Ground Truth | Core Safety Metric (Verified) | Core Accuracy Metric (Verified) | Identified Accounting Defect | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RAGTruth** | 2,700 | 1,757 Fact<br>943 Halluc | **FSR = 0.0000**<br>(0 / 943 false supported) | **Acc = 35.26%**<br>F1 = 51.90% | 436 `PARTIALLY_SUPPORTED` records omitted from coverage/abstention. | **CONDITIONALLY VERIFIED** |
| **HaluEval** | 3,000 | 1,500 Fact<br>1,500 Halluc | **FSR = 0.1593**<br>(239 / 1,500 false supported) | **Acc = 72.50%**<br>F1 = 75.35% | 19 `PARTIALLY_SUPPORTED` records omitted from coverage/abstention. | **CONDITIONALLY VERIFIED** |
| **HotpotQA** | 7,405 | 7,405 queries<br>(10 cands/q) | Candidate Reranking | **Recall@1: 0.4154**<br>**Recall@10: 0.9876**<br>**MRR@10: 0.8965** | Full-corpus status correctly blocked; 182 multi-hop queries had zero token overlap with 2nd gold doc. | **INDEPENDENTLY VERIFIED** |
| **MS MARCO** | 10,047 | 9,706 evaluated<br>341 unannotated | Candidate Reranking | **Recall@1: 0.2311**<br>**Recall@10: 0.9768**<br>**MRR@10: 0.4626** | 341 unannotated queries correctly skipped per TREC protocol; denominator scope clarified. | **INDEPENDENTLY VERIFIED** |
| **G1 & G2** | 0 in QA sets | N/A | Dedicated 680 Unit Tests | Unit Suite Passing (100%) | N/A | **NOT_EVALUABLE** (Scientifically Honest) |
