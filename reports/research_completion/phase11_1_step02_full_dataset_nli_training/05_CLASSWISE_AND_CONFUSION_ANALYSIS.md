# TrustRAG — Phase 11.1, Step 2: Full-Dataset NLI Training Audit
## 05 — Classwise & Confusion Analysis

- **Audit Date:** 2026-11-14T18:25:00Z
- **Auditor:** Senior ML Training Engineer & Independent Experimental Auditor

---

### 1. Final Confusion Matrix Status

Because training was halted during preflight before model initialization and execution, no post-training confusion matrix was generated.

```
                  Predicted ENT   Predicted CON   Predicted NEU     Total
True ENTAILMENT               -               -               -         -
True CONTRADICTION            -               -               -         -
True NEUTRAL                  -               -               -         -
Total Predicted               -               -               -         -
```
*(Status: NOT EXECUTED — Training Blocked at Preflight Gate)*

---

### 2. Validation Split Baseline Class Breakdown (Reference)

For future reference upon remediation, the ground truth support distribution of `data/processed/sft_v2/nli/validation.jsonl` is:

| Ground Truth Class | Support Count | Split Prevalence | Natural Class Weight ($N / (3 \times N_c)$) | Proposed Weight |
| :--- | :--- | :--- | :--- | :--- |
| **`ENTAILMENT` (0)** | 1,662 | 62.43% | **0.534** | 1.00 |
| **`CONTRADICTION` (1)** | 356 | 13.37% | **2.492** | 3.50 |
| **`NEUTRAL` (2)** | 644 | 24.19% | **1.378** | 1.50 |
| **Total** | **2,662** | **100.00%** | **1.000** | - |

> [!NOTE]
> The natural inverse-frequency class weights for the training set ($N=10,815$, $N_{\text{ent}}=6707, N_{\text{con}}=1420, N_{\text{neu}}=2688$) are:
> - $w_{\text{ent}} = 10,815 / (3 \times 6,707) = \mathbf{0.538}$
> - $w_{\text{con}} = 10,815 / (3 \times 1,420) = \mathbf{2.539}$
> - $w_{\text{neu}} = 10,815 / (3 \times 2,688) = \mathbf{1.341}$
> 
> Normalizing relative to Entailment ($w / 0.538$) gives:
> - $w' = [1.00, 4.72, 2.49]$
> 
> Applying weights $w \approx [1.0, 3.5, 1.5]$ is appropriate **ONLY** under natural sequential or frequency-proportional sampling (`strategy="sequential"`), **NOT** under equal 1:1:1 stratified class-balanced sampling.

