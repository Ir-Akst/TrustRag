# Phase 05 — Step 01: Baseline Architecture Audit and Freeze

**Date:** 2026-11-11  
**Workspace:** `/home/aditya/rags/TrustRag` (`Ir-Akst/TrustRag`)  
**Python Environment:** `/home/aditya/rags/.venv/bin/python` (Python `3.14.9`)  
**Status:** PASS (Baseline frozen; ready for Step 2)

---

## 1. Purpose

Step 1 audits and freezes the Phase 04 baseline prior to any Phase 05 adaptive defense implementation. All Phase 00–04 interfaces (`G1`, `G2`, `G3`, `TrustAwareRetriever`, `EvidenceGroundedGenerator`, `SRMClient`, `TrustRAGPipeline`), baseline configuration (`configs/base.yaml`), datasets/splits (`data/`), test suite, type checks, and specification gates were verified untouched and passing.

---

## 2. Git & Release State Verification

Verified commands executed against local repository and remote `origin` (`https://github.com/Ir-Akst/TrustRag.git`):

1. `git branch -vv && git log -3 --oneline && git ls-remote --heads origin`
   - Active local branch: `phase-4` at commit `3e2da49` (`phase 4`)
   - Local `main`: `ed576a1`
   - Remote heads on `origin`:
     - `refs/heads/main`: `5855176d7b935a9b91641694977d97f81e06d9cb`
     - `refs/heads/phase-4`: `3e2da4997ca54d8ad5db70d7cacbb6fc192b0f9d`
     - `refs/heads/feature/your-feature`: `85d574f247562fc5f5cf0e6fee091b52fc76df0b`
2. `gh pr view 1 --repo Ir-Akst/TrustRag --json number,title,state,baseRefName,headRefName,mergedAt,mergeCommit`
   - PR `#1` (`"phase 4"`, `phase-4` -> `main`): `MERGED` at `2026-11-11T17:17:05Z`, `mergeCommit = 5855176d7b935a9b91641694977d97f81e06d9cb`.
3. `ls -1 reports/phase04_*.md | wc -l && ls -1 reports/evaluation/ | wc -l`
   - `13` Phase 04 markdown reports (`phase04_step01_*.md` through `phase04_step11_*.md`, `phase04_final_acceptance_report.md`, `phase04_implementation_report.md`).
   - `198` serialized evaluation artifacts under `reports/evaluation/`.
4. `git status --short data/`
   - Clean (`0` modified or untracked files under `data/`).

---

## 3. Baseline Test, Type-Check & Specification Verification

| Check | Command | Outcome |
| :--- | :--- | :--- |
| Full unit/component suite | `PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest -W error -q` | `310 passed, 2 deselected` (integration tests), `0` warnings, exit `0` (`7.56s`) |
| Static typing (`mypy`) | `PYTHONPATH=src /home/aditya/rags/.venv/bin/mypy src/trustrag/ --ignore-missing-imports` | `Success: no issues found in 74 source files`, exit `0` |
| Spec validation gates | `PYTHONPATH=src /home/aditya/rags/.venv/bin/python tools/spec_validation/run_all_validations.py` | `suite_status: PASS`, `10/10` validators, `13/13` gates `SATISFIED`, exit `0` |

Available scientific stack verified in `.venv` (no large-model downloads or extra dependencies required): `scikit-learn 1.9.1`, `scipy 1.18.1`, `numpy 2.5.4`, `pandas 3.1.1`, `pydantic 2.14.3`.

---

## 4. Frozen Baseline Configuration (`configs/base.yaml`)

Phase 05 must preserve `configs/base.yaml` unchanged as the immutable static fallback baseline and keep adaptive parameters strictly isolated under adaptive config/state schemas.

