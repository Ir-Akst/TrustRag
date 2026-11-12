# 17 — Missing Work & Prioritized Remediation Plan

This plan orders engineering remediation strictly by measured impact and blocking severity observed in the audit (`RED`/`BLACK` blockers first, followed by `YELLOW` security/research gaps).

---

## P0 — Immediate Execution & Platform Blockers

1. **Remove Unconditional `import resource` Crashes on Windows (`RED` Blocker)**
   - **Locations:** [service.py:7](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/serving/service.py#L7), [suites.py:1843](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/evaluation/suites.py#L1843).
   - **Fix:** Guard `resource` inside `try: import resource except ImportError: resource = None` (matching the existing `fcntl` fallback pattern in `api/audit.py:21`) and skip POSIX `RLIMIT_*` calls when `resource is None`.
   - **Unlocks:** `trustrag.serving`, `trustrag.api.*`, `cli --health`, `cli --adaptive`, live frontend dashboard tests, `test_srm_ablation_and_perf_smoke`, and all `8` serving/API pytest suites.

2. **Fix Dependency Drift & Broken `.venv313` Environment (`RED` Blocker)**
   - **Locations:** [pyproject.toml](file:///c:/Users/Dell/Desktop/trustrag/pyproject.toml), `requirements.txt`, `requirements-dev.txt`.
   - **Fix:** Add `scikit-learn` to core dependencies, replace `[dependency-groups] api` `fastapi`/`uvicorn` with `aiohttp`, and rebuild `.venv313` so all `35` collection errors disappear.

3. **Close Observed G1 & G2 Security Bypasses (`2/6` Live E2E Poison Leaks)**
   - **G1 Possessive Bypass (`text_utils.py:79`):** Expand `SHARED_THREAT_PATTERNS[0]` from `(?:all\s+)?` to allow possessives/determiners (`your`, `the`, `their`, `any`, etc.), plus add Base64/hex decoding and phrase-level repetition rate detection (`trigger_dos`), while removing false `FLAG (0.45)` on single benign ZWSP characters in ASCII prose.
   - **Retrieval Removal Cap Bypass (`04_poisoned_retrieval_instr` & `atk_duplicate_poison_3v1`):** Change `removal_cap_ratio` behavior or apply semantic/numeric claim-cluster consensus checks so multiple `POISONED` or near-duplicate unverified passages cannot slip past the `floor(K/2)` removal cap or outvote a verified clean passage `3v1`.
   - **Stealth Factual Poison (`p_out` / `atk_poisonedrag_stealth_factual`):** Detect inter-document numeric/factual contradiction inside G2 *before* generation rather than relying solely on imperative regex (`F4`) and missing offline `F1`/`F2`.

---

## P1 — Data Integrity, Verification Accuracy & Calibration Quality

4. **Acquire Genuine External Benchmarks & Eliminate Synthetic Template Leakage (`RED` / `BLACK`)**
   - Acquire full splits of `NQ`, `HotpotQA`, `MS MARCO`, `HaluEval`, `RAGTruth (18k)`, `LLM-AggreFact`, and `RSB` (or document verified access gates), replacing `benchmarks_backup` (`250`/`150` synthetic records built from `8` `_TEMPLATES` with exact `target_query` train/val/test leakage).
   - Short-circuit `load_dataset(..., offline=True)` when `data/raw/<name>` is empty so `7` loaders do not execute `HEAD` Hub network retries offline.

5. **Fix G3 False-Negatives & Extractive Circularity**
   - Fix phrasing sensitivity in unit conversion (`"1000 mg per day"` vs `"1 g daily"`, currently failing `coverage 0.60 < 0.65`) by canonicalizing unit tokens prior to lexical coverage calculation.
   - Restrict cross-document contradiction in coordinated clauses (`01_clean_factual`) so a second true predicate in `doc_boil_wiki` (`freezes at 0 C`) is not falsely contradicted by `doc_boil_nist` (`boils at 100 C`) unless both documents discuss freezing point.
   - Enforce minimum provenance/quality thresholds (`09_low_quality_ambiguous`) so extractive self-matching on vague/hedged text with `provenance=UNKNOWN` returns `UNVERIFIED` / `CAUTION` rather than `TRUSTED`.

6. **Recalibrate or Replace `platt_calibrator_v1.json`**
   - Resolve the `0.50`–`0.6667` clean false-positive rate observed with Platt calibration on `knowledge_poisoning` (McNemar `b=8, c=8`), retaining `temperature_calibrator_v1.json` (`FPR=0.0`) or retraining logistic calibration on deduplicated non-leaking splits with `F1`/`F2` features present.

---

## P2 — Real Neural Architecture, Test Hygiene & Deployment

7. **Implement Dense Retrieval, Local Persistence & Real Generator/SRM Stack (`BLACK` -> `GREEN`)**
   - Add dense bi-encoder embeddings + `faiss-cpu` ANN index with `save()`/`load()` persistence and explicit duplicate-ID rejection/deduplication (`dup_1`).
   - Enable native G2 `F1` (perplexity) and `F2` (embedding norm) scorers offline instead of `UNAVAILABLE` stubs.
   - Implement and run the ORPO/LoRA training pipeline for `Qwen2.5-3B-Instruct` SRM (`src/trustrag/training/`), verify neural checkpoints on disk, and replace `PROXY_ONLY` FilterRAG heuristics with real SLM inference.

8. **Code Hygiene, Logger Fix & Containerization**
   - Fix `get_logger()` handler stream caching (`utils/logging.py`) so `test_foundation.py` passes cleanly inside full-suite runs.
   - Remove redundant untracked `tests/test_*.py` clones after verification, resolve `43` `mypy` errors and `ruff` violations, and add `Dockerfile`, `docker-compose.yml`, and CI test workflows.

