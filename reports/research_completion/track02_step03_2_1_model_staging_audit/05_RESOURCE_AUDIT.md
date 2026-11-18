# Track 2, Step 3.2.1: Resource Audit & Memory Allocation Decomposition

**Audit Date:** November 14, 2026  
**Auditor:** Independent ML Infrastructure Auditor  

---

## 1. Measured Host Resource State

Telemetry measured directly via `/proc/meminfo` and `statvfs`:

| Resource Metric | Measured Host State | Assessment |
| :--- | :--- | :--- |
| **Total Physical RAM** | 16,029,880 kB (15.29 GB) | Base hardware installation. |
| **Available Physical RAM** | 3,014,912 kB (2.88 GB) | Effective unallocated physical memory buffer. |
| **Total Swap Space** | 6,143,996 kB (5.86 GB) | Paging partition on host SSD. |
| **Used Swap Space** | 6,143,580 kB (5.86 GB) | **99.99% Swap Exhausted (only 416 kB free).** |
| **Available Disk Storage**| 44.25 GB (294.23 GB filesystem)| 275 MB model snapshot accounts for $< 0.7\%$ of disk. |

---

## 2. In-Memory Resident Footprint Decomposition

A breakdown distinguishes empirical measurements from mathematical training projections:

```
[ In-Memory Footprint Component ]        [ Measured Status ]     [ Allocation Size ]
1. Python Runtime & C++ Shared Libs       Measured (Baseline)     ~14.3 MB -> ~230 MB
2. Pretrained Model Weights (FP16)        Measured (Post-Load)    ~284 MB (Net RSS: 514.9 MB)
3. Inference Activations (B=1, S=39)      Measured (Forward Pass) ~108 MB (Peak RSS: 623.1 MB)
---------------------------------------------------------------------------------------
4. Training Activations (B=8, S=512)      Projected               ~220 MB
5. Gradients (FP16/FP32)                  Projected               ~284 MB to ~568 MB
6. AdamW Optimizer States (FP32)          Projected               ~1,136 MB
---------------------------------------------------------------------------------------
Projected Full Training Peak RSS:         Theoretical             ~1.5 GB to ~1.8 GB
```

### Critical Distinction:
- **Empirically Measured in Step 3.2:**
  - Initial RSS: `14.33 MB`
  - Post-Load RSS: `514.92 MB`
  - Peak Forward Pass RSS: `623.10 MB`
- **Theoretical Training Estimates (Not Measured Yet):**
  - Gradient allocation: Requires $\approx 568\text{ MB}$ (if FP32 accumulation).
  - AdamW momentum & variance tensors: Requires $\approx 1,136\text{ MB}$.
  - Estimated Full Training RSS: $\approx 1.5\text{ to }1.8\text{ GB}$.

---

## 3. Training Feasibility & Guardrail Adherence

1. **Inference Safety:** Fully verified. Peak inference RSS (623.1 MB) left **2,618.7 MB** of available physical RAM untouched. Zero swap thrashing occurred.
2. **Forward/Backward Pilot Authorization:** Authorized for single-step pilot. An empirical measurement of actual backpropagation memory is required before multi-epoch training can be authorized.
3. **Multi-Epoch Training Caution:** Because swap is fully exhausted, multi-epoch training remains strictly unauthorized until a single-step full autograd pilot demonstrates that RSS does not exceed 2.2 GB.
