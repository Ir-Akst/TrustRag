# TrustRAG Research Completion — Track 1, Step 2: Dataset & Split Validation

## 1. Acquired Dataset Inventory

All datasets evaluated in this benchmark were acquired and validated during Track 1, Step 1. The datasets reside on disk with verified record counts and schema validation:

```
data/
|-- raw/
|   |-- halueval/
|   |   |-- qa_data.json (10,000 records)
|   |   |-- dialogue_data.json (10,000 records)
|   |   `-- summarization_data.json (10,000 records)
|   |-- hotpotqa/
|   |   `-- hotpot_val_distractor.parquet (7,405 queries)
|   |-- ms_marco/
|   |   `-- ms_marco_val_v1.1.parquet (10,047 queries)
|   `-- ragtruth/
|       |-- response.jsonl (9,219 generation records)
|       `-- source_info.jsonl (2,875 reference sources)
`-- processed/
    |-- halueval/
    |   `-- test.jsonl (3,000 balanced records)
    |-- hotpotqa/
    |   `-- test.jsonl (7,405 records)
    |-- ms_marco/
    |   `-- test.jsonl (10,047 records)
    `-- ragtruth/
        `-- test.jsonl (2,700 stratified test records)
```

---

## 2. Detailed Split Characterization

### 2.1 RAGTruth Test Split (`data/processed/ragtruth/test.jsonl`)
- **Total Records Evaluated:** 2,700
- **Ground Truth Distribution:**
  - `FACTUAL`: 1,757 records (65.07%)
  - `HALLUCINATED`: 943 records (34.93%)
- **Source Types:** News, Summarization, QA, Data-to-Text.
- **Data Integrity:** 100% of records possess non-empty document context and non-empty model responses. All labels match verified binary annotations.

### 2.2 HaluEval Test Split (`data/processed/halueval/test.jsonl`)
- **Total Records Evaluated:** 3,000
- **Ground Truth Distribution:**
  - `FACTUAL`: 1,500 records (50.00%)
  - `HALLUCINATED`: 1,500 records (50.00%)
- **Subdomain Composition:**
  - QA subset: 1,000 pairs (500 factual, 500 hallucinated)
  - Dialogue subset: 1,000 pairs (500 factual, 500 hallucinated)
  - Summarization subset: 1,000 pairs (500 factual, 500 hallucinated)
- **Data Integrity:** Perfectly balanced stratified test subset sampled with fixed random seed (42).

### 2.3 HotpotQA Validation Set (`data/raw/hotpotqa/hotpot_val_distractor.parquet`)
- **Total Queries Evaluated:** 7,405
- **Skipped Queries:** 0
- **Candidate Pool:** 10 paragraphs per query (2 gold Wikipedia paragraphs, 8 distractor paragraphs).
- **Corpus Evaluation Scope:** Distractor candidate re-ranking. Full open-domain corpus indexing is blocked pending acquisition of `hotpot_corpus.tsv` (5.23M passages).

### 2.4 MS MARCO Validation Set (`data/raw/ms_marco/ms_marco_val_v1.1.parquet`)
- **Total Queries in File:** 10,047
- **Evaluated Queries:** 9,706
- **Skipped Queries:** 341 (Queries with zero human-annotated relevant passages, `is_selected=0` across all candidate passages).
- **Candidate Pool:** 6 to 10 web snippet passages per query (mean: 10.0 passages).
- **Corpus Evaluation Scope:** Search snippet candidate re-ranking. Full open-domain corpus indexing is blocked pending acquisition of `collection.tsv` (8.84M passages).
