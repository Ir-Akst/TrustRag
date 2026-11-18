# Track 2, Step 3.2.1: Offline Model Loading & Classification Head Audit

**Audit Date:** November 14, 2026  
**Auditor:** Independent ML Infrastructure Auditor  
**Execution Environment:** `/home/aditya/rags/.venv-train/bin/python`  

---

## 1. Reproduction of Offline Loading Protocol

The offline loading protocol was independently verified under complete network containment:
- `HF_HUB_OFFLINE=1`
- `TRANSFORMERS_OFFLINE=1`
- `local_files_only=True` enforced on both `AutoTokenizer` and `AutoModelForSequenceClassification`.
- Outbound socket connections: **ZERO.**

---

## 2. Tokenizer Encoding & Decoding Verification

- **Class Loaded:** `DebertaV2Tokenizer`
- **Vocabulary Size:** `128,001` pieces (SentencePiece unigram vocabulary + special tokens).
- **Test Encoding:** `"TrustRAG verifies evidence grounding in retrieved passages."`
- **Generated Subword Tokens:** `['[CLS]', '▁Trust', 'RAG', '▁verifies', '▁evidence', '▁grounding', '▁in', '▁retrieved', '▁passages', '.', '[SEP]']`
- **Decoded String:** `"TrustRAG verifies evidence grounding in retrieved passages."`
- **Roundtrip Match:** **Exact bit-for-bit string match verified.**

---

## 3. Loading Key Discrepancies & Classifier Head Audit

When loading the upstream checkpoint into `DebertaV2ForSequenceClassification`, `transformers` reported the following parameter alignment:

### A. Unexpected Keys (Discarded from Checkpoint):
- `lm_predictions.lm_head.bias`
- `lm_predictions.lm_head.dense.bias`
- `lm_predictions.lm_head.dense.weight`
- `lm_predictions.lm_head.LayerNorm.bias`
- `lm_predictions.lm_head.LayerNorm.weight`
- `mask_predictions.classifier.bias`
- `mask_predictions.classifier.weight`
- `mask_predictions.dense.bias`
- `mask_predictions.dense.weight`
- `mask_predictions.LayerNorm.bias`
- `mask_predictions.LayerNorm.weight`

### B. Missing Keys (Newly Initialized from Scratch):
- `pooler.dense.weight` ($768 \times 768$)
- `pooler.dense.bias` ($768$)
- `classifier.weight` ($2 \times 768$)
- `classifier.bias` ($2$)

### Critical Classification Head Assessment:
> [!IMPORTANT]
> **Randomly Initialized Head Warning:**
> The entire classification projection head (`pooler` and `classifier`, totaling 592,130 parameters) was **newly initialized with random Gaussian weights** (`std=0.02`). 
> Consequently, the logits output during the inference test (`[0.1516, 0.2454]`) reflect **strictly random projections** of the pretrained representation. They do **NOT** provide any evidence that the model is trained or capable of binary hallucination classification. Training on downstream labeled data (`sft_v2/binary`) is mandatory before any classification utility exists.

---

## 4. Inference Forward Pass Telemetry

- **Input Prompt:** Question + Context + Candidate Answer (39 tokens).
- **Execution Mode:** Inference-only with `torch.no_grad()`.
- **CPU Execution Latency:** **322.5 ms** (Raptor Lake i7-1355U).
- **Output Softmax Probabilities:** `[0.4765625, 0.5234375]` (Near 50/50 uniform distribution, confirming random head initialization).
- **Floating Point Stability:** All logits and hidden activations evaluated to finite, non-NaN values.
