# TrustRAG Phase 09 — Architecture Assessment & Design

**Branch:** `phase-9` (branched cleanly from `phase-8 @ 9d01f19`, which originates from `phase-7 @ 1feb66f`)  
**Environment:** Offline Linux (`Python 3.14.9`, `aiohttp==3.14.5`, `pydantic==2.14.3`, `pydantic-settings==2.16.2`, `Node v26.13.0`, `npm 12.2.2`; `fastapi`/`uvicorn`/`torch`/`transformers` not installed offline)

---

## 1. Existing Architecture Inventory
1. **Serving Facade ([service.py](file:///home/aditya/rags/TrustRag/src/trustrag/serving/service.py)):**
   - `TrustRAGService`: Thread-safe (`RLock`) runtime wrapping `AdaptiveDefenseController`, `TrustRAGPipeline`, `SRMClient`, `TrustCalibrator`, `DriftMonitor`, and `AdaptationPolicyEngine`.
   - Exposes `initialize()`, `shutdown()`, `handle_query(ProductionQueryRequest)`, and `health() -> ServiceHealthStatus` (including `SRMBackendHealth`, `peak_rss_mib`, request/error/timeout counters).
2. **Core Defense Stages (Phase 08 Preserved):**
   - **G1 ([input_guardrail.py](file:///home/aditya/rags/TrustRag/src/trustrag/guardrails/input_guardrail.py), [paraphraser.py](file:///home/aditya/rags/TrustRag/src/trustrag/guardrails/paraphraser.py)):** Zero-width/NFKC normalization, injection/override detection (`ALLOW`/`FLAG`/`BLOCK`), optional controlled paraphrasing (`enable_paraphrasing=False` by default).
   - **G2 ([msd.py](file:///home/aditya/rags/TrustRag/src/trustrag/detection/msd.py), [signals.py](file:///home/aditya/rags/TrustRag/src/trustrag/detection/signals.py)):** 6-signal detector (`F1..F6`), `coverage_attenuated` missing-signal handling, `temp-train-v1` temperature calibration, majority-quorum `MINORITY_OUTLIER` attenuation, `removal_cap_ratio <= 0.5`.
   - **G3 ([output_verifier.py](file:///home/aditya/rags/TrustRag/src/trustrag/verification/output_verifier.py), [query_consistency.py](file:///home/aditya/rags/TrustRag/src/trustrag/verification/query_consistency.py)):** Atomic claim decomposition, evidence grounding (`SUPPORTED`/`CONTRADICTED`/`INSUFFICIENT_EVIDENCE`/`UNCERTAIN`), temporal/numeric/temperature conversions, query consistency, bounded re-answer (`enable_reanswer=False` by default).
   - **SRM ([client.py](file:///home/aditya/rags/TrustRag/src/trustrag/srm/client.py), [hf_local.py](file:///home/aditya/rags/TrustRag/src/trustrag/srm/hf_local.py), [registry.py](file:///home/aditya/rags/TrustRag/src/trustrag/srm/registry.py)):** `DeterministicFallbackBackend` active offline; `hf_local` registered (`BLOCKED` offline without `torch`/`transformers`).
3. **Configuration & Benchmarks:**
   - `Settings` + `configs/base.yaml`, `configs/adaptive/temperature_calibrator_v1.json`.
   - Verified benchmark artifact: `reports/phase08_comprehensive_benchmark.json` (static offline CPU-only baseline).
4. **Missing Layer:** No `src/trustrag/api/` HTTP API or `frontend/` dashboard existed prior to Phase 09.

---

## 2. Proposed API & UI Architecture

### 2.1 Framework Justification (Zero Unnecessary Dependencies)
- **Backend API:** **`aiohttp.web` (`aiohttp==3.14.5`) + Pydantic v2 (`2.14.3`)**.
  - *Justification:* `fastapi` and `uvicorn` are absent in the offline `.venv`, whereas `aiohttp` is already installed, provides native async HTTP routing, middleware (auth, CORS, security headers, `client_max_size`), non-blocking offloading of `TrustRAGService` via `asyncio.to_thread` + `asyncio.wait_for` timeouts, and `aiohttp.test_utils.TestClient` for deterministic integration testing without network access.
- **Frontend SPA:** **Modular ES6+ JavaScript + Semantic HTML5 + Responsive CSS3 (`frontend/`)**.
  - *Justification:* Running `npm install` for external React/Vite toolchains requires internet access unavailable offline. A zero-dependency ES-module SPA served directly by the TrustRAG API server works identically in dev and production offline, supports keyboard navigation, ARIA roles, strict XSS-safe DOM rendering (`textContent`), and unit testing via Node `v26.13.0` (`node --test`).

### 2.2 Components to Reuse vs Implement
- **Reused As-Is (Unmodified Core Defense):** `InputGuardrail`, `MultiSignalDetector`, `TrustAwareRetriever`, `OutputEvidenceVerifier`, `evaluate_query_consistency`, `TrustRAGPipeline`, `TrustRAGService`, `SRMClient`, `TrustCalibrator`, `Settings` / `load_config`.
- **Implemented in Phase 09 (`src/trustrag/api/` & `frontend/`):**
  1. `src/trustrag/api/schemas.py` — Typed Pydantic API request/response contracts + OpenAPI 3.1 JSON generator.
  2. `src/trustrag/api/audit.py` — Tamper-evident SHA-256 hash-chained `AuditLogStore` (JSONL + filtered query/pagination, no deletion/modification API, secret redaction).
  3. `src/trustrag/api/config_manager.py` — Whitelisted `RuntimeConfigManager` (`validate` diff preview, explicit `confirm=true` apply with JSON/YAML backup, `restore` defaults, non-weakenable security guardrails).
  4. `src/trustrag/api/monitoring.py` — Real-time latency percentile tracker (`p50/p95/p99` gated by minimum sample count `>= 5`) + explicit separation of live telemetry vs historical `phase08_comprehensive_benchmark.json`.
  5. `src/trustrag/api/security.py` — Bearer token auth (`TRUSTRAG_API_TOKEN`), strict CORS allowlist, CSP/nosniff/DENY headers, sliding-window rate limiter, safe error serialization.
  6. `src/trustrag/api/app.py` & `server.py` — `aiohttp.web` routes (`/api/v1/*`, `/openapi.json`, `/docs`, static `/`), graceful startup/shutdown hooks.
  7. `frontend/` — 8-view operational dashboard (Overview, G1 Security, G2 MSD 6-Signal Inspector, G3 Evidence Verification, SRM Health, Monitoring & Benchmarks, Safe Config Management, Audit Logs).

---

## 3. Security Boundaries & Data Flow
- **Trust Boundary:** Untrusted HTTP input -> `security.py` (payload cap `1 MiB`, rate limit, auth check on privileged/mutating routes, CORS) -> Pydantic schema validation -> `TrustRAGService` (`asyncio.wait_for` timeout) -> `InputGuardrail` -> `MultiSignalDetector` -> `OutputEvidenceVerifier` -> Public-safe DTOs (`safe_to_display` quarantine redaction).
- **Filesystem Isolation:** API never accepts arbitrary filesystem paths (`corpus_path`, `config_path`, `audit_path` are server-pinned). Config backups and audit JSONL write strictly to fixed subdirectories.
- **Explicitly Excluded:** Multi-tenant OAuth/SSO identity provider, live neural LLM/SRM weight downloading, arbitrary Python/YAML config injection, audit-log deletion endpoints, and synthetic metric generation.
