# Track 2, Step 3.3 — Section 04: Forward, Backward, and Optimization Results

## 1. Step-by-Step Optimization Telemetry

| Step | Example ID | Active Tokens | Loss | Logits [Class 0, Class 1] | Grad L2 Norm | Non-Zero Params | Weight Delta L2 | Fwd (ms) | Bwd (ms) | Opt (ms) | Total Step (ms) |
|:----:|------------|:-------------:|:----:|:-------------------------:|:------------:|:---------------:|:---------------:|:--------:|:--------:|:--------:|:---------------:|
| 1 | `...0_factual` | 62 / 128 | 0.5788 | `[-0.0122, -0.2557]` | 8.9239 | 106 / 106 | 0.000733 | 224.7 | 296.1 | 1261.6 | 1940.8 |
| 2 | `...0_hallucinated` | 65 / 128 | 0.8187 | `[-0.0598, -0.2968]` | 11.5438 | 106 / 106 | 0.000348 | 152.7 | 285.3 | 575.4 | 1144.2 |
| 3 | `...1000_factual` | 100 / 128 | 0.6164 | `[0.1285, -0.0314]` | 9.5794 | 106 / 106 | 0.000331 | 154.9 | 277.4 | 587.4 | 1146.6 |

## 2. Gradient Verification Analysis

1. **Finite Gradients:** All gradients evaluated to finite real numbers (`torch.isfinite(grad).all() == True`). No `NaN` or `Inf` was detected in any parameter tensor.
2. **Backpropagation Coverage:** Gradients were populated for all **106 of 106** trainable parameter tensors, from the final classification head down through the embedding matrix and relative position bias tables.
3. **Gradient Magnitude:**
   - Step 1 Gradient L2 Norm: **8.9239**
   - Step 2 Gradient L2 Norm: **11.5438**
   - Step 3 Gradient L2 Norm: **9.5794**
   The gradient norms are consistent with expected cross-entropy backpropagation through unnormalized classification heads.

## 3. Parameter Update Verification

To mathematically prove that optimization occurred:
- The L2 norm of the parameter delta was tracked on the classification weight tensor `model.classifier.weight`.
- Step 1: Delta = 0.000733
- Step 2: Delta = 0.000348
- Step 3: Delta = 0.000331
All deltas are strictly positive and non-zero, confirming active AdamW updates without saturation.

## 4. Latency Breakdown

- **Forward Propagation:** Average latency **177.5 ms** (Range: 152.7 ms – 224.7 ms).
- **Backward Propagation:** Average latency **286.3 ms** (Range: 277.4 ms – 296.1 ms).
- **Optimizer Step:**
  - Step 1 (Buffer Allocation): **1,261.6 ms** (AdamW allocates 1st and 2nd moment vectors for all 141.9M parameters, totaling ~1.13 GB).
  - Steps 2 & 3 (Steady State): **575.4 ms – 587.4 ms** (Average: **581.4 ms**).
- **Steady-State Step Latency:** **~1,145.4 ms** (~1.15 seconds per training sample).
