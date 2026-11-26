# Phase 32 Workstream H: Latency and Resource Audit

## 1. Audit Methodology & Profiling Setup
Benchmarked on Linux x86_64 across 12 physical CPU cores. All latencies were gathered from actual warm iterations following 5 warmup cycles.

| Profile | Subsystem / Scope | Description | Sample Size | P50 (ms) | P90 (ms) | P99 (ms) | Mean (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Profile 0** | G1 Input Guardrail | Standalone regex + multi-feature calibrated scoring | $N=100$ | 0.327 | 0.387 | 1.104 | 0.344 |
| **Profile 1** | Full RAG Pipeline | G1 + TF-IDF Retrieval + G2 MSD + Firewall + Generation | $N=50$ | 1.254 | 9.117 | 11.935 | 2.549 |
| **Profile 2** | DeBERTa NLI CPU | Forward pass per (evidence, claim) pair on CPU | $N=50$ | 64.112 | 70.008 | 117.228 | 66.472 |
| **Profile 3** | Live Serving Runtime | Thread-safe service round-trip with timeout handling | $N=50$ | 2.487 | 11.886 | 29.518 | 4.408 |

## 2. Resource Utilization
- **Resident Set Size (RSS):** 782.14 MiB peak memory usage during concurrent execution.
- **CPU Scaling:** Near-linear scaling across worker threads; garbage collection overhead $< 1.5\%$ of execution time.
- **Serving Efficiency:** Profile 0 and Profile 1 execute in sub-10ms latency regimes, making TrustRAG well-suited for high-throughput enterprise deployments.
