# TrustRAG — Phase 04 Implementation Report
## Evaluation, Experimental Benchmarking, and Performance Validation

**Date:** 2026-11-11  
**Repository:** `/home/aditya/rags/TrustRag` (mirrored from `Ir-Akst/TrustRag`, commit `ed576a1`)  
**Python Environment:** `Python 3.14.9` on `Linux-7.2.14-arch1-1-x86_64` (12 CPU cores, CPU-only)

---

## 1. Executive Summary

Phase 04 systematically built and executed a reproducible evaluation framework (`src/trustrag/evaluation/`) across all TrustRAG subsystems—G1 Input Guardrail, G2 Multi-Signal Detector (MSD), Trust-Aware Retrieval, Extractive Generation, Stage 7 Unicode Defense, G3 Output Evidence Verification, and HalluGuard-inspired SRM integration—without modifying Phase 00–03 defense logic or benchmark datasets.

**Headline Verified Outcomes:**
- **Security Protection (`E1` $\rightarrow$ `E7`, $N=43$ paired threat probes, Synthetic):** Threat prevention rose from **`37.2%` (`95% CI [24.4%, 52.1%]`)** to **`90.7%` (`95% CI [78.4%, 96.3%]`)** (McNemar exact $p < 10^{-6}$, Holm-adjusted $p < 10^{-6}$).
- **Direct Input Threats (`G1`, $N=4,000$ Synthetic + $N=100$ Real BoolQ):** `100.0%` recall on `PROMPT_INJECTION`, `MALICIOUS_INSTRUCTION`, and `TRIGGER_DOS` in `custom_security` (`375/375`) with **`0.0%` false positives** on `100` real BoolQ queries and `250` benign instruction-like controls; `83.3%` recall (`10/12`) on novel zero-day curated command/trigger probes.
- **Output Verification (`G3`):** **`0.0%` False-Support Rate** across both `hallucination` ($N=11$ real benchmark records) and `g3_linguistic_suite` ($N=25$ cases, `100.0%` pass rate), paired with conservative `27.3%` 3-class accuracy on paraphrased/tabular claims due to lexical-only matching (no NLI model loaded).
- **Clean Utility Tradeoff (`BoolQ`, $N=100$ Real Queries):** `Recall@5` dropped from `0.9000` (Original RAG) to `0.8200` (Full TrustRAG, McNemar $p = 0.0215$), reflecting `trust_weight=0.45` re-ranking displacement.
- **Computational Overhead (`N=100` BoolQ Queries, CPU-only):** End-to-end mean latency increased from `15.69 ms` (`63.73 QPS`) to `80.02 ms` (`12.49 QPS`, `p50=75.46 ms`, peak traced heap `4.76 MiB`).
- **Regression & Spec Safety:** `309/309` unit tests pass, `10/10` spec validators (`13/13` gates) pass, `0` mypy/ruff issues on Phase 04 code.

---

## 2. Phase 03 Baseline Verification

Executed prior to any Phase 04 implementation (`reports/phase04_step01_baseline_freeze.md`):
- **Regression Suite:** `303 passed, 2 deselected` (`integration`) in `2.27s`.
- **Specification Validation:** `10/10` validators (`suite_status: PASS`), `13/13` acceptance gates `SATISFIED`.
- **Bytecode Compilation:** `compileall` exited `0`.
- **Baseline Config Frozen:** `configs/base.yaml` (`seed=42`, `top_k=5`, `trust_weight=0.45`, `removal_cap_ratio=0.5`, `poison_threshold=0.38`, `trust_threshold=0.60`, `srm.backend=disabled`, `perplexity_backend=disabled`, `embedding_backend=tfidf_raw`).

---

## 3. Evaluation Infrastructure

