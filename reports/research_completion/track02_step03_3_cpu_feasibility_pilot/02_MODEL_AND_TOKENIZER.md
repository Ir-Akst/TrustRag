# Track 2, Step 3.3 — Section 02: Model Architecture and Tokenizer Audit

## 1. Staged Model Integrity & Offline Policy

- **Model Identifier:** `microsoft/deberta-v3-small`
- **Upstream Git Commit:** `a36c739020e01763fe789b4b85e2df55d6180012`
- **Local Directory:** `/home/aditya/rags/models/pretrained/deberta-v3-small`
- **Offline Flags:** `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `local_files_only=True`

All files were loaded strictly from the local filesystem without external network calls.

## 2. Tokenizer Architecture

- **Class:** `DebertaV2Tokenizer`
- **Vocabulary Size:** 128,001 tokens
- **Underlying SPM:** `spm.model` (2.44 MB SentencePiece model)
- **Offline Loading Latency:** 166.8 ms

## 3. Model Architecture & Checkpoint Analysis

- **Model Class:** `DebertaV2ForSequenceClassification`
- **Total Parameters:** 141,896,450
- **Trainable Parameters:** 141,896,450 (100% active in training mode)
- **Parameter Datatypes:** 100% `torch.float32` (converted from FP16 storage for CPU gradient computation)
- **Backbone Parameters:** 141,304,320
- **Classification Head Parameters:** 592,130

### Checkpoint Key Analysis:
1. **Intact Pretrained Weights:** All 102 backbone tensor layers from `deberta.*` (embeddings, encoder layers, relative position embeddings) loaded successfully.
2. **Missing Keys (Newly Initialized):**
   - `pooler.dense.weight` (768 x 768)
   - `pooler.dense.bias` (768)
   - `classifier.weight` (2 x 768)
   - `classifier.bias` (2)
   *Note: In accordance with standard Hugging Face DeBERTa-v3 architecture, the base pretrained checkpoint is a Masked Language Model (MLM). Sequence classification heads are newly initialized from a Gaussian distribution (`std=0.02`). They are NOT pretrained.*
3. **Unexpected Keys (Safely Discarded MLM Head):**
   - `mask_predictions.*` (dense, LayerNorm, classifier)
   - `lm_predictions.*` (dense, LayerNorm, bias)
   *These correspond to the pretraining masked language modeling objective and are discarded for sequence classification.*
