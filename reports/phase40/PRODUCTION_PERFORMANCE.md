# Production Neural Inference & Performance Report

**Service:** `TrustRAGService` Profile B (Live DeBERTa-v3-small CPU).

- **Cold-Start Latency:** **2401.91 ms** (vs. 8652.65 ms in Phase 39)
- **Warm Mean Latency ($N=15$):** **804.05 ms** (vs. 2577.91 ms in Phase 39 — **3.2x speedup**)
- **Warm P50 / P95:** **803.23 ms / 851.14 ms**
- **Genuine Neural Forward Passes:** **57 PyTorch `forward()` calls** across 60 batched NLI calls on 15 warm requests (3.8 batched forward passes/request vs. 24 sequential passes/request previously).
- **Peak RSS Memory:** **861.68 MB**
