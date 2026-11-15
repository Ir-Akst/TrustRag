# Track 2, Step 3.1: Host Resource Safety & Guardrail Specification

**Audit Date:** November 14, 2026  
**Auditor:** Independent ML Infrastructure Engineer  

---

## 1. Host Memory Pressure Analysis

The host machine displays severe memory paging:
- **Total Physical RAM:** 15.29 GB
- **Available Physical RAM:** 3.32 GB (21.7% of total)
- **Active Swap Space:** 5.86 GB total with **only 28.5 MB free (99.5% utilized)**.

### Operational Implication:
Because the Linux swap space is almost fully exhausted, the kernel has minimal capacity to page out dirty or anonymous pages. If any training or smoke test process attempts an unconstrained allocation exceeding available RAM, the kernel will not be able to page out additional background memory and will invoke the Linux OOM Killer (`kill -9`) immediately to terminate processes.

---

## 2. Hard Execution Guardrails for CPU Training

To ensure safety and reproducibility on this host, all future model training and testing must adhere to the following hard limits:

| Safety Parameter | Specified Hard Limit | Enforcement Mechanism |
| :--- | :--- | :--- |
| **Maximum Resident Set Size (RSS)** | **2.50 GB** | Process monitoring via `psutil` / Linux `ulimit -v` |
| **Worker Threads** | **`OMP_NUM_THREADS=4` to `6`** | Environment variable export & `torch.set_num_threads()` |
| **Batch Size (CPU Encoder)** | **Max 8 per step** | Gradient accumulation used for effective batch $\ge 16$ |
| **Sequence Length Truncation** | **Max 512 tokens** | Strict tokenizer clipping |
| **Thermal / Clock Ceiling** | **$\le 75^\circ\text{C}$ / Base TDP 15W** | `nice -n 10` execution priority |

---

## 3. Emergency Abort & Fallback Criteria

Any running process in `.venv-train` must be aborted immediately if any of the following conditions trigger:

1. **Available RAM drops below 1.0 GB** ($< 1,024\text{ MB}$).
2. **Process RSS exceeds 2.8 GB**.
3. **Swap thrashing occurs** (major page faults per second $> 100$).
4. **NaN or Inf values** detected in loss or gradient tensors.
5. **Thermal throttling forces CPU clock below 1.0 GHz**.

---

## 4. Safety Audit Verdict

The CPU environment architecture is deemed **SAFE FOR DISCRIMINATIVE ENCODERS (SMALL/BASE)** provided hard memory limits and thread bounds are strictly maintained. It is **UNSAFE FOR LARGE GENERATIVE MODELS (1.5B+)**, which will trigger immediate OS termination.
