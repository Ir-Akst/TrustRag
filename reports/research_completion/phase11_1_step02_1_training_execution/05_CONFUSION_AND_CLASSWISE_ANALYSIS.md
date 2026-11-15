# TrustRAG — Phase 11.1, Step 2.1: Confusion Matrix & Classwise Error Analysis

## 1. Step 0 Baseline Confusion Matrix

The confusion matrix on the 2,662 validation samples evaluated prior to training is structured as follows (Rows = Ground Truth, Columns = Prediction):

```
                   Predicted
                ENT    CON    NEU    Total
Actual  ENT  [    0,     0,  1662 ]   1,662
        CON  [    0,     0,   356 ]     356
        NEU  [    0,     0,   644 ]     644
Total        [    0,     0,  2662 ]   2,662
```

### 1.1 Structural Properties of Baseline Matrix
1. **Unilateral Trivial Prediction:**
   The randomly initialized linear projection head (`classifier.weight`, `classifier.bias`) possessed an initial marginal activation bias favoring Index 2 (`NEUTRAL`). Consequently, every sample across all 2,662 inputs was predicted as `NEUTRAL`.
2. **Support Preservation:**
   Because all samples were classified as `NEUTRAL`, the measured accuracy equals exactly:
   $$\text{Accuracy} = \frac{\text{Neutral Support}}{\text{Total Validation Set}} = \frac{644}{2,662} \approx 24.1923\%$$
3. **Zero Minority Recall:**
   Contradiction recall and Entailment recall were strictly 0.00%, illustrating the necessity of supervised gradient updates.

---

## 2. Gradient Dynamics & Optimization Behavior

Although the run was aborted before reaching an epoch boundary, telemetry captured across both runs confirms active loss convergence:
- **Rolling Loss Reduction (Run 1):** Decreased from 1.0893 (Step 50) to 0.6531 (Step 1,750).
- **Contradiction Penalty Influence:** The $3.5\times$ cross-entropy weight on Contradiction instances yielded steep gradient updates on misclassified contradiction instances (e.g., Step 1,200 loss spike to 3.6607, followed immediately by corrective recovery to 0.1757 at Step 1,300).
- **Absence of Final Confusion Matrix:** Because the watchdog aborted execution at Step 325, no final checkpoint was generated, precluding post-training confusion matrix computation.

