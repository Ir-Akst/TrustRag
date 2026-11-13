# 00 — Executive Summary: TrustRAG Full System Reality Check & Technical Audit

**Audit Timestamp (UTC):** `2026-11-12T17:38:51Z`
**Repository:** `c:\Users\Dell\Desktop\trustrag` (`HEAD = 713c54e2065b4cd37f63b2fb8c9a8bf3694ed831`, branch `main`)
**Host Environment:** `Windows-11-10.0.26200-SP0` | System Python `3.13.14` | Workspace `.venv313` (incomplete)
**Audit Mode:** Strictly read-only evidence-based technical verification (live execution, CLI subprocess probes, AST & dataset inspection, independent JSONL statistical recomputation)

---

## Overall Verdict: **`PARTIALLY FUNCTIONAL`**

| Composite Index | Recorded Value ([component_verdicts.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/component_verdicts.json)) | Reproduction Status from JSON Inventories | Summary Interpretation |
| :--- | :---: | :--- | :--- |
| **Component Readiness Score** | **`46.2%`** (weighted scalar) / **`45.86%`** (exact unweighted mean over `N = 14`) | Unweighted mean (`642 / 14 = 45.86%`) reproduces directly; `46.2%` per-component weight vector is **not exported** in `component_verdicts.json` (discrepancy documented below) | Functional in-memory TF-IDF/regex/extractive core pipeline, offset by Windows serving crash (`RED`), missing external data (`RED`), and missing neural training/weights (`BLACK`) |
| **Research-Paper Compliance Score** | **`28.0%`** (recorded scalar) | Item-level rubric weights are **not exported** in `component_verdicts.json`; underlying JSON/matrix counts show `0/7` full external datasets, `0/4` live neural SRM/weights, `0/28` research-scale parity | Software interfaces map ~`68%` of documented Paper A/B/C concepts, but execution relies on deterministic heuristics/proxies with zero trained weights or full-scale external corpora |

TrustRAG is **not a mock shell**—its core synchronous CPU pipeline (`G1 -> In-Memory TF-IDF Retriever -> G2 MSD -> Extractive Generator -> Answer Unicode Screen -> G3 Heuristic Verifier -> SRM DeterministicFallbackBackend`) executes end-to-end (`2.7 ms – 31.0 ms` warm per-query latency for this **local synchronous fallback implementation**, excluding any neural LLM/SRM inference). However, it is **not production-ready or research-complete**: `2/6` controlled end-to-end attacks leak poisoned facts into the final response (`atk_poisonedrag_stealth_factual` and `atk_duplicate_poison_3v1`), the HTTP serving/API layer crashes immediately on import on Windows (`ModuleNotFoundError: No module named 'resource'`), **zero model checkpoints exist within the verified repository search scope or Hugging Face hub cache**, and `6/7` target external research benchmarks contain `0` local records.

---

## 1. Score Transparency, Denominators & Audit Artifact Discrepancy

### A. Component Readiness Scoring & Verdict Treatment (`N = 14` Denominator)
All `14` subsystems in [component_verdicts.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/component_verdicts.json) are included in the full-system denominator (`N = 14`), with verdicts assigned under the strict 5-color audit scale:

