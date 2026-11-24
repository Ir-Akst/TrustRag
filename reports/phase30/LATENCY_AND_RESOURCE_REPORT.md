# Phase 30 — Deployment Latency & Resource Utilization Audit

---

## 1. Hardware & System Profiling Environment

- **Operating System:** Linux x86_64
- **Host CPU:** Multi-core Intel/AMD x86_64
- **PyTorch Threading:** Explicitly pinned to 10 threads (`torch.set_num_threads(10)`)
- **CUDA Hardware Acceleration:** `None (CPU Execution)`
- **Warmup Procedure:** 5 initial inference forward passes prior to latency metric collection.
- **Model Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`

---

## 2. Dual Deployment Latency Profiles

To preserve scientific rigor and research transparency, TrustRAG evaluates and discloses two distinct operational profiles:
1. **Production Serving Pipeline (Deterministic CPU Fallback)**: Real-time live serving mode using deterministic heuristics for low-latency production deployments.
2. **Offline Neural NLI Forward Pass**: Neural DeBERTa-v3 cross-encoder classification used in offline research validation.

### Empirical Latency Measurements:

| Operational Profile | Execution Mode | Active SRM Backend | Sample Count | P50 (ms) | P90 (ms) | P95 (ms) | P99 (ms) | Mean (ms) | FLOPs / Overhead |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Profile 0: G1 Standalone Guardrail** | Live Production | Compiled Regex Normalizer | 50 | **$0.15$** | $0.16$ | $0.16$ | **$0.50$** | $0.16$ | Minimal (CPU) |
| **Profile 1: End-to-End Pipeline** | Live Production | `DeterministicFallbackBackend`| 30 | **$1.70$** | $2.10$ | $2.77$ | **$4.49$** | $1.89$ | Zero Neural |
| **Profile 2: Offline DeBERTa-v3 Neural NLI**| Offline Research| `NeuralNLISRMBackend` | 20 | **$40.26$** | $43.97$ | $48.57$ | **$61.34$** | $41.95$ | Full Transformer Pass |

---

## 3. Resource Utilization & Memory Footprint

- **Baseline Peak Memory (RSS):** $343.47$ MiB (serving engine with full index).
- **Transformer Forward Pass Memory:** Adds $\approx 180$ MiB for DeBERTa model weights in memory.
- **CPU Utilization:** Controlled within allocated thread budget without saturating host CPU cores.

---

## 4. Publication Disclosures

1. **Sub-5ms End-to-End Serving**: The live production serving engine achieves a median P50 latency of **$1.70$ ms** (P99: $4.49$ ms) on standard CPU hardware when running in deterministic verification mode.
2. **Neural Model Latency Disclosure**: Real DeBERTa-v3 neural cross-encoder execution introduces **$40.26$ ms** of inference latency per claim-passage pair on CPU. Systems deploying neural SRM must account for this throughput budget or utilize GPU acceleration.
