# 15 — Deployment, Packaging & Resource Audit

**Host Measured:** `Windows-11-10.0.26200-SP0` | System Python `3.13.14` | `.venv313` (missing `sklearn`, `aiohttp`)
**Verdict:** `RED`

---

## 1. Deployment Readiness & Infrastructure Gaps

| Artifact / Requirement | Status on Disk | Impact & Audit Evidence |
| :--- | :---: | :--- |
| `Dockerfile` / `docker-compose.yml` / Kubernetes manifests | **Missing (`0`)** | No container build, Linux runtime target, healthcheck, or deployment automation exists |
| CI/CD workflows (`.github/workflows/*`) | **Missing (`0`)** | No automated test, lint, mypy, or security gate runs on commits |
| Windows cross-platform support (`serving` & `evaluation`) | **`RED` (Crash)** | `import resource` (`serving/service.py:7`, `evaluation/suites.py:1843`) raises `ModuleNotFoundError` on Windows |
| Audit log file locking (`api/audit.py:21`) | **Degraded** | `fcntl` fallback logs a warning disabling multi-process locking on Windows; concurrent writers risk interleaving |
| `pyproject.toml` vs code (`aiohttp` vs `fastapi`/`uvicorn`) | **Drifted** | `pyproject.toml` declares `fastapi`/`uvicorn[standard]` instead of `aiohttp`; `requirements.txt` omits `scikit-learn` & `aiohttp` |
| Offline `wheelhouse/` completeness | **Incomplete** | `65` wheels present, but omits `scikit-learn`, `aiohttp`, `torch`, `transformers`, and `faiss-cpu` |

---

## 2. Measured Resource Footprint (CPU / RAM / Latency)

All memory and timing probes ran purely on host CPU without GPU acceleration:

| Probe Run | Start RSS (MB) | End RSS (MB) | Measured Latency |
| :--- | :---: | :---: | :--- |
| Spec Validation Suite (`run_all_validations.py`) | `—` | `—` | `cold_import_init_ms = 22,101.71 ms` (`22.1 s` import cold start), `warm_p50 = 19.222 ms` |
| Subsystem Probes (`part2`) | `323.27` | `334.16` | G1: `0.24 – 8.27 ms`; Retriever (70 docs): `37.44 ms` index / `6.58 ms` query; G2: `5.55 ms`; G3: `5.81 – 11.73 ms` |
| E2E 10 Cases + BoolQ `n=15` (`part3`) | `317.32` | `319.73` | E2E cases: `0.721 ms` (G1 block) – `30.988 ms` (`04_poisoned`); BoolQ mean: `27.242 ms` |
| CLI Subprocess Cold Invocations (`part5`) | `—` | `—` | `cli_benign`: `7,621.29 ms` (`exit 0`), `cli_attack`: `8,135.60 ms` (`exit 0`), `cli_health`: `8,443.55 ms` (`exit 1`) |

**Deployment Blockers Summary:**
1. One-shot CLI scripts pay `~7.6 – 8.1 s` cold Python + `scikit-learn` import startup overhead per invocation.
2. Persistent serving (`trustrag.api.server` / `TrustRAGService`) is completely non-launchable on Windows until POSIX `resource` limits are guarded with `sys.platform` / try-except fallback, and `aiohttp` + `scikit-learn` are declared in `pyproject.toml` and `requirements.txt`.

