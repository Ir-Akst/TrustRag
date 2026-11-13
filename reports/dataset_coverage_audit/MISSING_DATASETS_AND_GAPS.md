# TrustRAG — Missing Datasets, Coverage Gaps & Misleading-Claim Audit

**Audit Date:** 2026-11-12  
**Repository:** `c:\Users\Dell\Desktop\trustrag` (`main` @ `1eeb831` + uncommitted minimization)

---

## 1. Master Inventory of Missing Datasets & Coverage Fractions

By **canonical dataset identity** (`20` deduplicated external datasets across Section 3 + `1` internal synthetic `custom_security` = `21` canonical entities; `36` total Section 3 items):

- **External Section 3 Coverage (Any physical data on disk, incl. hand-written smokes):** **`4 / 36` (`11.1%`)** by Section 3 item count (`BoolQ`, `RAGTruth`, `WiCE`, `ExpertQA`), or **`4 / 20` (`20.0%`)** of deduplicated external corpora.
- **Genuine Upstream External Data on Disk (`>=1` real record):** **`1 / 36` (`2.8%`)** (`BoolQ` `100` validation rows only; `SQuAD` tested `5` transient rows never persisted; `RAGTruth`/`WiCE`/`ExpertQA` hold only `3–5` synthetic/handcrafted smoke rows).
- **Full Research-Scale Corpus Parity Achieved:** **`0 / 36` (`0.0%`)**.
- **Configured `1eeb831:configs/datasets.yaml` Volume Realized:** Only **`BoolQ`** (`100`) + smoke fixtures (`11`) out of **`268,000`** configured external target records (`0.041%` by record volume; `4/12` = `33.3%` configured external entries non-empty at smoke level).

---

## 2. Exact Enumeration of Missing & Incomplete Datasets

### Category A — Configured External Datasets With Zero Persisted Records (`8` Core Corpora)

| Dataset | Configured Source (`1eeb831:configs/datasets.yaml`) | Target (`limit`) | Actual Disk Records (`WT` & `1eeb831`) | Root Cause / Blocker |
|---|---|---:|---:|---|
| **Natural Questions (`natural_questions`)** | `google-research-datasets/natural_questions` | `30,000` | `0` | Offline environment; never downloaded |
| **HotpotQA (`hotpotqa`)** | `hotpotqa/hotpot_qa` (`distractor`) | `30,000` | `0` | Offline environment; unit-tested with offline mock only |
| **MS-MARCO (`ms_marco`)** | `microsoft/ms_marco` (`v1.1`) | `100,000` | `0` | Offline environment; never downloaded |
| **SQuAD (`squad`)** | `rajpurkar/squad` (`plain_text`) | `20,000` | `0` persisted | `5` transient integration rows (`pytest -m integration`) never saved |
| **HaluEval-QA (`halueval`)** | `pminervini/HaluEval` (`qa`) | `10,000` | `0` | Offline environment; temp-fixture unit test only |
| **LLM-AggreFact (`llm_aggrefact`)** | `lytang/LLM-AggreFact` | `5,000` | `0` | Gated Hugging Face agreement + offline block; eval-only restriction |
| **RSB (`rsb`)** | `arXiv:2505.18543` | `5,000` | `0` | No public download URL; no local files provided (`local_import` stub only) |
| **FineWeb (`fineweb`)** | `HuggingFaceFW/fineweb` (`sample-10BT`) | `20,000` | `0` | Blocked/deferred in Phase 02 (`AcquisitionManager` P0–P2 policy) |

### Category B — Truncated or Synthetic-Smoke-Only Datasets (`5` Existing Datasets)

