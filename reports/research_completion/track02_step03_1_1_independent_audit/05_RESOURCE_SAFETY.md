# Track 2, Step 3.1.1: Resource Safety Assessment & Training Feasibility

**Audit Date:** November 14, 2026  
**Auditor:** Independent ML Infrastructure Auditor  

---

## 1. Dissecting Readiness Levels

A rigorous ML infrastructure audit requires decoupling high-level readiness into four distinct operational tiers:

```
[ Tier 1: Generic PyTorch Runtime ] ──► VERIFIED & READY
              │
              ▼
[ Tier 2: Pretrained Encoder Loading ] ─► BLOCKED (Missing Weights on Disk)
              │
              ▼
[ Tier 3: Forward/Backward Single-Step ] ─► CONDITIONALLY READY (Math Validated)
              │
              ▼
[ Tier 4: Multi-Epoch Training ] ───────► CONDITIONALLY READY (Requires Memory Guardrails)
```

### Detailed Evaluation of the Four Tiers:

### Tier 1: Generic PyTorch Runtime Readiness — `READY`
- **Current State:** The Python 3.10 virtual environment (`.venv-train`) has a fully operational, CPU-optimized installation of PyTorch (`2.14.1+cpu`), Transformers (`5.20.2`), and Accelerate (`1.15.0`).
- **Telemetry:** Basic CPU tensor arithmetic, multi-threaded GEMM matrix multiplication, autograd backward passes, AdamW optimization steps, and checkpoint I/O are 100% verified.
- **Verdict:** Fully established and functional.

### Tier 2: Pretrained Encoder Loading Readiness — `BLOCKED`
- **Current State:** There are **zero** model files or tokenizers for `microsoft/deberta-v3-small` stored anywhere locally.
- **Offline Constraint:** TrustRAG's `engine_config.py` explicitly forbids runtime remote downloading (`local_files_only: True`). Any attempt to invoke `from_pretrained("microsoft/deberta-v3-small")` will throw an immediate `ProviderError`.
- **Verdict:** Blocked pending authorized out-of-band staging into `/home/aditya/rags/models/pretrained/`.

### Tier 3: Forward/Backward Training Readiness — `CONDITIONALLY_READY`
- **Current State:** The mathematical feasibility of training a 141.9M parameter model on this host has been modeled:
  - Base Model Parameters (FP32): $\approx 568\text{ MB}$
  - Gradients (FP32): $\approx 568\text{ MB}$
  - AdamW Optimizer States: $\approx 1,136\text{ MB}$
  - Peak Resident Set Size (RSS): $\approx 1.5\text{ to }1.8\text{ GB}$.
- **Host Headroom:** Host available RAM is **3.34 GB**. The 1.8 GB memory footprint fits within the available physical RAM, leaving ~1.5 GB headroom.
- **Verdict:** Conditionally ready once weights are staged, provided a bounded batch size ($\le 8$) is used.

### Tier 4: Full Multi-Epoch Training Readiness — `CONDITIONALLY_READY`
- **Current State:** The host system's swap space is **99.9% consumed (only 48 kB free)**. If physical memory is exceeded, the kernel cannot page out memory and will invoke the Linux OOM Killer immediately.
- **Required Guardrails for Full Training:**
  1. `torch.set_num_threads(4)` to prevent thread contention across P-cores and E-cores.
  2. Physical batch size $\le 8$ with gradient accumulation = 2 (effective batch size 16).
  3. Periodic garbage collection (`gc.collect()`) after validation cycles.
  4. Sequence length capped at 512 tokens.

---

## 2. Assessment of Step 3.1 Pilot Claims

The Step 3.1 completion report claimed that a 3-step pilot established that:
- Peak RSS was only 420.6 MB.
- Throughput was 78.1 tokens/second.

**Auditor Finding:**
1. The 420.6 MB RSS was measured on a **0.48M parameter toy model**, not the 141.9M DeBERTa target model.
2. The 78.1 tok/s throughput represents toy matrix operations, not the 298x more compute-intensive DeBERTa operations.
3. Therefore, the Step 3.1 pilot **does not validate the resource safety of real DeBERTa-v3-small**. Real DeBERTa-v3-small will consume ~3.5–4.5x more memory (~1.5–1.8 GB) and have lower throughput (~15–25 tokens/s on CPU).
