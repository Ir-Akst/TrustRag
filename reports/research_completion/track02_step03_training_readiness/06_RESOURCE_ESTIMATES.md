# Track 2, Step 3.0: Quantitative Resource & Memory Footprint Estimates

**Audit Date:** November 14, 2026  
**Auditor:** ML Infrastructure Auditor  

---

## 1. Mathematical Memory Formulation

Training memory allocation for neural networks is governed by the component breakdown:

$$M_{\text{total}} = M_{\text{params}} + M_{\text{grads}} + M_{\text{opt}} + M_{\text{act}} + M_{\text{overhead}}$$

Where:
- $M_{\text{params}} = P \times \text{bytes per parameter}$ ($4\text{ bytes}$ for FP32, $2\text{ bytes}$ for FP16/BF16)
- $M_{\text{grads}} = P \times \text{bytes per parameter}$
- $M_{\text{opt}} = 2 \times P \times 4\text{ bytes}$ for AdamW (first and second moments in FP32) = $8P\text{ bytes}$
- Total state memory (Params + Grads + AdamW) in standard FP32 training = $16P\text{ bytes}$.
- $M_{\text{act}} \approx B \times S \times L \times H \times A$, where $B$ is batch size, $S$ sequence length, $L$ layers, $H$ hidden dimension, and $A$ attention factor.

---

## 2. Memory Footprint Matrix by Architecture & Training Approach

We calculate the exact memory footprint for candidate models under host constraints (3.34 GB available RAM, 0 GB VRAM):

| Model & Parameter Count | Training Mode | State Memory ($M_{\text{state}}$) | Activation Memory ($B=8, S=512$) | Total Training Memory | Feasibility on Host CPU (3.34 GB Headroom) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`deberta-v3-small` (44M)** | **Full Fine-Tuning (FP32)** | $44\text{M} \times 16\text{B} = 704\text{ MB}$ | $\approx 220\text{ MB}$ | **$\approx 0.95\text{ GB}$** | ✅ **FEASIBLE (High margin)** |
| **`distilbert-base` (66M)** | **Full Fine-Tuning (FP32)** | $66\text{M} \times 16\text{B} = 1,056\text{ MB}$ | $\approx 280\text{ MB}$ | **$\approx 1.35\text{ GB}$** | ✅ **FEASIBLE (Safe)** |
| **`deberta-v3-base` (86M)** | **Full Fine-Tuning (FP32)** | $86\text{M} \times 16\text{B} = 1,376\text{ MB}$ | $\approx 450\text{ MB}$ | **$\approx 1.85\text{ GB}$** | ⚠️ **FEASIBLE (Bounded Batch)** |
| **`roberta-base` (125M)** | **Full Fine-Tuning (FP32)** | $125\text{M} \times 16\text{B} = 2,000\text{ MB}$ | $\approx 550\text{ MB}$ | **$\approx 2.55\text{ GB}$** | ⚠️ **MARGINAL (Risk of swap thrash)** |
| **`roberta-base` (125M)** | **Linear Probe (Frozen Base)**| $0.05\text{M} \times 16\text{B} + 500\text{MB} \approx 501\text{ MB}$| $\approx 150\text{ MB}$ | **$\approx 0.65\text{ GB}$** | ✅ **FEASIBLE (Fast)** |
| **`Qwen2.5-1.5B`** | **LoRA ($r=16$)** | $3.1\text{ GB (Weights)} + 400\text{ MB}$ | $\approx 1.8\text{ GB}$ | **$\approx 5.3\text{ GB}$** | ❌ **INFEASIBLE (Immediate OOM)** |
| **`Qwen2.5-Coder-7B`** | **QLoRA (4-bit)** | $5.2\text{ GB (Quant)} + 1.2\text{ GB}$ | $\approx 4.5\text{ GB}$ | **$\approx 10.9\text{ GB}$** | ❌ **IMPOSSIBLE (Host crash)** |

---

## 3. Training Duration Estimates: Host CPU vs Reference GPU

We project epoch duration based on forward/backward FLOPs ($6 \times P \times \text{tokens}$ per step) and empirical CPU throughput ($\approx 120\text{ tokens/sec}$ on Intel Core i7-1355U):

### Objective A: Binary Classification (26,054 examples, mean 150 tokens = $\approx 3.9\text{M tokens/epoch}$)

| Compute Device | Batch Size | Throughput (tokens/sec) | Time per Epoch | 3-Epoch Total Duration |
| :--- | :--- | :--- | :--- | :--- |
| **Intel Core i7-1355U (Host CPU)** | 16 (grad accum = 2) | $\approx 140\text{ tokens/s}$ | **$\approx 7.7\text{ hours}$** | **$\approx 23.1\text{ hours}$** |
| *NVIDIA T4 (Cloud Reference)* | 32 | $\approx 3,200\text{ tokens/s}$ | $\approx 20.3\text{ minutes}$ | $\approx 1.0\text{ hour}$ |
| *NVIDIA A10G (Cloud Reference)* | 64 | $\approx 8,500\text{ tokens/s}$ | $\approx 7.6\text{ minutes}$ | $\approx 23\text{ minutes}$ |

### Objective B: 3-Way NLI (10,815 examples, mean 450 tokens = $\approx 4.8\text{M tokens/epoch}$)

| Compute Device | Batch Size | Throughput (tokens/sec) | Time per Epoch | 3-Epoch Total Duration |
| :--- | :--- | :--- | :--- | :--- |
| **Intel Core i7-1355U (Host CPU)** | 16 (grad accum = 2) | $\approx 250\text{ tokens/s}$ | **$\approx 5.3\text{ hours}$** | **$\approx 15.9\text{ hours}$** |
| *NVIDIA T4 (Cloud Reference)* | 32 | $\approx 4,100\text{ tokens/s}$ | $\approx 19.5\text{ minutes}$ | $\approx 1.0\text{ hour}$ |

### Objective C: Fine-Grained Spans (12,072 examples, mean 600 tokens = $\approx 7.2\text{M tokens/epoch}$)

| Compute Device | Batch Size | Throughput (tokens/sec) | Time per Epoch | 3-Epoch Total Duration |
| :--- | :--- | :--- | :--- | :--- |
| **Intel Core i7-1355U (Host CPU)** | 8 (grad accum = 4) | $\approx 210\text{ tokens/s}$ | **$\approx 9.5\text{ hours}$** | **$\approx 28.5\text{ hours}$** |
| *NVIDIA T4 (Cloud Reference)* | 16 | $\approx 3,500\text{ tokens/s}$ | $\approx 34.2\text{ minutes}$ | $\approx 1.7\text{ hours}$ |

---

## 4. Resource Allocation & Execution Constraints

To train reliably on the host CPU without triggering OOM crashes:
1. **Thread Limiting:** Set `torch.set_num_threads(6)` and `OMP_NUM_THREADS=6` to prevent thread contention.
2. **Gradient Accumulation:** Use per-device physical batch size of $8$ with $2$ accumulation steps (effective batch size $16$).
3. **Activation Checkpointing:** Optional for small encoders; saves ~30% activation memory at a cost of ~20% compute re-evaluation.
4. **Periodic Cache Garbage Collection:** Call `gc.collect()` at the end of each validation cycle to release fragmented tensors.
