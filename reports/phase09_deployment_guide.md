# TrustRAG Phase 09 — Production Deployment & Operations Guide

## 1. Tested Deployment Environment
- **OS / Runtime:** Linux CPU-only (`Python 3.14.9`, `aiohttp==3.14.5`, `pydantic==2.14.3`, `Node v26.13.0`)
- **Offline Operation:** Requires zero internet access, GPU, or downloaded LLM weights (`DeterministicFallbackBackend` executes cleanly).

---

## 2. Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `TRUSTRAG_ENV` | `development` | Set to `production` to enforce mandatory `TRUSTRAG_API_TOKEN`. |
| `TRUSTRAG_API_TOKEN` | *(unset)* | Bearer / `X-API-Key` token required in `production` mode. |
| `TRUSTRAG_HOST` | `127.0.0.1` | Bind address (`127.0.0.1` behind reverse proxy recommended). |
| `TRUSTRAG_PORT` | `8000` | HTTP port serving both `/api/v1/*` and the UI SPA at `/`. |
| `TRUSTRAG_CORS_ORIGINS` | *(empty)* | Comma-separated allowed origins (empty = same-origin only). |
| `TRUSTRAG_CORPUS_PATH` | *(auto boolq/demo)* | Optional path to local JSONL corpus (`limit=100` indexed at startup). |
| `TRUSTRAG_AUDIT_LOG` | `logs/audit_events.jsonl` | Append-only SHA-256 hash-chained audit JSONL file. |

---

## 3. Startup, Health Check & Shutdown

### Development Setup
```bash
PYTHONPATH=src /home/aditya/rags/.venv/bin/python -m trustrag.api.server --host 127.0.0.1 --port 8000 --env development
```

### Production Startup (Verified on `127.0.0.1:18090`)
```bash
export TRUSTRAG_ENV=production
export TRUSTRAG_API_TOKEN="replace-with-strong-random-token"
PYTHONPATH=src /home/aditya/rags/.venv/bin/python -m trustrag.api.server --host 127.0.0.1 --port 8000 --env production
```
*(After `pip install -e . --no-build-isolation`, `trustrag-api` console script is also available.)*

### Health & API Verification
```bash
curl -fsS http://127.0.0.1:8000/api/v1/health
curl -fsS -H "Authorization: Bearer $TRUSTRAG_API_TOKEN" http://127.0.0.1:8000/api/v1/srm/health
```
- **Graceful Shutdown:** Send `SIGTERM` (`kill -TERM <pid>`). `aiohttp` runs `on_cleanup`, calling `TrustRAGService.shutdown()` cleanly (verified exit code `0`).

---

## 4. Backup & Recovery Guidance
- **Configuration Backups:** Every confirmed update or restore writes a timestamped snapshot `configs/backups/config_backup_<UTC>_<seq>.json`. Restore defaults anytime via `POST /api/v1/config/restore` with `{"confirm": true}`.
- **Audit Log Retention:** Back up `logs/audit_events.jsonl` regularly; verify chain integrity via `GET /api/v1/audit/logs` (`chain_valid: true`).
