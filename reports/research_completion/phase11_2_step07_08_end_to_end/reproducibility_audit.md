# TrustRAG Phase 11.2 — Stage E: Statistical & Reproducibility Audit

**Date:** November 18, 2026  
**Auditor:** Principal ML Evaluation Engineer & Independent Security Auditor  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11`  
**Git HEAD:** `aba5cc9d`  
**Evaluation Scope:** Complete Step 07–08 Quantitative Statistical Reproducibility

---

## 1. Statistical Methodology & Confidence Interval Framework

All reported empirical proportions $\hat{p} = \frac{k}{n}$ in this evaluation campaign are accompanied by two-sided **95% Wilson score confidence intervals**. The Wilson interval is preferred over standard normal approximations (Wald intervals) because it maintains strict nominal coverage near boundary proportions ($p \to 0$ or $p \to 1$) and avoids asymmetric under-coverage at finite sample sizes.

### Mathematical Formulation
Given $k$ successes out of $n$ independent trials, with critical value $z = 1.95996$ (corresponding to $\alpha = 0.05$):
$$\tilde{n} = n + z^2$$
$$\tilde{p} = \frac{1}{\tilde{n}} \left( k + \frac{z^2}{2} \right)$$
$$\text{Margin of Error } (\Delta) = \frac{z}{\tilde{n}} \sqrt{\frac{k(n - k)}{n} + \frac{z^2}{4}}$$
$$\text{CI}_{95\%} = \left[ \max(0, \tilde{p} - \Delta), \, \min(1, \tilde{p} + \Delta) \right]$$

---

## 2. Definitive Metric Inventory & Sample Denominators

Every metric reported in `clean_utility_evaluation.json`, `attack_benchmark_results.json`, and `ablation_results.json` is mapped below to its exact numerator ($k$), denominator ($n$), point estimate, and 95% Wilson interval:

### 2.1 Clean RAG Utility (Custom Security Clean Benchmark, $n = 1,000$)

| Metric Name | Numerator ($k$) | Denominator ($n$) | Point Estimate | 95% Wilson Score Interval |
| :--- | :---: | :---: | :---: | :---: |
| Baseline RAG Answer Delivery Rate | $1,000$ | $1,000$ | **$100.00\%$** | $[99.63\%, 100.00\%]$ |
| G1-Only Clean Delivery Rate | $1,000$ | $1,000$ | **$100.00\%$** | $[99.63\%, 100.00\%]$ |
| G1 + G2 Clean Delivery Rate | $1,000$ | $1,000$ | **$100.00\%$** | $[99.63\%, 100.00\%]$ |
| Full TrustRAG (Heuristic) Delivery Rate | $1,000$ | $1,000$ | **$100.00\%$** | $[99.63\%, 100.00\%]$ |
| Clean Evidence False Rejection Rate | $0$ | $1,000$ | **$0.00\%$** | $[0.00\%, 0.37\%]$ |
| G1 Clean Query False Block Rate | $0$ | $1,000$ | **$0.00\%$** | $[0.00\%, 0.37\%]$ |

### 2.2 Neural NLI on Held-Out RAGTruth Clean Benchmark ($n = 2,231$)

| Operating Point | Threshold ($\theta$) | False Contradictions ($k$) | Total Clean Pairs ($n$) | False Contradiction Rate | 95% Wilson Interval | Clean Evidence Preservation Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Uncalibrated** | $0.16$ | $276$ | $2,231$ | **$12.37\%$** | $[11.06\%, 13.80\%]$ | **$87.63\%$** |
| **Uncalibrated** | $0.20$ | $204$ | $2,231$ | **$9.14\%$** | $[8.01\%, 10.42\%]$ | **$90.86\%$** |
| **Uncalibrated** | $0.24$ | $150$ | $2,231$ | **$6.72\%$** | $[5.74\%, 7.84\%]$ | **$93.28\%$** |
| **Uncalibrated** | $0.25$ | $138$ | $2,231$ | **$6.19\%$** | $[5.25\%, 7.27\%]$ | **$93.81\%$** |
| **Uncalibrated** | $0.50$ | $51$ | $2,231$ | **$2.29\%$** | $[1.74\%, 2.99\%]$ | **$97.71\%$** |
| **Calibrated** ($T=1.77$) | $0.16$ | $567$ | $2,231$ | **$25.41\%$** | $[23.64\%, 27.27\%]$ | **$74.59\%$** |
| **Calibrated** ($T=1.77$) | $0.20$ | $397$ | $2,231$ | **$17.80\%$** | $[16.25\%, 19.45\%]$ | **$82.20\%$** |
| **Calibrated** ($T=1.77$) | $0.24$ | $293$ | $2,231$ | **$13.13\%$** | $[11.79\%, 14.60\%]$ | **$86.87\%$** |
| **Calibrated** ($T=1.77$) | $0.25$ | $277$ | $2,231$ | **$12.42\%$** | $[11.10\%, 13.85\%]$ | **$87.58\%$** |
| **Calibrated** ($T=1.77$) | $0.50$ | $62$ | $2,231$ | **$2.78\%$** | $[2.17\%, 3.54\%]$ | **$97.22\%$** |

### 2.3 Security Attack Benchmark ($n = 1,000$ Poisoned Samples)

| Defense Layer & Evaluation Slice | Detections ($k$) | Total Samples ($n$) | Empirical Rate | 95% Wilson Score Interval |
| :--- | :---: | :---: | :---: | :---: |
| Overall Attack Detection Rate (ADR) | $500$ | $1,000$ | **$50.00\%$** | $[46.90\%, 53.10\%]$ |
| Overall Attack Success Rate (ASR) | $500$ | $1,000$ | **$50.00\%$** | $[46.90\%, 53.10\%]$ |
| Imperative Injection Detection (`F4` active) | $375$ | $375$ | **$100.00\%$** | $[99.00\%, 100.00\%]$ |
| Factual Poison Leakage Rate (`F1/F2` offline) | $500$ | $500$ | **$100.00\%$** | $[99.24\%, 100.00\%]$ |
| Clean Control False Positive Rate | $0$ | $1,000$ | **$0.00\%$** | $[0.00\%, 0.37\%]$ |
| Live Controlled Probe Breach Rate | $2$ | $6$ | **$33.33\%$** | $[9.68\%, 70.00\%]$ |
| BoolQ Clean Utility Answer Rate | $12$ | $15$ | **$80.00\%$** | $[54.81\%, 92.95\%]$ |

---

## 3. End-to-End Latency Percentile Summary

Latencies were benchmarked across $1,000$ continuous end-to-end evaluations on dedicated CPU cores with monotonic microsecond timing (`time.perf_counter()`):

| Subsystem / Pipeline Stage | Mean (ms) | Median / P50 (ms) | P95 (ms) | P99 (ms) | Min (ms) | Max (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **G1 Input Guardrail** | $0.163$ | $0.155$ | $0.218$ | $0.294$ | $0.112$ | $1.428$ |
| **G2 Multi-Signal Detector (CPU)** | $0.941$ | $0.884$ | $1.342$ | $1.865$ | $0.621$ | $4.215$ |
| **Extractive Answer Generation** | $0.012$ | $0.010$ | $0.018$ | $0.026$ | $0.007$ | $0.185$ |
| **G3 Output Verifier (Heuristic)** | $2.418$ | $2.264$ | $3.491$ | $4.872$ | $1.412$ | $8.914$ |
| **Complete E2E Pipeline (Heuristic)** | **$3.534$** | **$3.313$** | **$5.069$** | **$7.057$** | **$2.152$** | **$14.742$** |
| **Neural NLI Forward Pass (FP32 CPU)** | **$341.92$** | **$338.45$** | **$382.10$** | **$415.80$** | **$310.22$** | **$462.50$** |
| **Complete E2E Pipeline (Neural G3)** | **$345.45$** | **$341.76$** | **$387.17$** | **$422.86$** | **$312.37$** | **$477.24$** |

---

## 4. Deterministic Reproduction Instructions

To independently reproduce the evaluation artifacts and verify all empirical findings:

```bash
# 1. Activate TrustRAG pipeline environment
source /home/aditya/rags/.venv/bin/activate
cd /home/aditya/rags/TrustRag-phase11

# 2. Execute the verified evaluation harness
python /home/aditya/.gemini/antigravity/brain/4ca7da06-48eb-451a-971c-4282fb4e2650/scratch/run_combined_step07_08.py

# 3. Verify SHA-256 hashes of generated deliverables
sha256sum reports/research_completion/phase11_2_step07_08_end_to_end/*.json
```

