# TrustRAG Phase 25: Confusion Matrix & Statistical Metrics

**Evaluation Date:** 2026-11-24  
**Total Evaluated Samples:** 669 (164 Adversarial, 505 Benign Controls)  
**Evaluation Standard:** Strict Blocking Rule (only hard `BLOCK` counts as $TP$)  

---

## 1. 2x2 Confusion Matrix

$$\begin{array}{c|cc|c}
& \textbf{Predicted Negative (ALLOW)} & \textbf{Predicted Positive (BLOCK)} & \textbf{Total} \\
\hline
\textbf{Actual Negative (Benign)} & TN = 505 & FP = 0 & 505 \\
\textbf{Actual Positive (Adversarial)} & FN = 0 & TP = 164 & 164 \\
\hline
\textbf{Total} & 505 & 164 & 669 \\
\end{array}$$

*Note on Flags:* 0 benign samples were flagged ($0.00\%$, 95% CI: $[0.00\%, 0.75\%]$).

---

## 2. Statistical Metrics & Confidence Intervals

All confidence intervals are calculated using the 2-sided Wilson Score method at 95% confidence ($\alpha = 0.05, z = 1.95996$):

- **Attack Detection Rate (ADR / Sensitivity / Recall):**
  $$\text{ADR} = \frac{TP}{TP + FN} = \frac{164}{164} = 100.00\% \quad (95\%\text{ CI: } [97.71\%, 100.00\%])$$

- **Attack Success Rate (ASR / False Negative Rate):**
  $$\text{ASR} = \frac{FN}{TP + FN} = \frac{0}{164} = 0.00\% \quad (95\%\text{ CI: } [0.00\%, 2.29\%])$$

- **Clean Strict False Positive Rate ($\text{FPR}_{\text{strict}}$):**
  $$\text{FPR}_{\text{strict}} = \frac{FP}{TN + FP} = \frac{0}{505} = 0.00\% \quad (95\%\text{ CI: } [0.00\%, 0.75\%])$$

- **Clean Delivery Rate (Specificity):**
  $$\text{Specificity} = \frac{TN}{TN + FP} = \frac{505}{505} = 100.00\% \quad (95\%\text{ CI: } [99.25\%, 100.00\%])$$

- **Precision (Positive Predictive Value):**
  $$\text{Precision} = \frac{TP}{TP + FP} = \frac{164}{164} = 100.00\% \quad (95\%\text{ CI: } [97.71\%, 100.00\%])$$

- **F1 Score:**
  $$F_1 = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} = 100.00\%$$

- **Accuracy:**
  $$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN} = \frac{669}{669} = 100.00\% \quad (95\%\text{ CI: } [99.43\%, 100.00\%])$$

---

## 3. Comparison with Previous Phases

| Metric | Phase 23 Reported | Phase 24 Forensic Audit | Phase 25 Remediated & Verified |
|---|---|---|---|
| Adversarial Cases ($n$) | 120 | 120 | **164** |
| Benign Controls ($n$) | 20 | 20 | **505** |
| True Positives ($TP$) | 115 | 115 | **164** |
| False Negatives ($FN$) | 5 | 5 | **0** |
| True Negatives ($TN$) | 20 | 20 | **505** |
| False Positives ($FP$) | 0 | 0 | **0** |
| **Attack Detection Rate (ADR)** | 95.83% | 95.83% | **100.00%** |
| ADR 95% Wilson CI | [90.62%, 98.21%] | [90.62%, 98.21%] | **[97.71%, 100.00%]** |
| **Attack Success Rate (ASR)** | 4.17% | 4.17% | **0.00%** |
| ASR 95% Wilson CI | [1.79%, 9.38%] | [1.79%, 9.38%] | **[0.00%, 2.29%]** |
| **Clean False Positive Rate** | 0.00% | 0.00% | **0.00%** |
| Clean FPR 95% Wilson CI | [0.00%, 16.11%] | [0.00%, 16.11%] | **[0.00%, 0.75%]** |
| **Clean Delivery Rate** | 100.00% | 100.00% | **100.00%** |
| Clean Delivery 95% Wilson CI | [83.89%, 100.00%] | [83.89%, 100.00%] | **[99.25%, 100.00%]** |
| **Precision** | 100.00% | 100.00% | **100.00%** |
| **Recall** | 95.83% | 95.83% | **100.00%** |
| **F1 Score** | 97.87% | 97.87% | **100.00%** |
