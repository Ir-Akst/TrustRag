# TrustRAG — Track 2, Step 3.6: Resource Feasibility and Training Projections

## 1. Measured Benchmarks (Non-Training Operations)

- **Dataset Ingestion Throughput:** 10,815 records loaded and validated in **0.08 seconds** (130,881 rec/sec).
- **Forward Pass Latency (CPU, bs=1, seq_len=128):**
  * Median: **111.28 ms**
  * Mean: **221.40 ms**
- **Model Load Time (Offline from disk):** **0.81 seconds**.
- **Current Host Telemetry:**
  * Available Physical RAM: **6.5 GiB**
  * Free Swap Space: **3.4 GiB**
  * Available Disk Space: **44 GiB** on `/home/aditya/rags`

---

## 2. Resource Projections for Future Authorized Training

| Parameter | 1,000-Step Bounded NLI Pilot | Full NLI Training Epoch (10,815 steps) | Status / Basis |
| :--- | :---: | :---: | :--- |
| **Optimization Steps** | 1,000 steps | 10,815 steps | Configuration |
| **Batch Size** | 1 sample | 1 sample | CPU memory safety |
| **Step Time (fwd+bwd+opt)** | ~1.20 - 1.25 s/step | ~1.20 - 1.25 s/step | Measured empirically in Step 3.4.2 |
| **Estimated Wall-Clock Time** | **~21 - 25 minutes** | **~3.6 hours** | Projected |
| **Peak Resident Set Size (RSS)** | **~2,450 MB** | **~2,450 MB** | Streamed step memory is constant |
| **RAM Headroom Available** | **+4.0 GiB buffer** | **+4.0 GiB buffer** | Safe (Buffer > 50% total RAM) |
| **Swap Usage Risk** | Negligible (< 100 MB growth) | Low (< 250 MB growth) | Guarded by watchdog |
| **Watchdog Abort Threshold** | 700 MB available RAM | 700 MB available RAM | Hard cutoff active |

### Feasibility Conclusion
The host hardware possesses sufficient physical RAM (6.5 GiB available) and swap capacity (3.4 GiB free) to support a 1,000-step bounded NLI pilot safely on CPU without risking out-of-memory errors or system instability.
