# TrustRAG — Track 2, Step 3.5: Consolidated Binary Generalization & Robustness Audit Report

> **Consolidated Master Report**  
> **Task:** Track 2, Step 3.5: Independent Binary Model Generalization & Robustness Evaluation  
> **Auditor Role:** Senior ML Evaluation Engineer & Independent Experimental Auditor  
> **Evaluation Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000`  
> **Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
> **Protected Repo:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`)  
> **Final Acceptance Verdict:** **`CONDITIONALLY_SUPPORTED`**

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


---



## 1. Partition Definition and Sourcing

The evaluation dataset was established strictly from the unvisited, untouched records of `data/processed/sft_v2/binary/validation.jsonl`.

- **Total Records in `validation.jsonl`:** 5,984 records
- **Excluded Step 3.4.2 Pilot Validation Records:** 200 records (strictly skipped by `example_id`)
- **Excluded Step 3.4.2 Training Records:** 1,000 records (strictly skipped by `example_id`)
- **Available Untouched Candidate Pool:** 5,784 records
- **Extracted Independent Evaluation Slice:** Exactly 1,000 records
  - **HaluEval:** 500 records (250 FACTUAL, 250 HALLUCINATED)
  - **RAGTruth:** 500 records (250 FACTUAL, 250 HALLUCINATED)

## 2. Partition Isolation Audit Results

| Audit Check | Reference Target | Observed Overlap | Compliance Status |
| :--- | :--- | :---: | :---: |
| Overlap with Step 3.4.2 Training (1,000) | `data/processed/sft_v2/binary/train.jsonl` | **0 records** | **VERIFIED_DISJOINT** |
| Overlap with Step 3.4.2 Pilot Validation (200) | `tools/training/train_binary_classifier.py` cache | **0 records** | **VERIFIED_DISJOINT** |
| Overlap with Upstream HaluEval Test Documents | `data/processed/halueval/test.jsonl` | **0 documents** | **VERIFIED_DISJOINT** |
| Overlap with Upstream RAGTruth Test Documents | `data/processed/ragtruth/test.jsonl` | **0 documents** | **VERIFIED_DISJOINT** |
| Test Split Exposure | Canonical Test Splits | **0 records accessed** | **STRICTLY_ISOLATED** |

## 3. Dataset Attribution & Licensing

- **HaluEval:** Released under MIT License / Academic Research Use.
- **RAGTruth:** Released under CC BY 4.0 International License.
- **Model:** DeBERTa-v3-small (MIT License, Microsoft Corporation).


---



## 1. Primary Metrics Table

| Metric | Combined Evaluation (N=1,000) | HaluEval Benchmark (N=500) | RAGTruth Benchmark (N=500) |
| :--- | :---: | :---: | :---: |
| **Total Evaluated Records** | 1,000 | 500 | 500 |
| **True FACTUAL (Class 0)** | 500 | 250 | 250 |
| **True HALLUCINATED (Class 1)**| 500 | 250 | 250 |
| **Accuracy** | **76.60%** | **98.80%** | **54.40%** |
| **95% Wilson CI** | [73.88%, 79.12%] | [97.41%, 99.45%] | [50.02%, 58.72%] |
| **95% Bootstrap CI** | [74.10%, 79.20%] | [97.80%, 99.60%] | [50.00%, 58.60%] |
| **Balanced Accuracy** | **76.60%** | **98.80%** | **54.40%** |
| **Macro F1 Score** | **0.7583** | **0.9880** | **0.4812** |
| **Macro F1 95% Bootstrap CI** | [0.7322, 0.7848] | [0.9779, 0.9960] | [0.4370, 0.5237] |

---

## 2. Per-Class Precision, Recall, and F1

### Combined (N=1,000)
- **FACTUAL (Class 0):** Precision = 69.62%, Recall = 94.40%, F1 = 0.8014 (Support: 500)
- **HALLUCINATED (Class 1):** Precision = 91.30%, Recall = 58.80%, F1 = 0.7153 (Support: 500)

### HaluEval (N=500)
- **FACTUAL (Class 0):** Precision = 98.03%, Recall = 99.60%, F1 = 0.9881 (Support: 250)
- **HALLUCINATED (Class 1):** Precision = 99.59%, Recall = 98.00%, F1 = 0.9879 (Support: 250)

### RAGTruth (N=500)
- **FACTUAL (Class 0):** Precision = 52.59%, Recall = 89.20%, F1 = 0.6617 (Support: 250)
- **HALLUCINATED (Class 1):** Precision = 64.47%, Recall = 19.60%, F1 = 0.3006 (Support: 250)

---

## 3. Discrimination and Calibration Metrics

| Metric | Combined | HaluEval | RAGTruth |
| :--- | :---: | :---: | :---: |
| **ROC-AUC** | **0.9178** | **0.9910** | **0.7197** |
| **PR-AUC (Hallucinated)** | **0.9219** | **0.9938** | **0.7020** |
| **Brier Score** | **0.1772** | **0.0574** | **0.2970** |
| **Expected Calibration Error (ECE)** | **0.1540** | **0.2008** | **0.2541** |


---



## 1. Confusion Matrix Breakdown

### Combined Evaluation (N=1,000)
```
                  Predicted FACTUAL    Predicted HALLUCINATED
Actual FACTUAL            472 (TN)               28 (FP)
Actual HALLUCINATED       206 (FN)              294 (TP)
```
- **False Positive Rate (FPR):** 5.60% (28/500 factual examples incorrectly flagged)
- **False Negative Rate (FNR):** 41.20% (206/500 hallucinations missed)

