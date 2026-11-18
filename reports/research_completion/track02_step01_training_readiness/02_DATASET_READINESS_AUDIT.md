# TrustRAG — Track 1 / Track 2: Independent Neural Training Readiness Audit
# 02 — Comprehensive Dataset Readiness, Split & Schema Audit

**Audit Scope:** Deep empirical verification of all acquired, blocked, and deferred dataset files in `data/`, their schemas, split definitions, record counts, and suitability for neural training.

---

## 1. Dataset Inventory & Physical File Audit

| Benchmark Dataset | Storage Format | On-Disk Path | File Size | Valid Records | Split Distribution | Training Role | Acquisition Status |
| :--- | :---: | :--- | :---: | :---: | :--- | :---: | :---: |
| **RAGTruth** | JSONL | `data/processed/ragtruth/train.jsonl`<br>`data/processed/ragtruth/validation.jsonl`<br>`data/processed/ragtruth/test.jsonl` | 96.0 MB<br>**0 bytes**<br>17.0 MB | 15,090<br>**0**<br>2,700 | Train: 15,090<br>Val: **0 (EMPTY)**<br>Test: 2,700 | SFT Candidate (Raw)<br>G3 Test Evaluation | **ACQUIRED (PARTIAL SPLITS)** |
| **HaluEval** | JSONL | `data/processed/halueval/train.jsonl`<br>`data/processed/halueval/validation.jsonl`<br>`data/processed/halueval/test.jsonl` | 10.1 MB<br>2.2 MB<br>2.2 MB | 14,000<br>3,000<br>3,000 | Train: 14,000<br>Val: 3,000<br>Test: 3,000 | SFT / ORPO Candidate<br>G3 Validation & Test | **ACQUIRED (COMPLETE)** |
| **HotpotQA** | Parquet / JSONL | `data/raw/hotpotqa/hotpotqa_val_distractor.parquet`<br>`data/processed/hotpotqa/validation.jsonl` | 27.5 MB<br>3.0 MB | 7,405<br>7,405 | Train: **None**<br>Val: 7,405<br>Test: **None** | Retrieval Evaluation Only<br>**(NOT FOR TRAINING)** | **VALIDATION ONLY** |
| **MS MARCO** | Parquet / JSONL | `data/raw/ms_marco/ms_marco_val_v1.1.parquet`<br>`data/processed/ms_marco/validation.jsonl` | 21.4 MB<br>2.6 MB | 10,047<br>10,047 | Train: **None**<br>Val: 10,047<br>Test: **None** | Retrieval Evaluation Only<br>**(NOT FOR TRAINING)** | **VALIDATION ONLY** |
| **Natural Questions**| Parquet | N/A (Deferred) | 0 | 0 | None | First-stage retrieval | **DEFERRED (DISK LIMIT)** |
| **LLM-AggreFact** | Parquet | N/A (Gated HF Hub) | 0 | 0 | None | Evaluation Benchmark | **ACCESS BLOCKED** |
| **RSB** | JSONL | N/A (Unreleased) | 0 | 0 | None | Security Benchmark | **ACCESS BLOCKED** |

---

## 2. Detailed Dataset Inspections

### 2.1 RAGTruth (`data/processed/ragtruth/`)
- **Schema:** `record_id` (str), `source_id` (str), `document` (str), `claim` (str), `label` (str), `source_dataset` (str), `source_split` (str), `metadata` (dict).
- **Label Distribution:**
  - `train.jsonl` (15,090 records): `FACTUAL` = 8,369 (55.46%), `HALLUCINATED` = 6,721 (44.54%).
  - `test.jsonl` (2,700 records): `FACTUAL` = 1,757 (65.07%), `HALLUCINATED` = 943 (34.93%).
