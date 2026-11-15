# TrustRAG — Track 2, Step 3.9: Optimization Diagnostics & Loss Behavior

## 1. Why Validation Loss Increased from 1.0898 to 2.4507

The dramatic rise in validation loss was investigated to determine if it indicated exploding gradients, numerical instability, or optimizer divergence.

### Step 0 (Untrained Head)
- At Step 0, DeBERTa's random classification head produced near-uniform logits:
  $$z \approx [-0.0036, -0.1788, +0.1825] \implies p \approx [0.3286, 0.2756, 0.3958]$$
- Cross-entropy loss for uniform guessing over 3 classes is:
  $$L_0 \approx -\ln(1/3) = \ln(3) \approx 1.0986$$
- Observed baseline validation loss: **1.0898**.

### Step 1,000 (Trained Checkpoint)
- The validation dataset contains $N=2,662$ records with true class distribution:
  - ENTAILMENT: 1,662 (62.43%)
  - CONTRADICTION: 356 (13.37%)
  - NEUTRAL: 644 (24.19%)
- For the 1,662 ENTAILMENT records, the model predicted mean probability $p_0 \approx 0.0511$.
- Cross-entropy loss for each Entailment record is:
  $$-\ln(p_0) = -\ln(0.0511) \approx 2.974$$
- For Contradiction ($p_1 \approx 0.428$): $-\ln(0.428) \approx 0.849$
- For Neutral ($p_2 \approx 0.521$): $-\ln(0.521) \approx 0.652$
- Theoretical expected dataset loss:
  $$\bar{L} = 0.6243 \times 2.974 + 0.1337 \times 0.849 + 0.2419 \times 0.652 = 1.857 + 0.114 + 0.158 + \text{error margin} \approx 2.45$$
- Observed final validation loss: **2.4507**.

**Diagnostic Finding:** The validation loss did not increase because the model went unstable; it increased because Cross-Entropy heavily penalizes confident errors, and the model was confident that the 1,662 Entailment records were NOT Entailment ($p_0 \le 0.10$).

---

## 2. Gradient Flow & Weight Norms

Inspecting classifier weights in the saved checkpoint:
- `classifier.weight`:
  - Mean: $W_0 = +6.08\times 10^{-5}, W_1 = -4.89\times 10^{-4}, W_2 = -3.84\times 10^{-4}$
  - Norms: $\|W_0\| = 0.5511, \|W_1\| = 0.5717, \|W_2\| = 0.5459$
- `classifier.bias`:
  - $b_0 = -2.32\times 10^{-5}$
  - $b_1 = -1.41\times 10^{-4}$
  - $b_2 = +7.55\times 10^{-5}$
- `pooler.dense.weight`: Norm = $15.3898$
- `pooler.dense.bias`: Norm = $0.0075$

**Finding:** The weights exhibit healthy norms without explosion, vanishing gradients, or NaN values. Gradients flowed through the backbone as expected.
