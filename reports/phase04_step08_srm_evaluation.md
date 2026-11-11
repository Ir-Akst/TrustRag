# TrustRAG Phase 04 — Step 8: SRM (Small Reasoning Model) Evaluation

**Date:** 2026-11-11  
**Component Evaluated:** `SRMClient` (`src/trustrag/srm/client.py`) & `src/trustrag/srm/backends.py`

---

## 1. Backend Availability Inventory (Strictly Verified)

| Backend Category | Availability Status | Evidence Observed |
|---|---|---|
| **Trained HalluGuard Checkpoint** | **NOT AVAILABLE** | Zero `.pt` / `.safetensors` / `.gguf` checkpoints present in repository |
| **Local Ollama (`local_ollama`)** | **UNAVAILABLE** | `http://localhost:11434/api/tags` returned `ConnectError` |
| **External API (`openai_compatible`)** | **UNCONFIGURED / NOT EXECUTED** | `OPENAI_API_KEY` and `TRUSTRAG_LLM_OPENAI_API_KEY` unset; zero external API calls claimed |
| **Deterministic Fallback (`DeterministicFallbackBackend`)** | **AVAILABLE** | Active default (`halluguard-srm-fallback`, `backend="disabled"`) |

---

## 2. Deterministic Fallback Evaluation (`data/benchmarks/hallucination`, $N=11$)

| Metric | Observed Result (`halluguard-srm-fallback`) | Notes |
|---|---|---|
| **Agreement with G3** | **1.0000 (11 / 11)** | Deterministic fallback synthesizes G3 claim outcomes + G2 trust scores directly |
| **Justification Validity Rate** | **1.0000 (11 / 11)** | Non-empty `reasoning_trace` and per-claim `rationale` on all cases |
| **Structured Output Validity Rate** | **1.0000 (11 / 11)** | Valid `verdict` enum + confidence $\in [0, 1]$ |
| **Fallback Rate** | **1.0000** | 100% fallback execution |
| **Classification Accuracy / Macro-F1** | `0.2727` / `0.2889` | Identical to G3 alone (`SUPPORTED` F1 `0.3333`, `CONTRADICTED` F1 `0.3333`, `NOT_ENOUGH_EVIDENCE` F1 `0.2000`) |
| **Mean Prompt Tokens (if sent to LLM)** | `31.27` tokens/sample | Estimated query + passage footprint |
| **Execution Latency** | `mean = 0.0160 ms`, `p50 = 0.0143 ms`, `p95 = 0.0237 ms` | Negligible overhead |

**Key Finding:** Because no trained HalluGuard checkpoint or live LLM server is present, the deterministic fallback provides **0 independent accuracy improvement** over G3 alone; its role in Phase 04 is reliable structured verdict synthesis, trace logging, and fail-safe degradation.

---

## 3. Adapter Failure-Path & In-Process HTTP Contract Evaluation ($N=9$ Scenarios)

*(Note: Loopback HTTP tests exercise an in-process `127.0.0.1` test server strictly to validate HTTP client transport, timeout handling, malformed JSON recovery, and markdown-fenced JSON parsing—not live LLM reasoning accuracy.)*

| Scenario | Backend Used | Execution Status | `is_fallback` | Verdict | Deterministic Repeat | Mean Lat (ms) | Error Detail Recorded |
|---|---|---|---:|---|---:|---:|---|
| `srm_disabled` | `deterministic_fallback` | `DISABLED` | `True` | `TRUSTWORTHY` | `True` | 0.015 | SRM backend disabled |
| `backend_disabled` | `deterministic_fallback` | `DISABLED` | `True` | `TRUSTWORTHY` | `True` | 0.007 | SRM backend disabled |
| `ollama_unavailable` | `deterministic_fallback` | `UNAVAILABLE` | `True` | `TRUSTWORTHY` | `True` | 6.180 | `[Errno 111] Connection refused` |
| `openai_no_key` | `deterministic_fallback` | `UNAVAILABLE` | `True` | `TRUSTWORTHY` | `True` | 0.014 | No API credential configured |
| `ollama_timeout_fallback` | `deterministic_fallback` | `TIMEOUT` | `True` | `TRUSTWORTHY` | `True` | 51.738 | Timed out after `0.05s` |
| `ollama_malformed_fallback` | `deterministic_fallback` | `UNAVAILABLE` | `True` | `TRUSTWORTHY` | `True` | 128.736 | Non-JSON payload error caught |
| `ollama_valid_loopback_mock` | `local_ollama` | `SUCCESS` | `False` | `TRUSTWORTHY` | `True` | 2.901 | `None` (loopback HTTP mock) |
| `ollama_fenced_json_loopback` | `local_ollama` | `SUCCESS` | `False` | `TRUSTWORTHY` | `True` | 1.962 | `None` (loopback HTTP mock) |
| `openai_valid_loopback_mock` | `openai_compatible` | `SUCCESS` | `False` | `TRUSTWORTHY` | `True` | 1.588 | `None` (loopback HTTP mock) |

---

## 4. Step 8 Acceptance Verdict

- [x] Available vs. unavailable backends explicitly established without fabricating live model scores.
- [x] Disabled, unavailable, timeout, malformed-response, valid-JSON, fenced-JSON, and deterministic fallback paths tested (`9/9` deterministic).
- [x] Execution status and fallback attribution fully traceable in `SRMResponse`.

**Step 8 Status:** **PASS** — Ready to proceed to Step 9 (Ablation Study).

