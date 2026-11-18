# TrustRAG — Track 2, Step 3.13: Forward-Only Resource Profile Audit

### 1. Hardware Topology Reconciliation

The audit independently inspected `/proc/cpuinfo` and `lscpu`:
- **CPU Model:** 13th Gen Intel(R) Core(TM) i7-1355U
- **Sockets:** 1
- **Physical Cores:** 10 cores (2 Performance-cores with HyperThreading + 8 Efficient-cores)
- **Logical CPUs (Hardware Threads):** 12 threads
- **Base/Max Clock:** 1.7 GHz / 5.0 GHz

> [!IMPORTANT]
> The Step 3.12 report described execution on a "16-Core Intel CPU". The physical hardware is an **Intel Core i7-1355U with 10 physical cores and 12 logical CPUs**.
> PyTorch was configured with `torch.set_num_threads(16)`, creating a software oversubscription of 4 threads over the 12 available logical CPUs.

---

### 2. CPU Forward Latency & Memory Verification

- **Execution Constraints:** `torch.no_grad()`, `model.eval()`, FP32 precision, offline weights.
- **Empirical Measurements (50 Validation Samples / 320 Chunks):**
  - Single-Window 384 Total Time: 100.17 s (2,003.36 ms / sample)
  - Multi-Chunk 384 Total Time: 613.16 s (12,263.27 ms / sample)
  - Measured Per-Chunk Latency: 1,916.14 ms (~1.92 s)
  - Latency Multiplier: 6.12x (reflecting an average of 6.4 chunks/sample across the 50-sample evaluation slice)
  - Peak Resident Set Size (RSS): 1.84 GB – 1.91 GB
  - Peak Swap Allocation Growth: **0.0 MB**

---

### 3. Engineering Assessment

1. **Forward Feasibility:** CPU execution is memory-safe (<2.0 GB RSS) with zero swap growth.
2. **Latency Tradeoff:** Real-time inference on CPU requires ~1.92 s per chunk. Full validation set inference (11,849 chunks) would require ~6.3 hours on CPU, but under 20 minutes on an NVIDIA RTX/A100 GPU using batched tensor evaluation ($[B \times K, L]$).
