# 09 — Answer Generator, Serving Layer, REST API & Frontend Audit

**Modules:** [generator.py](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/generation/generator.py), [service.py](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/serving/service.py), [app.py](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/api/app.py), [frontend/](file:///c:/Users/Dell/Desktop/trustrag/frontend/)
**API Inventory JSON:** [api_inventory.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/api_inventory.json)

---

## 1. Answer Generator (`YELLOW`, Readiness `40%`)

`TrustRAGGenerator` executes reliably as a deterministic extractive responder (`part2_subsystems.json`), but contains **no built-in generative LLM client**:

| Probe | Behavior Observed |
| :--- | :--- |
| `extractive` (default mode in `configs/base.yaml`) | Selects sentences verbatim with inline `[doc_id]` citations (`"Water freezes at 0 degrees Celsius. [d1] ... [d1]"`, `abstained=False`) |
| `llm_error_fallback` / `llm_no_callable` | Without a Python `llm_callable` argument (or if `llm_callable` raises), falls back to `"extractive_fallback"` copy-paste |
| `empty_docs` | Fails closed cleanly: `abstained=True`, `reason="NO_TRUSTED_EVIDENCE"` |

---

## 2. Serving Service & AIOHTTP REST API (`RED`, Readiness `15%`)

### Critical Windows Host Crash (`ModuleNotFoundError: No module named 'resource'`)
Importing any serving or API entry module crashes immediately at [service.py:7](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/serving/service.py#L7) because the Unix-only standard library `resource` module does not exist on Windows:

| Module Probed | Imported on Windows 11? | Exact Error |
| :--- | :---: | :--- |
| `trustrag.serving` | **No (`False`)** | `ModuleNotFoundError: No module named 'resource'` (`service.py:7`) |
| `trustrag.api` | **No (`False`)** | Same, transitive via `api/app.py:46 -> serving` |
| `trustrag.api.app` | **No (`False`)** | Same |
| `trustrag.api.server` | **No (`False`)** | Same |
| `trustrag.api.audit` | Yes (`True`) | Uses optional `fcntl` guard (`audit.py:21`), logs warning that multi-process file locking is disabled on Windows |
| `trustrag.api.monitoring` / `security` | Yes (`True`) | Clean pure-Python imports |

### CLI Impact
- `python -m trustrag.pipeline.cli --query "..."`: **Exit `0`** (`7.62 s` benign, `8.14 s` attack).
- `python -m trustrag.pipeline.cli --health`: **Exit `1`** (`8.44 s`) — crashes importing `trustrag.serving`. `--adaptive` is equally blocked.

### Verified Registered HTTP Routes (Static Code Inspection — Live Server `NOT VERIFIED` on Windows)
- `GET /api/v1/health` (`auth_exempt=True`), `GET /api/v1/srm/health`, `GET /api/v1/openapi.json`
- `POST /api/v1/pipeline/execute`, `POST /api/v1/query`, `POST /api/v1/g1/analyze`, `POST /api/v1/retrieval/evidence`, `POST /api/v1/g2/analyze`, `POST /api/v1/g3/verify`
- `GET /api/v1/monitoring/summary`, `GET /api/v1/audit/logs`, `GET /api/v1/config`, `PUT /api/v1/config`

Note also **dependency specification drift**: `pyproject.toml` lists `fastapi` and `uvicorn[standard]` under `api`, while `src/trustrag/api/` uses **`aiohttp`**.

---

## 3. Dashboard Frontend SPA (`YELLOW`, Readiness `70%`)

- **Test Execution:** `node --test frontend/tests/dashboard.test.mjs` exited **`0`** with **`5/5` tests passing** (`857 ms`).
- **Integration Reality:** Inspection confirms real `fetch('/api/v1/...')` API calls and safe DOM helpers (no static/mock telemetry arrays). Marked `YELLOW` strictly because the backend server cannot start on this Windows host, preventing live UI-to-API integration testing (`NOT VERIFIED` live).

