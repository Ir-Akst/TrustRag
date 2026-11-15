# TrustRAG Research Completion — Track 1, Step 2.2: RAGTruth Corrected Results

## 1. Experimental Overview
- **Dataset:** RAGTruth Test Split ([test.jsonl](file:///home/aditya/rags/TrustRag-phase11/data/processed/ragtruth/test.jsonl))
- **Total Records:** 2,700 (1,757 Factual, 943 Hallucinated)
- **Predictions Persisted:**
  - [predictions_ragtruth_no_verification.jsonl](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_step02_2_corrected_baselines/predictions_ragtruth_no_verification.jsonl)
  - [predictions_ragtruth_default.jsonl](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_step02_2_corrected_baselines/predictions_ragtruth_default.jsonl)
  - [predictions_ragtruth_strict.jsonl](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_step02_2_corrected_baselines/predictions_ragtruth_strict.jsonl)

---

## 2. Quantitative Results Breakdown

| Metric | No Verification | Default G3 (0.65) | Strict G3 (0.80) |
| :--- | :--- | :--- | :--- |
| **SUPPORTED** | 2,700 | 9 | 3 |
| **CONTRADICTED** | 0 | 1,885 | 1,914 |
| **PARTIALLY_SUPPORTED** | 0 | 436 | 343 |
| **INSUFFICIENT_EVIDENCE** | 0 | 280 | 379 |
| **UNCERTAIN** | 0 | 90 | 61 |
| **Strict FSR** | 100.00% (943/943) | **0.0000** (0/943) | **0.0000** (0/943) |
| **Partial-Inclusive Unsafe Acceptance** | 100.00% (943/943) | **7.74%** (73/943) | **5.94%** (56/943) |
| **False Contradiction Rate (FCR)** | 0.00% (0/1757) | **62.61%** (1100/1757) | **64.03%** (1125/1757) |
| **Partial-Inclusive Factual Rejection** | 0.00% (0/1757) | 83.27% (1463/1757) | 80.36% (1412/1757) |
| **Explicit Decisive Coverage** | 100.00% (2700/2700) | 70.15% (1894/2700) | 71.00% (1917/2700) |
| **Partial-Support Coverage** | 0.00% | 16.15% (436/2700) | 12.70% (343/2700) |
| **Strict Abstention Rate** | 0.00% | 13.70% (370/2700) | 16.30% (440/2700) |
| **Conservative Accuracy** | 65.07% | 35.26% | 35.04% |
| **Conservative F1** | 0.00% | 51.90% | 51.81% |
| **Decisive Accuracy** | 65.07% | 41.92% | 41.31% |
| **Decisive F1** | 0.00% | 58.80% | 58.38% |
| **Runtime / Throughput** | 0.02s (165,705 rec/s) | 69.36s (38.9 rec/s) | 66.97s (40.3 rec/s) |
