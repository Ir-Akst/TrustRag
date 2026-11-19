# TrustRAG — Project-Wide Architecture Audit

**Date:** 2026-11-19T03:26:00+05:30  
**Auditor:** Principal Software Engineer & ML Systems Architect  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `application-integration`  
**Base Release:** `trustrag-v1.0.0-rc1` (`531bff32745ede1bd1b38609cc6daf653d3eff24`)  

---

## 1. System Overview and Architecture Topology

TrustRAG is an enterprise-grade, secure Retrieval-Augmented Generation (RAG) defense framework designed to eliminate knowledge-base poisoning, adversarial prompt injection, and hallucinations through a layered defense pipeline:

- **G1 (Input Guardrail):** Sanitizes user queries, strips command delimiters, detects base64 and urlsafe evasions, and applies adaptive query paraphrasing.
- **G2 (Multi-Signal Detector - MSD):** Evaluates retrieved document passages across orthogonal security signals ($F_1$ through $F_6$: heuristic signatures, perplexity divergence, semantic drift, structural entropy, provenance trust, and cross-document agreement).
- **G3 (Evidence & Output Verifier):** Performs claim decomposition and rigorous natural language inference (NLI) using a calibrated, frozen neural DeBERTa-v3-small checkpoint supplemented with numeric and polarity consistency verification.
- **SRM (Security & Reliability Monitor):** Controls fail-safe degradation, circuit breaking, fallback policies, and health telemetry.
- **Control Plane & Operational Dashboard:** A lightweight, dependency-free vanilla modern SPA served via a secure asynchronous REST API (`aiohttp`), offering operational visibility, interactive testing, configuration management, and hash-chained audit logging.

---

## 2. Component-by-Component Inventory

### 2.1 Frontend Architecture
- **Framework:** Vanilla Modern ES2022 JavaScript SPA with zero client-side npm build dependencies.
- **Entry Point:** `frontend/index.html` referencing `/src/app.js` and styling `/styles.css`.
- **Module Structure:**
  - `frontend/src/app.js`: Application lifecycle, view routing, real-time connectivity status polling, and DOM event orchestration.
  - `frontend/src/api.js`: Strongly-typed `TrustRAGApiClient` handling asynchronous REST requests, Bearer token injection, and structured `ApiError` propagation.
  - `frontend/src/views.js`: Modular view renderers for Overview, G1 Input Security, G2 Multi-Signal Analysis, G3 Evidence Verification, SRM Health, Monitoring, Configuration, and Audit Logs.
  - `frontend/src/formatters.js`: Sanitized rendering utilities, latency formatters, and decision tone color mapping with strict XSS prevention (`el()` DOM text nodes).
- **Testing:** Node.js native test runner (`node --test tests/*.test.mjs`), validating XSS immunity, signal representation, and error decoding.

### 2.2 Backend Architecture
- **Framework:** Python asynchronous web application using `aiohttp` and `pydantic` v2 schemas.
- **Entry Points:**
  - CLI Server Runner: `src/trustrag/api/server.py` (`python -m trustrag.api.server`).
  - Application Factory: `src/trustrag/api/app.py` (`create_app()`).
- **Middleware & Security:**
  - `trustrag/api/security.py`: Bearer token authentication, sliding-window rate limiting per client IP, global exception handling, secure CORS headers, and path traversal prevention.
- **Audit Logging:**
  - `trustrag/api/audit.py`: Append-only, SHA-256 hash-chained JSONL audit ledger (`AuditLogStore`) guaranteeing tamper evidence.
- **Runtime Configuration:**
  - `trustrag/api/config_manager.py`: Live parameter mutation with atomic rollback, diff validation, and multi-version snapshots.

### 2.3 Retrieval & Security Pipeline
- **Retriever:** `trustrag/retrieval/retriever.py` implementing `TrustAwareRetriever` with lexical BM25 and vector-space scoring over verified document corpora.
- **G1 Input Guard:** `trustrag/guardrails/input_guardrail.py` implementing regex scanning, base64/url-adjacent decoding, length caps, and paraphrasing dispatch.
- **G2 Multi-Signal Detector:** `trustrag/detection/msd.py` and `trustrag/detection/signals.py` computing weighted fusion scores and individual signal telemetry ($F_1$ through $F_6$).
- **G3 Output Verifier:** `trustrag/verification/output_verifier.py` implementing claim extraction, numeric anomaly detection, and neural NLI verification.