Implemented under `src/trustrag/evaluation/`:
- `schemas.py`: `ExperimentConfig`, `SampleOutcome`, `ErrorRecord`, `ExperimentResult` with deterministic SHA-256 experiment IDs.
- `loader.py`: `load_evaluation_partition()` validating every record via Pydantic, recording corrupt JSON lines and schema errors in `invalid_records` (never counted as successful predictions), computing partition & manifest SHA-256 hashes, and checking CRLF-normalized manifest integrity.
- `metrics.py`: Binary/multiclass metrics, ROC-AUC/PR-AUC (safe `None` when single-class), `Precision@K`, `Recall@K`, `MRR`, percentile distribution summaries, Wilson 95% CIs, percentile bootstrap 95% CIs, exact binomial McNemar's test, paired permutation test, and Cohen's $d$.
- `runner.py`: `EvaluationRunner` enforcing `set_random_seed`, explicit error/skip/invalid accounting, `perf_counter` timing, structured JSON logging, and exporting `.json`, `_metrics.csv`, and `_samples.csv` artifacts (`198` files produced in `reports/evaluation/`).
- `suites.py`: Modular evaluation suites for Steps 3–11.

---

## 4. Dataset and Benchmark Integrity

- **Leakage & Quality:** `0` cross-split `source_id` overlaps and `0` `content_hash` overlaps across `train`/`val`/`test` in all 4 benchmarks (`data/benchmarks/` and `data/benchmarks_backup/`); `0` invalid or unknown-label records (`DatasetQualityAuditor`).
- **CRLF vs. LF Manifest Observation:** `ManifestManager.validate_manifest()` reports byte-size/hash diffs on Linux because original manifests hashed Windows `\r\n` bytes prior to Git LF checkout; normalizing `\n` $\rightarrow$ `\r\n` verifies **100% SHA-256 content identity** on all 28 partition files.
- **Active vs. Backup Benchmark Sizes:** Active `data/benchmarks/` holds the `limit=10` rebuild from `scratch/run_phase02_full.py` (`clean_rag`: 7/1/2, `knowledge_poisoning`: 14/2/4, `hallucination`: 7/1/3, `adversarial_robustness`: 22/4/4 with 10 within-split duplicates). Preserved `data/benchmarks_backup/` (`clean_rag`: 70/15/15, `knowledge_poisoning`: 104/22/24, `adversarial_robustness`: 174/36/40 with 0 duplicates) and `data/raw/custom_security/raw_train.jsonl` (2,000 records) were evaluated alongside active splits without modifying any `data/` files (`git status --short data/` clean).

---

## 5. Clean RAG Baseline

*Source Type:* **Measured Real Data** (`boolq`).

| Dataset / Split | Configuration | $N$ | P@1 | R@5 | MRR | GT Doc Hit | Faithfulness | Abstention | Mean Lat (ms) | QPS |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Active `clean_rag/test` | Original RAG | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.84 | 544.6 |
| Active `clean_rag/test` | Full TrustRAG | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 4.42 | 226.4 |
| Backup `clean_rag/test` | Original RAG | 15 | 0.7333 | 0.8000 | 0.7667 | 0.8000 | 0.7333 | 0.2000 | 2.74 | 365.4 |
| Backup `clean_rag/test` | Full TrustRAG | 15 | 0.7333 | 0.8000 | 0.7667 | 0.8000 | 0.7333 | 0.2000 | 6.63 | 150.9 |
| Backup `clean_rag/train` | Original RAG | 70 | **0.8714** | **0.9286** | **0.8940** | **0.9143** | 0.6571 | 0.0143 | 7.68 | 130.2 |
| Backup `clean_rag/train` | Full TrustRAG | 70 | 0.7571 | 0.8571 | 0.7945 | 0.8286 | 0.6429 | 0.0143 | 19.98 | 50.0 |

*Note:* `boolean_exact_match = 0.0` across all runs because `AnswerGenerator` operates in `extractive` mode (returning verbatim sentences rather than `"yes"`/`"no"`).

---

## 6. Knowledge Poisoning Results

*Source Type:* **Synthetic Benchmark Data** (`custom_security`).

