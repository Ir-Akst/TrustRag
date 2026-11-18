# TrustRAG Research Completion — Track 1, Step 2: G3 Output Verification on RAGTruth

## 1. Summary of Results

Evaluation of the G3 Output Verifier (`FactVerificationPipeline`) on the 2,700 test records of the canonical RAGTruth benchmark.

- **Evaluated Records:** 2700
- **Ground Truth Distribution:** 1757 FACTUAL, 943 HALLUCINATED
- **Execution Time:** 70.78s
- **Throughput:** 38.1 records/second

---

## 2. Verdict Distribution

| Verdict | Count | Percentage |
| :--- | :--- | :--- |
| `CONTRADICTED` | 1885 | 69.81% |
| `PARTIALLY_SUPPORTED` | 436 | 16.15% |
| `INSUFFICIENT_EVIDENCE` | 280 | 10.37% |
| `UNCERTAIN` | 90 | 3.33% |
| `SUPPORTED` | 9 | 0.33% |
| **Total** | **2,700** | **100.00%** |

---

## 3. Classification & Safety Metrics

### 3.1 Primary Safety Metrics
- **False Supported Rate (FSR):** **0.0000** (0/943)
  - *Zero hallucinated claims were falsely certified as supported.*
- **False Contradiction Rate (FCR):** **0.6261** (1100/1757)
  - *1,100 of 1,757 factual claims were incorrectly flagged as contradicted due to lexical divergence.*
- **Abstention Rate:** **0.1370** (370 records)
- **Decisive Coverage:** **0.7015**

### 3.2 Standard Binary Classification Metrics (Positive = Hallucinated)
- **Accuracy:** 35.26%
- **Balanced Accuracy:** 50.26%
- **Precision:** 35.04%
- **Recall:** 100.00%
- **F1 Score:** 51.90%
- **False Positive Rate (FPR):** 99.49%

### 3.3 Confusion Matrix
- **True Positives (TP):** 943 (Hallucinated correctly identified)
- **False Positives (FP):** 1748 (Factual incorrectly flagged)
- **True Negatives (TN):** 9 (Factual correctly accepted)
- **False Negatives (FN):** 0 (Hallucinated missed — ZERO)

---

## 4. In-Depth Analysis

The heuristic G3 verifier operates under an asymmetric safety bias: it strictly requires lexical token support. When text is hallucinated, lexical support in the context is absent, leading to 100% recall of hallucinations (943 / 943 detected). However, when factual claims paraphrase the source document with synonyms or alternative phrasing, the lexical verifier fails to match tokens, generating false contradictions. This establishes the quantitative benchmark that Track 2 neural NLI models must surpass.
