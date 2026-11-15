# Track 2, Step 3.2: Staged Model File Inventory & Technical Verification

**Audit Date:** November 14, 2026  
**Auditor:** Senior ML Infrastructure Engineer  
**Staged Model Directory:** `/home/aditya/rags/models/pretrained/deberta-v3-small/`  
**Upstream Commit:** `a36c739020e01763fe789b4b85e2df55d6180012`  

---

## 1. Complete File Inventory

An exhaustive catalog of all staged model artifacts was constructed:

| File Name | Exact File Size (Bytes) | Size (MB) | Purpose in DeBERTa Pipeline | Verification Method |
| :--- | :--- | :--- | :--- | :--- |
| **`pytorch_model.bin`** | 286,059,269 | 272.81 MB | Pretrained model weights (state_dict in PyTorch pickle format) | SHA-256 Verified & Model Loaded |
| **`spm.model`** | 2,464,616 | 2.35 MB | SentencePiece unigram vocabulary model (128,000 subwords) | Native SPM & DebertaV2Tokenizer Verified |
| **`README.md`** | 3,585 | < 0.01 MB | Official Hugging Face model card & license documentation | Text Inspected |
| **`config.json`** | 578 | < 0.01 MB | Model architecture hyperparameters & configuration | JSON Parsed & AutoConfig Loaded |
| **`.gitattributes`** | 1,175 | < 0.01 MB | Git LFS tracking configuration from upstream repository | Text Inspected |
| **`tokenizer_config.json`** | 52 | < 0.01 MB | Tokenizer mapping rules and special token references | JSON Parsed |

**Total Snapshot Footprint:** **288,529,275 bytes (275.16 MB)** across 6 files.

---

## 2. Completeness & Integrity Checks

1. **No Partial Shards:** `pytorch_model.bin` is a monolithic 286 MB weight file. No multi-shard indices (`pytorch_model.bin.index.json`) are required for `deberta-v3-small`.
2. **Tokenizer Vocabulary Completeness:** `spm.model` contains all 128,000 base pieces; `AutoTokenizer` extends this to 128,001 with special tokens (`[PAD]`, `[CLS]`, `[SEP]`, `[UNK]`, `[MASK]`).
3. **Architecture Match:** `config.json` verifies:
   - `hidden_size`: 768
   - `num_hidden_layers`: 6
   - `num_attention_heads`: 12
   - `intermediate_size`: 3072
   - `relative_attention`: true
   - `pos_att_type`: `["p2c", "c2p"]` (Disentangled position attention)