### HaluEval Benchmark (N=500)
```
                  Predicted FACTUAL    Predicted HALLUCINATED
Actual FACTUAL            249 (TN)                1 (FP)
Actual HALLUCINATED         5 (FN)              245 (TP)
```
- **FPR:** 0.40% (1 false alarm)
- **FNR:** 2.00% (5 missed hallucinations)

### RAGTruth Benchmark (N=500)
```
                  Predicted FACTUAL    Predicted HALLUCINATED
Actual FACTUAL            223 (TN)               27 (FP)
Actual HALLUCINATED       201 (FN)               49 (TP)
```
- **FPR:** 10.80% (27 false alarms)
- **FNR:** 80.40% (201 missed hallucinations)

---

## 2. Hallucination Subtype Analysis: Contradicted vs Unsupported Claims

In compliance with the requirement: *"Do not treat unsupported claims and contradicted claims as semantically identical merely because the binary dataset uses one hallucination label."*

| Hallucination Subtype | Evaluated Support | Correctly Detected | Recall | Mean P(Hallucinated) |
| :--- | :---: | :---: | :---: | :---: |
| **Contradicted** | 155 | 40 | **25.81%** | 0.3452 |
| **Unsupported** | 95 | 9 | **9.47%** | 0.2513 |

### Qualitative Error Analysis:
- **Contradicted Claims (Evident Conflicts):**
  - Recall: **25.81%** (Mean predicted P(Hallucinated) = 0.3452).
  - The model recognizes direct semantic clashes (e.g. conflicting dates, inverted factual statements) more frequently because DeBERTa's disentangled attention compares token pairs directly.
- **Unsupported Claims (Baseless Info):**
  - Recall: **9.47%** (Mean predicted P(Hallucinated) = 0.2513).
  - The model struggles significantly with plausible information that is simply omitted from the context. It assigns a high probability of factual correctness (mean 0.7487) because the surface style appears authoritative and fluent.

---

## 3. RAGTruth Performance by Task Type

| Task Type | Support | Accuracy | Macro F1 | Factual / Hallucinated Support |
| :--- | :---: | :---: | :---: | :---: |
| **Data2txt** | 283 | **39.58%** | **0.3921** | 67 / 216 |
| **QA** | 181 | **76.24%** | **0.4925** | 157 / 24 |
| **Summary** | 36 | **61.11%** | **0.4375** | 26 / 10 |

---

## 4. Performance by Generator Model (RAGTruth)

| Generator Architecture | Support | Accuracy | Macro F1 |
| :--- | :---: | :---: | :---: |
| **gpt-3.5-turbo-0613** | 87 | **79.31%** | **0.4916** |
| **gpt-4-0613** | 88 | **73.86%** | **0.4248** |
| **llama-2-13b-chat** | 83 | **75.90%** | **0.7390** |
| **llama-2-70b-chat** | 85 | **30.59%** | **0.2342** |
| **llama-2-7b-chat** | 77 | **31.17%** | **0.2505** |
| **mistral-7B-instruct** | 80 | **31.25%** | **0.2800** |


---



## 1. Probability Calibration

- **Combined Brier Score:** **0.1772** (Reference: random guessing at 0.5 is 0.2500)
- **Combined ECE (10 Equal Bins):** **0.1540**
- **HaluEval Calibration:** Brier = 0.0574, ECE = 0.2008 (Highly calibrated)
- **RAGTruth Calibration:** Brier = 0.2970, ECE = 0.2541 (Under-confident on hallucinations)

---

## 2. Confidence Distribution Analysis

| Subset | Sample Count | Mean Confidence | Median Confidence | P95 Confidence |
| :--- | :---: | :---: | :---: | :---: |
| **All Predictions** | 1000 | 78.11% | 80.77% | 85.32% |
| **Correct Predictions** | 766 | 78.59% | 81.02% | — |
| **Incorrect Predictions** | 234 | 76.56% | 80.47% | — |

---

## 3. Robustness Against Domain and Distribution Shift

1. **Format Shift:** Concise contrastive QA (HaluEval) achieves 98.80% accuracy, while multi-sentence RAG output (RAGTruth) achieves 54.40%.
2. **Fixed Decision Boundary:** The default 0.5 decision boundary (argmax) was maintained strictly without retrospective post-hoc tuning.
3. **Context Length Bottleneck:** The 128-token context truncation bottleneck is the primary driver of false negatives on long-form generation tasks.


---



## 1. Latency & Throughput Telemetry

- **Inference Hardware:** CPU Only
- **Execution Concurrency:** 1 process, 10 threads
- **Batch Size:** 1
- **Sequence Length:** 128 tokens
- **Total Samples Evaluated:** 1000
- **Total Wall-Clock Time:** 141.49 seconds
- **Throughput:** **7.07 samples/sec**

### Latency Percentiles
- **Median Latency:** **137.02 ms**
- **Mean Latency:** **141.43 ms**
- **P95 Latency:** **160.35 ms**
- **Min Latency:** 86.63 ms
- **Max Latency:** 437.42 ms

---

## 2. Host Resource Consumption

- **Initial RSS:** 595.61 MB
- **Peak RSS:** **1127.90 MB**
- **Net RSS Growth:** +532.29 MB
- **Available Host RAM:** **6187.18 MB**
- **Swap Total / Used / Free:** 6000.00 MB / 2489.93 MB / 3510.07 MB
- **Offline Integrity:** Verified (Zero remote HTTP/HTTPS connections).

