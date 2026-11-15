# TrustRAG — Track 2, Step 3.9: Class Collapse Forensic Analysis

## 1. The Anomaly

In Step 3.8 final evaluation across $N=2,662$ validation samples:
- **Entailment (True Count: 1,662):** **0 predictions** (0.0% precision, 0.0% recall, 0.0% F1).
- **Contradiction (True Count: 356):** **389 predictions** (68 correct, 321 false positives).
- **Neutral (True Count: 644):** **2,273 predictions** (574 correct, 1,699 false positives).

---

## 2. Logit and Probability Distribution Forensics

Inspecting the saved Step 3.8 model on validation samples reveals why Entailment was never chosen:

### Raw Logits ($z$)
- **$z_0$ (ENTAILMENT):** Mean = **-1.4479** | Max = **-0.7765** | Min = **-2.1521**
- **$z_1$ (CONTRADICTION):** Mean = **+0.7830** | Max = **+1.2960** | Min = **+0.1721**
- **$z_2$ (NEUTRAL):** Mean = **+0.9576** | Max = **+2.0113** | Min = **-0.2734**

**Key Insight:** $z_0$ is negative for **100% of validation records**. Its maximum value across all evaluated records is **-0.7765**, whereas $z_1$ and $z_2$ are positive virtually everywhere. Because $\text{argmax}(z)$ chooses the maximum logit, and $z_0$ is always far below $\max(z_1, z_2)$, Entailment is mathematically unreachable.

### Softmax Probabilities ($p$)
- **$p_0$ (ENTAILMENT):** Mean = **0.0511 (5.1%)** | Max = **0.1031 (10.3%)**
- **$p_1$ (CONTRADICTION):** Mean = **0.4278 (42.8%)** | Max = **0.6120**
- **$p_2$ (NEUTRAL):** Mean = **0.5211 (52.1%)** | Max = **0.8410**

Across all 2,662 records, the model never assigned greater than 10.3% probability to ENTAILMENT.

---

## 3. Mathematical Mechanism of Logit Suppression

In Cross-Entropy loss for a multiclass classification problem:
$$L = -\ln\left(\frac{e^{z_y}}{\sum_j e^{z_j}}\right) = -z_y + \ln\left(\sum_j e^{z_j}\right)$$

The gradient with respect to logit $z_k$ is:
$$\frac{\partial L}{\partial z_k} = p_k - \mathbb{I}(y = k)$$

When the true label $y \neq 0$ (i.e. the sample is CONTRADICTION or NEUTRAL):
$$\frac{\partial L}{\partial z_0} = p_0 - 0 = p_0 > 0$$

Under gradient descent with learning rate $\eta$:
$$z_0^{(t+1)} \approx z_0^{(t)} - \eta p_0$$

Because $\frac{\partial L}{\partial z_0} > 0$ on every non-Entailment step, the optimizer continuously pushes $z_0$ **downwards**.

During the final **295 consecutive optimizer steps** where $y \in \{1, 2\}$ exclusively:
- The optimizer received 295 consecutive positive gradient pushes against $z_0$.
- Not a single step ($y=0$) pushed $z_0$ upwards ($p_0 - 1 < 0$).
- Consequently, $z_0$ was driven into deep negative territory (-1.45), suppressing $p_0$ to ~5%.