| Verdict Color | Definition Applied | Subsystem Count (`N = 14`) | Subsystems & Recorded `readiness_pct` | Category Mean | How Treated in Overall Readiness |
| :--- | :--- | :---: | :--- | :---: | :--- |
| **`GREEN`** | Verified working end-to-end with real inputs/execution | **`0 / 14`** (`0.0%`) | None | `—` | Full readiness credit (`85–100%`) |
| **`YELLOW`** | Implemented cleanly in part, but limited scope, fallback/proxy, bypasses, or unverified live dependencies | **`9 / 14`** (`64.3%`) | `G1` (`68%`), `Retriever` (`45%`), `G2 MSD` (`52%`), `Generator` (`40%`), `G3` (`62%`), `Pipeline & CLI` (`65%`), `Adaptive` (`65%`), `Dashboard SPA` (`70%`), `Eval Harness` (`70%`) | `59.67%` (`537 / 9`) | Included in denominator with partial credit reflecting real execution gaps and bypasses |
| **`BLUE`** | Core execution/inference blocked by external OS, network, package, GPU, or weight dependency | **`1 / 14`** (`7.1%`) | `Small Reasoning Model (SRM)` (`25%`) | `25.00%` | Included in denominator (`N = 14`), receiving credit **only** for `SRMClient` schema, `<think>` parser, citation check, and `DeterministicFallbackBackend` (`0%` neural credit) |
| **`RED`** | Fails contract, crashes on import/host runtime, broken tests/tooling, or synthetic/missing data pipeline | **`3 / 14`** (`21.4%`) | `Serving & AIOHTTP API` (`15%`), `Datasets & Offline Acquisition` (`25%`), `Testing, Tooling & Deployment` (`35%`) | `25.00%` (`75 / 3`) | Included in denominator with low credit for static code/partial local utilities despite critical failures |
| **`BLACK`** | Core artifact or training capability missing | **`1 / 14`** (`7.1%`) | `Training, Fine-Tuning & Model Weights` (`5%`) | `5.00%` | Included in denominator (`5%` reflects scalar JSON calibrator files only; `0%` neural weights/scripts) |

- **Exact JSON Reproducibility Check (Unweighted vs Weighted):**
  - Summing the `14` `readiness_pct` integers in `component_verdicts.json`:
    `68 + 45 + 52 + 40 + 62 + 25 + 65 + 65 + 15 + 70 + 25 + 5 + 70 + 35 = 642`
    - **Unweighted Mean (`N = 14`):** `642 / 14 = 45.857%` (**`45.9%`**)
    - **Unweighted Mean Excluding `BLUE` (`N = 13`):** `617 / 13 = 47.46%`
  - **Documented Discrepancy:** `component_verdicts.json` records `"component_readiness_pct": 46.2` and `"research_compliance_pct": 28.0` as pre-summarized scalars **without** persisting the `14`-element subsystem weight vector or an item-level compliance rubric inside the JSON file. Because this correction must not invent missing weights post-hoc or alter existing JSON artifacts, `46.2%` (`+0.34 pp` above the unweighted mean `45.86%`) and `28.0%` are flagged as **not independently reproducible from `component_verdicts.json` alone**.