- **Paired Single-Injection into Clean KB (`Backup test`, $N=12$ pairs):** `Original RAG` `ASR = 0.6667` (`PoisonEv=8`, `CleanEv=44`) $\rightarrow$ `RAG+G2`, `RAG+G2+G3`, and `Full TrustRAG` **`ASR = 0.1667` (`-75%` relative)**, **`PreventedOrFlagged = 1.0000`**, `CleanEv=50`, `PoisonEv=2`.
- **Full-Split Mixed Corpus (`Backup test`, $N=3$ queries):** `ASR = 0.6667` for both Original RAG and TrustRAG because 50/50 symmetric `KNOWLEDGE_POISONING` conflicts are marked `UNCERTAIN` (`overall_trust_decision = "FLAGGED"`) rather than quarantined, whereas `TRIGGER_DOS` is caught `4/4` (`POISONED`) at all retrieval ranks 1–5.
- **Removal Cap Enforcement:** `0` violations ($\text{removals} \le \lfloor K/2 \rfloor$) across all runs.

---

## 7. G1 Results

| Suite | Source Type | $N$ | Acc | Prec | Rec | F1 | FPR | Orig. Input Preserved | Mean Lat (ms) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `boolq/validation` | **Real** | 100 | 1.0000 | — | — | — | **0.0000** | 100% | 0.035 |
| `backup_adv_test` | **Synthetic** | 80 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | **0.0000** | 100% | 0.068 |
| `custom_security` | **Synthetic** | 4,000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | **0.0000** | 100% | 0.068 |
| `g1_curated_probes` | **Synthetic** | 18 | 0.8889 | 1.0000 | 0.8333 | 0.9091 | **0.0000** | 100% | 0.168 |

Zero false positives on benign controls (including `250` `BENIGN_INSTRUCTION_LIKE` records and Persian ZWNJ). Two novel curated probes (`curl -X POST ... -d @/etc/passwd` and `[TRIGGER_ACTIVATE_DOS]`) bypassed static regexes.

---

## 8. G2 Results

*Source Type:* **Synthetic Benchmark Data** (`custom_security`).

- **Combined Metrics (`backup_adv_test`, $N=40$):** Strict `POISONED` `Prec=1.000`, `Rec=0.588`, `F1=0.741`, `FPR=0.000`, `ROC-AUC=0.8951`, `PR-AUC=0.9000`, `Brier=0.1466`, `ECE=0.1410`.
- **Combined Metrics (`custom_security`, $N=2,000$):** Strict `POISONED` `Prec=1.000`, `Rec=0.429`, `F1=0.600`, `FPR=0.000`, `ROC-AUC=0.7857`; `0` non-amplifying weight violations.
- **Signals:** `F1 (perplexity)` and `F2 (embedding_norm)` unavailable (`0%`, disabled/require_configured); `F4 (instruction_content)` [heuristic] is strongest (`AUC=0.7941`); `F5 (consensus_deviation)` [heuristic] improves combined AUC (`val` drop `-0.1587` when ablated); `F6 (provenance)` uniform (`0.7500`, `AUC=0.5000`); optional FilterRAG `freq_density` [heuristic] achieves `AUC=0.7059` (`backup_adv_test`).
- **Validation-Only Threshold Sensitivity (`val`, $N=36$):** Decisions invariant across `pt in [0.25, 0.75]`, `tt in [0.55, 0.85]`; frozen defaults retained.

---

## 9. G3 Results

- **`data/benchmarks/hallucination` (`all`, $N=11$ Real Benchmark Records):**
  - Answer & Claim 3-class `Accuracy = 0.2727`, `Macro-F1 = 0.2889` (`test` $N=3$: `Acc = 0.6667`, `Macro-F1 = 0.5556`).
  - **False-Support Rate = `0.0000` (`0/6`)**; Unsupported Binary `Recall = 1.0000`, `F1 = 0.7500`; Evidence Traceability = **`100%`**.
  - Lexical/acronym paraphrases (`ECB` vs `European Central Bank`, `CRISPR-Cas9`, tabular Kepler-22b) and un-united numeric conflicts (`50` vs `100 degrees Celsius`, `1985` vs `1928`) route conservatively to `INSUFFICIENT_EVIDENCE`.
- **`g3_linguistic_suite` ($N=25$ Spec & Linguistic Probes):** **`25/25` (`100.0%`) pass**, `0` false support, covering coordinated predicates, irregular past comma-splices, `ScheduleAssertion`, negation, restrictive scope, dosage conflicts, and Stage 7 Unicode answer quarantine.

