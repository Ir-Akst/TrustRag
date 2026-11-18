# Track 2, Step 3.3 — Section 05: Resource Consumption and Telemetry

## 1. Process Memory Footprint (RSS)

- **Initial Process Footprint (Python startup):** 213.52 MB
- **Post-Model Load RSS:** 1,044.57 MB (DeBERTa-v3-small model in FP32 format)
- **Post-Forward Pass (Step 1):** 1,212.88 MB (Activation buffers)
- **Post-Backward Pass (Step 1):** 1,725.11 MB (Gradient buffers for 141.9M parameters)
- **Post-Optimizer Step (Step 1):** 2,316.62 MB (AdamW 1st & 2nd momentum buffers allocated)
- **Peak RSS Across Entire Pilot:** **2,369.99 MB** (~2.31 GB)
- **Final Post-Pilot Process RSS:** **2,336.48 MB**

## 2. Host RAM Availability & Safety Margin

| Milestone | Process RSS (MB) | Available Host RAM (MB) | Swap Used (MB) | Swap Free (MB) |
|-----------|:----------------:|:-----------------------:|:--------------:|:--------------:|
| Pre-Load | 213.5 | 6,122.5 | 2,647.9 | 3,352.0 |
| Post-Load | 1,044.6 | 5,644.2 | 2,647.9 | 3,352.0 |
| Step 1 Post-Opt | 2,316.6 | 4,609.4 | 2,848.6 | 3,151.4 |
| Step 2 Post-Opt | 2,370.0 | 4,597.4 | 2,848.6 | 3,151.4 |
| Step 3 Post-Opt | 2,336.5 | 4,629.6 | 2,848.6 | 3,151.4 |

- **Minimum Available RAM Observed:** **4,597.36 MB**
- **Safety Margin:** Maintained **3,897.36 MB** above the 700.0 MB abort threshold at all times.
- **Swap Drift:** +200.68 MB. Swap headroom remained stable at **> 3,151 MB**.

## 3. CPU Utilization and Concurrency

- Concurrency was explicitly restricted to 4 threads (`torch.set_num_threads(4)`).
- CPU utilization remained stable across the 4 pinned threads without spiking the remaining 8 threads of the host system.
