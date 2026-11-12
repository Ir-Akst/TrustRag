# Phase 08 — Step 06: Query Consistency & High-Trust Re-Answer Report

**Branch:** `phase-8`  
**Added / Modified Modules:** `src/trustrag/verification/{query_consistency.py,output_verifier.py,__init__.py}`, `src/trustrag/pipeline/trustrag_pipeline.py`, `src/trustrag/config/engine_config.py`, `src/trustrag/engine/schemas.py`  
**Tests Added:** `tests/unit/test_phase_08_step06_query_consistency.py`

---

## 1. Query Consistency & Controlled Re-Answer Implementation

1. **Query Consistency Checker (`src/trustrag/verification/query_consistency.py`):**
   - Computes lexical + TF-IDF intent alignment (`evaluate_query_consistency`) between `query` and candidate `answer_text`.
   - Detects **topic hijacks** (grounded off-topic responses), **spurious DoS refusals** (`"cannot answer"` / `"refuse"` emitted when evidence matches `query >= 0.20`), and **temporal query-anchor mismatches** (e.g., query asks for `2023`, answer references only `2019`).
   - Integrated into `OutputEvidenceVerifier.verify(..., query=...)`: failed query consistency downgrades `VERIFIED`/`PARTIALLY_SUPPORTED` cleanly to `UNVERIFIED` / `INSUFFICIENT_EVIDENCE`.
2. **Bounded High-Trust Subset (`Ê`) Re-Answer Workflow (`TrustRAGPipeline.run`):**
   - Selects non-conflicted `admissible_docs` meeting `min_reanswer_trust_score` (`0.60`).
   - Controlled by explicit config flags (`enable_reanswer`, `max_reanswer_attempts` bounded `0..3`, `min_reanswer_trust_score`, `reanswer_timeout_seconds`).
   - Never bypasses verification: every regenerated answer executes Unicode inspection + full G3 + Query Consistency before release; abstains cleanly on timeout or inconclusive results; preserves initial response/status inside `metadata["reanswer_audit"]` & `execution_trace`.
   - Backward-compatible `_invoke_verifier` inspects verifier method signatures so existing custom test spies continue passing cleanly.

## 2. Verification Results

- `mypy` (`10 / 10` files): **`0` errors**.
- `ruff check` (`query_consistency.py`, `__init__.py`, `test_phase_08_step06_query_consistency.py`): **`0` errors**.
- `pytest` (`test_phase_08_step06_query_consistency.py`, `test_phase_03_defense.py`, `test_phase_03_g3_verification.py`): **`173 passed in 2.02s`**.
- `tools/spec_validation/run_all_validations.py`: **`PASS` (`10 / 10` validators, `13 / 13` gates)**.
