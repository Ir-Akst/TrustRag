# Track 2, Step 3.4.2 — Section 04: Resource Telemetry & Safeguard Audit

## 1. Safety Threshold Verification

All three active memory limits and wall-clock ceilings were strictly adhered to throughout the entire 1,000-step execution:

| Safeguard | Configured Limit | Realized Value During Run | Margin to Abort | Abort Status |
|-----------|:----------------:|:-------------------------:|:---------------:|:------------:|
| **Physical Available RAM** | $\ge 700.0\text{ MB}$ | **4,339.07 MB** (Lowest observed) | $+3,639.07\text{ MB}$ | **NO BREACH** |
| **Swap Growth from Baseline** | $\le 500.0\text{ MB}$ | **+11.91 MB** (Peak growth) | $+488.09\text{ MB}$ | **NO BREACH** |
| **Minimum Free Swap** | $\ge 1,000.0\text{ MB}$ | **3,549.42 MB** (Lowest free) | $+2,549.42\text{ MB}$ | **NO BREACH** |
| **Wall-Clock Duration** | $\le 1,800.0\text{ s}$ (30 min) | **1,293.4 seconds** (~21.56 min) | $+506.6\text{ s}$ (~8.4 min) | **NO BREACH** |
| **CPU Concurrency** | 4 threads | Fixed to 4 pinned threads | Monitored | **COMPLIANT** |

---

## 2. Memory Footprint Trajectory

- **Initial Process Footprint (Python startup):** 370.3 MB
- **Post-Model Load RSS (141.9M FP32 weights):** ~1,045 MB
- **Steady-State Process RSS (Steps 50–1,000):** Maintained between **2,354 MB and 2,444 MB**.
- **Peak RSS Observed Across Entire Run:** **2,444.55 MB** (~2.39 GB).
- **Post-Run Available Host RAM:** **5,061.0 MB** (Host exited with $> 5.0\text{ GB}$ free physical RAM).
