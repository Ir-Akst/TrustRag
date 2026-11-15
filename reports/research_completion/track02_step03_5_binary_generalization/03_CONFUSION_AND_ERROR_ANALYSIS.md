# TrustRAG — Track 2, Step 3.5: Confusion Matrix & Fine-Grained Error Analysis

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
