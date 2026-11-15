# TrustRAG Track 2, Step 2: Dataset Transformation Report

## 1. Pipeline Architecture

The transformation pipeline implemented in [`tools/data_prep/prepare_sft_dataset.py`](file:///home/aditya/rags/TrustRag-phase11/tools/data_prep/prepare_sft_dataset.py) processes canonical datasets into a single evidence-grounded fine-tuning format (`sft_v1`).

```
Canonical Preprocessed Data
├── data/processed/ragtruth/train.jsonl (15,090 records, 2,515 sources)
├── data/processed/halueval/train.jsonl  (14,000 records, 7,000 sources)
└── data/processed/halueval/validation.jsonl (3,000 records, 1,500 sources)
                     │
                     ▼
          prepare_sft_dataset.py
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
  RAGTruth 80/20          HaluEval Canonical
  Source Partition         Split Integration
         │                       │
         └───────────┬───────────┘
                     ▼
             Leakage Verifier
                     ▼
          Output: data/processed/sft_v1/
          ├── train.jsonl (26,072)
          └── validation.jsonl (6,018)
```

---

## 2. RAGTruth Transformation Mechanics

1. **Source Document Grouping:**
   - Input: 15,090 records from `data/processed/ragtruth/train.jsonl`.
   - Records are grouped by `source_id`, yielding exactly 2,515 distinct source documents.
2. **Deterministic Partitioning:**
   - Seed: `42`.
   - Ratio: 80% train, 20% validation.
   - Train sources: 2,012 source IDs ($12,072$ records).
   - Validation sources: 503 source IDs ($3,018$ records).
3. **Target Formatting:**
   - For `FACTUAL` examples: serialized with verdict `"SUPPORTED"`, grounding status `"GROUNDED"`, and empty hallucination spans.
   - For `HALLUCINATED` examples: extracts human span annotations (`text`, `conflict_type`, `meta`) directly from record metadata, serialized with verdict `"CONTRADICTED"`.

---

## 3. HaluEval Transformation Mechanics

1. **Pre-partitioned Source Alignment:**
   - Upstream HaluEval QA provides cleanly segregated train (7,000 sources) and validation (1,500 sources) splits.
2. **Dual-Record Pair Unpacking:**
   - For each source QA query, two examples are generated:
     - `right_answer`: Mapped to `FACTUAL`, verdict `"SUPPORTED"`, provenance `"halueval_qa_original_annotations: canonical right_answer grounded in context passage"`.
     - `hallucinated_answer`: Mapped to `HALLUCINATED`, verdict `"CONTRADICTED"`, provenance `"halueval_qa_original_annotations: canonical hallucinated_answer conflicting with or unsupported by passage"`.
   - Train: 14,000 records (7,000 factual, 7,000 hallucinated).
   - Validation: 3,000 records (1,500 factual, 1,500 hallucinated).

---

## 4. Class Balance and Distribution Census

### Training Split (`train.jsonl`)
- **Total Records:** 26,072
- **FACTUAL:** 15,970 (61.25%)
- **HALLUCINATED:** 10,102 (38.75%)
- **Source Breakdown:**
  - RAGTruth: 12,072 records (8,970 Factual / 3,102 Hallucinated)
  - HaluEval: 14,000 records (7,000 Factual / 7,000 Hallucinated)

### Validation Split (`validation.jsonl`)
- **Total Records:** 6,018
- **FACTUAL:** 3,734 (62.05%)
- **HALLUCINATED:** 2,284 (37.95%)
- **Source Breakdown:**
  - RAGTruth: 3,018 records (2,234 Factual / 784 Hallucinated)
  - HaluEval: 3,000 records (1,500 Factual / 1,500 Hallucinated)

### Class Ratio Stability
The ratio of factual to hallucinated examples in training (61.25% / 38.75%) and validation (62.05% / 37.95%) matches within 0.8%, preserving identical underlying distributional characteristics across splits.

