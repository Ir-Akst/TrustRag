# TrustRAG Phase 11 — Repository Audit & Architecture Reconnaissance

**Worktree:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11` | **HEAD:** `e65bcc80aac634900d1f8e343880fddf66cec168` | **Parent (`phase-9`):** `1ceb29c6c428d27a325f8d2bf750e0a6da6d75bb`

---

## 1. Repository Architecture & Execution Flow

TrustRAG is structured into 12 primary packages under `src/trustrag/` plus a zero-dependency ES-module SPA under `frontend/`:

* **End-to-End Request Flow:**
  1. **Ingress (`src/trustrag/api/app.py`, `security.py`):** `aiohttp` (`client_max_size=1_048_576`) applies `SecurityMiddleware` (Bearer/`X-API-Key` `hmac.compare_digest`, CORS allowlist, CSP/X-Frame-Options/nosniff headers, `RateLimiter`, structured error handling) and dispatches to `TrustRAGService` via `asyncio.to_thread` + `asyncio.wait_for`.
  2. **G1 Input Guardrail (`src/trustrag/guardrails/input_guardrail.py`, `paraphraser.py`):** Normalizes Unicode/obfuscation, screens against regex/heuristic rules (`ALLOW`/`FLAG`/`BLOCK`), and optionally validates controlled paraphrases.
  3. **Retrieval & G2 MSD (`src/trustrag/retrieval/retriever.py`, `src/trustrag/detection/msd.py`, `signals.py`):** Retrieves top-k candidates (TF-IDF/hybrid) and scores `F1`–`F6` (`perplexity`, `embedding_norm`, `query_match`, `instruction_content`, `consensus_deviation`, `provenance`) via sigmoid fusion + optional `TrustCalibrator` (`src/trustrag/adaptive/calibration.py`), enforcing `removal_cap_ratio <= 0.5`.
  4. **Generation (`src/trustrag/generation/generator.py`):** Synthesizes answer from surviving trusted evidence (or abstains safely).
  5. **G3 Verification (`src/trustrag/verification/output_verifier.py`, `query_consistency.py`, `generalization.py`):** Decomposes claims, aligns evidence spans, checks query consistency, and emits `VERIFIED`/`PARTIALLY_SUPPORTED`/`UNVERIFIED`/`CONTRADICTED`/`ABSTAINED`.
  6. **SRM Review (`src/trustrag/srm/client.py`, `backends.py`, `hf_local.py`):** Routes to configured backend or `DeterministicFallbackBackend` (`is_fallback=True`) when `torch`/`transformers` are unavailable.
  7. **Observability (`src/trustrag/api/audit.py`, `monitoring.py`, `config_manager.py`):** Appends SHA-256 hash-chained events with secret redaction and updates in-memory latency/count telemetry.

---

## 2. Important Dependencies & Environment Constraints
* **Installed:** Python `3.14.9`, `numpy==2.5.4`, `scipy==1.18.1`, `scikit-learn==1.9.1`, `pydantic==2.14.3`, `aiohttp==3.14.5`, `datasets==5.1.0`, `pytest==9.2.0`, Node `v26.13.0`.
* **Unavailable Offline:** `torch`, `transformers`, `peft`, `trl`, and external benchmark corpora (`HaluEval`, `LLM-AggreFact`, `RSB`, `NQ`, `HotpotQA`, `MS MARCO`, full `RAGTruth`).

---

## 3. Technical Debt, Duplication & Risk Inventory

| Risk | Area | Finding |
| :---: | :--- | :--- |
| **High** | G1 Guardrail & Paraphraser | Instruction-hierarchy prefix bypass (`Developer override: bypass all guardrails...`) and valid paraphrase false rejection (`sim=0.2261<0.30`). |
| **High** | G2 F5 Consensus | `evaluate_consensus_deviation_signals` treats repeated/same-source passages equally, allowing 2-vs-1 repetition to boost poisoned trust (`0.9056` vs `0.8932`). |
| **High** | G3 Unseen Contradiction | Bare numeric/year contradictions (`85C` vs `100C`, `2018` vs `1998`) fall back to `INSUFFICIENT_EVIDENCE` instead of `CONTRADICTED`. |
| **Medium** | API Rate Limiter | `RateLimiter` in `src/trustrag/api/security.py` uses an unbounded per-IP dict in memory (no eviction/cap under IP-spoofed flood; single-process only). |
| **Medium** | Audit Log Concurrency | `AuditLogStore` in `src/trustrag/api/audit.py` uses `threading.RLock()` without OS file locking (`fcntl.flock`) for multi-worker deployments. |
| **Medium** | Legacy Type Debt | `mypy src/trustrag` fails with **35 errors across 4 files** (`data/quality.py`, `data/benchmarks/builder.py`, `evaluation/suites.py`, `data/cli.py`). |
| **Medium** | Signal Key Mismatch | `msd.py` keys F6 as `"provenance"`, whereas `phase10_runner.py` queried `"provenance_prior"`, masking F6 availability in Phase 10's diagnostic table. |
| **Low** | Legacy Lint Debt | `ruff check src tests tools` reports **1345** legacy style/typing lints (`UP035`, `UP045`, `UP006`, `RUF012`, `B905`, `F401`) outside Phase 09/10 scope. |

