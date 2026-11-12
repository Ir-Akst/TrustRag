# Phase 08 — Step 02: SRM Backend Architecture Report

**Branch:** `phase-8`  
**Modified / Added Modules:** `src/trustrag/srm/{registry.py,backends.py,client.py,__init__.py}`, `src/trustrag/engine/schemas.py`, `src/trustrag/config/engine_config.py`  
**Tests Added:** `tests/unit/test_phase_08_step02_srm_backend.py`

---

## 1. Architecture Summary

1. **Separated Pluggable Selection (`SRMBackendRegistry` in `src/trustrag/srm/registry.py`):** Decouples backend instantiation (`disabled`, `local_ollama`, `openai_compatible`, `hf_local`, `custom`) from `SRMClient` business logic.
2. **Lifecycle & Explicit Health Contract (`BaseSRMBackend`, `SRMBackendHealth`):** Exposes `initialize()`, `shutdown()`, `health_check()`, `invoke()`, `invoke_batch(max_batch_size=...)`, `verify_claims()`, and `classify_evidence(blind_to_g3_heuristics=True)`.
3. **Configuration Controls (`SRMConfig`):** Supports `inference_mode` (`think`/`non_think`), `device` (`auto`/`cpu`/`cuda`), `max_new_tokens`, `batch_size`, `local_files_only=True` (prevents unintended remote weight downloads), `trust_remote_code=False`, and `enforce_citation_grounding=True`.
4. **Hardened Parser (`_parse_srm_json`):** Extracts optional `<think>...</think>` blocks cleanly before balanced JSON extraction, maps judgments into the 5-way `HallucinationCategory` (`GROUNDED`, `INTRINSIC_HALLUCINATION`, `EXTRINSIC_HALLUCINATION`, `INSUFFICIENT_EVIDENCE`, `CONTRADICTED`), and checks `cited_spans` substrings against retrieved passages (`verified_citations`).
5. **No Silent Fallback Guarantee:** Setting `fallback_on_error=False` forces real `TimeoutError` / `ProviderError` / `ModelError` propagation. When `fallback_on_error=True`, fallback outputs explicitly carry `is_fallback=True`, `execution_status`, and `error_detail`.

## 2. Verification Results

- `mypy`: `7 / 7` source files passed (`0` errors).
- `ruff check` (`registry.py`, `client.py`, `__init__.py`, `test_phase_08_step02_srm_backend.py`): **`0` errors**.
- `pytest -W error -q tests/unit/test_phase_08_step02_srm_backend.py tests/unit/test_phase_03_defense.py`: all tests passed (`3` new Step 02 suites + existing Phase 03 defense tests).
- **Offline Reality Check:** No live LLM/SLM backend is running offline (`LocalOllamaBackend.health_check()` reports unreachable at `127.0.0.1:11434`); `DeterministicFallbackBackend` remains preserved cleanly as an explicit non-neural fallback.
