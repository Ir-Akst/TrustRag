# Statistical Analysis & Confidence Interval Audit

**Auditor:** Senior Statistical Reviewer & Evaluation Auditor  
**Confidence Level:** 95% Wilson Score Interval ($\alpha = 0.05, z = 1.95996$)

---

## 1. Statistical Methodology

Wilson score intervals with continuity considerations were computed across all empirical evaluations in Phase 31. This avoids the severe under-coverage of normal approximation intervals near 0% and 100%.

Formula:
$$w = \frac{p + \frac{z^2}{2n} \pm z \sqrt{\frac{p(1-p)}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$

---

## 2. Comprehensive Wilson Interval Table

| Evaluation Suite | Sample Size ($n$) | Successes ($k$) | Point Estimate | Wilson 95% Confidence Interval |
| :--- | :---: | :---: | :---: | :---: |
| **Indirect Injection: Prune Recall** | 200 | 125 | 62.50% | **[55.61%, 68.91%]** |
| **Indirect Injection: Leakage Rate** | 200 | 75 | 37.50% | **[31.09%, 44.39%]** |
| **Indirect Injection: Clean FPR** | 200 | 0 | 0.00% | **[0.00%, 1.88%]** |
| **Adaptive Red-Team: ADR** | 200 | 102 | 51.00% | **[44.12%, 57.84%]** |
| **Adaptive Red-Team: ASR** | 200 | 98 | 49.00% | **[42.16%, 55.88%]** |
| **Adaptive Red-Team: Clean FPR** | 200 | 0 | 0.00% | **[0.00%, 1.88%]** |
| **Multilingual: Global ADR** | 450 | 95 | 21.11% | **[17.59%, 25.12%]** |
| **Multilingual: Global Clean FPR** | 450 | 0 | 0.00% | **[0.00%, 0.85%]** |
| **Multilingual: Non-Latin Native ADR** | 125 | 40 | 32.00% | **[24.43%, 40.69%]** |
| **Sybil 50% Poisoning Removal** | 100 | 100 | 100.00% | **[96.30%, 100.00%]** |
| **Sybil 60% Poisoning Removal** | 120 | 100 | 83.33% | **[75.65%, 88.94%]** |
| **Sybil 80% Poisoning Removal** | 160 | 100 | 62.50% | **[54.79%, 69.63%]** |
| **Fail-Safe Compliance** | 8 | 8 | 100.00% | **[67.56%, 100.00%]** |

---

## 3. Power Analysis & Statistical Limitations

1. **Clean False-Positive Upper Bound:** With $n=450$ benign multilingual queries and 0 false positives, the true clean FPR is bounded below $0.85\%$ at the 95% confidence level.
2. **Adaptive Attack Uncertainty:** The adaptive ADR estimate of $51.00\%$ has a margin of error of $\pm 6.86\%$, reflecting natural variation across heterogeneous attack families.
3. **Sybil Cap Determinism:** The removal rate at 60% poisoning ($83.33\%$) and 80% poisoning ($62.50\%$) is mathematically bounded by the removal cap $\lfloor K/2 \rfloor = 5$.
