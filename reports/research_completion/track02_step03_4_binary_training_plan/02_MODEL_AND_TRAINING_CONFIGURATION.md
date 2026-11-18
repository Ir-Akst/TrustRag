# Track 2, Step 3.4 — Section 02: Model and Training Configuration

## 1. Architecture and Weights Setup

- **Model Class:** `transformers.DebertaV2ForSequenceClassification`
- **Source Weights:** `/home/aditya/rags/models/pretrained/deberta-v3-small` (Commit `a36c739020e01763fe789b4b85e2df55d6180012`)
- **Parameter Breakdown:**
  - Backbone: 141,304,320 parameters (102 tensor weights, initialized from pretrained checkpoint).
  - Head/Pooler: 592,130 parameters (4 tensor weights, newly initialized with Gaussian $\sigma=0.02$).
  - Total: 141,896,450 parameters.
- **Precision:** `torch.float32`.
- **Dropout:** Default architecture dropout (`0.1` hidden dropout, `0.1` attention dropout).

---

## 2. Optimization Configuration

- **Optimizer:** `torch.optim.AdamW`
- **Initial Learning Rate:** $2 	imes 10^{-5}$ (`2e-5`)
- **Weight Decay:** $0.01$ (applied to non-bias, non-LayerNorm parameters)
- **Betas:** $(eta_1 = 0.9, eta_2 = 0.999)$
- **Epsilon:** $1 	imes 10^{-8}$
- **Batch Size:** $1$
- **Gradient Accumulation Steps:** $1$ (direct parameter update on every step)
- **Total Training Steps:** $1,000$ (1 complete pass through the 1,000-example slice)
- **Learning Rate Schedule:**
  - Linear warmup for the first $100$ steps ($10\%$ of training).
  - Linear decay from step $101$ to $1,000$ down to $0.0$.
  - *Purpose:* Warmup prevents the randomly initialized classification head from destabilizing pretrained backbone representations during initial optimization steps.

---

## 3. Why Batch Size 1 and Seq Len 128?

1. **Memory Stability:** Batch size 1 consumes ~2.37 GB of RSS on CPU (including AdamW momentum buffers). Increasing batch size to 8 would increase activation memory to ~4.5 GB, approaching the host physical RAM boundary and risking OOM.
2. **Empirical Reproducibility:** Batch size 1 and sequence length 128 match the exact parameters verified in the Step 3.3 feasibility pilot.
