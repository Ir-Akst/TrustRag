# Latency and Deployment Truthfulness Audit

**Auditor:** Principal Performance Engineer & Independent ML Auditor  
**Hardware Platform:** Intel Core i7 / 12 Logical Cores / Linux x86_64

---

## 1. Truthfulness Disclosure: Live Serving vs Offline Research

> [!IMPORTANT]
> **Independent Audit Finding on Model Deployment:**
> The live TrustRAG API server (`src/trustrag/api/server.py`) operates with `SRMConfig.backend = "disabled"` and `verification_mode = "heuristic"`. Production inference uses the deterministic CPU fallback pipeline.
> The trained DeBERTa-v3-small checkpoint (`/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`) is evaluated strictly in offline research harnesses and is **not** actively loaded into the live HTTP serving memory space. Claims of live neural serving must not be conflated with the deterministic CPU production server.

---

## 2. Latency Benchmarks Across Execution Profiles

Benchmarked over 100 queries per profile under identical CPU load conditions:

| Execution Profile | Description | Active in Live Server | P50 (ms) | P90 (ms) | P99 (ms) | Mean (ms) | Min (ms) | Max (ms) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Profile 0: G1 Standalone** | G1 Input Guardrail (Regex + Normalization) | **Yes** | **0.2073** | 0.3849 | 0.6084 | 0.2334 | 0.1245 | 0.6084 |
| **Profile 1: Deterministic Serving** | Full Pipeline (G1 + TF-IDF Retrieval + G2 MSD + Gen) | **Yes** | **2.4684** | 24.1288 | 33.2299 | 11.0171 | 1.6893 | 33.2299 |
| **Profile 2: Offline Neural NLI** | DeBERTa-v3-small Forward Pass on CPU (batch=1, max_len=128) | **No** (Offline Only) | **72.2765** | 220.9812 | 343.4576 | 113.4828 | 42.5346 | 343.4576 |
| **Profile 3: Live Neural Serving** | Live Server with DeBERTa Active | **No** (Disabled) | N/A | N/A | N/A | N/A | N/A | N/A |

---

## 3. Hardware & Memory Resource Consumption

- **CPU Cores:** 12 logical cores (10 physical cores)
- **Baseline Memory RSS (Python + Pipeline):** 433.16 MB
- **Peak Memory RSS (Loading DeBERTa weights into RAM):** 780.96 MB
- **Memory Footprint Delta:** +347.80 MB
- **Throughput Capacity (Deterministic Pipeline):** ~400 queries/sec per CPU core.
- **Throughput Capacity (Neural CPU):** ~14 queries/sec per CPU core.
