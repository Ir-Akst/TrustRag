# Production Performance & Neural Authenticity Verification

- **Cold-Start Latency:** **3147.43 ms**
- **Warm Mean Latency ($N=15$):** **963.35 ms** (vs. **2577.91 ms** in Phase 39 — **2.68x speedup**)
- **Warm P50 / P95 / P99:** **861.61 ms / 1318.88 ms / 1318.88 ms**
- **Peak RSS:** **842.38 MB**
- **Genuine PyTorch Forward Passes:** **57 `forward()` calls** across 60 batched NLI calls (**3.80 passes/request**).
- **Deterministic Pair Cache:** **148 hits / 212 misses** (only caches exact identical `(premise, hypothesis)` pairs under frozen `eval()` weights).
- **Lifecycle Stress:** Concurrency (8/8 OK), Timeout (`TIMEOUT` abstained), and Shutdown (`SERVICE_SHUTDOWN` abstained) all passed.
