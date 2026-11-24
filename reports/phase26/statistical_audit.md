# TrustRAG Phase 26: Statistical Audit Report

**Evaluation Date:** 2026-11-24  
**Evaluator:** Principal Statistical Evaluation Specialist & Independent Auditor  

---

## 1. Global Metrics & Confusion Matrix (Unseen Adversarial + Independent Benign)

$$\begin{array}{c|cc|c}
& \textbf{Predicted Negative (ALLOW)} & \textbf{Predicted Positive (BLOCK)} & \textbf{Total} \\
\hline
\textbf{Actual Negative (Benign)} & TN = 500 & FP = 0 & 500 \\
\textbf{Actual Positive (Adversarial)} & FN = 141 & TP = 359 & 500 \\
\hline
\textbf{Total} & 641 & 359 & 1000 \\
\end{array}$$

### Statistical Metric Formulation:

1. **Attack Detection Rate (ADR / Sensitivity / Recall):**
   $$\text{ADR} = \frac{TP}{TP + FN} = \frac{359}{500} = 71.80\% \quad (95\%\text{ Wilson CI: } [67.70\%, 75.57\%])$$

2. **Attack Success Rate (ASR / False Negative Rate):**
   $$\text{ASR} = \frac{FN}{TP + FN} = \frac{141}{500} = 28.20\% \quad (95\%\text{ Wilson CI: } [24.43\%, 32.30\%])$$

3. **Clean False Positive Rate ($\text{FPR}_{\text{strict}}$):**
   $$\text{FPR}_{\text{strict}} = \frac{FP}{TN + FP} = \frac{0}{500} = 0.00\% \quad (95\%\text{ Wilson CI: } [0.00\%, 0.76\%])$$

4. **Clean Delivery Rate (Specificity):**
   $$\text{Specificity} = \frac{TN}{TN + FP} = \frac{500}{500} = 100.00\% \quad (95\%\text{ Wilson CI: } [99.24\%, 100.00\%])$$

5. **Precision (Positive Predictive Value):**
   $$\text{Precision} = \frac{TP}{TP + FP} = \frac{359}{359} = 100.00\% \quad (95\%\text{ Wilson CI: } [98.95\%, 100.00\%])$$

6. **F1 Score:**
   $$F_1 = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} = 2 \times \frac{1.0 \times 0.7180}{1.0 + 0.7180} = 83.59\%$$

7. **Accuracy:**
   $$\text{Accuracy} = \frac{TP + TN}{1000} = \frac{859}{1000} = 85.90\% \quad (95\%\text{ Wilson CI: } [83.60\%, 87.95\%])$$

---

## 2. Statistical Comparison: In-Domain vs. Unseen Distribution

| Cohort | Adversarial Samples | True Positives ($TP$) | Attack Detection Rate | Attack Success Rate | Wilson 95% CI (ADR) |
|---|---|---|---|---|---|
| **Phase 25 In-Distribution** | 164 | 164 | **100.00%** | **0.00%** | [97.71%, 100.00%] |
| **Phase 26 Unseen Adversarial** | 500 | 359 | **71.80%** | **28.20%** | [67.70%, 75.57%] |
| **Delta ($\Delta$)** | +336 | - | **-28.20%** | **+28.20%** | $p < 0.0001$ (Two-proportion z-test) |

**Statistical Insight:** The statistically significant drop of $28.20\%$ ($z = 7.62, p < 0.0001$) confirms that Phase 25's 100% ADR was an artifact of testing known, in-distribution prompt patterns. When evaluated on genuinely unseen attacks with novel vocabulary and non-Western languages, the true empirical security posture of the deterministic guardrail is $71.80\%$.
