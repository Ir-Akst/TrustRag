# TrustRAG — Track 1, Step 2.1: Independent Benchmark Metric Integrity Audit
## 05. Baseline Fairness Audit

### 1. Comparative Fairness Checklist

| Audit Criterion | Verification Status | Audit Evidence & Analysis |
| :--- | :--- | :--- |
| **Identical Records Across Modes** | **PASS** | `no_verification`, `default_g3`, and `strict_g3` evaluated the exact identical 2,700 records in RAGTruth and 3,000 records in HaluEval. |
| **Ground Truth Consistency** | **PASS** | All modes evaluated against identical ground truth labels without modification or relabeling. |
| **Zero Test-Set Tuning** | **PASS** | No hyperparameters, weights, or thresholds were fitted or tuned on test set records. |
| **Zero Ground-Truth Leakage** | **PASS** | Neither verifier nor retriever receives ground-truth labels during inference. |
| **No-Verification Baseline Definition** | **PASS** | Correctly simulates unverified RAG pass-through (always predicts `SUPPORTED`). |
| **Configuration Distinction** | **DEFECT (DEF-02)** | `strict_g3` used identical effective configuration to `default_g3` due to discarded keyword arguments in Pydantic. |

---

### 2. Abstention Handling & Defense Posture

In safety-critical defense pipelines:
- The system treats `SUPPORTED` as the sole certification of factual safety.
- Non-decisive outcomes (`INSUFFICIENT_EVIDENCE`, `UNCERTAIN`, `PARTIALLY_SUPPORTED`) are flagged as unverified (safe fallback).
- While this safety posture is methodologically fair, reporting must distinguish **classification false positives** (1,748 on RAGTruth) from **explicit contradictions** (1,100 on RAGTruth).
