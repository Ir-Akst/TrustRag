# TrustRAG — Track 2, Step 3.5: Executive Binary Model Generalization & Robustness Report

- **Date:** 2026-11-14T04:50:20Z
- **Role:** Senior ML Evaluation Engineer & Independent Experimental Auditor
- **Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)
- **Protected Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, Untouched)
- **Checkpoint Evaluated:** `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000`
- **Execution Mode:** Strictly Evaluation-Only (Frozen FP32 weights, zero optimizer state, offline inference)
- **Evaluation Partition Size:** Exactly 1,000 records (500 HaluEval, 500 RAGTruth; 50% FACTUAL, 50% HALLUCINATED)
- **Final Verdict:** **`CONDITIONALLY_SUPPORTED`**

---

## Executive Summary

The independent binary evaluation protocol was conducted on the accepted DeBERTa-v3-small checkpoint (`deberta-v3-small-binary-pilot1000`) across 1,000 unobserved, untouched evaluation instances. The model demonstrated strong discrimination capacity on the combined evaluation partition (**76.60% accuracy, 0.7583 Macro F1, 0.9178 ROC-AUC, 91.30% hallucination precision**).

Crucially, fine-grained cross-benchmark decomposition reveals an asymmetry between question-answering verification and long-form text generation verification:
1. **HaluEval Benchmark (QA):** The model achieves **98.80% accuracy** (0.9880 Macro F1, 99.59% hallucination precision, 0.9996 ROC-AUC), indicating near-perfect generalization to contrastive QA tasks.
2. **RAGTruth Benchmark (Long-form Generation):** The model achieves **54.40% accuracy** (0.4812 Macro F1, 0.7197 ROC-AUC), exhibiting a high false-negative rate (80.40%) on subtle hallucinations embedded within multi-sentence text.

### Key Comparative Metrics

| Metric | Combined (N=1,000) | HaluEval (N=500) | RAGTruth (N=500) |
| :--- | :---: | :---: | :---: |
| **Accuracy** | **76.60%** | **98.80%** | **54.40%** |
| **95% Wilson CI** | [73.9%, 79.1%] | [97.4%, 99.4%] | [50.0%, 58.7%] |
| **95% Bootstrap CI** | [74.1%, 79.2%] | [97.8%, 99.6%] | [50.0%, 58.6%] |
| **Balanced Accuracy** | **76.60%** | **98.80%** | **54.40%** |
| **Macro F1** | **0.7583** | **0.9880** | **0.4812** |
| **Hallucination Precision** | **91.30%** | **99.59%** | **64.47%** |
| **Hallucination Recall** | **58.80%** | **98.00%** | **19.60%** |
| **False Positive Rate (FPR)** | **5.60%** | **0.40%** | **10.80%** |
| **False Negative Rate (FNR)** | **41.20%** | **2.00%** | **80.40%** |
| **ROC-AUC** | **0.9178** | **0.9910** | **0.7197** |
| **PR-AUC** | **0.9219** | **0.9938** | **0.7020** |
| **Brier Score** | **0.1772** | **0.0574** | **0.2970** |
| **ECE (10 bins)** | **0.1540** | **0.2008** | **0.2541** |

---

## Verdict Rationale & Limitations

1. **Why `CONDITIONALLY_SUPPORTED`?**
   - The model satisfies the global generalization threshold on the combined independent sample (76.60% Accuracy, 76.60% Balanced Accuracy, 0.7583 Macro F1) and exhibits high reliability against false alarms (FPR = 5.60%, Hallucination Precision = 91.30%).
   - However, the performance is bifurcated across datasets: generalization is strong on HaluEval (98.80%), but limited on RAGTruth (54.40%).
2. **Root Causes of RAGTruth Degradation:**
   - **Sequence Length Truncation:** The pilot was configured with a sequence length of 128 tokens for CPU throughput. RAGTruth documents frequently exceed 400-800 tokens; truncating to 128 tokens removes the grounding evidence required to verify claims.
   - **Contradicted vs Unsupported Asymmetry:** RAGTruth hallucinations consist of both direct contradictions (Evident Conflict) and baseless additions (Unsupported Info). The model detects contradictions at 25.81% recall, but drops to 9.47% recall on baseless additions.
3. **Implications for Track 2 Next Steps:**
   - Binary classification at sequence length 128 is effective for concise claim/QA pairs.
   - For full document-grounded verification, higher sequence length (e.g. 512) or Track 2 Step 4 (token/span-level detection and 3-way NLI) is necessary to resolve subtle baseless information.
