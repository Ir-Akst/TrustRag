# Track 2, Step 3.0: Hardware Inventory & Host Resource Audit

**Audit Date:** November 14, 2026  
**Auditor:** ML Infrastructure Auditor  
**Host Architecture:** x86_64 Linux  

---

## 1. Compute Infrastructure (CPU)

An exhaustive hardware probe was executed via `/proc/cpuinfo` and OS system utilities:

| Parameter | Observed Host Specification | Implication for Neural Training |
| :--- | :--- | :--- |
| **CPU Model** | 13th Gen Intel(R) Core(TM) i7-1355U | Modern mobile/ultrabook Raptor Lake architecture. |
| **Physical Cores** | 10 Cores (2 Performance-cores + 8 Efficient-cores) | Heterogeneous compute; P-cores support AVX2/FMA, E-cores handle auxiliary I/O. |
| **Logical Threads** | 12 Execution Threads | Thread scheduling must be pinned (OMP_NUM_THREADS=4 to 8) to avoid thread thrashing. |
| **Base / Boost Clock** | 1.70 GHz (Base) / Up to 5.00 GHz (Max Turbo) | Thermal throttling expected under sustained 100% all-core workload (15W base TDP). |
| **SIMD Extensions** | SSE4.2, AVX, AVX2, FMA3, Intel DL Boost (AVX-VNNI) | Accelerated INT8/FP32 matrix multiplication supported; no AVX-512. |
| **Hardware Virtualization**| VT-x / VMX present | Container and sandbox execution supported without hardware virtualization overhead. |

---

## 2. Memory Subsystem (RAM & Swap)

Memory inspection via `/proc/meminfo` and kernel telemetry reveals severe existing memory pressure:

| Metric | Measured Value | Percentage of Total | Operational Assessment |
| :--- | :--- | :--- | :--- |
| **Total System RAM** | 16,029,880 kB (15.29 GB) | 100.0% | Standard desktop/laptop memory pool. |
| **Free Physical RAM** | 1,563,696 kB (1.49 GB) | 9.8% | Low immediate unallocated buffer. |
| **Available Physical RAM** | 3,500,648 kB (3.34 GB) | 21.8% | Maximum head-room for non-swapping allocation. |
| **Total Swap Space** | 6,143,996 kB (5.86 GB) | 100.0% | Configured paging partition on SSD. |
| **Free Swap Space** | 91,056 kB (0.09 GB) | 1.5% | **Critical Alert: 98.5% of swap is currently consumed.** |

> [!CAUTION]
> **Swap Saturation Warning:** The host operating system currently has over 5.77 GB of memory paged out to swap. Launching any process requiring more than 2.5 GB of resident set size (RSS) will induce immediate page-fault thrashing, severe CPU stall cycles, or invoke the Linux Out-Of-Memory (OOM) Killer.

---

## 3. Accelerator Infrastructure (GPU / NPU)

A diagnostic scan for accelerators was conducted:
- `which nvidia-smi`: Command not found (return code 127).
- Kernel module check: No `nvidia`, `amdgpu`, or `habanalabs` modules loaded.
- PyTorch CUDA check: Not applicable (PyTorch not installed).
- GPU Count: **0**
- Total VRAM: **0.00 GB**
- CUDA / ROCm / MPS Runtime: **Unavailable**

**Verdict:** The system is an exclusively CPU-bound platform. All neural tensor operations, forward passes, backpropagation passes, and optimizer updates must execute via host CPU threads.

---

## 4. Persistent Storage Subsystem

Storage capacity was evaluated using `statvfs` on the workspace filesystem:

| Filesystem Mount | Total Capacity | Free / Available Space | Utilization % | Assessment |
| :--- | :--- | :--- | :--- | :--- |
| `/home/aditya` (ext4) | 294.23 GB | 46.07 GB | 84.3% | Sufficient headroom for small encoder models and datasets. |
| Sandbox virtual mount | 7.70 GB | 7.70 GB | 0.0% | Local isolation sandbox mount. |

### Storage Budget for Training:
- Dataset storage required (`sft_v2` all variants): ~0.15 GB (Already staged).
- Small encoder checkpoint (`deberta-v3-small` / `distilbert`): ~0.25 to 0.50 GB per checkpoint.
- 5 checkpoint saves + optimizer states: ~3.0 GB to 5.0 GB.
- **Available storage (46.07 GB) is completely adequate for discriminative model training.**
- Storing multiple full generative checkpoints (1.5B–7B models @ 3GB–14GB each) would quickly exhaust the remaining 46 GB.

---

## 5. Practical Execution & Resource Limits

Under host constraints, the practical limits for reproducible training on this host are:
1. **Maximum Resident Memory per Process:** $\le 2.50\text{ GB}$ (to prevent OOM killer triggering).
2. **Maximum Model Parameter Count on CPU:** $\le 100\text{M parameters}$ (e.g., DistilBERT, DeBERTa-v3-small, MiniLM).
3. **Recommended Execution Threads:** `OMP_NUM_THREADS=4` to `6` (utilizing the 2 P-cores and selected E-cores to minimize context switching latency).
4. **Thermal Envelope:** Continuous training jobs exceeding 4 hours will likely encounter CPU thermal downclocking from 5.0 GHz turbo to 1.7–2.2 GHz base clock.
