# Phase 07 — Step 03: Benchmark Integrity Audit

**Audit Date:** 2026-11-12  
**Branch:** `phase-7` (`cc1961e`)  
**Policy:** Forensic inspection only. Original datasets, splits, manifests, and Phase 04–06 JSON results are preserved unmodified.

---

## 1. Local Dataset Inventory, Provenance & Checksum Verification

All JSONL partitions under `data/benchmarks/`, `data/benchmarks_backup/`, `data/processed/`, and `data/raw/` were audited independently.

### 1.1 Split Counts, Manifest Checksums & Duplication Matrix

| Location & Dataset | Split | Records (`n`) | Unique (`query\|\|text`) | Within-Split Duplicates | Cross-Split Sample Overlap | Label Distribution | Manifest SHA-256 Verification |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `data/benchmarks/clean_rag` | `train` | 7 | 7 | 0 | 0 | N/A (QA retrieval) | Valid (CRLF) |
| `data/benchmarks/clean_rag` | `val` | 1 | 1 | 0 | 0 | N/A | Valid (CRLF) |
| `data/benchmarks/clean_rag` | `test` | 2 | 2 | 0 | 0 | N/A | Valid (CRLF) |
| `data/benchmarks/knowledge_poisoning` | `train` | 14 | 14 | 0 | 0 | `clean=7`, `poisoned=7` (50/50) | Valid (CRLF) |
| `data/benchmarks/knowledge_poisoning` | `val` | 2 | 2 | 0 | 0 | `clean=1`, `poisoned=1` | Valid (CRLF) |
| `data/benchmarks/knowledge_poisoning` | `test` | 4 | 4 | 0 | 0 | `clean=2`, `poisoned=2` | Valid (CRLF) |
| `data/benchmarks/adversarial_robustness` | `train` | **22** | **14** | **8 (36.4%)** | 0 | `clean=11`, `poisoned=11` | Valid (CRLF) |
| `data/benchmarks/adversarial_robustness` | `val` | **4** | **2** | **2 (50.0%)** | 0 | `clean=2`, `poisoned=2` | Valid (CRLF) |
| `data/benchmarks/adversarial_robustness` | `test` | 4 | 4 | 0 | 0 | `clean=2`, `poisoned=2` | Valid (CRLF) |
| `data/benchmarks/hallucination` | `train` | 7 | 7 | 0 | 0 | `CONTRADICTED=3, SUPPORTED=3, NEE=1` | Valid (CRLF) |
| `data/benchmarks/hallucination` | `val` | 1 | 1 | 0 | 0 | `SUPPORTED=1` | Valid (CRLF) |
| `data/benchmarks/hallucination` | `test` | 3 | 3 | 0 | 0 | `SUPPORTED=1, CONTRADICTED=1, NEE=1` | Valid (CRLF) |
| `data/benchmarks_backup/clean_rag` | `train/val/test` | 70 / 15 / 15 (100) | 70 / 15 / 15 | 0 | 0 | N/A (BoolQ subset) | Valid (CRLF) |
| `data/benchmarks_backup/knowledge_poisoning` | `train/val/test` | 104 / 22 / 24 (150) | 104 / 22 / 24 | 0 | 0 | Exact 50/50 (`52/52`, `11/11`, `12/12`) | Valid (CRLF) |
| `data/benchmarks_backup/adversarial_robustness` | `train/val/test` | 174 / 36 / 40 (250) | 174 / 36 / 40 | 0 | 0 | Exact 50/50 (`87/87`, `18/18`, `20/20`) | Valid (CRLF) |
| `data/benchmarks_backup/hallucination` | `train/val/test` | 7 / 1 / 3 (11) | 7 / 1 / 3 | 0 | 0 | Identical to `benchmarks/hallucination` | Valid (CRLF) |
| `data/processed/boolq/validation.jsonl` | `validation` | 100 | 100 | 0 | — | BoolQ boolean passages | — |
| `data/processed/boolq/custom_splits/*` | `train/val/test` | 70 / 15 / 15 | 70 / 15 / 15 | 0 | — | Byte-sized match to `backup/clean_rag` | — |
| `data/raw/custom_security/raw_train.jsonl` | `train` | 2,000 | 2,000 | 0 | **Overlap (see §2)** | `clean=1,000`, `poisoned=1,000` | Logged in `acquisition_log.jsonl` |
| `data/raw/expertqa/test.jsonl` | `test` | **3** | 3 | 0 | 0 | `supported=1, unsupported=1, ambiguous=1` | No manifest |
| `data/raw/ragtruth/test.jsonl` | `test` | **5** | 5 | 0 | 0 | `factual=3, hallucinated=2` | Logged (`raw_test.jsonl`, `n=5`) |
| `data/raw/wice/test.jsonl` | `test` | **3** | 3 | 0 | 0 | `supported=1, refuted=1, NEE=1` | No manifest |

