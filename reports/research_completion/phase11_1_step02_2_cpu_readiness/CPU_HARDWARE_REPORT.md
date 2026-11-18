# TrustRAG — Phase 11.1, Step 2.2: CPU Hardware Characterization & Topology Audit

## 1. Executive Hardware Specification

This report documents the physical and architectural characteristics of the target execution platform for DeBERTa-v3-small sequence classification training in a CPU-only environment.

| Parameter | Specification / Measured Metric | Architectural Context |
| :--- | :--- | :--- |
| **Processor Model** | 13th Gen Intel(R) Core(TM) i7-1355U | Raptor Lake U-series (Mobile / Ultrabook) |
| **Microarchitecture** | Golden Cove (P-core) + Gracemont (E-core) | Heterogeneous Hybrid x86_64 |
| **Physical Cores** | 10 Physical Cores | 2 Performance Cores (P-cores) + 8 Efficient Cores (E-cores) |
| **Logical Threads** | 12 Execution Threads | 2 P-cores $\times$ 2 threads (SMT) + 8 E-cores $\times$ 1 thread |
| **Base / Max Frequency** | 1.70 GHz base / 5.00 GHz max turbo | P-cores boost to 5.00 GHz; E-cores boost to 3.70 GHz |
| **Vector Extensions** | AVX, AVX2, FMA3, AVX-VNNI | Lacks AVX-512; supports 256-bit vector operations |
| **NUMA Topology** | 1 NUMA Node (Node 0: CPUs 0–11) | Unified memory addressing; zero NUMA node traversal penalty |
| **Host Total RAM** | 15,654 MB (~15.3 GiB) | LPDDR5 / DDR5 unified physical memory |
| **Host Total Swap** | 5,999 MB (~5.86 GiB) | Linux swap space on NVMe storage |
| **Dedicated GPU** | None Available | Training executes strictly on CPU in IEEE FP32 |

---

## 2. Microarchitecture & Core Topology

Inspection of `/sys/devices/system/cpu` and `lscpu -e` demonstrates the heterogeneous distribution of processing resources:

```
Core ID   Logical CPUs   Core Type       Base / Max Clock     L1d / L1i Cache      L2 Cache
---------------------------------------------------------------------------------------------
Core 0    CPU 0, 1       P-core (SMT)    400 / 5000 MHz       48K / 32K per core   1.25 MiB
Core 1    CPU 2, 3       P-core (SMT)    400 / 5000 MHz       48K / 32K per core   1.25 MiB
Core 2    CPU 4          E-core          400 / 3700 MHz       32K / 64K per core   2.00 MiB cluster
Core 3    CPU 5          E-core          400 / 3700 MHz       32K / 64K per core   shared w/ Core 2-5
Core 4    CPU 6          E-core          400 / 3700 MHz       32K / 64K per core   shared w/ Core 2-5
Core 5    CPU 7          E-core          400 / 3700 MHz       32K / 64K per core   shared w/ Core 2-5
Core 6    CPU 8          E-core          400 / 3700 MHz       32K / 64K per core   2.00 MiB cluster
Core 7    CPU 9          E-core          400 / 3700 MHz       32K / 64K per core   shared w/ Core 6-9
Core 8    CPU 10         E-core          400 / 3700 MHz       32K / 64K per core   shared w/ Core 6-9
Core 9    CPU 11         E-core          400 / 3700 MHz       32K / 64K per core   shared w/ Core 6-9
---------------------------------------------------------------------------------------------
Unified L3 Cache: 12.0 MiB shared across all 10 cores
```

### 2.1 Cache Hierarchy & Memory Bandwidth Constraints
- **L1 Cache:** 352 KiB L1 Data + 576 KiB L1 Instruction total.
- **L2 Cache:** 6.5 MiB total (1.25 MiB dedicated to each P-core; 2.0 MiB shared across each 4-core E-cluster).
- **L3 Cache:** 12 MiB unified Smart Cache.
- **Implication for Deep Learning:** Transformer attention heads and dense projection matrices ($W_q, W_k, W_v, W_o$) for DeBERTa-v3-small (768 hidden dimensions) exceed the L2 cache per core during matrix multiplications, making memory bus throughput and vector register efficiency critical bottlenecks.

---

## 3. Empirical PyTorch Intra-Op Thread Benchmarking

In earlier steps, the training runner arbitrarily set:
`torch.set_num_threads(16)`
On a system with only 12 logical execution units, this induced severe thread oversubscription, context switching jitter, and cache line invalidation.

To determine the mathematically optimal thread allocation, an empirical benchmark of forward and backward passes was conducted directly on the target machine with DeBERTa-v3-small (Sequence Length = 384 tokens, Batch Size = 1):

| Configured Threads | Target Allocation | Measured Time / Pass | Relative Throughput | Observations |
| :---: | :--- | :---: | :---: | :--- |
| **4** | P-cores only (4 SMT threads) | **1.718s** | 1.00$\times$ | High clock (5 GHz) but underutilizes 8 E-cores |
| **8** | P-cores + 4 E-cores | **1.368s** | 1.26$\times$ | Substantial parallel scaling |
| **10** | **Physical core count (2P + 8E)** | **1.317s** | **1.30$\times$** | **Optimal throughput; eliminates SMT latency** |
| **12** | All logical threads (SMT + E) | **1.345s** | 1.28$\times$ | Slight regression due to P-core SMT thread contention |
| **16** | **Previous runner setting** | **2.002s** | **0.86$\times$** | **Severe 34.2% regression due to thread oversubscription** |

### 3.1 Hardware Topology Audit Conclusion
1. **Oversubscription Penalty:** Setting 16 threads degraded execution velocity by **34.2%** (from 1.317s to 2.002s per step).
2. **Optimal Setting:** The physical core count of **10 threads** (`torch.set_num_threads(10)`) delivers the lowest execution latency by assigning exactly one worker thread per physical compute core, entirely bypassing hyperthreaded resource contention on the P-cores.
3. **Inter-Op Parallelism:** `torch.set_num_interop_threads(1)` is optimal to ensure execution graph sequencing does not spawn conflicting worker threads.

