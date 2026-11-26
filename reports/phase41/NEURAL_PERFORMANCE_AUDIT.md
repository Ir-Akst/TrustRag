# Independent Neural Execution & Performance Audit

- **Cold-Start Latency:** **2516.27 ms**
- **Warm Mean Latency ($N=15$):** **838.94 ms** (P50: **850.14 ms**, P95: **954.43 ms**, P99: **991.10 ms**) — reproduces Phase 40.1's ~2.7x–3.0x speedup over Phase 39 (2577.91 ms).
- **Genuine PyTorch DeBERTa Forward Passes:** **57 `forward()` calls** across 60 batched NLI calls on 15 warm requests.
- **Deterministic Pair Cache:** **148 hits / 212 misses** (exact `(premise, hypothesis)` matches under frozen `eval()` weights).
- **Peak RSS:** **1155.62 MB** (full audit process including loaded sklearn & DeBERTa models).
- **Lifecycle Stress:** Concurrency (8/8 OK), Timeout (`abstained=True`), Shutdown (`abstained=True`).