| Dataset | Target / Canonical Full Scale | Actual Local Rows (`WT` / `1eeb831`) | Coverage % | Specific Processing / Authenticity Gap |
|---|---:|---:|---:|---|
| **`BoolQ`** | `10,000` (full ~`15,942` / val `3,270`) | `100` (`+10` WT `clean_rag`) | `1.0%` target (`0.63%` full) | Tiny validation slice only; `BoolQAdapter` left `title=""` and `relevant_document_ids=[]`; `custom_splits/` deleted from WT |
| **`RAGTruth`** | `18,000` | `5` (`test.jsonl` in `hallucination/train+val`) | `0.028%` | `raw_train` download **FAILED**; `5` `test.jsonl` rows are hand-written mock records (`ragtruth_qa_001..`), **0 rows in `hallucination/test.jsonl`** |
| **`WiCE`** | `5,000` (upstream `~1,967` claims) | `3` (`hallucination/train+test`) | `0.06%` | Hand-written 3-row smoke fixture (`wice_001..`); unlogged in `acquisition_log.jsonl` |
| **`ExpertQA`** | `5,000` (upstream `~2,177`) | `3` (`hallucination/train+test`) | `0.06%` | Hand-written 3-row smoke fixture (`expertqa_001..`); unlogged in `acquisition_log.jsonl` |
| **`custom_security`** | `5,000` (`2,000` generated raw in `1eeb831`) | `50` WT / `400` backup (`2,000` raw) | `1%` WT / `8%` backup / `40%` raw | Synthesized deterministically from **only `8` static templates**; `10/30` WT `adv` duplicates; `100%` cross-split query leakage; `BENIGN_INSTRUCTION_LIKE` label defect |

### Category C — Completely Unimplemented Research Sub-Benchmarks, Attacks & Pretraining Pipelines (`23` Section 3 Items)

1. **`RSB` 13 Attack Methods (`0` data, `0` attack generators):**
   - `REFERENCE ONLY` (named in Phase 07 reports, unimplemented): `BPRAG`, `WPRAG`, `AGGD`, `CRAG-AS`, `CRAG-AK` *(cited as `CRAG`)*, `AgentPoison`, `BadRAG`, `Phantom`.
   - `MISSING` (zero code or report mentions): `BPI`, `WPI`, `JamInject`, `JamOracle`, `JamOpt`.
2. **Corpus Composition Stress Tests (`0` data, `0` mentions):** `EX-M`, `EX-L`.
3. **`LLM-AggreFact` Component Benchmarks (`0` rows, `0` mentions, outside mock `WiCE`/`ExpertQA`):** `AGGREFACT`, `TofuEval`, `REVEAL`, `ClaimVerify`, `FactCheck-GPT`, `LFQA`.
4. **HalluGuard Pretraining / ORPO Data Pipeline (`0` data, `0` scripts):** `Dclean`, `HalluClaim`, `HalluClaim-pref`.

---

## 3. Implementation, Environment, & Post-Minimization Gaps

