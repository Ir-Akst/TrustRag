# TrustRAG — Master Dataset Inventory (Phases 01–10 Audit)

**Audit Date:** 2026-11-12  
**Repository:** `c:\Users\Dell\Desktop\trustrag`  
**Git Branch / HEAD:** `main` @ [`1eeb831`](file:///c:/Users/Dell/Desktop/trustrag/.git/HEAD) (*Merge pull request #5 from Ir-Akst/phase-9*), with uncommitted working-tree repository minimization/consolidation changes preserved intact.  
**Scope:** Both **(a) Current Working Tree** and **(b) Pre-Minimization Baseline (`1eeb831`)**.

---

## 1. Executive Summary & Dual-State Repository Reality

An audit of TrustRAG requires inspecting two distinct states simultaneously:
1. **Current Working Tree (Post-Minimization Uncommitted State):** Contains **13 JSONL data files** (`161` total records, `162.8 KB` across `data/processed/boolq/` and `data/benchmarks/`), **2 calibration artifacts** ([platt_calibrator_v1.json](file:///c:/Users/Dell/Desktop/trustrag/configs/adaptive/platt_calibrator_v1.json), [temperature_calibrator_v1.json](file:///c:/Users/Dell/Desktop/trustrag/configs/adaptive/temperature_calibrator_v1.json)), and **1 static benchmark snapshot** ([benchmark_reference.json](file:///c:/Users/Dell/Desktop/trustrag/configs/benchmark_reference.json)). All dataset loaders (`1eeb831:src/trustrag/data/`), `1eeb831:configs/datasets.yaml`, `1eeb831:data/raw/`, `1eeb831:data/benchmarks_backup/`, `1eeb831:data/processed/boolq/custom_splits/`, and `1eeb831:src/trustrag/evaluation/` were removed in the uncommitted minimization pass.
2. **Pre-Minimization Git Baseline (`1eeb831`):** Contains `13` dataset adapter modules (`1eeb831:src/trustrag/data/loaders/*.py`), acquisition/splitting/quality tooling, `2,111` raw records (`2,000` synthetic `custom_security` + `100` backup + `11` smoke hallucination records), `100` processed BoolQ records, `511` `benchmarks_backup` records (`100` Clean RAG, `150` Knowledge Poisoning, `11` Hallucination, `250` Adversarial Robustness), `71` active `data/benchmarks` records, and `212` evaluation output files (`82` JSON runs) under `1eeb831:reports/evaluation/`.

> **Critical Provenance Finding:** Only **BoolQ** (`100` records) contains genuine records acquired from an external upstream dataset. The cached files for `ragtruth` (`5` rows), `wice` (`3` rows), and `expertqa` (`3` rows) are **hand-authored / synthetic smoke fixtures** mimicking upstream schemas, not authentic subsets extracted from ParticleMedia/RAGTruth, ryokamoi/wice, or chaitanyamalaviya/ExpertQA. All security datasets (`custom_security`, `knowledge_poisoning`, `adversarial_robustness`) are **100% synthetic** outputs from `8` hardcoded templates.

---

## 2. Deduplicated Canonical Dataset Summary Counts

Counting by **canonical dataset identity** (avoiding double-counting `data/benchmarks/*` composite splits that repackage `boolq`, `custom_security`, `ragtruth`, `wice`, and `expertqa`, and treating the 13 RSB attack methods + 2 `EX-M`/`EX-L` variants as benchmark scenarios rather than 15 independent source corpora):

| Metric | Count | Canonical Entities Included / Explanation |
| --- | ---: | --- |
| **Total Section 3 Listed Items Investigated** | **36** | Groups A (`5`), B (`14`: `RSB` + `13` attack methods), C (`2`), D (`11`), E (`4`) |
| **Repo Non-Canonical Datasets Discovered** | **1** | `custom_security` (`TrustRAG-Synthetic-Security-Benchmark-v1.0`, synthetic generator) |
| **Total Deduplicated Canonical Datasets** | **21** | External: `5` QA (`NQ`, `HotpotQA`, `MS-MARCO`, `SQuAD`, `BoolQ`) + `1` Security (`RSB` encompassing `13` attack methods & `2` corpus variants) + `11` Hallucination (`HaluEval-QA`, `RAGTruth`, `LLM-AggreFact`, `AGGREFACT`, `TofuEval`, `WiCE`, `REVEAL`, `ClaimVerify`, `FactCheck-GPT`, `ExpertQA`, `LFQA`) + `3` Synthetic/Pretrain (`FineWeb`, `Dclean`, `HalluClaim` incl. `-pref`) + **`1`** Repo Internal (`custom_security`). *(If `HalluClaim` and `HalluClaim-pref` are counted separately: `22`; if sub-benchmarks inside `LLM-AggreFact` are collapsed: `15`.)* |
| **Physically Downloaded / Present on Disk (`>=1` row)** | **5** *(4 ext + 1 internal)* | `BoolQ` (`100` real), `RAGTruth` (`5` smoke), `WiCE` (`3` smoke), `ExpertQA` (`3` smoke), `custom_security` (`2,000` raw `1eeb831` / `50` WT / `400` backup `1eeb831`) |
| **Genuine External Downloads (`>=1` real upstream row)** | **1** | `BoolQ` (`100` / `~16,000` validation records). `SQuAD` had `5` transient integration-test rows never saved to disk. |
| **Preprocessed (`>=1` usable artifact)** | **5** *(4 ext + 1 internal)* | `BoolQ`, `RAGTruth`, `WiCE`, `ExpertQA`, `custom_security` (via `data/benchmarks/` & `data/processed/`) |
| **Integrated into TrustRAG Components** | **5** *(physically)* + `8` *(stub adapters in `1eeb831`)* | Physically consumed by G1/G2/G3/Adaptive/API: `BoolQ`, `RAGTruth`, `WiCE`, `ExpertQA`, `custom_security`. Historical `1eeb831` code-only stubs (`0` data): `NQ`, `HotpotQA`, `MS-MARCO`, `SQuAD`, `RSB`, `HaluEval`, `LLM-AggreFact`, `FineWeb`. |
| **Used in Model / Calibrator Training (`TRAINING USED`)** | **2** *(no neural weights)* | `BoolQ` (`clean_rag/train`) + `custom_security` (`kp/train` & `adv/train`) — used ONLY to fit Platt & Temperature logistic/scalar calibrators and an offline ML-FilterRAG logistic proxy; **zero LLM/SRM/NLI weights trained**. |
| **Used in Validation (`VALIDATION USED`)** | **5** | `BoolQ`, `custom_security`, `RAGTruth` (`1` row in `hallucination/val`), plus `WiCE`/`ExpertQA` schema validation via `hallucination` |
| **Used in Evaluation / Testing (`TESTED`)** | **5** | `BoolQ`, `custom_security`, `RAGTruth` (`n=5`), `WiCE` (`n=3` in `hallucination`/`raw`), `ExpertQA` (`n=3`) |
| **Experimentally Verified (`VERIFIED`)** | **5** *(smoke/dev scale ONLY)* | `BoolQ` (`100` rows), `custom_security` (synthetic), `RAGTruth` (`5` smoke), `WiCE` (`3` smoke), `ExpertQA` (`3` smoke) — all reproduced deterministically at `seed=42`, **zero at full research scale**. |
| **Missing Datasets (`MISSING` w/ 0 records)** | **14** *(or **8** explicit `datasets.yaml` targets + **6** `LLM-AggreFact` sub-benchmarks + pipeline)* | Core/configured (`8`): `NQ`, `HotpotQA`, `MS-MARCO`, `SQuAD`, `RSB`, `HaluEval-QA`, `LLM-AggreFact`, `FineWeb`; Unimplemented research/sub-datasets: `AGGREFACT`, `TofuEval`, `REVEAL`, `ClaimVerify`, `FactCheck-GPT`, `LFQA`, `Dclean`, `HalluClaim`, `HalluClaim-pref`, plus `13` RSB attacks & `2` corpus variants. |
| **Reference-Only Items (`REFERENCE ONLY` — named in reports, 0 data/code)** | **9** | In `1eeb831:reports/phase07_*`: `BPRAG`, `WPRAG`, `AGGD`, `CRAG`, `AgentPoison`, `BadRAG`, `Phantom`, `HalluClaim`, `HalluClaim-pref` *(note: these are ALSO missing from execution, counted under `MISSING` above when evaluating research spec compliance)*. |

---

## 3. Complete 36-Item Classification Table (Section 3 Canonical Inventory)

Primary classification strictly follows the highest evidence-backed tier: `A. DOWNLOADED` < `B. PREPROCESSED` < `C. INTEGRATED` < `D. TRAINING USED` < `E. VALIDATION USED` < `F. TESTED` < `G. VERIFIED`; unassigned items receive `H. REFERENCE ONLY` or `I. MISSING`.

| # | Section 3 Item | Group | Canonical Identity | Primary Classification (WT / `1eeb831`) | Secondary Labels | Physical Records (`WT` / `1eeb831` raw+backup) | Highest Evidence Basis |
|---:|---|---|---|---|---|---:|---|
| 1 | **Natural Questions (NQ)** | A | `natural_questions` | **`MISSING`** | Code stub only (`1eeb831`) | `0` / `0` | `configs/benchmark_reference.json` (`BLOCKED`), `1eeb831:loaders/natural_questions.py` |
| 2 | **HotpotQA** | A | `hotpotqa` | **`MISSING`** | Code stub + mock test (`1eeb831`) | `0` / `0` | `configs/benchmark_reference.json` (`BLOCKED`), `1eeb831:loaders/hotpotqa.py` |
| 3 | **MS-MARCO** | A | `ms_marco` | **`MISSING`** | Code stub only (`1eeb831`) | `0` / `0` | `configs/benchmark_reference.json` (`BLOCKED`), `1eeb831:loaders/ms_marco.py` |
| 4 | **SQuAD** | A | `squad` | **`MISSING`** | `1eeb831` stub; 5 transient test rows | `0` / `0` persisted | `1eeb831:loaders/squad.py`, `tests/integration/test_data_acquisition.py` |
| 5 | **BoolQ** | A | `boolq` | **`VERIFIED`** *(100-row smoke subset; 99% of 10k target missing)* | `DOWNLOADED`, `PREPROCESSED`, `INTEGRATED`, `TRAINING USED` (calibrator), `VALIDATION USED`, `TESTED` | `100` (`+10` derived) / `100` (`+100` backup) | `data/processed/boolq/validation.jsonl`, `configs/benchmark_reference.json`, `configs/adaptive/*.json` |
| 6 | **RSB benchmark** | B | `rsb` | **`MISSING`** | Local-import stub + mock test (`1eeb831`) | `0` / `0` | `configs/benchmark_reference.json` (`BLOCKED`), `1eeb831:loaders/rsb.py` |
| 7 | **BPRAG** | B | RSB / Paper B attack scenario | **`REFERENCE ONLY`** *(via RSB = `MISSING`)* | Cited in Phase 07 gap/audit | `0` / `0` | `1eeb831:reports/phase07_step03_benchmark_integrity_audit.md` |
| 8 | **WPRAG** | B | RSB / Paper B attack scenario | **`REFERENCE ONLY`** *(via RSB = `MISSING`)* | Cited in Phase 07 gap/audit | `0` / `0` | `1eeb831:reports/phase07_step03_benchmark_integrity_audit.md` |
| 9 | **BPI** | B | RSB / Paper B attack scenario | **`MISSING`** *(via RSB; 0 repo mentions)* | None | `0` / `0` | Unmentioned in codebase (`git grep` = 0 hits) |
| 10 | **WPI** | B | RSB / Paper B attack scenario | **`MISSING`** *(via RSB; 0 repo mentions)* | None | `0` / `0` | Unmentioned in codebase (`git grep` = 0 hits) |
| 11 | **AGGD** | B | RSB / Paper B attack scenario | **`REFERENCE ONLY`** *(via RSB = `MISSING`)* | Cited in Phase 07 audit | `0` / `0` | `1eeb831:reports/phase07_step03_benchmark_integrity_audit.md` |
| 12 | **CRAG-AS** | B | RSB / Paper B attack scenario | **`REFERENCE ONLY`** *(`CRAG` cited via RSB = `MISSING`)* | Specific `-AS` suffix unmentioned | `0` / `0` | `CRAG` in `phase07_step03_benchmark_integrity_audit.md`; exact `-AS` absent |
| 13 | **CRAG-AK** | B | RSB / Paper B attack scenario | **`REFERENCE ONLY`** *(`CRAG` cited via RSB = `MISSING`)* | Specific `-AK` suffix unmentioned | `0` / `0` | `CRAG` in `phase07_step03_benchmark_integrity_audit.md`; exact `-AK` absent |
| 14 | **JamInject** | B | RSB / Paper B attack scenario | **`MISSING`** *(via RSB; 0 repo mentions)* | None | `0` / `0` | Unmentioned in codebase (`git grep` = 0 hits) |
| 15 | **JamOracle** | B | RSB / Paper B attack scenario | **`MISSING`** *(via RSB; 0 repo mentions)* | None | `0` / `0` | Unmentioned in codebase (`git grep` = 0 hits) |
| 16 | **JamOpt** | B | RSB / Paper B attack scenario | **`MISSING`** *(via RSB; 0 repo mentions)* | None | `0` / `0` | Unmentioned in codebase (`git grep` = 0 hits) |
| 17 | **AgentPoison** | B | RSB / Paper B attack scenario | **`REFERENCE ONLY`** *(via RSB = `MISSING`)* | Cited in Phase 07 reports | `0` / `0` | `1eeb831:reports/phase07_research_traceability_matrix.md` |
| 18 | **BadRAG** | B | RSB / Paper B attack scenario | **`REFERENCE ONLY`** *(via RSB = `MISSING`)* | Cited in Phase 07 reports | `0` / `0` | `1eeb831:reports/phase07_research_traceability_matrix.md` |
| 19 | **Phantom** | B | RSB / Paper B attack scenario | **`REFERENCE ONLY`** *(via RSB = `MISSING`)* | Cited in Phase 07 reports | `0` / `0` | `1eeb831:reports/phase07_research_traceability_matrix.md` |
| 20 | **EX-M** | C | Paper B corpus-composition variant | **`MISSING`** *(0 repo mentions)* | None | `0` / `0` | Unmentioned (`git grep` = 0 hits; only synthetic `mixed` run in `custom_security`) |
| 21 | **EX-L** | C | Paper B corpus-composition variant | **`MISSING`** *(0 repo mentions)* | None | `0` / `0` | Unmentioned (`git grep` = 0 hits) |
| 22 | **HaluEval-QA** | D | `halueval` | **`MISSING`** | Adapter stub + temp-fixture test (`1eeb831`) | `0` / `0` | `configs/benchmark_reference.json` (`BLOCKED`), `1eeb831:loaders/halueval.py` |
| 23 | **RAGTruth** | D | `ragtruth` | **`VERIFIED`** *(5 smoke rows ONLY = `0.028%` of 18k; full corpus `MISSING`)* | `DOWNLOADED` (smoke), `PREPROCESSED`, `INTEGRATED`, `VALIDATION USED`, `TESTED` | `5` *(in `hallucination`)* / `5` (`raw`) | `data/benchmarks/hallucination/{train,val}.jsonl`, `configs/benchmark_reference.json` (`PARTIALLY_READY`) |
| 24 | **LLM-AggreFact** | D | `llm_aggrefact` | **`MISSING`** | Adapter + license blocker (`1eeb831`) | `0` / `0` | `configs/benchmark_reference.json` (`BLOCKED`), `1eeb831:loaders/llm_aggrefact.py` |
| 25 | **AGGREFACT** | D | `aggrefact` (or `LLM-AggreFact` predecessor) | **`MISSING`** *(0 repo mentions)* | None | `0` / `0` | Neither standalone nor inside missing `LLM-AggreFact` |
| 26 | **TofuEval** | D | `LLM-AggreFact` sub-benchmark | **`MISSING`** *(0 repo mentions)* | None | `0` / `0` | Unmentioned; `LLM-AggreFact` itself `BLOCKED` |
| 27 | **WiCE** | D | `wice` *(independent + in `LLM-AggreFact`)* | **`VERIFIED`** *(3 smoke rows ONLY = `0.06%` of 5k; full corpus `MISSING`)* | `DOWNLOADED` (smoke), `PREPROCESSED`, `INTEGRATED`, `TESTED` | `3` *(in `hallucination`)* / `3` (`raw`) | `data/benchmarks/hallucination/{train,test}.jsonl`, `1eeb831:reports/evaluation/phase07_step04_benchmarks.json` |
| 28 | **REVEAL** | D | `LLM-AggreFact` sub-benchmark | **`MISSING`** *(0 repo mentions)* | None | `0` / `0` | Unmentioned; `LLM-AggreFact` itself `BLOCKED` |
| 29 | **ClaimVerify** | D | `LLM-AggreFact` sub-benchmark | **`MISSING`** *(0 repo mentions)* | None | `0` / `0` | Unmentioned; `LLM-AggreFact` itself `BLOCKED` |
| 30 | **FactCheck-GPT** | D | `LLM-AggreFact` sub-benchmark | **`MISSING`** *(0 repo mentions)* | None | `0` / `0` | Unmentioned; `LLM-AggreFact` itself `BLOCKED` |
| 31 | **ExpertQA** | D | `expertqa` *(independent + in `LLM-AggreFact`)* | **`VERIFIED`** *(3 smoke rows ONLY = `0.06%` of 5k; full corpus `MISSING`)* | `DOWNLOADED` (smoke), `PREPROCESSED`, `INTEGRATED`, `TESTED` | `3` *(in `hallucination`)* / `3` (`raw`) | `data/benchmarks/hallucination/{train,test}.jsonl`, `1eeb831:reports/evaluation/phase07_step04_benchmarks.json` |
| 32 | **LFQA** | D | `LLM-AggreFact` sub-benchmark | **`MISSING`** *(0 repo mentions)* | None | `0` / `0` | Unmentioned; `LLM-AggreFact` itself `BLOCKED` |
| 33 | **FineWeb** | E | `fineweb` | **`MISSING`** | Adapter + usage rule (`1eeb831`); blocked in Ph02 | `0` / `0` | `1eeb831:loaders/fineweb.py`, `1eeb831:acquisition/manager.py:L111` |
| 34 | **Dclean** | E | HalluGuard web cleaning stage | **`MISSING`** *(0 repo mentions)* | None | `0` / `0` | Unmentioned in codebase (`git grep` = 0 hits) |
| 35 | **HalluClaim** | E | HalluGuard synthetic claim set | **`REFERENCE ONLY`** *(for Paper A SRM training: `MISSING`)* | Explicitly marked `Absent` in Ph07 | `0` / `0` | `1eeb831:reports/phase07_research_traceability_matrix.md` (`A5`) |
| 36 | **HalluClaim-pref** | E | HalluGuard ORPO preference set | **`REFERENCE ONLY`** *(for Paper A SRM training: `MISSING`)* | Implicitly marked `Absent` in Ph07 | `0` / `0` | `1eeb831:reports/phase07_research_traceability_matrix.md` (`A6`) |

---

## 4. Non-Canonical, Synthetic, and Composite Dataset Artifacts in Repository

| Dataset / Benchmark Artifact | Canonical Source(s) | Working Tree Path(s) & Size | `1eeb831` Path(s) & Size | Record Count (`WT` / `1eeb831`) | Primary Classification | Notes & Limitations |
|---|---|---|---|---:|---|---|
| **`custom_security`** | Internal generator (`security_generator.py`, 8 templates) | Via `knowledge_poisoning` & `adversarial_robustness` | `data/raw/custom_security/raw_train.jsonl` (`2,315,794` B), `raw_train_backup.jsonl` (`116,770` B) | `0` raw (`50` derived) / `2,000` raw (`+100` raw backup) | **`VERIFIED`** *(synthetic dev benchmark)* | `8` unique queries repeated across variations; `100%` overlap with `benchmarks_backup` test |
| **`clean_rag`** *(composite split)* | `BoolQ` (`validation.jsonl` subset) | [train.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/clean_rag/train.jsonl), [val.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/clean_rag/val.jsonl), [test.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/clean_rag/test.jsonl) (`9,667` B total) | `data/benchmarks/clean_rag/*` (`10` rows) & `data/benchmarks_backup/clean_rag/*` (`100` rows, `93,711` B) | `10` (`7/1/2`) / `10` active + `100` backup (`70/15/15`) | Derivative of **`BoolQ`** | WT split shrunk `10x` (`test=2`); backup matches `boolq/validation.jsonl` 100% |
| **`knowledge_poisoning`** *(composite split)* | `custom_security` (`2` families: `KNOWLEDGE_POISONING`, `TRIGGER_DOS`) | [train.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/knowledge_poisoning/train.jsonl), [val.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/knowledge_poisoning/val.jsonl), [test.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/knowledge_poisoning/test.jsonl) (`23,300` B total) | Active (`20` rows) + `data/benchmarks_backup/knowledge_poisoning/*` (`150` rows, `171,892` B) | `20` (`14/2/4`) / `20` active + `150` backup (`104/22/24`) | Derivative of **`custom_security`** | Only `3` unique queries in backup (`100%` cross-split query overlap); WT `test` has `KNOWLEDGE_POISONING` only |
| **`adversarial_robustness`** *(composite split)* | `custom_security` (`5`–`6` families) | [train.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/adversarial_robustness/train.jsonl), [val.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/adversarial_robustness/val.jsonl), [test.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/adversarial_robustness/test.jsonl) (`35,062` B total) | Active (`30` rows) + `data/benchmarks_backup/adversarial_robustness/*` (`250` rows) | `30` (`22/4/4`) / `30` active + `250` backup (`174/36/40`) | Derivative of **`custom_security`** | WT has **`10/30` (`33.3%`) duplicate records** (`8/22` train, `2/4` val); backup mislabels `BENIGN_INSTRUCTION_LIKE` controls as `poisoned` |
| **`hallucination`** *(composite split)* | `ragtruth` (`5`) + `wice` (`3`) + `expertqa` (`3`) | [train.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/hallucination/train.jsonl), [val.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/hallucination/val.jsonl), [test.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/hallucination/test.jsonl) (`5,834` B total) | Active (`11` rows) + `data/benchmarks_backup/hallucination/*` (`11` rows) | `11` (`7/1/3`) / `11` (`7/1/3`) | Composite of **3 smoke fixtures** | Zero `ragtruth` in `test.jsonl`; all 11 entries are small synthetic/handcrafted test examples |
| **In-code test probe suites** | Hardcoded in `1eeb831:src/trustrag/evaluation/suites.py` & `tools/phase07_benchmark_audit.py` | Removed with `evaluation/` (archived in [benchmark_reference.json](file:///c:/Users/Dell/Desktop/trustrag/configs/benchmark_reference.json)) | `evaluation/suites.py`, `phase07_benchmark_audit.py` | `g1_curated_probes` (`18`), `g3_linguistic_suite` (`25`), `g3_generalization` (`13`), `query_consistency` (`4`) | **Code Fixtures** (Not external datasets) | Unit/probe suites only |

---

## 5. Detailed Dataset Provenance Profiles

*(Metadata not recorded in manifests, logs, or configs is marked `UNKNOWN`.)*

### 5.1 Physically Present Datasets (`WT` and/or `1eeb831`)

1. **BoolQ (`boolq`)**
   - **Original Name / Source / Version:** Google BoolQ (Clark et al., 2019, NAACL) / `google/boolq` (Hugging Face `default` config) / Version: `UNKNOWN` (manifest sets internal `1.0.0`).
   - **Download URL / Date / License:** `https://huggingface.co/datasets/google/boolq` / Retrieval Date: `2026-11-07T19:16:37.684465+00:00` (`1eeb831:data/processed/boolq/manifest.json`) / `CC-BY-SA-3.0`.
   - **Paths & Formats:** WT: [data/processed/boolq/validation.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/processed/boolq/validation.jsonl) (`93,711` B CRLF; SHA-256 `aaad91da64bb69f2ed70c0fb53ea43d5fb94b91effa717a3e02bddcb7168bc48` on LF in manifest) + `data/benchmarks/clean_rag/{train,val,test}.jsonl` (`7,374` / `961` / `1,332` B). `1eeb831` also stored `data/benchmarks_backup/clean_rag/` (`100` rows) & `data/processed/boolq/custom_splits/` (`100` rows). Format: JSONL.
   - **Counts & Labels:** `100` records (`100` unique queries, `100` unique `metadata.passage` texts, `0` explicit `relevant_document_ids`, `0` claims). Answer distribution: `yes=70`, `no=30` (WT `clean_rag`: `yes=8, no=2`). Full upstream BoolQ validation has `3,270` rows (~`15,942` total); TrustRAG holds `100` (`0.63%` of full dataset, `1.0%` of `10,000` configured target).
   - **Schema:** `QueryRecord` (`query_id`, `query`, `source_dataset`, `source_split`, `source_id`, `metadata{title, passage}`, `relevant_document_ids`, `answer`, `content_hash`). Note `BoolQAdapter` emitted `title=""`, `relevant_document_ids=[]`, `query_id="_<first 30 chars>"`.
   - **Preprocessing / Splitting / Seed:** NFKC normalization, whitespace collapse, SHA-256 deduplication (`0` duplicates). Backup/custom split `70/15/15` (`seed=42`); WT `clean_rag` `7/1/2` (`seed=42`, built with `limit` truncation).

2. **RAGTruth (`ragtruth`)**
   - **Original Name / Source / Version:** RAGTruth (Niu et al., 2024) / Configured: `https://github.com/ParticleMedia/RAGTruth`; **Actual Local Provenance:** Hand-authored/local mock fixture `data/raw/ragtruth/test.jsonl` (`raw_train` failed offline; `raw_test` logged in `1eeb831:data/raw/acquisition_log.jsonl` at `2026-11-07T20:02:27.807255+00:00` requesting `10`, acquiring `5`, SHA-256 `b8446016d2daf404f0676609645eaa65c0dcc0e76c1dd090901b6f47dfd8f13d`).
   - **License / Paths / Formats:** `MIT` (claimed upstream). WT: embedded inside [data/benchmarks/hallucination/train.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/hallucination/train.jsonl) (`4` rows) & [val.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/hallucination/val.jsonl) (`1` row). `1eeb831` also had `data/raw/ragtruth/test.jsonl` (`1,904` B) & `raw_test.jsonl` (`2,748` B).
   - **Counts & Labels:** `5` records total (`5` passages, `5` claims/responses, `0` questions; tasks labeled `qa:2, summary:2, data2text:1`; labels `factual=3 [SUPPORTED], hallucinated=2 [CONTRADICTED]`), vs canonical target `18,000` (`0.028%`).
   - **Schema & Splits:** Raw `{id, passage, response, label, task, model, labels}` -> `ClaimVerificationRecord` `{record_id, document, claim, label, justification, source_dataset, source_id, content_hash}`. Split into `hallucination/train` (`4`) & `val` (`1`), leaving `0` in `test`. Seed `42`.

3. **WiCE (`wice`)**
   - **Original Name / Source / Version:** WiCE (Kamoi et al., 2023) / Configured: `https://github.com/ryokamoi/wice` / Version & Acquisition Date: `UNKNOWN` (unlogged in `acquisition_log.jsonl`; pre-populated smoke fixture `1eeb831:data/raw/wice/test.jsonl`, `1,007` B).
   - **License / Counts / Labels:** `ODC-BY / CC-BY-SA`. `3` synthetic/handwritten smoke records (`3` passages, `3` claims; labels `supported=1`, `refuted=1 [CONTRADICTED]`, `not_enough_info=1 [NOT_ENOUGH_EVIDENCE]`) vs `5,000` target (`0.06%`). WT: embedded in `data/benchmarks/hallucination/train.jsonl` (`2`) & `test.jsonl` (`1`).

4. **ExpertQA (`expertqa`)**
   - **Original Name / Source / Version:** ExpertQA (Malaviya et al., 2024) / Configured: `https://github.com/chaitanyamalaviya/ExpertQA` / Version & Acquisition Date: `UNKNOWN` (unlogged smoke fixture `1eeb831:data/raw/expertqa/test.jsonl`, `1,069` B).
   - **License / Counts / Labels:** `MIT`. `3` smoke records (`3` passages, `3` claims; labels `supported=1`, `unsupported=1 [CONTRADICTED]`, `ambiguous=1 [NOT_ENOUGH_EVIDENCE]`) vs `5,000` target (`0.06%`, or `0.14%` of ~2,100). WT: embedded in `data/benchmarks/hallucination/train.jsonl` (`1`) & `test.jsonl` (`2`).

5. **Custom Security (`custom_security` -> `knowledge_poisoning` & `adversarial_robustness`)**
   - **Original Name / Source / Provenance:** Internal synthetic generator (`1eeb831:src/trustrag/data/benchmarks/security_generator.py`), tagged `"TrustRAG-Synthetic-Security-Benchmark-v1.0 (Development Benchmark, Synthetic Data)"` (`MIT`). Generated from `8` hardcoded templates (`sec_pair_0000..0999`).
   - **Dates & Checksums:** `acquisition_log.jsonl` records `100` rows on `2026-11-07T20:01:44Z` / `20:02:12Z` (`sha256: 8b36fde...`) and `2,000` rows on `2026-11-08T13:28:29Z` (`2,317,794` B CRLF; `sha256: e895bd65ee5a8d485ed9c5f50a9eb29ddc31420a53206e776fd549631b8c1e8c`).
   - **Active WT Counts:** `knowledge_poisoning`: `20` rows (`14/2/4`, `8` unique queries? actually `7/1/2` unique `source_id` -> `10` pairs); `adversarial_robustness`: `30` rows (`22/4/4`, ONLY `20` unique docs due to `10` duplicate rows!). `1eeb831:benchmarks_backup` had `150` (`kp`: `75` clean / `75` poisoned, `3` unique queries) and `250` (`adv`: `125` clean / `125` poisoned, `5` unique queries).
   - **Schema & Seed:** `SecurityRecord` (`record_id, document, passage, clean_poison_label, attack_family, attack_subtype, trigger_metadata, target_query, target_behavior, provenance, source_dataset, source_id, metadata, content_hash`), deterministic `seed=42`.

### 5.2 Configured-But-Empty (`MISSING`) Datasets in `1eeb831:configs/datasets.yaml`

| Dataset | Official Source / URI | License | Configured Target (`limit`) | Local Files / Records | Blocking Reason |
|---|---|---|---:|---:|---|
| **`natural_questions`** | `google-research-datasets/natural_questions` | `CC-BY-SA-3.0` | `30,000` | `0` files / `0` rows | Never downloaded; offline sandbox |
| **`hotpotqa`** | `hotpotqa/hotpot_qa` (`distractor`) | `CC-BY-SA-4.0` | `30,000` | `0` files / `0` rows | Never downloaded; offline sandbox |
| **`ms_marco`** | `microsoft/ms_marco` (`v1.1`) | `MSR-LA` | `100,000` | `0` files / `0` rows | Never downloaded; offline sandbox |
| **`squad`** | `rajpurkar/squad` (`plain_text`) | `CC-BY-SA-4.0` | `20,000` | `0` files persisted | `5` rows tested transiently via `pytest -m integration` in Ph01 |
| **`halueval`** | `pminervini/HaluEval` (`qa`) | `MIT` | `10,000` | `0` files / `0` rows | Never downloaded; offline sandbox |
| **`llm_aggrefact`** | `lytang/LLM-AggreFact` | `CC-BY-ND-4.0` | `5,000` | `0` files / `0` rows | Gated HF access + offline sandbox |
| **`rsb`** | `arXiv:2505.18543` | `Pending / Unverified` | `5,000` | `0` files / `0` rows | No public download URL; no local files supplied |
| **`fineweb`** | `HuggingFaceFW/fineweb` (`sample-10BT`) | `ODC-By-1.0` | `20,000` | `0` files / `0` rows | Blocked/deferred in Phase 02 (`manager.py:L111`) |

All remaining Section 3 datasets (`AGGREFACT`, `TofuEval`, `REVEAL`, `ClaimVerify`, `FactCheck-GPT`, `LFQA`, `Dclean`, `HalluClaim`, `HalluClaim-pref`, `EX-M`, `EX-L`, and the `13` RSB attacks) have `UNKNOWN` download metadata and `0` files across both states.