---

## 2. Critical Benchmark Integrity Findings

### Finding 1: `data/benchmarks/` vs `data/benchmarks_backup/` Shrinkage & Historical Inconsistency
- `data/benchmarks/` holds tiny toy splits (`clean_rag=10`, `knowledge_poisoning=20`, `adversarial_robustness=30`, `hallucination=11`), whereas `data/benchmarks_backup/` holds larger prior builds (`100 / 150 / 250 / 11`).
- **Proof in Historical Artifacts:**
  - `reports/evaluation/clean_rag_baseline_clean_rag_test_f7f98cd4da.json` ran on `data/benchmarks/clean_rag/test.jsonl` (`n=2`), whereas `phase06_comprehensive_benchmark.json` ran `clean_rag_test_n15` on the 15-sample split.
  - `reports/evaluation/poisoning_rag_g2_g3_mixed_knowledge_poisoning_test_11c01170ad.json` ran on `data/benchmarks_backup/knowledge_poisoning/test.jsonl` (`n=24`), NOT `data/benchmarks/` (`n=4`).
  - `configs/adaptive/platt_calibrator_v1.json` reports `sample_count=428` (`clean_count=308, attack_count=120`) from `phase05_step02_calibration.json` (`adv=174 + kp=104 + clean_rag_docs=150 = 428`), proving calibration was trained on **`data/benchmarks_backup/*/train.jsonl`**, NOT `data/benchmarks/*/train.jsonl`.
- **Root Audit Vulnerability:** `reports/benchmark_validation_summary.json` shows Windows-style path validation failures (`Manifest file not found: data\benchmarks\clean_rag`) during an earlier automated run, and `reports/benchmark_build_summary.txt` records build argument errors for `hallucination` and `adversarial_robustness`.

### Finding 2: BoolQ / `platt_calibrator_v1` Cross-Dataset Contamination (`70/100` Overlap)
- Forensic query-hash intersection proves:
  - `len(boolq/validation.jsonl ∩ benchmarks_backup/clean_rag/train.jsonl) = 70 / 100`!
  - `len(boolq/validation.jsonl ∩ benchmarks_backup/clean_rag/val.jsonl) = 15 / 100`!
  - `len(boolq/validation.jsonl ∩ benchmarks_backup/clean_rag/test.jsonl) = 15 / 100`!
- **`boolq/validation.jsonl` (`n=100`) is the exact union of `backup/clean_rag` `train + val + test` (`70+15+15`).**
- **Impact:** Evaluating `platt_calibrator_v1.json` (which was fitted on `backup/clean_rag/train`) across all `100` rows of `boolq/validation.jsonl` (as done in `phase06_comprehensive_benchmark.json` and `phase05_step02_calibration.json`) includes **70% in-sample calibration training data** alongside 15 val and 15 clean held-out test queries. In Step 04, we report `clean_rag/test (n=15)` and held-out non-train `boolq` subset separately from `n=100`.