---

## 10. SRM Results

- **Backend Availability:** Trained HalluGuard checkpoint = **Not Available**; Local Ollama = **Unavailable** (`ConnectError`); OpenAI-compatible API = **Unconfigured** (no API key); Deterministic Fallback (`halluguard-srm-fallback`) = **Available**.
- **Deterministic Fallback (`hallucination`, $N=11$):** `100%` agreement with G3, `100%` justification & JSON structure validity, `Accuracy = 0.2727` (`0` independent gain over G3), `mean latency = 0.016 ms`.
- **Adapter Contract Matrix (9 scenarios, including in-process loopback HTTP mock):** `9/9` deterministic recovery on disabled, connection refused, missing key, timeout (`51.7 ms`), malformed JSON (`128.7 ms`), and valid/fenced JSON loopback parsing.

---

## 11. Ablation Study

Evaluated across `E1`–`E7` (`seed=42`, `top_k=5`, $N=58$ queries/threats):

| Arm | Modules | Clean R@5 | Clean Faith. | Clean FPR | Corpus Inj. ASR | Direct Query ASR | Combined ASR | Mean Lat (ms) | QPS |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **E1** | Original RAG | 0.8000 | 0.7333 | 0.0000 | 0.4483 | 1.0000 | 0.6279 | 3.68 | 271.8 |
| **E2** | RAG + G1 | 0.8000 | 0.7333 | 0.0000 | 0.4483 | **0.0000** | 0.3023 | **2.66** | **375.4** |
| **E3** | RAG + G2 | 0.8000 | 0.7333 | 0.0000 | **0.1379** | 1.0000 | 0.4186 | 6.17 | 162.1 |
| **E4** | RAG + G3 | 0.8000 | 0.7333 | 0.0000 | 0.4483 | 1.0000 | 0.6279 | 7.62 | 131.3 |
| **E5** | RAG + G1 + G2 | 0.8000 | 0.7333 | 0.0000 | **0.1379** | **0.0000** | **0.0930** | 4.38 | 228.2 |
| **E6** | RAG + G1 + G2 + G3 | 0.8000 | 0.7333 | 0.0000 | **0.1379** | **0.0000** | **0.0930** | 8.15 | 122.8 |
| **E7** | Full TrustRAG + SRM | 0.8000 | 0.7333 | 0.0000 | **0.1379** | **0.0000** | **0.0930** | 7.55 | 132.4 |

*Isolation Note:* Because `TrustAwareRetriever` invokes G2 even when `MSDConfig.enabled=False`, `E1`/`E2`/`E4` isolated raw retrieval via `_retrieve_indexed_candidates` without modifying Phase 03 code.

---

## 12. Performance Evaluation

Measured on `data/processed/boolq/validation.jsonl` ($N=100$ real BoolQ docs/queries, CPU-only):
- **Indexing:** `90.89 ms`, `2.807 MiB` peak traced heap; Process Max RSS = `231.23 MiB`.
- **Stage Breakdown (Mean ms):** `G1 = 0.077`, `Retrieval = 3.020`, `G2 = 7.466`, `Generation = 3.107`, `Stage7 Unicode = 0.288`, `G3 = 9.624` (top bottleneck), `SRM Fallback = 0.028`.
- **End-to-End Comparison:** Original RAG `15.69 ms` (`63.73 QPS`, `2.12 MiB`) vs. TrustRAG without SRM `71.14 ms` (`14.06 QPS`, `4.76 MiB`) vs. TrustRAG with SRM Fallback `80.02 ms` (`12.49 QPS`, `4.76 MiB`, `CPU util = 0.997`).

---

## 13. Statistical Validation

