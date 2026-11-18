# TrustRAG Research Completion — Track 1, Step 2: G3 Output Verification on HaluEval

## 1. Summary of Results

Evaluation of the G3 Output Verifier (`FactVerificationPipeline`) on 3,000 balanced records from HaluEval (1,500 factual, 1,500 hallucinated).

- **Evaluated Records:** 3000
- **Ground Truth Distribution:** 1500 FACTUAL, 1500 HALLUCINATED
- **Execution Time:** 9.93s
- **Throughput:** 302.0 records/second

---

## 2. Verdict Distribution

| Verdict | Count | Percentage |
| :--- | :--- | :--- |
| `INSUFFICIENT_EVIDENCE` | 1571 | 52.37% |
| `SUPPORTED` | 1153 | 38.43% |
| `CONTRADICTED` | 235 | 7.83% |
| `UNCERTAIN` | 22 | 0.73% |
| `PARTIALLY_SUPPORTED` | 19 | 0.63% |
| **Total** | **3,000** | **100.00%** |

---

## 3. Classification & Safety Metrics

### 3.1 Primary Safety Metrics
- **False Supported Rate (FSR):** **0.1593** (239/1500)
  - *Significant reduction compared to the 100% false supported rate of unverified systems.*
- **False Contradiction Rate (FCR):** **0.0087** (13/1500)
  - *Only 13 out of 1,500 factual claims were falsely contradicted.*
- **Abstention Rate:** **0.5310** (1593 records)
- **Decisive Coverage:** **0.4627**

### 3.2 Standard Binary Classification Metrics (Positive = Hallucinated)
- **Accuracy:** 72.50%
- **Balanced Accuracy:** 72.50%
- **Precision:** 68.27%
- **Recall:** 84.07%
- **F1 Score:** 75.35%
- **False Positive Rate (FPR):** 39.07%

### 3.3 Confusion Matrix
- **True Positives (TP):** 1261 (Hallucinated detected)
- **False Positives (FP):** 586 (Factual incorrectly flagged)
- **True Negatives (TN):** 914 (Factual correctly accepted)
- **False Negatives (FN):** 239 (Hallucinated missed)

---

## 4. In-Depth Analysis

On HaluEval, TrustRAG achieved **72.50% overall accuracy** and a **75.35% F1 score**. Because HaluEval's factual samples are closely aligned with reference documents, the False Contradiction Rate is very low (0.87%). However, because many HaluEval answers are very concise (e.g. single-word or short entity answers), the verifier abstained with `INSUFFICIENT_EVIDENCE` on 1,571 records. In safety classification, treating insufficient evidence as unverified flags these safely, but highlights the necessity of semantic entailment over pure length-sensitive lexical overlap.
