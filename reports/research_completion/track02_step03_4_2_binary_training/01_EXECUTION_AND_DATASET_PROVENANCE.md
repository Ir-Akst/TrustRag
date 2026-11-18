# Track 2, Step 3.4.2 — Section 01: Execution and Dataset Provenance

## 1. Dataset Provenance and Verified Split Composition

Training and validation subsets were deterministically extracted from:
- `data/processed/sft_v2/binary/train.jsonl` (SHA-256: `28014e3000632d4fc02e088a24d5ba7e5be156173d19ebf4a0a4c28424269d03`)
- `data/processed/sft_v2/binary/validation.jsonl` (SHA-256: `0a80e1ec608d002a0a2df3358055609ee35b3be79f17066929e79870be5f60cb`)

### A. Training Subset (Exactly 1,000 Records):
- **Sampling Strategy:** `stratified_source_balanced`
- **Source Breakdown:**
  - `halueval`: 500 records (250 FACTUAL, 250 HALLUCINATED)
  - `ragtruth`: 500 records (250 FACTUAL, 250 HALLUCINATED)
- **Total Class Counts:** Exactly 500 FACTUAL (Class 0) and 500 HALLUCINATED (Class 1).
- **Zero Document Leakage:** Verified via `verify_split_isolation()` prior to model loading.

### B. Validation Subset (Exactly 200 Records):
- **Source Breakdown:**
  - `halueval`: 100 records (50 FACTUAL, 50 HALLUCINATED)
  - `ragtruth`: 100 records (50 FACTUAL, 50 HALLUCINATED)
- **Total Class Counts:** Exactly 100 FACTUAL (Class 0) and 100 HALLUCINATED (Class 1).
- **Test-Set Access:** Strictly prohibited and rejected.

---

## 2. Input Serialization Format

Each record was serialized into two distinct text sequences:
- **Text A (Query and Evidence Context):** `f"{rec['question_or_claim']} {rec['context_or_evidence']}"`
- **Text B (Candidate Output Response):** `rec['candidate_response']`
- **Tokenization:** `DebertaV2Tokenizer` (SentencePiece vocab 128,001), padded to `max_length=128`, truncated at 128 tokens.
- **Label Mapping:** `"FACTUAL"` $	o 0$, `"HALLUCINATED"` $	o 1$.
