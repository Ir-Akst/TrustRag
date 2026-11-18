# TrustRAG — Track 2, Step 3.5: Evaluation Data Provenance & Isolation Audit

## 1. Partition Definition and Sourcing

The evaluation dataset was established strictly from the unvisited, untouched records of `data/processed/sft_v2/binary/validation.jsonl`.

- **Total Records in `validation.jsonl`:** 5,984 records
- **Excluded Step 3.4.2 Pilot Validation Records:** 200 records (strictly skipped by `example_id`)
- **Excluded Step 3.4.2 Training Records:** 1,000 records (strictly skipped by `example_id`)
- **Available Untouched Candidate Pool:** 5,784 records
- **Extracted Independent Evaluation Slice:** Exactly 1,000 records
  - **HaluEval:** 500 records (250 FACTUAL, 250 HALLUCINATED)
  - **RAGTruth:** 500 records (250 FACTUAL, 250 HALLUCINATED)

## 2. Partition Isolation Audit Results

| Audit Check | Reference Target | Observed Overlap | Compliance Status |
| :--- | :--- | :---: | :---: |
| Overlap with Step 3.4.2 Training (1,000) | `data/processed/sft_v2/binary/train.jsonl` | **0 records** | **VERIFIED_DISJOINT** |
| Overlap with Step 3.4.2 Pilot Validation (200) | `tools/training/train_binary_classifier.py` cache | **0 records** | **VERIFIED_DISJOINT** |
| Overlap with Upstream HaluEval Test Documents | `data/processed/halueval/test.jsonl` | **0 documents** | **VERIFIED_DISJOINT** |
| Overlap with Upstream RAGTruth Test Documents | `data/processed/ragtruth/test.jsonl` | **0 documents** | **VERIFIED_DISJOINT** |
| Test Split Exposure | Canonical Test Splits | **0 records accessed** | **STRICTLY_ISOLATED** |

## 3. Dataset Attribution & Licensing

- **HaluEval:** Released under MIT License / Academic Research Use.
- **RAGTruth:** Released under CC BY 4.0 International License.
- **Model:** DeBERTa-v3-small (MIT License, Microsoft Corporation).
