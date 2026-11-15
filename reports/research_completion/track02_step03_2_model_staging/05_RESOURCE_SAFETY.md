# Track 2, Step 3.2: Resource Safety & Memory Telemetry Audit

**Audit Date:** November 14, 2026  
**Auditor:** Senior ML Infrastructure Engineer  
**Staged Model Target:** `microsoft/deberta-v3-small` (141.9M Parameters)  

---

## 1. Memory Overhead: Model Staging vs Runtime Inference

The physical footprint of model staging was measured:
- **Persistent Disk Storage:** ~286 MB (Weights) + ~2.4 MB (SPM model) + metadata $\approx 290\text{ MB}$.
- **Disk Utilization Impact:** Disk free space changed from 44.54 GB to ~44.25 GB ($< 0.7\%$ impact).
- **Staging Safety:** Fully compliant with host disk constraints; $> 44\text{ GB}$ remains available.

---

## 2. In-Memory Resident Footprint (Inference vs Full Training)

| Operational Mode | Parameter Precision | State Memory | Activation Memory ($B=1, S=128$) | Total Process RSS | Host Available RAM Headroom |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Model Load & Idle Evaluation** | FP32 (Params only) | $\approx 568\text{ MB}$ | $0\text{ MB}$ | **$\approx 850\text{ to }950\text{ MB}$** | **$\approx 2.4\text{ to }2.6\text{ GB}$ (SAFE)** |
| **Inference Forward Pass ($B=1$)** | FP32 (No grad) | $\approx 568\text{ MB}$ | $\approx 15\text{ MB}$ | **$\approx 920\text{ to }980\text{ MB}$** | **$\approx 2.3\text{ to }2.5\text{ GB}$ (SAFE)** |
| **Full Fine-Tuning Step ($B=8$)** | FP32 (Params + Grads + AdamW) | $\approx 2,272\text{ MB}$ | $\approx 220\text{ MB}$ | **$\approx 2.5\text{ to }2.8\text{ GB}$** | **$\approx 0.5\text{ to }0.8\text{ GB}$ (TIGHT)** |

---

## 3. Host Swap Saturation Warning & Guardrails

- The host operating system operates with **99.9% swap consumption (only ~6 MB free)**.
- **Safety Verdict for Step 3.2:**
  - Loading the model and executing a single forward pass without autograd consumes $\le 1.0\text{ GB}$ RSS, which is **completely safe** and well within the 3.5 GB available physical RAM.
  - Zero swap paging occurs during inference.
- **Guardrail for Future Training:**
  - Full backward passes and AdamW updates must enforce physical batch size $\le 4$ (with gradient accumulation) and thread pinning (`OMP_NUM_THREADS=4`) to stay within 2.2 GB resident memory.
