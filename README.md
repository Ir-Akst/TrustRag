# TrustRAG — Trustworthy Retrieval-Augmented Generation Security Platform

[![TrustRAG Release](https://img.shields.io/badge/release-v1.0.0--rc1-blue.svg)](https://github.com/Ir-Akst/TrustRag)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-brightgreen.svg)](pyproject.toml)
[![Architecture](https://img.shields.io/badge/architecture-G1%20%E2%86%92%20G2%20%E2%86%92%20G3%20%E2%86%92%20SRM-orange.svg)](docs/architecture.md)
[![Verification](https://img.shields.io/badge/verification-DeBERTa--v3--small--NLI-purple.svg)](models/trained/)

TrustRAG is a research-grade, production-ready Retrieval-Augmented Generation (RAG) security framework designed to protect language model applications against prompt injection, knowledge-base poisoning, hallucinated claims, and conflicting context.

TrustRAG pairs pre-retrieval and in-retrieval multi-signal security screening with real-time neural Natural Language Inference (NLI) claim verification, backed by a tamper-evident audit log and an interactive operational dashboard.

---

## Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │              User Query                │
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │   G1: Input Guardrail & Sanitization   │
                      │   (Prompt Injection & Risk Scoring)    │
                      └──────────────────┬─────────────────────┘
                                         │ [Clean Query]
                                         ▼
                      ┌────────────────────────────────────────┐
                      │       Trust-Aware Corpus Search        │
                      └──────────────────┬─────────────────────┘
                                         │ [Candidate Passages]
                                         ▼
                      ┌────────────────────────────────────────┐
                      │  G2: Multi-Signal Detector (MSD F1-F6) │
                      │  (Poisoning & Conflict Filtering)      │
                      └──────────────────┬─────────────────────┘
                                         │ [Admissible Evidence]
                                         ▼
                      ┌────────────────────────────────────────┐
                      │           Answer Generation            │
                      └──────────────────┬─────────────────────┘
                                         │ [Candidate Answer]
                                         ▼
                      ┌────────────────────────────────────────┐
                      │    G3: Output Evidence Verifier        │
                      │    (DeBERTa-v3-small NLI + Numeric)    │
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │      SRM (Self-Reasoning Module)       │
                      │   (HalluGuard / Fallback Arbitration)  │
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
                                   Final Output:
                         [ALLOW / BLOCK / ABSTAIN]
```

### Defense Layers

1. **G1 — Input Guardrail:**
   Pre-retrieval defense analyzing incoming user prompts for direct and indirect prompt injection, instruction override patterns, delimiter manipulation, and adversarial jailbreaks. Blocks malicious prompts before retrieval or LLM execution.
2. **G2 — Multi-Signal Detector (MSD F1–F6):**
   In-retrieval candidate screening assessing passages across 6 orthogonal signals:
   - **F1:** Source Credibility & Provenance
   - **F2:** Retrieval Confidence & Text Alignment
   - **F3:** Intra-Corpus Semantic Consistency & Polarity Conflict
   - **F4:** Cross-Source Agreement
   - **F5:** Linguistic & Stylistic Anomaly Detection
   - **F6:** Temporal Freshness & Metadata Validation
3. **G3 — Output Evidence Verifier (Neural NLI + Numeric Conflict Engine):**
   Post-generation verification decomposing candidate answers into atomic factual claims, executing neural NLI cross-examination against retained evidence using a fine-tuned **DeBERTa-v3-small NLI** checkpoint. Enforces strict contradiction precedence (`p_con >= 0.20`), numeric/unit conflict checking, and entailment thresholding (`p_ent >= 0.50`).
4. **SRM — Self-Reasoning Module:**
   Secondary reasoning arbitration engine supporting configurable HTTP backends and deterministic fallback to guarantee zero unverified information leakage.

---

## Full-Stack Operational Dashboard

TrustRAG includes a single-page application (SPA) dashboard served directly by the backend web server with zero external CDN dependencies:

- **1. Overview & Verification:** Interactive testing console to submit user queries, inspect retrieved passages, view real-time G1/G2/G3 verdicts, examine atomic claim classifications (ENTAILMENT / CONTRADICTION / NEUTRAL), and inspect final ALLOW / BLOCK / ABSTAIN decisions.
- **2. G1 Input Security:** Detailed inspection of prompt injection risk scores, triggered heuristic patterns, and query sanitization traces.
- **3. G2 Multi-Signal (F1–F6):** Real-time candidate passage assessment table displaying trust scores, poisoning flags, and signal weights.
- **4. G3 Evidence & Claims:** Deep dive into atomic claim decomposition, neural NLI probabilities (`p_ent`, `p_con`, `p_neu`), and numeric conflict detection.
- **5. Corpus & Ingestion:** Live evidence ingestion form allowing operators to add verified reference documents directly to the active corpus.
- **6. SRM Backend Health:** Service status, fallback diagnostics, and latency percentiles.
- **7. Monitoring & Benchmarks:** System telemetry, request throughput, error tracking, and benchmark evaluation summaries.
- **8. Configuration:** Dynamic runtime parameter inspection, schema validation, and config updates with automatic JSON backup.
- **9. Audit Logs:** Tamper-evident, filterable audit event stream recording all security decisions and execution latencies.

---

## Unified REST API Reference

The backend exposes a high-performance REST API with comprehensive OpenAPI 3.1 documentation available at `/docs` and `/openapi.json`.

### Core Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Lightweight service liveness probe |
| `GET` | `/api/v1/status` | Comprehensive runtime, model checkpoint, and subsystem status |
| `POST` | `/api/v1/verify` | Unified end-to-end RAG verification with real neural inference |
| `POST` | `/api/v1/security/scan` | Pre-retrieval G1 and G2 security screening |
| `POST` | `/api/v1/evidence` | Ingest factual evidence documents into active retrieval corpus |
| `POST` | `/api/v1/pipeline/execute` | Execute complete integrated TrustRAG pipeline |
| `GET` | `/api/v1/monitoring/metrics` | Measured runtime telemetry and performance counters |
| `GET` | `/api/v1/config` | Inspect active configuration snapshot |
| `POST` | `/api/v1/config/apply` | Apply validated runtime configuration changes |
| `GET` | `/api/v1/audit/logs` | Query filtered audit logs |

### Verification Request Example (`POST /api/v1/verify`)

```bash
curl -X POST http://localhost:8000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{
    "query": "At what temperature does water boil?",
    "evidence": ["At standard atmospheric pressure, pure water boils at 100 degrees Celsius."],
    "answer": "Water boils at 100 degrees Celsius at sea level.",
    "enable_neural": true
  }'
```

**Response:**
```json
{
  "request_id": "a1b2c3d4e5f6",
  "query": "At what temperature does water boil?",
  "decision": "ALLOW",
  "answer": "Water boils at 100 degrees Celsius at sea level.",
  "g1_result": {"decision": "ALLOW", "risk_score": 0.0, "blocked": false},
  "g2_result": {"evaluated_count": 1, "retained_count": 1, "mean_trust_score": 0.95},
  "g3_result": {
    "status": "SUPPORTED",
    "claims": [
      {
        "claim_id": "claim_1",
        "claim_text": "Water boils at 100 degrees Celsius at sea level.",
        "outcome": "SUPPORTS",
        "verdict": "SUPPORTED",
        "confidence": 0.8401,
        "explanation": "Entailed by retrieved evidence (Neural NLI Entailment (p_ent=0.8401 >= 0.50))."
      }
    ]
  },
  "verification_mode": "hybrid",
  "neural_model_loaded": true,
  "execution_time_ms": 146.4,
  "timestamp": "2026-11-19T00:00:00Z"
}
```

---

## Frozen Neural Model Checkpoint

The neural verifier is powered by a fine-tuned DeBERTa-v3-small Natural Language Inference model located at:
```
/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch
```

### Checkpoint Integrity Verification

To cryptographically verify all 8 checkpoint weights and config files:

```bash
cd /home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch
sha256sum -c checksums.sha256
```

All 8 files will report `OK`:
- `added_tokens.json: OK`
- `config.json: OK`
- `model.safetensors: OK`
- `special_tokens_map.json: OK`
- `spm.model: OK`
- `tokenizer_config.json: OK`
- `tokenizer.json: OK`
- `training_args.bin: OK`

---

## Quick Start & Local Setup

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/Ir-Akst/TrustRag.git
cd TrustRag

# Create Python virtual environment (Python 3.10+ recommended)
python3 -m venv .venv
source .venv/bin/activate

# Upgrade packaging tools and install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment configuration:
```bash
cp .env.example .env
```

### 3. Launch Backend & Dashboard

```bash
python -m trustrag.api.server --host 127.0.0.1 --port 8000 --frontend-dir frontend
```

The application is now accessible:
- **Interactive UI Dashboard:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **OpenAPI Schema:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## Test Suite Execution

TrustRAG contains comprehensive unit, frontend, and integration test suites:

### 1. Python Unit & Integration Tests
```bash
PYTHONPATH=.:src pytest tests/unit/test_unified_api_endpoints.py tests/unit/test_phase_09_api.py tests/unit/test_phase12_step02_neural_g3.py tests/unit/test_phase_09_fullstack_integration.py -v
```

### 2. Frontend Unit Tests (Node.js Test Runner)
```bash
cd frontend
node --test tests/*.test.mjs
```

### 3. Live End-to-End Integration Test
```bash
PYTHONPATH=.:src python scripts/e2e_integration_test.py
```

---

## Production Deployment (Docker)

### Docker Build & Run

```bash
# Build multi-stage container
docker build -t trustrag:v1.0.0-rc1 .

# Run container
docker run -d \
  --name trustrag-service \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  trustrag:v1.0.0-rc1
```

### Docker Compose

```bash
docker compose up -d
docker compose ps
docker compose logs -f trustrag-api
```

---

## Security Policy & Reproducibility

- **Fail-Safe Principle:** If any model or backend component becomes unavailable, the system safely abstains (`ABSTAIN`) rather than producing unverified output.
- **Zero Fabrication:** Metrics, signal scores, and verification decisions are strictly derived from executable artifacts. Unavailable signals are reported as `UNAVAILABLE` rather than imputed.
- **Model Immutability:** Pre-trained and fine-tuned checkpoints are treated as strictly immutable and read-only.
- **Cryptographic Auditability:** Every pipeline run generates SHA-256 integrity hashes recorded in the structured audit trail.

---

## License

Apache-2.0 License. See [LICENSE](LICENSE) for details.
