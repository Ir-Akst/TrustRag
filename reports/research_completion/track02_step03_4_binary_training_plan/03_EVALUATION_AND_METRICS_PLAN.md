# Track 2, Step 3.4 — Section 03: Evaluation and Metrics Plan

## 1. Metric Hierarchy

The bounded training experiment will track metrics across training and validation:

### A. Primary Loss Metric
- **Loss Function:** `torch.nn.CrossEntropyLoss(reduction='mean')`
- Tracked on every training step (logged every 50 steps) and on the 200-sample validation set.

### B. Classification Performance Metrics
1. **Accuracy:**
   $$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$
2. **Balanced Accuracy:**
   $$\text{Balanced Accuracy} = \frac{1}{2} \left( \frac{TP}{TP + FN} + \frac{TN}{TN + FP} \right)$$
   *(Accounts for any local split imbalances).*
3. **Precision, Recall, and F1 (Per-Class and Macro):**
   - Class 0 (`FACTUAL`): Precision, Recall, F1.
   - Class 1 (`HALLUCINATED`): Precision, Recall, F1.
   - Macro F1: Arithmetic mean of $F1_0$ and $F1_1$.
4. **Confusion Matrix:**
   - True Positives ($TP$: Predicted Hallucinated, Actually Hallucinated)
   - False Positives ($FP$: Predicted Hallucinated, Actually Factual)
   - True Negatives ($TN$: Predicted Factual, Actually Factual)
   - False Negatives ($FN$: Predicted Factual, Actually Hallucinated)

---

## 2. Evaluation Protocol & Checkpoints

- **Step 0 Baseline Evaluation:** Run validation inference on the 200 validation samples using the freshly initialized classification head. This establishes the pre-training random baseline (expected loss $\approx 0.693$, accuracy $\approx 50\%$).
- **Periodic Training Telemetry:** Every 50 steps, compute rolling average training loss, gradient L2 norm, and parameter update delta norm.
- **Step 1,000 Post-Training Evaluation:** Run validation inference on the 200 validation samples. Compare pre-training vs. post-training metrics to prove whether the model learned the hallucination discrimination task.

---

## 3. Explicit Abstention Policy

**Abstention is NOT part of this binary objective.**
In accordance with task constraints, the model outputs binary logits across two classes (`FACTUAL` vs. `HALLUCINATED`). No neutral/uncertain threshold or abstention mechanism will be applied unless separately specified and justified.
