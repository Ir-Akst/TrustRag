# Production Neural Inference & Lifecycle Audit

**Service Audited:** `TrustRAGService` (`src/trustrag/serving/service.py`) with `ProductionQueryRequest`.  
**Instrumentation:** Hooked both `EvidenceGroundedVerifier._predict_nli_pair` and the underlying HuggingFace `DeBERTa` model's `forward()` method.

## 1. Profile A (Deterministic Fallback) vs. Profile B (Live Neural DeBERTa)

| Metric | Profile A (Deterministic) | Profile B (Neural DeBERTa CPU) |
|---|---|---|
| Cold-Start Latency | 81.325 ms | **8652.653 ms** (includes model load + 24 passes) |
| Warm Requests Audited | 20 | 15 |
| Warm Forward Passes / Request | 0 | **24.0** (360 NLI calls, 496 torch forwards) |
| G1 Mean Latency | — | **1.906 ms** |
| Neural NLI Mean / Request | 0 ms | **2505.935 ms** (**104.414 ms / pass**) |
| Full Request Mean Latency | 56.435 ms | **2577.909 ms** |
| P50 / P90 / P95 / P99 (ms) | 56.25 / 57.62 / 58.61 / 58.61 | **2545.24 / 2856.56 / 2936.24 / 2948.62** |
| Process CPU Time (Profile B) | — | **406.923 s** |
| Peak RSS Memory | — | **777.93 MB** (+437.80 MB delta) |

## 2. Lifecycle Stress Verification
- **Concurrency (12 mixed Profile A/B threads, 4 workers):** 12/12 completed cleanly (`OK` / `ABSTAINED`).
- **Timeout (`request_timeout_seconds=0.0001`):** Returned `status=ERROR`, `g1_decision=TIMEOUT`, `abstained=True`.
- **Cancellation:** Queued `Future.cancel()` succeeded cleanly without corrupting active worker state.
- **Shutdown:** `service.shutdown()` followed by query returned `status=ERROR`, `g1_decision=SERVICE_SHUTDOWN`, `abstained=True`.