### B. What Reproduces Directly for Research Compliance
Cross-checking the saved machine-readable inventories yields these exact verifiable compliance denominators:
- **External Research Datasets ([dataset_inventory.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/dataset_inventory.json), `N = 7` targets):** `0/7` (`0.0%`) full-scale ready, `1/7` (`14.3%`) `PARTIALLY_READY` (`ragtruth`: `5/18,000` records = `0.028%` of canonical size), `6/7` (`85.7%`) `BLOCKED` (`0` local records).
- **Neural Models & SRM Backends ([model_inventory.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/model_inventory.json)):** `0` trained neural weights (`neural_checkpoints_found: []`), `0` training scripts (`training_scripts_found: []`), `1/4` SRM backends runnable offline (`deterministic_fallback`, `is_real_model: false`); `3/4` real model backends (`hf_local`, `local_ollama`, `openai_compatible`) unavailable.
- **28-Item Paper Traceability Ledger ([RESEARCH_COMPLIANCE_MATRIX.md](file:///c:/Users/Dell/Desktop/trustrag/reports/dataset_coverage_audit/RESEARCH_COMPLIANCE_MATRIX.md), `N = 28` items across Papers A, B, C):** `0/28` (`0.0%`) research-scale experimental reproduction (`0/9` Paper A, `0/11` Paper B, `0/8` Paper C), while ~`68%` of software concepts exist as interfaces, deterministic heuristics, or extractive proxies.

---

## 2. Research Specification Classification (Mandatory vs Proposed vs Comparative vs Optional)

> **Source Basis Note:** Raw PDFs (`TrustRAG_RAG_Security_Paper.pdf`, `HalluGuard`, `2508.02835v2.pdf`) are **absent** from the workspace. Classification below strictly follows the repository’s traceability documents ([RESEARCH_COMPLIANCE_MATRIX.md](file:///c:/Users/Dell/Desktop/trustrag/reports/dataset_coverage_audit/RESEARCH_COMPLIANCE_MATRIX.md), [phase10_research_traceability_matrix.md](file:///c:/Users/Dell/Desktop/trustrag/reports/phase10_research_traceability_matrix.md), and [configs/evaluation/phase10_eval.yaml](file:///c:/Users/Dell/Desktop/trustrag/configs/evaluation/phase10_eval.yaml)).

| Tier / Classification | Research Source | Components & Datasets | Implemented Reality & Gaps |
| :--- | :--- | :--- | :--- |
| **1. Mandatory TrustRAG Specification Requirements** | Paper B (`TrustRAG_RAG_Security_Paper.pdf`) & Phase 00–03 Core Specs | G1 canonicalization + query paraphrasing; Retriever; G2 6-signal MSD (`F1..F6`) + `floor(K/2)` cap; Pre-gen containment; Evidence-grounded Generator; G3 verifier + query consistency + re-answering; Core benchmarks (`RSB`, `HaluEval-QA`, `BoolQ`, `NQ`, `HotpotQA`, `MS MARCO`) | Heuristic/TF-IDF core runs (`G1`, `G3`, `F3..F6`); **gaps:** dense embeddings/FAISS missing, `F1`/`F2` `UNAVAILABLE` offline, LLM `q'` & generator LLM absent, `enable_reanswer: false` default, stealth factual poison & 3v1 breaches (`2/6`), `RSB`/`HaluEval`/`NQ`/`HotpotQA`/`MS MARCO` = `0` records |
| **2. Proposed Architectural Components** | Paper A (`HalluGuard` SRM integration in TrustRAG architecture) | Closed-book Qwen SRM (`Qwen/Qwen2.5-3B-Instruct`, `<think>` reasoning, 5-class span judgments); ORPO + LoRA training on `FineWeb -> Dclean -> HalluClaim`; evaluation on `RAGTruth (18k)` & `LLM-AggreFact` | Inference wrappers (`hf_local`, `local_ollama`, `openai_compatible`) and schema/fallback implemented (`BLUE`); **missing:** ORPO/LoRA training pipeline, local weights, `torch`/`transformers`; `RAGTruth` has `5/18,000` records, `LLM-AggreFact`/`FineWeb` = `0` |
| **3. Comparative Research Baselines** | Paper C (`2508.02835v2` FilterRAG / ML-FilterRAG) & Standard Baselines | `FilterRAG_Threshold`, `ML_FilterRAG`, `Combined_MSD_FilterRAG` (`Freq-Density` via intermediate SLM `a_j = SLM(q_i, d_j)`), `Original_RAG`, `SQuAD` | **Explicitly NOT mandatory TrustRAG runtime functionality.** FilterRAG is isolated in `evaluation/filterrag_experiment.py` (`MSDConfig.enable_freq_density = False`), defaults to `BLOCKED_NO_LIVE_SLM`, and runs offline only as `PROXY_ONLY` extractive heuristics (`ML_FilterRAG AUC = 0.2990`); `SQuAD` has `0` persisted rows |
| **4. Optional Enhancements** | Engineering / Phase 05–09 Extensions | `aiohttp` REST API (`src/trustrag/api/`), serving SLA wrappers (`src/trustrag/serving/`), vanilla JS Dashboard SPA (`frontend/src/`), adaptive threshold/policy controller (`src/trustrag/adaptive/`) | Adaptive framework implemented (`YELLOW`, though Platt causes `0.50`–`0.6667` FPR); Dashboard SPA unit-tested (`5/5` Node tests); API/Serving **`RED`** on Windows (`import resource` crash) |

---

## 3. Component Verdict Summary (14 Subsystems)

| Subsystem | Module | Verdict | Readiness | Key Verified Finding |
| :--- | :--- | :---: | :---: | :--- |
| **G1 Input Guardrail** | `src/trustrag/guardrails/input_guardrail.py` | `YELLOW` | `68%` | Blocks explicit directives, Cyrillic homoglyphs, fullwidth ASCII, malformed ZWJ; bypassed by Base64, word floods, & `"Ignore your safety rules"`; false-flags benign ZWSP (`0.45`) |
| **Trust-Aware Retriever** | `src/trustrag/retrieval/retriever.py` | `YELLOW` | `45%` | Ephemeral `TfidfVectorizer` (1–2 ngrams) + G2 trust blending; no dense vectors/FAISS, no `save`/`load`, silent `dup_1#1` ID mutation |
| **G2 Multi-Signal Detector (MSD)** | `src/trustrag/detection/msd.py` | `YELLOW` | `52%` | Offline uses `4/6` signals (`F1`/`F2` `UNAVAILABLE`); stealth factual poison scores `0.9283 (CLEAN)`; 3v1 repetition attacks rank `CLEAN` (`0.7834`) |
| **Answer Generator** | `src/trustrag/generation/generator.py` | `YELLOW` | `40%` | Extractive sentence copier with `[doc_id]` citations + fail-closed abstention; no built-in OpenAI/Ollama/HF LLM client |
| **G3 Output Evidence Verifier** | `src/trustrag/verification/output_verifier.py` | `YELLOW` | `62%` | `25/25` Phase 08 linguistic regression probes pass (`-10 C` vs `10 C`); `2/4` (`0.50`) unseen probes in Phase 10 `canonical_v2`; phrased unit conversion fails (`0.60 < 0.65`); low-quality self-matches `TRUSTED` |
| **Small Reasoning Model (SRM)** | `src/trustrag/srm/client.py` | `BLUE` | `25%` | Default `backend: disabled` runs `halluguard-srm-fallback`; `hf_local` (missing checkpoint/`torch`), `local_ollama` (`WinError 10013`), `openai_compatible` (no key) unavailable offline |
| **End-to-End Pipeline & CLI** | `src/trustrag/pipeline/trustrag_pipeline.py` | `YELLOW` | `65%` | CLI `--query` succeeds (`exit 0`, cold subprocess `7.6–8.1 s`); `--health`/`--adaptive` crash on Windows (`resource`); `12/15` BoolQ utility, `2/6` controlled attacks leak poison |
| **Adaptive Calibration & Policy** | `src/trustrag/adaptive/` | `YELLOW` | `65%` | Validated SHA-256 JSON Platt/Temperature calibrators & rollback; Platt triggers `0.50`–`0.6667` FPR on `knowledge_poisoning` (`b=8, c=8`, net zero accuracy gain) |
| **Serving & AIOHTTP API** | `src/trustrag/serving/service.py` | `RED` | `15%` | Crashes on import on Windows (`import resource` line 7); blocks `trustrag.api.*` and `8` test files; `pyproject.toml` lists `fastapi`/`uvicorn` while code uses `aiohttp` |
| **Dashboard Frontend (SPA)** | `frontend/src/` | `YELLOW` | `70%` | Vanilla JS SPA with real `fetch('/api/v1/*')` calls (`5/5` Node tests pass); live serving blocked on Windows by backend crash |
| **Datasets & Offline Acquisition** | `src/trustrag/data/` | `RED` | `25%` | `6/7` target external datasets missing (`0` records), `ragtruth` `5/18k`, `custom_security` uses 8 cyclic templates with split leakage; `7` loaders ignore `offline=True` |
| **Training & Model Weights** | Workspace + HF Hub Cache Scope | `BLACK` | `5%` | `0` model checkpoints in repo scope & HF hub cache, `0` ORPO/LoRA scripts, `torch`/`transformers`/`peft`/`trl` absent; `2` scalar JSON calibrators exist |
| **Evaluation & Stats Harness** | `src/trustrag/evaluation/` | `YELLOW` | `70%` | Independent recomputation matches Phase 10 JSONL `100%`; `suites.py:1843` crashes on Windows (`resource`); FilterRAG baselines are `PROXY_ONLY` |
| **Testing, Tooling & Deployment** | `tests/`, `pyproject.toml` | `RED` | `35%` | `644` passed, `3` failed, `2` deselected, `8` files blocked on Windows; `.venv313` fails `35` collections; `ruff` `24,503` lines; `mypy` `43` errors; `0` Docker/CI |

---

## 4. Verification Precision Details (Tests, Models, G3, Datasets & Latency)

### A. Test Suite Accounting (Collected vs Executed vs Blocked)
- **Static Repository AST Inventory (`50` files):** `665` `def test_*` functions (`42/50` files mock-free).
- **Windows Collection Block (`8` files, `48` static `def test_*` functions):** Blocked prior to collection by `ModuleNotFoundError: No module named 'resource'` (`serving/service.py:7`): `test_api_and_integration.py`, `test_srm_and_serving.py`, `test_phase_06_generalization_and_serving.py`, `test_phase_08_step10_serving_reliability.py`, `test_phase_09_api.py`, `test_phase_09_fullstack_integration.py`, `test_phase_11_independent_audit.py`, and `test_phase_11_remediation.py`. (An un-ignored `pytest` call on system Python aborts immediately during collection with `7` collection errors.)
- **Runnable Suite on System Python `3.13.14` (`42` importable files, ignoring the `8` blocked files):**
  - **Collected items:** **`649`** (including parametrized expansions)
  - **Deselected (`-m "not integration"`):** **`2`** (`test_boolq_sample_acquisition`, `test_squad_sample_acquisition`)
  - **Executed items:** **`647`** -> **`644 passed, 3 failed`** (`54.87 s`)
    - Failures: `test_foundation.py::test_logger_json_output` & `test_logger_filters_secret` (handler caching + `capfd` order pollution; **pass `9/9` standalone in `4.72 s`**) + `test_phase_04_suites.py::test_srm_ablation_and_perf_smoke` (`import resource` at `suites.py:1843`).
- **Workspace `.venv313`:** Fails with **`35` collection errors** (`missing scikit-learn`, `aiohttp`, plus `resource`).
- **Frontend Node Suite (`node --test frontend/tests/dashboard.test.mjs`):** **`5/5` passed** (`0` failed, `857 ms`).

### B. Verified Model Checkpoint & Inference Scope
1. **Repository Checkpoint Search (`c:\Users\Dell\Desktop\trustrag`):** Recursive search across `*.pt`, `*.pth`, `*.safetensors`, `*.bin`, `*.gguf`, `*.onnx`, `*.pkl`, `*.joblib` found **`0` model weights in TrustRAG’s source, config, or data paths** (the only hits in the tree were 2 third-party package files inside `.venv313\Lib\site-packages\`: `numpy/.../astype_copy.pkl` (`716` B) and `a1_coverage.pth` (`206` B)). Only `platt_calibrator_v1.json` and `temperature_calibrator_v1.json` exist under `configs/adaptive/`.
2. **Hugging Face & Ollama Local Cache Inspection:** `C:\Users\Dell\.cache\huggingface\hub` contains only `datasets--alan-turing-institute--turing-synthetic-radar-dataset` (**`0` cached `models--*` checkpoints**; `Qwen/Qwen2.5-3B-Instruct` is absent). `C:\Users\Dell\.ollama\models` does not exist on this host.
3. **External Model Availability:** `torch`, `transformers`, `peft`, and `trl` are not installed; `hf_local` (missing local checkpoint/`torch`), `local_ollama` (`[WinError 10013]`), and `openai_compatible` (`Missing API credential`) all report `available=False`.
4. **Model Training Evidence:** `training_scripts_found: []` (`0` ORPO/LoRA/SFT training scripts exist). Only logistic/temperature calibration JSONs and `ML_FilterRAG` proxy logistic regression were fitted on `train` splits.
5. **Live Inference Verification:** Live execution was verified **only** for `DeterministicFallbackBackend` (`halluguard-srm-fallback`, `is_real_model=False`) and extractive sentence generation (`mode: extractive`). Real neural SRM and neural LLM inference are **`NOT VERIFIED`**.

### C. G3 Verification Evidence Precision
- **Phase 08 Linguistic Regression Suite (`25/25`, `100%`):** Verifies targeted deterministic regression cases (negation polarity, temporal years, `DEF-09` negative sign `-10 C` vs `10 C`, active/passive swaps). **This is a unit regression suite, NOT general-purpose hallucination detection accuracy.**
- **Phase 10 Unseen Probes (`2/4`, `50.0%` in `phase10_canonical_v2`; `4/4` in `phase11_remediated`):** In `canonical_v2`, G3 missed `unseen_num_contra` and `unseen_temp_contra` as `INSUFFICIENT_EVIDENCE` (`Macro F1 = 0.50`) before Phase 11 heuristic adjustments; the probe set contains only `4` items. External hallucination coverage consists only of `ragtruth` (`n=5`, `acc=0.60`, `fpr=0.6667`), `wice` (`n=3`), and `expertqa` (`n=3`).
- **Known Architectural Weaknesses Confirmed Live:** Unit conversion (`"1000 mg"` vs `"1 g"` passes at `1.00`) **fails phrased equivalents** (`"1000 mg per day"` vs `"1 g daily"` -> `INSUFFICIENT_EVIDENCE`, lexical coverage `0.60 < 0.65`); multi-clause synthesis falsely triggers conflict (`01_clean_factual`: freeze `0 C` vs boiling `100 C` -> `UNVERIFIED`); extractive vague text self-grounds (`09_low_quality_ambiguous` -> `TRUSTED`).

### D. Dataset Provenance & Usage Separation
| Category | Datasets & Exact Counts |
| :--- | :--- |
| **Missing (`0` local records)** | `natural_questions`, `hotpotqa`, `ms_marco`, `squad`, `fineweb`, `halueval`, `llm_aggrefact`, `rsb` (`8` adapters; `6/7` target external benchmarks in `phase10_eval.yaml` absent) |
| **Partially Available** | `ragtruth` (`5` records vs `18,000` target, `0.028%`), `boolq` (`100` sample records `70/15/15`, `~0.63%` of full corpus), `wice` (`3` smoke records), `expertqa` (`3` smoke records) |
| **Locally Available** | `boolq` (`100`), `ragtruth` (`5` in `test.jsonl`), `wice` (`3`), `expertqa` (`3`), `custom_security` (`2,000` raw + `100` backup + `benchmarks`/`benchmarks_backup`) |
| **Synthetic Datasets** | `custom_security` (`2,000` records cycling `_TEMPLATES[i % 8]` in [security_generator.py](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/data/benchmarks/security_generator.py#L28-L150)) + derived `benchmarks*/{adversarial_robustness, knowledge_poisoning}` (with `5` / `3` / `2` `target_query` overlap across splits and `8`/`2` exact duplicates in `benchmarks/`) |
| **Consumed During Training / Fitting** | **`0` neural weights trained.** Platt (`n=428`) and Temperature (`n=478`) scalar calibrators fitted on `benchmarks_backup/{adv_rob, kp, clean_rag}/train.jsonl`; `ML_FilterRAG` proxy fitted on `n=403` train rows |
| **Consumed During Evaluation** | `benchmarks_backup/{adv_rob n=40, kp n=24, clean_rag n=15}` in Phase 10 bundles; `ragtruth` smoke (`n=5`); `FilterRAG` proxy (`64` sec + `75` clean); live BoolQ probe (`n=15`); Phase 08 linguistic probes (`n=25`) |

### E. Performance & Latency Qualification
All sub-`35 ms` warm latencies (`2.7 ms – 31.0 ms` across the 10 E2E traces; `27.24 ms` mean on BoolQ `n=15`) apply **strictly to the existing synchronous CPU-only local implementation using in-memory `TfidfVectorizer`, deterministic regex/heuristic G1/G2/G3 logic, extractive copy-paste generation, and `DeterministicFallbackBackend` (`0.01–0.377 ms`)**. They do **not** represent latency under dense vector retrieval, LLM generation, or neural SRM inference. Cold subprocess CLI startup takes `7.62 s – 8.44 s` (`cold_import_init_ms = 22,101.71 ms` in `run_all_validations.py`).

---

## Direct Evidence-Based Answers to the 15 Section-19 Audit Questions

1. **Does TrustRAG run end-to-end with zero crashes on this host?**
   **No.** CLI `--query` runs (`exit 0`), but `python -m trustrag.pipeline.cli --health`, `--adaptive`, `trustrag.serving`, `trustrag.api.*`, and `test_srm_ablation_and_perf_smoke` crash on Windows 11 with `ModuleNotFoundError: No module named 'resource'` (`serving/service.py:7`, `evaluation/suites.py:1843`).
2. **Are canonical research datasets actually downloaded and used?**
   **No.** `6/7` canonical external datasets (`natural_questions`, `hotpotqa`, `ms_marco`, `halueval`, `llm_aggrefact`, `rsb`) have `0` records (`BLOCKED`); `ragtruth` has `5/18,000` records (`PARTIALLY_READY`, `acc=0.60`, `parity_claimed=False`). Local evaluation uses `boolq` (`100`), `wice`/`expertqa` (`3` each), and synthetic `custom_security`.
3. **Is `custom_security` real or synthetically generated?**
   **100% synthetically generated.** [security_generator.py](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/data/benchmarks/security_generator.py#L28-L150) deterministically cycles `_TEMPLATES[i % 8]` with `[<topic> - Item <variation>]`.
4. **Is there data leakage across train/val/test splits?**
   **Yes.** Exact `target_query` overlap exists across `train`/`val`/`test`: `5` in `benchmarks_backup/adversarial_robustness`, `3` in `benchmarks_backup/knowledge_poisoning`, and `2` (`train`/`test`) in `benchmarks/{adversarial_robustness, knowledge_poisoning}`, plus `8` train / `2` val exact document duplicates in `benchmarks/adversarial_robustness`.
5. **Are any neural models trained, fine-tuned, or loaded locally?**
   **No.** Within the verified repository and HF hub cache scope, `0` neural model weights, `0` ORPO/LoRA training scripts, and `0` cached `models--*` directories exist; `configs/base.yaml` defaults to `srm.backend: disabled` and `generation.mode: extractive`.
6. **Is the Small Reasoning Model (SRM) real or a fallback?**
   **Deterministic rule-based fallback (`BLUE`).** Live runs execute `DeterministicFallbackBackend` (`halluguard-srm-fallback`, `is_fallback=True`, `execution_status="DISABLED"`); `hf_local`, `local_ollama`, and `openai_compatible` report `available=False` offline (`NOT VERIFIED`).
7. **Does G1 reliably block prompt injections and obfuscations without hurting benign queries?**
   **Partially.** Blocks `direct_injection` (`0.90`), `indirect_html` (`0.85`), `role_hijack` (`0.95`), `cyrillic_confusable` (`1.0`), `fullwidth_obf` (`1.0`), and rejects `DEF-08` paraphrase drift; bypassed (`ALLOW`, `0.0`) by Base64, word floods, and `"Ignore your safety rules"`, while false-flagging benign ZWSP (`FLAG`, `0.45`).
8. **Does the Retriever use dense semantic search and persist its index?**
   **No.** Ephemeral in-memory `TfidfVectorizer` (1–2 grams) + lexical overlap (`has_save_method=False`, `has_load_method=False`), no FAISS/dense vectors/chunking, silent `dup_1 -> dup_1#1` ID mutation.
9. **Does G2 MSD detect PoisonedRAG factual poisoning and coordinated repetition offline?**
   **No.** `F1`/`F2` are `UNAVAILABLE` offline; stealth factual `p_out` scores `0.9283 (CLEAN)`, `3v1` duplicates score `CLEAN (0.7834)`, and `removal_cap_limit=1` lets repeat poisons leak in `2/6` controlled E2E attacks.
10. **Does G3 Output Verifier catch hallucinations, negations, numeric conflicts, and unit equivalences?**
    **Partially.** Passes `25/25` Phase 08 linguistic regression probes (`DEF-09` fixed), but scored `2/4` (`0.50`) unseen probes in Phase 10 `canonical_v2`, fails phrased units (`"1000 mg per day"` vs `"1 g daily"`, `0.60 < 0.65`), falsely flags `01_clean_factual` as `UNVERIFIED`, and self-grounds vague `lq_1` (`09`) as `TRUSTED`.
11. **Are G1/G2/G3 thresholds and adaptive calibrators helping without collateral damage?**
    **Mixed / unsafe on Platt.** `temperature_calibrator_v1.json` preserves `FPR=0.0`; `platt_calibrator_v1.json` inflates clean FPR to `0.50` standalone and `0.6667` in Phase 10 E2E on `knowledge_poisoning` (`b=8, c=8`, net zero accuracy gain `0.50 -> 0.50`).
12. **Do the AIOHTTP REST API and Dashboard Frontend work live on this Windows host?**
    **API: No (`RED`); Frontend unit tests: `5/5`, live UI blocked.** `trustrag.api.*` crashes importing `resource` (`service.py:7`), and `pyproject.toml` lists `fastapi`/`uvicorn` instead of `aiohttp`.
13. **Are previously reported Phase 10 numbers mathematically consistent with their saved artifacts?**
    **Yes (`100%` arithmetic match), with methodological caveats.** Per-example JSONLs reproduce `bundle.json` counts/accuracies, but evaluate small synthetic/BoolQ sets (`n=15–40`), disabled SRM fallback, and `PROXY_ONLY` FilterRAG heuristics.
14. **Does the test suite pass cleanly, and is the code lint/type-clean?**
    **No.** Across `42` Windows-importable files (`649` collected), **`644 passed, 3 failed, 2 deselected`** (`8` serving/API files blocked on collection; `.venv313` hits `35` errors; `ruff` outputs `24,503` lines; `mypy src` reports `43` errors in `6` files).
15. **What are the top 3 blocking gaps before TrustRAG fulfills its research and production goals?**
    1. **Cross-Platform Serving & Packaging:** Guard `import resource` (`service.py:7`, `suites.py:1843`) and align `pyproject.toml`/`.venv313` (`aiohttp`, `scikit-learn`).
    2. **Semantic Security & Neural Pipeline:** Add dense retrieval/FAISS persistence, active G2 `F1`/`F2` & inter-doc contradiction checks (closing `2/6` poison leaks), fix G3 phrased units/coordinated-clause false conflicts, and implement/train ORPO SRM + neural LLM generation.
    3. **Genuine External Benchmarks:** Acquire canonical external corpora (`NQ`, `HotpotQA`, `MS MARCO`, `HaluEval`, `RAGTruth 18k`, `LLM-AggreFact`, `RSB`), fix `offline=True` HF retries, and eliminate synthetic 8-template split leakage.

---

## Navigation Index (24 Deliverables in `reports/reality_audit/`)

- **Machine-Readable JSONs:** [component_verdicts.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/component_verdicts.json) | [dataset_inventory.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/dataset_inventory.json) | [model_inventory.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/model_inventory.json) | [api_inventory.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/api_inventory.json) | [experiment_results.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/experiment_results.json)
- **Detailed Reports (`01`–`18`):** [01_REPOSITORY_DISCOVERY.md](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/01_REPOSITORY_DISCOVERY.md) through [18_EVIDENCE_AND_EXECUTION_LOG.md](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/18_EVIDENCE_AND_EXECUTION_LOG.md)
