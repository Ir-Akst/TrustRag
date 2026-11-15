# TrustRAG Research Completion — Track 1, Step 1: Dataset Schema Validation

**Date**: 2026-11-13  
**Branch**: `phase-11`  
**Repository**: `/home/aditya/rags/TrustRag-phase11`  

---

## 1. Schema Validation Framework

TrustRAG enforces strict Pydantic schemas on all ingested datasets. Records are normalized into one of four canonical schema models defined in `src/trustrag/data/schemas.py`:

1. `ClaimVerificationRecord`: Used for hallucination benchmarks (RAGTruth, HaluEval, LLM-AggreFact).
2. `QueryRecord`: Used for QA and retrieval benchmarks (HotpotQA, MS MARCO, Natural Questions).
3. `SecurityRecord`: Used for adversarial robustness benchmarks (RSB).
4. `DocumentRecord`: Used for passage and raw corpus indexing.

---

## 2. Ingested Dataset Schema Conformance

### RAGTruth (`ClaimVerificationRecord`)
- **Required Fields**:
  - `record_id`: Unique identifier formatted as `ragtruth_<id>`.
  - `document`: Non-empty source context text.
  - `claim`: Non-empty LLM-generated output text.
  - `label`: Strictly constrained to `"FACTUAL"` or `"HALLUCINATED"`.
  - `source_dataset`: `"ragtruth"`.
- **Validation Results**:
  - 17,790 records validated.
  - Schema errors: **0**.
  - Missing field errors: **0**.
  - Empty text errors: **0**.
  - Conformance Rate: **100.0%**.

### HaluEval (`ClaimVerificationRecord`)
- **Required Fields**:
  - `record_id`: Formatted as `halueval_<id>_factual` or `halueval_<id>_hallucinated`.
  - `document`: Wikipedia grounding knowledge passage.
  - `claim`: Generated answer under evaluation.
  - `label`: Exactly balanced `"FACTUAL"` (10,000) and `"HALLUCINATED"` (10,000).
  - `source_dataset`: `"halueval"`.
- **Validation Results**:
  - 20,000 claims validated across train, validation, and test splits.
  - Schema errors: **0**.
  - Label syntax errors: **0**.
  - Conformance Rate: **100.0%**.

### HotpotQA (`QueryRecord`)
- **Required Fields**:
  - `query_id`: Canonical HotpotQA `_id`.
  - `query`: Question text requiring multi-hop reasoning.
  - `answer`: Gold reference answer string.
  - `relevant_document_ids`: List of document titles identified as supporting facts.
  - `source_dataset`: `"hotpotqa"`.
- **Validation Results**:
  - 7,405 records validated.
  - Missing question text: **0**.
  - Missing answer string: **0**.
  - Conformance Rate: **100.0%**.

### MS MARCO (`QueryRecord`)
- **Required Fields**:
  - `query_id`: Bing search log query ID.
  - `query`: Web search query string.
  - `answer`: Reference answer extracted from relevant web passages.
  - `metadata`: Contains passage count and query type.
  - `source_dataset`: `"ms_marco"`.
- **Validation Results**:
  - 10,047 records validated.
  - Malformed records: **0**.
  - Conformance Rate: **100.0%**.

---

## 3. Deduplication and Content Hash Integrity

For every processed record, a SHA-256 content hash of `(document, claim)` or `(query, answer)` is computed to detect exact and near-duplicates:
- **RAGTruth**: 17,790 records with 0 cross-split leakage between train and test splits.
- **HaluEval**: 10,000 unique source items partitioned deterministically; exactly 0 cross-split leakage between train (70%), validation (15%), and test (15%).
- **HotpotQA**: Distractor validation split contains 7,405 unique questions.
- **MS MARCO**: Validation split contains 10,047 unique queries.