| Section | Frozen Key Parameters |
| :--- | :--- |
| `app` | `env: development`, `log_level: INFO`, `random_seed: 42` |
| `guardrails` (G1) | `enabled: true`, `max_input_length: 4096`, `flag_threshold: 0.35`, `block_threshold: 0.70`, `block_on_empty: true`, `strip_zero_width_for_analysis: true` |
| `retrieval` | `top_k: 5`, `candidate_multiplier: 3`, `min_relevance_score: 0.01`, `filtering_mode: remove_with_cap`, `filter_low_trust: true`, `enforce_removal_cap: true`, `removal_cap_ratio: 0.5`, `trust_weight: 0.45` |
| `msd` (G2) | `enabled: true`, weights `(F1=0.8, F2=0.8, F3=1.2, F4=2.0, F5=1.0, F6=0.8)`, `bias: 0.0`, `trust_threshold: 0.60`, `poison_threshold: 0.38`, `instruction_poison_threshold: 0.55`, `instruction_flag_threshold: 0.30`, `missing_signal_policy: coverage_attenuated`, `min_available_signals: 2`, `min_available_weight_ratio: 0.25`, `perplexity_backend: disabled` (`mean=25.0`, `std=15.0`, `z=2.0`), `embedding_backend: tfidf_raw`, `embedding_norm_reference_policy: require_configured` (`z=2.0`), `provenance_priors: {}`, `enable_freq_density: false` |
| `generation` | `mode: extractive`, `max_context_docs: 3`, `max_sentences_per_doc: 2`, `abstain_on_empty_context: true` |
| `verification` (G3) | `enabled: true`, `min_support_coverage: 0.65`, `min_relevance_for_check: 0.10`, `strict_numeric_matching: true`, `strict_negation_check: true` |
| `srm` | `enabled: true`, `backend: disabled`, `model_name: halluguard-srm-fallback`, `timeout_seconds: 5.0`, `temperature: 0.0`, `fallback_on_error: true` |

---

## 5. Architecture & Phase 05 Adaptation Integration Audit

### 5.1 Core Modules & Schemas Audited

- **Configuration (`src/trustrag/config/engine_config.py`, `src/trustrag/config/settings.py`):** Validation dataclasses `GuardrailsConfig`, `RetrievalConfig`, `MSDConfig`, `GenerationConfig`, `VerificationConfig`, `SRMConfig` loaded via `load_config()`. Adaptive overrides in Phase 05 can wrap or produce validated snapshot configs without mutating `configs/base.yaml`.
- **Input Guardrail G1 (`src/trustrag/guardrails/input_guardrail.py`):** `InputGuardrail.evaluate(user_input) -> G1Assessment`. Exposes `risk_score`, flags, and action (`allow` / `flag` / `block`) controlled by `flag_threshold` and `block_threshold`.
- **Six-Signal MSD G2 (`src/trustrag/detection/msd.py`, `src/trustrag/engine/schemas.py`):**
  - `MultiSignalDetector.assess_candidates(...)` and `assess_document(...)` emit `G2DocumentAssessment` containing raw signal details (`SignalDetail` for F1–F6 with `available`, `value`, `raw_value`, `z_score`, `effective_weight`, `is_heuristic`), `trust_score`, `decision`, `available_signals_count`, `available_weight_ratio`, `instruction_risk_score`, `conflict_detected`, and `removed_by_cap`.
  - Uncalibrated aggregation computes centered logits (`2 * s_i - 1`), `coverage_attenuated` (`confidence_scale = min(1.0, weight_ratio)`), and `tier_factor` (`1.0` / `0.65` / `0.20`).
  - **Calibration Hook:** G2 exposes raw scalar `trust_score` plus per-signal `SignalDetail` entries, enabling post-hoc Platt scaling, Isotonic regression, or Temperature scaling on `train`/`val` splits while retaining `trust_score` backward compatibility and static fallback.
- **Trust-Aware Retrieval (`src/trustrag/retrieval/retriever.py`):** `TrustAwareRetriever.retrieve_trusted(...)` applies `trust_weight` reranking and bounded `floor(K * removal_cap_ratio)` filtering cap.
  - **Context-Aware Thresholding Hook:** Retrieval candidate distributions (score variance, consensus agreement, query complexity/type, G1 flag state, available signal coverage) are observable upstream of filtering without letting retrieved document instructions steer thresholds.
