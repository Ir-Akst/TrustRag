# TrustRAG Research Completion — Track 1, Step 2.2: HaluEval Corrected Results

## 1. Experimental Overview
- **Dataset:** HaluEval Test Split ([test.jsonl](file:///home/aditya/rags/TrustRag-phase11/data/processed/halueval/test.jsonl))
- **Total Records:** 3,000 (1,500 Factual, 1,500 Hallucinated)
- **Predictions Persisted:**
  - [predictions_halueval_no_verification.jsonl](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_step02_2_corrected_baselines/predictions_halueval_no_verification.jsonl)
  - [predictions_halueval_default.jsonl](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_step02_2_corrected_baselines/predictions_halueval_default.jsonl)
  - [predictions_halueval_strict.jsonl](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_step02_2_corrected_baselines/predictions_halueval_strict.jsonl)

---

## 2. Quantitative Results Breakdown

| Metric | No Verification | Default G3 (0.65) | Strict G3 (0.80) | Strict Impact |
| :--- | :--- | :--- | :--- | :--- |
| **SUPPORTED** | 3,000 | 1,153 | 1,050 | -103 (-8.9%) |
| **CONTRADICTED** | 0 | 235 | 235 | Invariant |
| **PARTIALLY_SUPPORTED** | 0 | 19 | 20 | +1 |
| **INSUFFICIENT_EVIDENCE** | 0 | 1,571 | 1,675 | +104 (+6.6%) |
| **UNCERTAIN** | 0 | 22 | 20 | -2 |
| **Strict FSR** | 100.00% (1500/1500) | **15.93%** (239/1500) | **9.07%** (136/1500) | **-43.1% Relative Leakage** |
| **Partial-Inclusive Unsafe Acceptance** | 100.00% (1500/1500) | **17.20%** (258/1500) | **10.40%** (156/1500) | **-39.5% Relative Leakage** |
| **False Contradiction Rate (FCR)** | 0.00% (0/1500) | **0.87%** (13/1500) | **0.87%** (13/1500) | **Zero Utility Degradation** |
| **Explicit Decisive Coverage** | 100.00% (3000/3000) | 46.27% (1388/3000) | 42.83% (1285/3000) | -3.44% |
| **Partial-Support Coverage** | 0.00% | 0.63% (19/3000) | 0.67% (20/3000) | +0.04% |
| **Strict Abstention Rate** | 0.00% | 53.10% (1593/3000) | 56.50% (1695/3000) | +3.40% |
| **Conservative Accuracy** | 50.00% | 72.50% | **75.93%** | **+3.43% Net Accuracy** |
| **Conservative F1** | 0.00% | 75.35% | **79.07%** | **+3.72% F1 Gain** |
| **Decisive Accuracy** | 50.00% | 81.84% | **88.40%** | **+6.56% Decisive Acc** |
| **Decisive F1** | 0.00% | 63.79% | **74.87%** | **+11.08% Decisive F1** |
| **Runtime / Throughput** | 0.01s (523,106 rec/s) | 8.87s (338.2 rec/s) | 8.95s (335.1 rec/s) | Nominal |
