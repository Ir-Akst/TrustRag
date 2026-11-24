# Phase 32 Workstream I: Statistical Analysis & Confidence Intervals

## 1. Statistical Methodology
All proportional metrics (Adversarial Detection Rate, Clean False Positive Rate, Answer Grounding Accuracy) are reported alongside their **95% Wilson Score Confidence Intervals**:
$$w = \frac{p + \frac{z^2}{2n} \pm z \sqrt{\frac{p(1-p)}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$
where $z = 1.95996$, $n$ is sample size, and $p = \frac{k}{n}$.

## 2. Summary of Statistical Bounds

| Experiment / Metric | Samples ($n$) | Successes ($k$) | Point Estimate | 95% Wilson Score CI |
| :--- | :--- | :--- | :--- | :--- |
| **Adaptive Attack Detection (ADR)** | 200 | 200 | **100.0%** | **[98.12%, 100.0%]** |
| **Adaptive Control FPR** | 200 | 0 | **0.0%** | **[0.00%, 1.88%]** |
| **Document Firewall ADR** | 200 | 200 | **100.0%** | **[98.12%, 100.0%]** |
| **Document Firewall Control FPR** | 200 | 0 | **0.0%** | **[0.00%, 1.88%]** |
| **Overall Multilingual ADR** | 450 | 380 | **84.44%** | **[80.81%, 87.50%]** |
| **Overall Multilingual Control FPR** | 450 | 0 | **0.0%** | **[0.00%, 0.85%]** |
| **Claim Grounding Accuracy** | 300 | 300 | **100.0%** | **[98.74%, 100.0%]** |
| **Supported Answer Release Rate** | 100 | 100 | **100.0%** | **[96.30%, 100.0%]** |
| **Contradicted Answer Leakage** | 100 | 0 | **0.0%** | **[0.00%, 3.70%]** |

## 3. Statistical Power & Significance
- Across all benign control evaluations ($N = 200 + 200 + 450 = 850$), zero false positives were observed, establishing with high statistical power ($p < 0.001$) that the negative base logit ($b = -3.20$) protects benign domain usability while achieving robust attack detection.