### Finding 3: Severe Query-Group Leakage Across `train/val/test` in Security Benchmarks
- Both `knowledge_poisoning` and `adversarial_robustness` split *at the individual passage level* instead of grouping by `target_query`:
  - `data/benchmarks_backup/knowledge_poisoning`: **Only `3` unique `target_query` strings across ALL `150` rows** (`train` has 3, `val` has 3, `test` has 3 -> **100% query overlap `tr∩te = 3/3`**).
  - `data/benchmarks_backup/adversarial_robustness`: **Only `5` unique `target_query` strings across ALL `250` rows** (`train` has 5, `val` has 5, `test` has 5 -> **100% query overlap `tr∩te = 5/5`**).
  - `data/raw/custom_security/raw_train.jsonl` (`n=2,000`): Composed of synthetic templated permutations over **only `8` unique `target_query` strings** (`250` rows per query across 6 families). Furthermore, `raw_train.jsonl` has **100% passage overlap (`24/24` and `40/40`) with `benchmarks_backup` test splits** — so `raw_train.jsonl` MUST NOT be treated as an independent training set against `benchmarks_backup/test`.
  - `data/benchmarks/knowledge_poisoning` & `adversarial_robustness`: `2/2` queries in `test.jsonl` overlap with `train.jsonl`. Worse, `data/benchmarks/*/test.jsonl` (`n=4`) contains ONLY `KNOWLEDGE_POISONING` rows (zero `PROMPT_INJECTION`, `TRIGGER_DOS`, `MALICIOUS_INSTRUCTION`, or `CONFLICTING_EVIDENCE` test coverage!).

### Finding 4: Severe Within-Split Duplication in `data/benchmarks/adversarial_robustness`
- Verified directly by script and confirmed by `data/benchmarks/adversarial_robustness/quality_report.json`:
  - `train.jsonl`: **8 duplicates out of 22 (36.4%)** (`14` unique).
  - `val.jsonl`: **2 duplicates out of 4 (50.0%)** (`2` unique).
  - Overall `duplicate_rate = 0.3333` (`10 / 30` records duplicated).
- Evaluating or training on `data/benchmarks/adversarial_robustness` without deduplicating inflates weights on repeated passages and distorts tiny-sample statistics.

### Finding 5: Sample-Size & Statistical Power Ceilings
- Real-world claim verification caches contain **tiny smoke samples only**: `expertqa/test.jsonl` (`n=3`), `wice/test.jsonl` (`n=3`), `ragtruth/test.jsonl` (`n=5`), `hallucination/test.jsonl` (`n=3`). These are suitable strictly for deterministic edge-case sanity checks — **zero statistical generalization can be inferred from `n=3..5`.**
- Real-world retrieval (`boolq/validation.jsonl`, `n=100`, uncontaminated held-out test `n=15`) uses **corpus sizes equal to the evaluated partition (`N=15` or `N=100`)** rather than realistic `10k–1M` passage corpora. Top-5 retrieval over `N=15` (returning `33%` of the entire corpus by default!) yields inflated `Recall@5` compared to real-world dense/BM25 retrieval.

### Finding 6: Metric Implementation & Baseline Fairness Audit (`src/trustrag/evaluation/metrics.py` & `suites.py`)
- **`metrics.py`:** `compute_binary_classification_metrics`, `roc_auc_score`, `average_precision_score`, `wilson_confidence_interval`, `bootstrap_confidence_interval`, and exact binomial `mcnemar_test` are mathematically sound.
- **`suites.py` Fairness / Validity Risks:**
  1. In `evaluate_clean_rag_baseline()` (`suites.py:L158-164`), `boolean_exact_match` compares extractive document sentences against BoolQ ground-truth `"true"` / `"false"` labels (`clean_ans.strip().lower() == "true"`), forcing `boolean_exact_match = 0.0` for BOTH Original RAG and TrustRAG because `AnswerGenerator` is extractive rather than an abstractive QA model.
  2. In `phase05_step09_adaptive_ablation.json`, clean retrieval recall@5 evaluated over `n=15` BoolQ docs and security ASR evaluated over templated synthetic fixtures were tabulated side by side; as required in Phase 07, security and utility across disparate corpora must remain strictly stratified and non-equated.
  3. **Seed Reproducibility:** `TrustRAGPipeline.__init__` sets `set_random_seed(42)`, and `TfidfVectorizer` + Python sorting (`(-score, rank, doc_id)`) make all offline evaluations deterministic under fixed seed `42` (verified empirically in Step 04).

