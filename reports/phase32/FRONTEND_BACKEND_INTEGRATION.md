# Phase 32 Workstream G: Frontend & Backend Integration

## 1. Architectural Alignment
TrustRAG's FastAPI serving layer (`src/trustrag/api/server.py`) and runtime service (`src/trustrag/serving/service.py`) provide end-to-end telemetry consumption for both CLI clients and web frontends:

1. **Structured Telemetry Schema:**
   - Every inference response contains `inference_mode`, indicating whether the answer was generated via deterministic execution or verified by neural DeBERTa CPU forward passes.
   - Guardrail risk assessments include matched threat families, calibrated probabilities, and audit content hashes.
   - Quarantined document segments include sentence-level provenance records detailing why each clause was isolated.

2. **UI Safety Contract:**
   - Responses blocked by G1 or quarantined by G2/Firewall are flagged with `safe_to_display: false`.
   - The UI displays sanitized error explanations rather than raw malicious payloads or internal stack traces.

3. **Production Telemetry Verification:**
   - API endpoints (`POST /query`, `GET /health`, `POST /verify_answer`) were validated for schema conformance, UTF-8 normalization, and thread safety.
