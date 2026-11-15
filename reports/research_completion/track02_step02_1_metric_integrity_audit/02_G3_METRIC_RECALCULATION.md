# TrustRAG — Track 1, Step 2.1: Independent Benchmark Metric Integrity Audit
## 02. G3 Metric Recalculation

### 1. Mathematical Definitions

To eliminate any ambiguity between standard classification errors and defense safety measures, every metric is formally defined below:

- **Target Binary Setup:**
  - Positive Class ($Y=1$): `HALLUCINATED`
  - Negative Class ($Y=0$): `FACTUAL`
- **Default Pipeline Decision Rule:**
  $$\hat{Y} = \begin{cases} 0 & \text{if } \text{Verdict} = \text{SUPPORTED} \\ 1 & \text{if } \text{Verdict} \in \{\text{CONTRADICTED}, \text{INSUFFICIENT\_EVIDENCE}, \text{UNCERTAIN}, \text{PARTIALLY\_SUPPORTED}\} \end{cases}$$
- **Confusion Matrix:**
  - $TP$: Ground Truth = `HALLUCINATED`, Verdict $\neq$ `SUPPORTED`
  - $TN$: Ground Truth = `FACTUAL`, Verdict = `SUPPORTED`
  - $FP$: Ground Truth = `FACTUAL`, Verdict $\neq$ `SUPPORTED` (Classification False Alarm)
  - $FN$: Ground Truth = `HALLUCINATED`, Verdict = `SUPPORTED` (Safety Failure / False Supported)
- **Safety Metrics:**
  - **False Supported Rate (FSR):** $\frac{FN}{\text{Total Hallucinated}}$
  - **False Contradiction Rate (FCR):** $\frac{\text{Count}(Y=0 \land \text{Verdict}=\text{CONTRADICTED})}{\text{Total Factual}}$
  - **Strict Abstention Rate:** $\frac{\text{Count}(\text{Verdict} \in \{\text{INSUFFICIENT\_EVIDENCE}, \text{UNCERTAIN}\})}{N}$
  - **Inclusive Abstention Rate:** $\frac{\text{Count}(\text{Verdict} \in \{\text{INSUFFICIENT\_EVIDENCE}, \text{UNCERTAIN}, \text{PARTIALLY\_SUPPORTED}\})}{N}$
  - **Strict Decisive Coverage:** $\frac{\text{Count}(\text{Verdict} \in \{\text{SUPPORTED}, \text{CONTRADICTED}\})}{N}$
  - **Inclusive Decisive Coverage:** $\frac{\text{Count}(\text{Verdict} \in \{\text{SUPPORTED}, \text{CONTRADICTED}, \text{PARTIALLY\_SUPPORTED}\})}{N}$

---

### 2. Discrepancy Resolution & Audit Recalculation

#### 2.1 The RAGTruth 436-Record Discrepancy Resolved
- **Problem Statement:** In Step 2 reports: Total = 2,700, Decisive reported = 1,894, Abstention reported = 370. $2,700 - (1,894 + 370) = 436$ records unaccounted for.
- **Audit Identification:** The 436 missing records have verdict **`PARTIALLY_SUPPORTED`** (363 on `FACTUAL`, 73 on `HALLUCINATED`).
- **Cause:** The script author calculated `decisive_coverage` as `SUPPORTED + CONTRADICTED` (9 + 1,885 = 1,894) and `abstention_count` as `INSUFFICIENT_EVIDENCE + UNCERTAIN` (280 + 90 = 370), entirely omitting `PARTIALLY_SUPPORTED` from both sums.
- **Reconciliation:**
  - **Strict Partitioning (Partial counted as Non-Decisive / Abstention):**
    - Decisive Coverage: $1,894 / 2,700 = \mathbf{70.15\%}$
    - Abstention Rate: $(370 + 436) / 2,700 = 806 / 2,700 = \mathbf{29.85\%}$
    - Sum: $70.15\% + 29.85\% = \mathbf{100.00\%}$
  - **Inclusive Partitioning (Partial counted as Decisive Certification):**
    - Decisive Coverage: $(1,894 + 436) / 2,700 = 2,330 / 2,700 = \mathbf{86.30\%}$
    - Abstention Rate: $370 / 2,700 = \mathbf{13.70\%}$
    - Sum: $86.30\% + 13.70\% = \mathbf{100.00\%}$

#### 2.2 The HaluEval 19-Record Discrepancy Resolved
- **Problem Statement:** Total = 3,000, Decisive reported = 1,388, Abstention reported = 1,593. $3,000 - (1,388 + 1,593) = 19$ records unaccounted for.
- **Audit Identification:** The 19 missing records have verdict **`PARTIALLY_SUPPORTED`** (all 19 on `HALLUCINATED`).
- **Reconciliation:**
  - **Strict Partitioning:**
    - Decisive Coverage: $1,388 / 3,000 = \mathbf{46.27\%}$
    - Abstention Rate: $(1,593 + 19) / 3,000 = 1,612 / 3,000 = \mathbf{53.73\%}$
    - Sum: $46.27\% + 53.73\% = \mathbf{100.00\%}$
  - **Inclusive Partitioning:**
    - Decisive Coverage: $(1,388 + 19) / 3,000 = 1,407 / 3,000 = \mathbf{46.90\%}$
    - Abstention Rate: $1,593 / 3,000 = \mathbf{53.10\%}$
    - Sum: $46.90\% + 53.10\% = \mathbf{100.00\%}$

---

### 3. Recomputed Metric Tables

| Metric | RAGTruth (Verified Baseline) | RAGTruth (Lenient Partial) | HaluEval (Verified Baseline) | HaluEval (Lenient Partial) |
| :--- | :--- | :--- | :--- | :--- |
| **Total Evaluated** | 2,700 | 2,700 | 3,000 | 3,000 |
| **True Positive (TP)** | 943 | 870 | 1,261 | 1,242 |
| **True Negative (TN)** | 9 | 372 | 914 | 914 |
| **False Positive (FP)** | 1,748 | 1,385 | 586 | 586 |
| **False Negative (FN)** | **0** | 73 | 239 | 258 |
| **Accuracy** | 35.26% | 46.00% | 72.50% | 71.87% |
| **Balanced Accuracy** | 50.26% | 56.72% | 72.50% | 71.87% |
| **Precision** | 35.04% | 38.58% | 68.27% | 67.94% |
| **Recall (Hallucination)** | **100.00%** | 92.26% | 84.07% | 82.80% |
| **F1 Score** | 51.90% | 54.41% | 75.35% | 74.64% |
| **False Supported Rate (FSR)** | **0.0000** (0/943) | 0.0774 (73/943) | **0.1593** (239/1500) | 0.1720 (258/1500) |
| **False Contradiction Rate (FCR)** | **0.6261** (1100/1757) | 0.6261 (1100/1757) | **0.0087** (13/1500) | 0.0087 (13/1500) |
| **Classification FPR** | **99.49%** (1748/1757) | 78.83% (1385/1757) | **39.07%** (586/1500) | 39.07% (586/1500) |
| **Strict Abstention Rate** | 13.70% (370/2700) | 13.70% | 53.10% (1593/3000) | 53.10% |
| **Inclusive Abstention Rate** | **29.85%** (806/2700) | 29.85% | **53.73%** (1612/3000) | 53.73% |
| **Strict Decisive Coverage** | **70.15%** (1894/2700) | 70.15% | **46.27%** (1388/3000) | 46.27% |
| **Inclusive Decisive Coverage** | **86.30%** (2330/2700) | 86.30% | **46.90%** (1407/3000) | 46.90% |