- **Security Gain (`E7` vs `E1`, $N=43$):** `0.9070` vs `0.3721`, McNemar $p < 10^{-6}$ (Holm-adjusted $p < 10^{-6}$).
- **G2 Trust Separation (`custom_security`, $N=2,000$):** Clean `0.7774 [0.7718, 0.7833]` vs Poisoned `0.5442 [0.5300, 0.5581]`, Mann-Whitney $U = 773,437.5$, $p = 1.12 \times 10^{-107}$.
- **Clean Utility Tradeoff (`BoolQ`, $N=100$):** `Recall@5` `0.9000` vs `0.8200`, McNemar $p = 0.0215$ (Holm-adjusted $p = 0.0215 < 0.05$ — statistically significant).
- **Latency Overhead (`BoolQ`, $N=100$):** $\Delta = +17.67\text{ ms}$, Cohen's $d = 1.9492$, paired permutation $p = 0.0002$ (Holm-adjusted $p = 0.0004$).
- **Seed Sensitivity (`42, 123, 999`):** `0.0000` variance across all tested metrics.

---

## 14. Regression Results

- `PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest` $\rightarrow$ **`309 passed, 2 deselected`** (`integration`), `exit=0`, `7.08s`.
- `PYTHONPATH=src /home/aditya/rags/.venv/bin/python tools/spec_validation/run_all_validations.py` $\rightarrow$ **`suite_status: PASS`**, **`10/10` validators**, **`13/13` gates SATISFIED**, `exit=0`.
- `/home/aditya/rags/.venv/bin/python -m compileall -q src tests` $\rightarrow$ `exit=0`.
- `/home/aditya/rags/.venv/bin/ruff check src/trustrag/evaluation tests/unit/test_phase_04_*.py` $\rightarrow$ **`All checks passed!`**, `exit=0`.
- `PYTHONPATH=src /home/aditya/rags/.venv/bin/mypy src/trustrag/evaluation/ --ignore-missing-imports` $\rightarrow$ **`Success: no issues found in 6 source files`**, `exit=0`.

---

## 15. Reproducibility Information

- Global random seed `42` (`set_random_seed`), exact config in `configs/base.yaml`, editable package `trustrag 0.1.0`.
- All 198 raw JSON/CSV experiment artifacts persisted under `reports/evaluation/`, plus step reports `reports/phase04_step01_*.md` through `reports/phase04_final_acceptance_report.md`.
- Re-run tests: `PYTHONPATH=src .venv/bin/pytest`; re-run spec gates: `PYTHONPATH=src .venv/bin/python tools/spec_validation/run_all_validations.py`; invoke suites via `trustrag.evaluation.suites`.

---

## 16. Limitations

1. **No Trained HalluGuard SRM or Live NLI/LLM Backend:** `torch`, `transformers`, local Ollama, external LLM APIs, and trained checkpoints are absent; SRM results reflect deterministic fallback + loopback HTTP transport verification only, and G3 uses lexical/TF-IDF verification (reducing recall on paraphrased `SUPPORTED` claims).
2. **Synthetic Security Corpora:** `knowledge_poisoning` and `adversarial_robustness` rely on `custom_security` synthetic templates (`is_synthetic=True`) rather than live production poisoning corpora.
3. **Small Active `hallucination` ($N=11$) & Truncated `data/benchmarks/` Splits ($N=2\text{--}4$):** Required evaluating preserved `data/benchmarks_backup/` splits alongside active `data/benchmarks/`.
4. **Symmetric Factual Poisoning Not Quarantined by Default:** Symmetric 50/50 factual conflicts without instruction triggers are marked `FLAGGED` rather than quarantined prior to generation.
5. **Clean Retrieval Tradeoff:** `trust_weight=0.45` produces a statistically significant `-8.0 pp` `Recall@5` reduction on 100 BoolQ queries.

---

## 17. Remaining Blockers

- **Critical Blockers for Phase 04 Acceptance:** **None.**
- **Deferred Dependencies for Phase 05 / Production:** Live HalluGuard SRM checkpoint training/mounting, optional NLI cross-encoder for G3 paraphrase recall, dense neural retriever comparison, and `data/benchmarks/` restoration from `data/benchmarks_backup/` if full-scale active splits are desired.

---

## 18. Final Acceptance Decision

All 12 Phase 04 steps have been executed sequentially from actual code and datasets without fabrication, with complete statistical validation, regression safety (`309/309` tests, `13/13` spec gates), and full limitation disclosure.

ACCEPTED