### Finding 7: Label Semantics Conflict on `BENIGN_INSTRUCTION_LIKE` Controls (`adversarial_robustness`)
- In `data/benchmarks_backup/adversarial_robustness/{train,val,test}.jsonl`, records with `attack_family == "BENIGN_INSTRUCTION_LIKE"` carry `clean_poison_label == "poisoned"` on alternate variants (e.g., `3` of `6` records in `test.jsonl`), while simultaneously recording `metadata.expected_security_outcome == "permit_legitimate_procedural_content"` (harmless sourdough/baking controls).
- `src/trustrag/adaptive/calibration.py:L344` explicitly excludes `fam == "BENIGN_INSTRUCTION_LIKE"` from `is_atk=1` (`120` attacks out of `174` adv + `104` kp in `platt_calibrator_v1`), whereas naive evaluators reading `clean_poison_label == "poisoned"` directly will misclassify benign controls as false negatives. Step 04 reports metrics BOTH on all `n=64` security test docs (using `is_true_attack = (clean_poison_label == "poisoned" and attack_family != "BENIGN_INSTRUCTION_LIKE")`, treating `BENIGN_INSTRUCTION_LIKE` as benign FP controls) AND stratified per attack family (`KNOWLEDGE_POISONING`, `TRIGGER_DOS`, `PROMPT_INJECTION`, `MALICIOUS_INSTRUCTION`, `CONFLICTING_EVIDENCE`, `BENIGN_INSTRUCTION_LIKE`).

---

## 3. Unavailable / `BLOCKED` External Benchmarks & Offline Boundaries

The following canonical research benchmarks from Papers A, B, and C are **NOT present locally** and **CANNOT be downloaded** in the offline sandbox (`huggingface` / `github` unreachable, zero pre-cached corpora on disk):

| Benchmark Dataset | Referenced In | Configured Location (`configs/datasets.yaml`) | Local Disk Status | Phase 07 Status | Exact Blocking Dependency |
| --- | --- | --- | --- | --- | --- |
| **Natural Questions (`nq`)** | Paper B & Paper C | `google-research-datasets/natural_questions` | **0 records** (`data/raw/natural_questions` absent) | **`BLOCKED`** | Network download + storage + PoisonedRAG corpus |
| **HotpotQA** | Paper B & Paper C | `hotpotqa/hotpot_qa` (`distractor`) | **0 records** | **`BLOCKED`** | Network download + multi-hop QA LM |
| **MS-MARCO (`v1.1`)** | Paper B & Paper C | `microsoft/ms_marco` | **0 records** | **`BLOCKED`** | Network download + dense retriever |
| **SQuAD** | Baseline QA | `rajpurkar/squad` | **0 records** | **`BLOCKED`** | Network download |
| **RSB (RAG Security Bench, 13 attacks)** | Paper B (§7) | `arXiv:2505.18543` (`data/raw/rsb` absent) | **0 records** | **`BLOCKED`** | Upstream RSB benchmark & attack generators (`BPRAG`, `WPRAG`, `AGGD`, `CRAG`, `AgentPoison`, `BadRAG`, `Phantom`) + dense retriever/LLM |
| **HaluEval-QA (`10,000` items)** | Paper A & Paper B (§8) | `pminervini/HaluEval` (`qa`) | **0 records** | **`BLOCKED`** | Network download + full 10k QA split |
| **LLM-AggreFact (CC-BY-ND-4.0)** | Paper A (75.7% benchmark) | `lytang/LLM-AggreFact` | **0 records** | **`BLOCKED`** | Network download + gated access + GPU SRM inference |
| **RAGTruth (Full Test Subset)** | Paper A (84.0% benchmark) | `ParticleMedia/RAGTruth` | **Only `5` smoke rows** (`test.jsonl`) | **Partial Smoke Only (`Full = BLOCKED`)** | Network download of full test corpus + 4B ORPO/LoRA model |
| **FineWeb (`sample-10BT`)** | Paper A (`HalluClaim`) | `HuggingFaceFW/fineweb` | **0 records** | **`BLOCKED`** | Network download + teacher LLM synthesis |