### 2.4 Neural NLI & Checkpoint Loading
- **Model Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`
  - Architecture: `DebertaV2ForSequenceClassification` (6 layers, 12 attention heads, hidden size 768).
  - Checkpoint files verified bit-for-bit via SHA-256 manifest: `model.safetensors`, `config.json`, `tokenizer.json`, `tokenizer_config.json`.
- **Inference Engine:** `OutputEvidenceVerifier` in `src/trustrag/verification/output_verifier.py`.
  - Backends: `heuristic`, `neural_nli`, and `hybrid` (neural scoring + numeric validation).
  - Forward pass executes locally on CPU/GPU via Hugging Face `transformers` and `torch`.

### 2.5 Database & Persistence
- **Audit Storage:** Local append-only cryptographically chained JSONL files (`logs/audit_events.jsonl`).
- **Configuration Snapshots:** Versioned YAML/JSON files under `configs/`.
- **Corpus Storage:** Structured JSONL files (`data/raw/` and `data/processed/`).

### 2.6 Deployment Configuration
- **Containerization:** `Dockerfile` (Python multi-stage container) and `docker-compose.yml`.
- **Environment Management:** Environment-based overrides via `TRUSTRAG_HOST`, `TRUSTRAG_PORT`, `TRUSTRAG_CORPUS_PATH`, `TRUSTRAG_AUDIT_LOG`, and `.env`.

---

## 3. Integration & API Endpoint Inventory

| HTTP Method | Route | Description | Status |
|---|---|---|:---:|
| `GET` | `/health` | Lightweight service health ping | *To be aligned* |
| `GET` | `/api/v1/health` | Comprehensive multi-subsystem health status | **Active** |
| `GET` | `/api/v1/status` | Runtime status & model backend readiness | *To be aligned* |
| `POST` | `/api/v1/verify` | Unified end-to-end RAG verification endpoint | *To be aligned* |
| `POST` | `/api/v1/security/scan` | Pre-retrieval G1 & G2 security scan | *To be aligned* |
| `POST` | `/api/v1/evidence` | Evidence registration and corpus ingestion | *To be aligned* |
| `POST` | `/api/v1/g1/analyze` | G1 input sanitization analysis | **Active** |
| `POST` | `/api/v1/g2/analyze` | G2 passage multi-signal scoring | **Active** |
| `POST` | `/api/v1/g3/verify` | G3 proposition-level evidence verification | **Active** |
| `POST` | `/api/v1/evidence/retrieve` | Semantic evidence retrieval | **Active** |
| `POST` | `/api/v1/pipeline/execute` | End-to-end pipeline execution | **Active** |
| `GET` | `/api/v1/monitoring/metrics` | Latency, throughput, and error metrics | **Active** |
| `GET` | `/api/v1/config` | Read runtime configuration | **Active** |
| `POST` | `/api/v1/config/apply` | Apply runtime configuration modifications | **Active** |
| `GET` | `/api/v1/audit/logs` | Query tamper-evident audit ledger | **Active** |
| `GET` | `/openapi.json` | OpenAPI 3.1 schema specification | **Active** |
| `GET` | `/docs` | Interactive API documentation | **Active** |

---

## 4. Architectural Readiness Verdict

The TrustRAG codebase is mature, well-factored, and robust. The existing `aiohttp` web server and vanilla frontend architecture should be maintained without rewriting. Enhancements will focus strictly on exposing the unified routes required by Phase 5 (`GET /health`, `GET /api/v1/status`, `POST /api/v1/verify`, `POST /api/v1/security/scan`, `POST /api/v1/evidence`), hooking the neural model loader cleanly into the service pipeline, and enriching the frontend dashboard controls to support all required verification actions.

