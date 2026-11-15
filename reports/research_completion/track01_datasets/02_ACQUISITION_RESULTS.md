# TrustRAG Research Completion — Track 1, Step 1: Acquisition Results

**Date**: 2026-11-13  
**Branch**: `phase-11`  
**Repository**: `/home/aditya/rags/TrustRag-phase11`  

---

## 1. Physical Artifact Inventory

All downloaded raw artifacts and normalized processed records have been verified against canonical remote checksums.

### Raw Storage (`data/raw/`)

| Dataset | File Name | Size (Bytes) | SHA-256 Checksum | Record Count |
| :--- | :--- | :--- | :--- | :--- |
| **RAGTruth** | `response.jsonl` | 21,458,735 | `e4c2e4ac24fff676d8984cc61c35d791612fadc58015335d97dd632375e18073` | 17,790 |
| **RAGTruth** | `source_info.jsonl` | 15,117,971 | `0dffc26ea9f3c1c3d7c7e8336b56ef1646e3cec876edffcca3c9c624d12d578b` | 2,965 |
| **HaluEval** | `qa_data.json` | 6,164,420 | `89ed139ec5e3a3169a0b30e45569ac1283846f76f27f7bb5e908ee6deed57e88` | 10,000 |
| **HotpotQA** | `hotpotqa_val_distractor.parquet` | 27,452,575 | `c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6` | 7,405 |
| **MS MARCO** | `ms_marco_val_v1.1.parquet` | 21,391,358 | `67aca2e1b2fffe418a6bd317142887c90973c9c98dd8d940eaae3f8521daed7c` | 10,047 |

*Total Raw Storage Footprint: ~91.5 MB*

---

### Processed Storage (`data/processed/`)

| Dataset | Split File | Size (Bytes) | SHA-256 Checksum | Record Count |
| :--- | :--- | :--- | :--- | :--- |
| **RAGTruth** | `train.jsonl` | 96,020,628 | `29056a653cad65b40f8898e06cc195979a1859fb988896f0ceab60841a79d547` | 15,090 |
| **RAGTruth** | `test.jsonl` | 16,963,121 | `55f5ec8bf47039551fc5fe64fbdf35306422c50402a1d6cc9dd1b3bfe12540f1` | 2,700 |
| **HaluEval** | `train.jsonl` | 10,123,599 | `28b4793f1a953c1f45e83fa0ad6074c6e1689277315dffa99923d9e0cf51de3c` | 14,000 |
| **HaluEval** | `validation.jsonl` | 2,176,620 | `d58ccd53812174106a8237bb3577b389cf630924a09170dad17f9afd8d4aee45` | 3,000 |
| **HaluEval** | `test.jsonl` | 2,183,178 | `93873eb19dcd7e08b6d89add90d1d3f3652689d9ee649d1d800c1a95431aa904` | 3,000 |
| **HotpotQA** | `validation.jsonl` | 3,009,303 | `2db3e688ad9b7e4fafc4c80e6fd0ecd39a7be06c19c87b90aa1239dfa71eb746` | 7,405 |
| **MS MARCO** | `validation.jsonl` | 2,563,989 | `a33845903b8e5a1fd2bed0ecfd68aa50b40527f05237e1688425a7249502474a` | 10,047 |

*Total Processed Record Count: **55,242 records***  
*Total Processed Storage Footprint: ~133.0 MB*

---

## 2. Acquisition Pipeline Details

1. **RAGTruth Ingestion**:
   - Acquired raw `response.jsonl` and `source_info.jsonl` from ParticleMedia/RAGTruth.
   - Performed primary-key join between response model generations and source article texts using `source_id`.
   - Partitioned records into native RAGTruth splits (`train`: 15,090, `test`: 2,700).

2. **HaluEval Ingestion**:
   - Acquired canonical `qa_data.json` containing 10,000 QA pairs.
   - Expanded each item deterministically into two `ClaimVerificationRecord` instances:
     - Factual claim: Grounded in knowledge, paired with right answer (`label="FACTUAL"`).
     - Hallucinated claim: Grounded in knowledge, paired with hallucinated answer (`label="HALLUCINATED"`).
   - Applied a fixed random seed (42) to partition into 70% train (14,000 claims), 15% validation (3,000 claims), and 15% test (3,000 claims).

3. **HotpotQA Ingestion**:
   - Acquired official distractor validation split parquet from Hugging Face Hub (`hotpotqa/hotpot_qa`).
   - Parsed supporting facts and converted each example into a canonical `QueryRecord` with gold answer and title-based reference document IDs.

4. **MS MARCO Ingestion**:
   - Acquired official v1.1 validation split parquet from Hugging Face Hub (`microsoft/ms_marco`).
   - Extracted queries, human answers, and candidate passage metadata, transforming them into canonical `QueryRecord` instances.