1. **Phase 10 Completely Absent:** Phases `01–09` exist in Git commit history; Phase `10` has `0` files, `0` commits, `0` tags, and `0` reports.
2. **Uncommitted Working-Tree Regression & Broken Re-Executability:** The post-Phase 09 minimization pass deleted `1eeb831:src/trustrag/data/`, `src/trustrag/evaluation/`, `tools/`, `configs/datasets.yaml`, `data/raw/`, `data/benchmarks_backup/`, `data/processed/boolq/custom_splits/`, and prior `reports/`. While runtime `api`/`pipeline`/`srm` code remains in WT:
   - End-to-end benchmark evaluation suites (`phase07_benchmark_audit.py`, `phase08_comprehensive_benchmark.py`, `suites.py`, `filterrag_experiment.py`) cannot be re-executed from WT.
   - Calibration artifacts [platt_calibrator_v1.json](file:///c:/Users/Dell/Desktop/trustrag/configs/adaptive/platt_calibrator_v1.json) (`n=428`) and [temperature_calibrator_v1.json](file:///c:/Users/Dell/Desktop/trustrag/configs/adaptive/temperature_calibrator_v1.json) (`n=478`) remain in WT fitted on deleted `data/benchmarks_backup/`, while surviving WT `data/benchmarks/` holds only shrunk `10/20/30/11` splits (with `10/30` duplicates in `adv`).
3. **Zero Neural Models / Heavy ML Stack:** `torch`, `transformers`, `peft`, and `trl` are all uninstalled; Ollama is unreachable; `0` `.safetensors`/`.gguf`/`.pt`/`.bin` checkpoints exist. Consequently, G2 `F1_perplexity` (`disabled`), dense G2 `F2_embedding_norm` (`require_configured` inactive), neural G3/HalluGuard 4B SRM (`DeterministicFallbackBackend`), trusted LLM `q'` paraphraser, and FilterRAG generative SLM `a_j = SLM(q_i, d_j)` are non-operational in practice.

---

## 4. Audit of Unverified, Overstated, or Misleading Historical Claims

| Artifact / Claim Location | Claim Found in Historical / Repo Files | Contradicting Empirical Evidence | Risk Level |
|---|---|---|---|
| `1eeb831:reports/phase_02_report.md` (`Section B & D`) | Claimed `ragtruth` (`10` raw), `wice`, `expertqa`, `boolq` `ACQUIRED`, and all 4 benchmarks **`Quality Status: PASS` / `Leakage Detected: NO (PASS)`** (`Clean RAG 100 / KP 150 / Adv 250`). | `1eeb831:data/raw/acquisition_log.jsonl` proves `ragtruth` `raw_train` **FAILED** and `raw_test` acquired only **`5`** hand-written mock rows (not `10` real rows); `benchmarks_backup` had **`100%` cross-split query leakage** (`3/3` in KP, `5/5` in Adv) & **`100%` template overlap**; `BENIGN_INSTRUCTION_LIKE` mislabeled 50% of controls as `"poisoned"`. | **HIGH** |
| `1eeb831:data/benchmarks/adversarial_robustness/` (`Ph02` -> WT) | Active `data/benchmarks/` retained shrunk `10/20/30` splits alongside `benchmark_validation_summary.json` / build errors. | Active `adversarial_robustness` contains **`10 / 30` (`33.33%`) exact duplicate records** (`8/22` train, `2/4` val), directly contradicting Phase 02's `"Duplicate Records: 0"` claim (which applied only to the backup build). | **HIGH** |
| `1eeb831:reports/evaluation/phase06_comprehensive_benchmark.json` (Ph06) | Evaluated `platt-mixed-v1` adaptive pipeline across `boolq/validation.jsonl` (`N=100`) as a Clean RAG test benchmark. | `70 / 100` (`70%`) of `boolq/validation.jsonl` was identical to `benchmarks_backup/clean_rag/train.jsonl` used to train `platt-mixed-v1`, inflating/contaminating clean calibration stats (exposed later in Phase 07). | **HIGH** |
| [configs/benchmark_reference.json](file:///c:/Users/Dell/Desktop/trustrag/configs/benchmark_reference.json) (`L781-827`, copied from `phase08_comprehensive_benchmark.json`) | Labels `"ragtruth"` as **`"status": "PARTIALLY_READY"`** (`evaluated_records: 5`) with `paper_reference: "Niu et al., 2024"`, implying 5 partial records from RAGTruth. | Forensic inspection of `ragtruth_qa_001`..`ragtruth_data_005` confirms all 5 rows are **synthetic/hand-authored mock test fixtures**, **not** authentic records sampled from ParticleMedia/RAGTruth. *(Phase 07/08 correctly refused `parity_claimed=true`, but the `"PARTIALLY_READY"` label masks synthetic fixture provenance.)* | **MEDIUM** |
| `1eeb831:src/trustrag/evaluation/suites.py` (`boolean_exact_match`) | Computed `boolean_exact_match = 0.0` for `Original_RAG` & `TrustRAG` on BoolQ `clean_rag/test`. | Pipeline `AnswerGenerator` is strictly **extractive** (returns passage sentences), never generating `"true"`/`"false"`, making `boolean_exact_match = 0.0` a pipeline-task format mismatch rather than QA semantic failure. | **LOW** |