- **Evidence-Grounded Generator & G3 Verifier (`src/trustrag/verification/output_verifier.py`):** `OutputEvidenceVerifier.verify(answer_text, evidence_docs, *, abstained=False) -> G3VerificationReport` emits claim-level verdicts (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`, `UNCERTAIN`) and `support_coverage`.
  - Observed baseline distribution on `data/benchmarks/hallucination` (`n=11` across train/val/test): `{'INSUFFICIENT_EVIDENCE': 8, 'CONTRADICTED': 2, 'SUPPORTED': 1}` (known low three-class separation weakness carried forward from Phase 04).
- **SRM & Fallback (`src/trustrag/srm/client.py`, `src/trustrag/srm/backends.py`):** `SRMClient.reason` routes to `LocalOllamaBackend`, `OpenAICompatibleAPIBackend`, or `DeterministicFallbackBackend`.
- **Orchestrator (`src/trustrag/pipeline/trustrag_pipeline.py`):** `TrustRAGPipeline.run(query, *, top_k=None, answer_override=None) -> PipelineResponse` connects G1 -> Retrieval/G2 -> Generation -> G3 -> SRM. Ideal single integration point for non-intrusive Phase 05 telemetry, drift windowing, calibration, context thresholding, G3 feedback monitoring, and policy-gated rollback.

### 5.2 Dataset & Split Inventory (Zero Test-Leakage Boundary)

Configured in `configs/datasets.yaml` (13 registered datasets): `natural_questions`, `hotpotqa`, `ms_marco`, `squad`, `boolq`, `halueval`, `ragtruth`, `llm_aggrefact`, `wice`, `expertqa`, `rsb`, `custom_security`, `fineweb`.

- **Small canonical splits (`data/benchmarks/`):** `clean_rag` (7/1/2), `knowledge_poisoning` (14/2/4), `hallucination` (7/1/3), `adversarial_robustness` (22/4/4; note 10 within-split duplicates documented in Phase 04).
- **Larger backup splits (`data/benchmarks_backup/`):** `100` / `150` / `11` / `250` records (`0` duplicates).
- **Synthetic paired corpus (`data/raw/custom_security/raw_train.jsonl`):** `2,000` paired synthetic records (`1,000` clean/poison pairs; explicitly synthetic).
- **Phase 05 Split Hygiene Rule:** All Platt/Isotonic/Temperature calibrators and baseline drift reference windows MUST be fitted exclusively on `train`/`val` splits (`test` splits remain strictly held out).

---

## 6. Frozen Baseline Quantitative Snapshot (Phase 04 Observed Evidence)

1. **Ablation Study (`reports/evaluation/step09_ablation_study.json`):**
   - `E1_Original_RAG`: `clean_recall_at_5 = 0.8000`, `clean_faithfulness = 0.7333`, `clean_fpr_block_or_quarantine = 0.0`, `corpus_injection_asr = 0.4483`, `corpus_injection_prevented_or_flagged = 0.5517`, `direct_query_attack_asr = 1.0`, `combined_threat_asr = 0.6279`, `mean_latency_ms = 9.6818`, `p95_latency_ms = 13.6237`, `throughput_qps = 103.29`.
   - `E7_Full_TrustRAG_SRM_Fallback`: `clean_recall_at_5 = 0.8000`, `clean_faithfulness = 0.7333`, `clean_fpr_block_or_quarantine = 0.0`, `corpus_injection_asr = 0.1379`, `corpus_injection_prevented_or_flagged = 1.0`, `direct_query_attack_asr = 0.0`, `combined_threat_asr = 0.0930` (90.70% threat prevention, synthetic workload), `mean_latency_ms = 12.9164`, `p95_latency_ms = 27.0628`, `throughput_qps = 77.42`.
2. **Performance & Overhead (`reports/evaluation/step10_performance.json`, `boolq/validation.jsonl`, `corpus_docs=100`, `num_queries=100`):**
   - `original_rag`: `mean = 15.6882 ms`, `p50 = 16.3336 ms`, `p95 = 17.4185 ms`, `throughput_qps = 63.73`, `peak_traced_heap_mib = 2.115`.
   - `trustrag_no_srm`: `mean = 71.1358 ms`, `p50 = 66.0461 ms`, `p95 = 122.2087 ms`, `throughput_qps = 14.06`, `peak_traced_heap_mib = 4.76`.
   - `trustrag_with_srm_fallback`: `mean = 80.0226 ms`, `p50 = 75.4615 ms`, `p95 = 142.6222 ms`, `throughput_qps = 12.49`, `peak_traced_heap_mib = 4.76`.
3. **Phase 04 Reported Benchmark Baselines (`reports/phase04_implementation_report.md`):**
   - `backup_adv_test` (`N=40`): G2 `ROC-AUC = 0.8951`, `Brier = 0.1466`, `ECE = 0.1410`.
   - Clean `boolq/validation` (`N=100`): `Recall@5` dropped from `0.9000` to `0.8200` (McNemar `p = 0.0215`), representing the primary utility trade-off target for Phase 05 adaptive calibration & thresholding.

---

## 7. Step 1 Acceptance Decision

- [x] GitHub and local release state (`phase-4` @ `3e2da49`, PR `#1` merged into `main` @ `5855176d`) verified.
- [x] Phase 00–04 tests (`310 passed, 2 deselected`, 0 warnings), `mypy` (`0` issues in `74` files), and `spec_validation` (`10/10`, `13/13` gates `SATISFIED`) verified passing.
- [x] `configs/base.yaml` baseline and `data/` split integrity verified untouched and frozen.
- [x] Adaptation hook points, split-hygiene rules, and security boundaries mapped across G1, G2, Retrieval, G3, SRM, and `TrustRAGPipeline`.

**Acceptance Verdict:** **PASS** — Step 1 complete. Ready to proceed to Step 2 (Adaptive Trust Calibration).

