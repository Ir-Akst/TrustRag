# TrustRAG — Track 2, Step 3.14: Resource Feasibility & Training Cost Estimate

### 1. Hardware Inventory

- **Host Processor:** 13th Gen Intel(R) Core(TM) i7-1355U
- **Physical Cores:** 10 cores (2 Performance-cores with HyperThreading + 8 Efficient-cores)
- **Logical CPUs (Hardware Threads):** 12 logical CPUs
- **PyTorch Allocation:** `torch.set_num_threads(16)` (Software oversubscription: 16 threads across 12 hardware threads)

---

### 2. Bounded Pilot Training Cost Estimation (1,000 Optimizer Steps)

Estimates based on measured CPU forward-only latency (~2.00 s / sample in single 384; ~12.26 s / sample in multi-chunk):

| Architecture | Forward Latency | Forward + Backward + Step | 1,000 Optimizer Steps | Feasibility Status |
| :--- | :--- | :--- | :--- | :--- |
| **Single-Window 384 (Step 3.10 Remediated)** | ~2.00 s | ~4.50 s | ~4,500 s (**~1.25 hours**) | **FEASIBLE ON CPU** |
| **Multi-Chunk MIL (Bag Pooling, 4.35 chunks avg)** | ~12.26 s | ~25.00 s | ~25,000 s (**~6.94 hours**) | **MARGINAL ON CPU** |
| **Naive Chunk Expansion (~4,350 chunk steps)** | ~1.92 s | ~4.50 s | ~19,575 s (**~5.44 hours**) | **REJECTED (Corrupts Labels)** |

---

### 3. Memory Safety

- Single-window training peak RSS is estimated at **2.4–2.8 GB RAM**, well within the 15+ GB available system memory.
- Active watchdog thresholds (RAM >85%, Swap growth >500 MB) provide automated tripwire protection against memory degradation.
