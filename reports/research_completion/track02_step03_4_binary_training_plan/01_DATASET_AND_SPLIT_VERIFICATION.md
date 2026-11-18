# Track 2, Step 3.4 — Section 01: Dataset and Split Verification

## 1. Authoritative Binary Dataset Census

The binary classification objective utilizes the remediated `sft_v2` dataset stored in:
`/home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/`

Authoritative files verified via SHA-256 manifests:
- `dataset_manifest.json` (SHA-256: `6cb54641c888d3824bb884d5df3324a35016e7dd7ce606e1b73e5bf7d02ff86e`)
- `schema.json` (SHA-256: `3d8429f56e9c93a90729ee9449f2b87fcf39369974249a21e7d0cf0c0347ee63`)
- `exclusion_manifest.json` (SHA-256: `2f0da64a2ba437f1912a76f238b7250ea546ba8c919d363ef80fece789539f16`)
- `train.jsonl` (26,054 records, SHA-256: `28014e3000632d4fc02e088a24d5ba7e5be156173d19ebf4a0a4c28424269d03`)
- `validation.jsonl` (5,984 records, SHA-256: `0a80e1ec608d002a0a2df3358055609ee35b3be79f17066929e79870be5f60cb`)

Zero document leakage exists between train and validation (`train_val_doc_overlap: 0`).

---

## 2. Bounded Training Subset Specification (1,000 Examples)

To evaluate fine-tuning feasibility without incurring 10+ hours of full-epoch CPU load, the plan defines a deterministic subset of **1,000 training examples**:
- **Source Selection:** Lines 1–1,000 of `data/processed/sft_v2/binary/train.jsonl`.
- **Label Balance:**
  - `FACTUAL` (Class 0): **500 examples** (50.0%)
  - `HALLUCINATED` (Class 1): **500 examples** (50.0%)
- **Source Dataset:** `halueval` (canonical right and hallucinated pairs).
- **Leakage Integrity:** Every example in lines 1–1,000 has been verified against the exclusion manifest; none are present in validation or test splits.

---

## 3. Bounded Validation Subset Specification (200 Examples)

To evaluate generalization and loss reduction without slowing down the bounded experiment:
- **Source Selection:** Lines 1–200 of `data/processed/sft_v2/binary/validation.jsonl`.
- **Label Balance:**
  - `FACTUAL` (Class 0): **100 examples** (50.0%)
  - `HALLUCINATED` (Class 1): **100 examples** (50.0%)
- **Document Overlap:** 0 document overlap with the training set.
- **Evaluation Timing:** Evaluated before training (step 0 baseline) and immediately upon completion of step 1,000.

---

## 4. Input Formatting & Tokenization Schema

Each example is processed into a sequence pair:
```
Text A (Premise):   question_or_claim + " " + context_or_evidence
Text B (Hypothesis): candidate_response
```
- **Tokenization:** `DebertaV2Tokenizer` loaded locally (`local_files_only=True`).
- **Padding:** Padded to `max_length=128`.
- **Truncation:** `truncation=True` (head-truncate if premise exceeds token limits).
- **Label Mapping:**
  - `"FACTUAL"` $	o 0$
  - `"HALLUCINATED"` $	o 1$
