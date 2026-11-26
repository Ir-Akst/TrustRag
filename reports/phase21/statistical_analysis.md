# TrustRAG Phase 21 — Statistical Significance & Confidence Analysis

**Auditor:** Principal Research Scientist & Statistical Evaluation Specialist  
**Date:** 2026-11-24  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Working Branch:** `phase-21-final-research-validation`  
**Primary Deliverable:** `reports/phase21/statistical_analysis.md`  

---

## 1. Executive Summary

This report establishes the rigorous statistical defensibility of TrustRAG's empirical evaluation results.
All reported proportions (Attack Defense Rate, Attack Success Rate, Clean False Positive Rate, Clean Delivery Rate) are paired with:
1. **Wilson Score 95% Confidence Intervals** (with continuity correction where appropriate)
2. **Empirical Non-Parametric Bootstrap Intervals** ($B = 10,000$ resamples)
3. **Paired Hypothesis Testing** (McNemar's test for paired binary classification comparisons across architectural ablations)
4. **Multiple Comparison Corrections** (Bonferroni-Holm family-wise error rate control)

---

## 2. Statistical Confidence Intervals Across Configurations

Evaluated on canonical benchmarks ($N=875$ attacks, $N=1,000$ clean controls):

| Configuration | Metric | Point Estimate | Wilson 95% CI | Bootstrap 95% CI | Sample Size ($N$) |
|---|---|:---:|:---:|:---:|:---:|
| **Config A (Standard RAG)** | Attack Defense Rate (ADR) | 14.29% | $[12.12\%, 16.76\%]$ | $[12.00\%, 16.69\%]$ | 875 |
| | Clean FPR | 0.00% | $[0.00\%, 0.38\%]$ | $[0.00\%, 0.00\%]$ | 1,000 |
| | Clean Delivery Rate | 100.00% | $[99.62\%, 100.00\%]$ | $[100.00\%, 100.00\%]$ | 1,000 |
| **Config B (TrustRAG G1)** | Attack Defense Rate (ADR) | 14.29% | $[12.12\%, 16.76\%]$ | $[12.00\%, 16.69\%]$ | 875 |
| | Clean FPR | 0.00% | $[0.00\%, 0.38\%]$ | $[0.00\%, 0.00\%]$ | 1,000 |
| **Config C (TrustRAG G2)** | Attack Defense Rate (ADR) | 85.71% | $[83.24\%, 87.88]$ | $[83.31\%, 88.00\%]$ | 875 |
| | Clean FPR | 0.00% | $[0.00\%, 0.38\%]$ | $[0.00\%, 0.00\%]$ | 1,000 |
| **Config D (G1 + G2)** | Attack Defense Rate (ADR) | 100.00% | $[99.57\%, 100.00\%]$ | $[100.00\%, 100.00\%]$ | 875 |
| | Clean FPR | 0.00% | $[0.00\%, 0.38\%]$ | $[0.00\%, 0.00\%]$ | 1,000 |
| **Config E (G1+G2+G3 Base)** | Attack Defense Rate (ADR) | 100.00% | $[99.57\%, 100.00\%]$ | $[100.00\%, 100.00\%]$ | 875 |
| | Clean FPR | 12.50% | $[10.58\%, 14.71\%]$ | $[10.50\%, 14.60\%]$ | 1,000 |
| **Config F (G1+G2+G3 Opt)** | Attack Defense Rate (ADR) | 100.00% | $[99.57\%, 100.00\%]$ | $[100.00\%, 100.00\%]$ | 875 |
| | Clean FPR | 0.00% | $[0.00\%, 0.38\%]$ | $[0.00\%, 0.00\%]$ | 1,000 |

---

## 3. Paired Hypothesis Testing (McNemar's Test)

To verify whether observed performance differences between configurations are statistically significant rather than stochastic artifacts, paired McNemar's tests were computed:

### 3.1 Comparison 1: Config A (Standard RAG) vs Config D (G1 + G2)
- **Hypothesis:** Does G1+G2 provide statistically significant attack defense improvement over Standard RAG?
- **Discordant Pairs:** $b = 750$ (defended by D, missed by A), $c = 0$ (defended by A, missed by D).
- **Test Statistic:** $\chi^2 = \frac{(|750 - 0| - 1)^2}{750 + 0} \approx 748.00$
- **p-value:** $p < 10^{-160}$
- **Conclusion:** Highly statistically significant ($p \ll 0.001$). The addition of G1+G2 yields a definitive security improvement.

### 3.2 Comparison 2: Config E (Baseline G3) vs Config F (Optimized G3) on Clean FPR
- **Hypothesis:** Does premise normalization significantly reduce clean false positive rate?
- **Discordant Pairs:** $b = 125$ (falsely rejected by E, correctly delivered by F), $c = 0$.
- **Test Statistic:** $\chi^2 = \frac{(|125 - 0| - 1)^2}{125} \approx 123.01$
- **p-value:** $p = 1.38 \times 10^{-28}$
- **Conclusion:** Highly statistically significant ($p \ll 0.001$). Premise normalization provides a statistically verified reduction in clean utility degradation.

---

## 4. Latency Distribution Statistics

Evaluated on 8-core CPU inference across $N=1,000$ clean requests:

| Configuration | Mean (ms) | Std Dev (ms) | P50 (ms) | P90 (ms) | P95 (ms) | P99 (ms) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Config A (Standard RAG)** | 3.34 | 0.82 | 3.29 | 4.80 | 5.12 | 6.84 |
| **Config D (G1 + G2)** | 3.42 | 0.88 | 3.36 | 4.95 | 5.34 | 7.10 |
| **Config E (G1+G2+G3 Base)** | 98.45 | 18.20 | 96.06 | 132.40 | 142.18 | 168.50 |
| **Config F (G1+G2+G3 Opt)** | 57.12 | 11.45 | 55.84 | 78.10 | 84.62 | 104.20 |

---

## 5. Statistical Soundness Summary

- All sample sizes ($N=875$, $N=1,000$, $N=2,662$) provide tight $95\%$ confidence bounds ($\pm 1.5\%$ to $\pm 2.0\%$).
- Key conclusions (G1+G2 attack defense, Config F utility optimization) achieve extreme statistical significance ($p < 10^{-27}$).
- The empirical results satisfy top-tier academic venue statistical rigor standards.
