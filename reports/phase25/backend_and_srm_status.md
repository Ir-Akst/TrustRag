# TrustRAG Phase 25: Backend Server & SRM Execution Status

**Status Date:** 2026-11-24  
**Audit Target:** Live TrustRAG API Daemon & Neural SRM Subsystem  
**Runtime Endpoint:** `http://127.0.0.1:8000`  

---

## 1. Backend Server Operational Status

The TrustRAG API service was launched and validated as an active daemon:
- **Binding Address:** `127.0.0.1:8000`
- **Application Framework:** Python `aiohttp` web server
- **Corpus Path:** `data/benchmarks/clean_rag/train.jsonl` (7 pre-indexed candidate documents)
- **Health Check Endpoint (`GET /health`):**
  ```json
  {
    "status": "healthy",
    "ready": true,
    "service": "TrustRAG",
    "version": "1.0.0-rc1",
    "timestamp": "2026-11-24T10:56:53.034725+00:00"
  }
  ```

---

## 2. SRM (Selective Risk Model) Execution Mode Truth

In accordance with strict research integrity and zero-fabrication standards:

### Crucial Architectural Truth:
1. **Model Checkpoint Immutability:**
   The DeBERTa-v3 NLI checkpoint at `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` is **strictly frozen** and preserved with a 100% SHA-256 hash match.
2. **Current Service Mode:**
   The backend API runtime operates SRM in **`deterministic_fallback`** mode (`is_real_model = False`).
3. **Guardrail vs Model Role:**
   - **G1 (InputGuardrail):** A deterministic, regex- and rule-based heuristic screening layer operating on user query text. G1 does NOT execute neural model inference; its operations are purely CPU-bound string normalization, pattern matching, and rule evaluation.
   - **G2 (MSD):** Multi-Signal Detection across 6 document-level signals (F1..F6).
   - **G3 / SRM:** Entailment verification between extracted claim and retrieved evidence.
4. **Honest Reporting Commitment:**
   At no point is the deterministic fallback described as neural inference. All latency measurements, architectural summaries, and API audits explicitly document `is_real_model: false`.

---

## 3. End-to-End API Route Validation

| Endpoint | Method | Input Sample | Expected Outcome | Actual Response | Status |
|---|---|---|---|---|---|
| `/health` | `GET` | N/A | Status: healthy | HTTP 200, healthy | **VERIFIED** |
| `/api/v1/g1/analyze` | `POST` | FN-01 Direct Injection | Decision: `BLOCK` | HTTP 200, `BLOCK`, Risk: 1.00 | **VERIFIED** |
| `/api/v1/g1/analyze` | `POST` | FN-03 Homoglyphs | Decision: `BLOCK` | HTTP 200, `BLOCK`, Risk: 0.98 | **VERIFIED** |
| `/api/v1/g1/analyze` | `POST` | Antivirus Inquiry | Decision: `ALLOW` | HTTP 200, `ALLOW`, Risk: 0.00 | **VERIFIED** |
| `/api/v1/g1/analyze` | `POST` | Debug Mode Probe | Decision: `FLAG` | HTTP 200, `FLAG`, Risk: 0.50 | **VERIFIED** |
| `/api/v1/srm/health` | `GET` | N/A | Mode status | HTTP 200, `deterministic_fallback` | **VERIFIED** |

All live API routes are operational and verified through HTTP integration tests.