- **Metadata Fields:** `metadata` contains `task_type` (Summary, QA, Data2Text), `source` (CNN/DM, PubMed, etc.), `model` (gpt-4, gpt-3.5-turbo, mistral-7B), and `hallucination_spans` (character offsets and conflict taxonomy).
- **Critical Finding — Empty Validation Split:**
  - `data/processed/ragtruth/validation.jsonl` is **0 bytes** (0 records).
  - While training data (15,090 records) and testing data (2,700 records) exist, there is no validation set for hyperparameter tuning or early stopping on RAGTruth.
  - An 80/20 train/validation split must be carved out of `train.jsonl` prior to any neural training.

### 2.2 HaluEval (`data/processed/halueval/`)
- **Schema:** `record_id` (str), `source_id` (str), `document` (str), `claim` (str), `label` (str), `source_dataset` (str), `source_split` (str), `metadata` (dict).
- **Label Distribution:**
  - `train.jsonl` (14,000 records): `FACTUAL` = 7,000 (50.00%), `HALLUCINATED` = 7,000 (50.00%).
  - `validation.jsonl` (3,000 records): `FACTUAL` = 1,500 (50.00%), `HALLUCINATED` = 1,500 (50.00%).
  - `test.jsonl` (3,000 records): `FACTUAL` = 1,500 (50.00%), `HALLUCINATED` = 1,500 (50.00%).
- **Metadata Fields:** `metadata` contains `query` (the question) and `pair_type` (`right_answer` vs `hallucinated_answer`).
- **Data Balance & Integrity:** Perfectly balanced 50/50 across all splits with exact 1-to-1 pairing per `source_id`.

### 2.3 HotpotQA & MS MARCO — Validation-Only Warning
- **HotpotQA:** Contains only `hotpotqa_val_distractor.parquet` (7,405 queries).
- **MS MARCO:** Contains only `ms_marco_val_v1.1.parquet` (10,047 queries).
- **CRITICAL AUDIT ASSERTION:** Neither HotpotQA nor MS MARCO contains a training split in this repository. These datasets were acquired strictly to evaluate candidate retrieval and re-ranking. **Treating or feeding any portion of HotpotQA validation or MS MARCO validation into neural training is strictly prohibited** as it constitutes catastrophic data leakage.

### 2.4 Blocked Benchmarks Status
1. **LLM-AggreFact:** Hosted on Hugging Face (`lytang/LLM-AggreFact`) under a gated license (**CC-BY-ND-4.0**).
   - CC-BY-ND explicitly forbids derivative works; it cannot be legally used for model fine-tuning.
   - Access requires interactive web portal acceptance and an authenticated `HF_TOKEN`.
2. **RSB (RAG Security Bench):** Paper published on arXiv (arXiv:2505.18543), but no public dataset repository exists.
3. **Natural Questions (NQ):** Download deferred due to environment bandwidth and storage constraints (full train set is ~40 GB across 287 shards).

---

## 3. Dataset Licensing & Permitted Usage

| Dataset | Declared License | Permitted for Training | Permitted for Evaluation | Commercial Use |
| :--- | :---: | :---: | :---: | :---: |
| **RAGTruth** | Apache 2.0 / MIT | **YES** | **YES** | Yes |
| **HaluEval** | MIT License | **YES** | **YES** | Yes |
| **HotpotQA** | CC-BY-SA 4.0 | No (Val-only acquired) | **YES** | Attribution required |
| **MS MARCO** | Microsoft Research License | No (Val-only acquired) | **YES** | Non-commercial research |
| **LLM-AggreFact**| CC-BY-ND 4.0 | **NO (Forbidden by ND)**| **YES** | Non-derivative only |

---

## 4. Dataset Readiness Conclusion

The repository possesses **29,090 raw training records** across RAGTruth (15,090) and HaluEval (14,000). However, dataset readiness for neural training is **CONDITIONALLY_READY** pending:
1. Resolving the 0-byte RAGTruth validation split.
2. Maintaining strict isolation so that validation-only retrieval datasets (HotpotQA, MS MARCO) are never touched by training pipelines.

