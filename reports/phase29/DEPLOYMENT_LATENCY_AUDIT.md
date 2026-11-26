# Phase 29 — Deployment Latency Audit & Hardware Disclosure

---

## 1. Hardware & System Configuration

- **Platform:** Linux x86_64
- **CPU Architecture:** Multi-core Intel/AMD x86_64
- **PyTorch Thread Count:** 10 threads (`torch.set_num_threads(10)`)
- **CUDA Device:** `None (CPU Execution)`
- **Warmup Procedure:** 5 initial inference passes prior to latency recording.

---

## 2. Dual Deployment Latency Profiles

The manuscript must never report fallback latency as neural inference latency. The empirical benchmarks establish two distinct operational profiles:

| Operational Profile | Execution Mode | Active Backend | P50 (ms) | P90 (ms) | P95 (ms) | P99 (ms) | Neural FLOPs |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Profile 0: G1 Guardrail Standalone** | Production | Compiled Regex Normalizer | **$0.27$** | $0.39$ | $0.41$ | **$0.45$** | Zero |
| **Profile 1: End-to-End Pipeline (CPU Fallback)**| Production | `DeterministicFallbackBackend` | **$8.69$** | $10.91$ | $13.97$ | **$17.42$** | Zero |
| **Profile 2: Offline DeBERTa-v3 Neural NLI** | Offline Research | `NeuralNLISRMBackend` | **$46.46$** | $48.07$ | $49.27$ | **$53.01$** | Full Transformer Pass |

---

## 3. Disclosures for Publication

1. **Sub-10ms Pipeline**: TrustRAG achieves sub-10ms ($8.69$ ms median) end-to-end latency only when operating in deterministic fallback mode (`is_real_model = False`).
2. **Neural NLI Overhead**: Running real neural NLI inference on CPU introduces **$46.46$ ms** of latency per candidate pair, representing a $\approx 5\times$ latency increase over the deterministic baseline.
