# Phase 08 — Step 03: Real Model Integration Report

**Branch:** `phase-8`  
**Added / Modified Modules:** `src/trustrag/srm/hf_local.py` (`HuggingFaceLocalSRMBackend`), `src/trustrag/srm/registry.py`, `src/trustrag/srm/__init__.py`  
**Tests:** `tests/unit/test_phase_08_step03_model_integration.py`  
**Live Model Inference Status:** **`BLOCKED`** (optional `torch`, `transformers`, `peft` not installed; Ollama daemon inactive; zero 4B model checkpoints staged on disk; automatic downloads disabled via `local_files_only=True`).

---

## 1. Adapter Capabilities & Safeguards

1. **Optional CPU/GPU Transformers + PEFT Integration (`HuggingFaceLocalSRMBackend`):** Lazy imports `torch`, `transformers`, and optional `peft.PeftModel` inside `_import_optional_runtime()` so offline environments stay clean and never trigger runtime import crashes when deep-learning dependencies are absent.
2. **Tokenizer & Checkpoint Compatibility Validation:** Verifies callable encoding + `decode()` + `eos_token_id`/`pad_token_id` assignment + model `generate()` method before readiness; refuses remote Hub downloads when `local_files_only=True`.
3. **Structured 5-Category Evidence Judgment:** Validates JSON outputs across `GROUNDED`, `INTRINSIC_HALLUCINATION`, `EXTRINSIC_HALLUCINATION`, `INSUFFICIENT_EVIDENCE`, and `CONTRADICTED`, capturing `claim_id`, `evidence_ids`, `cited_spans`, `verified_citations`, `confidence`, and `rationale`.
4. **Resource, Timeout & OOM Protection:** Enforces bounded timeouts (`ThreadPoolExecutor` + `timeout_seconds`), controlled batching (`batch_size`), automatic cleanup on `MemoryError` / CUDA OOM (`shutdown()` + `ModelError`), and explicitly tags `model_config_snapshot["confidence_calibrated"] = False`.

## 2. Verification & Honest Parity Status

- `mypy`: `6 / 6` files passed (`0` errors).
- `ruff check`: `0` errors on `hf_local.py`, `registry.py`, `__init__.py`, and `test_phase_08_step03_model_integration.py`.
- `pytest`: `6 passed in 0.43s` covering `test_phase_08_step02_srm_backend.py` + `test_phase_08_step03_model_integration.py` (test-double adapter validating all 5 categories, `<think>` parsing, timeout, OOM cleanup, incompatible tokenizer, and missing checkpoint rejection).
- **Research Parity Boundary:** HalluGuard's ORPO-trained 4B model checkpoint and `84.0%` RAGTruth / `75.7%` LLM-AggreFact balanced accuracy are **NOT reproduced** offline (`BLOCKED`).
