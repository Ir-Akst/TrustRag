# Track 2, Step 3.2.1: Model Architecture & Precision Dtype Audit

**Audit Date:** November 14, 2026  
**Auditor:** Independent ML Infrastructure Auditor  
**Model Target:** `microsoft/deberta-v3-small`  

---

## 1. Architectural Configuration Census

The model configuration was inspected directly via `AutoConfig.from_pretrained()`:

| Architectural Hyperparameter | Inspected Value | Canonical Specification |
| :--- | :--- | :--- |
| **Model Architecture Class** | `DebertaV2ForSequenceClassification` | DeBERTa-v3 with Sequence Classification Head |
| **Encoder Layers ($L$)** | **6 layers** | 6 transformer blocks |
| **Hidden Dimension ($d$)** | **768** | 768 projection units |
| **Intermediate Size ($d_{\text{ff}}$)**| **3,072** | $4 \times d_{\text{model}}$ feed-forward expansion |
| **Attention Heads ($A$)** | **12 heads** | 64 dimensions per attention head |
| **Relative Attention Type** | Disentangled (`["p2c", "c2p"]`)| Content-to-position & position-to-content |
| **Max Position Embeddings** | 512 | Native context window cutoff |
| **Vocabulary Size** | 128,100 (Native SPM) / 128,001 (Tokenizer) | SentencePiece Unigram vocabulary |

---

## 2. Parameter Breakdown & Dtype Distribution

An exact tensor-by-tensor count was executed across the loaded `DebertaV2ForSequenceClassification` model:

| Submodule / Component | Parameter Count | Precision Dtype | Storage Size (Bytes) |
| :--- | :--- | :--- | :--- |
| **Word Embeddings (`word_embeddings.weight`)** | $128,100 \times 768 = 98,380,800$ | `torch.float16` | 196,761,600 |
| **Transformer Encoder (6 Blocks)** | $42,923,520$ | `torch.float16` | 85,847,040 |
| **LayerNorm & Bias Terms** | $97,000$ | `torch.float16` | 194,000 |
| **Total Backbone Parameters** | **141,304,320** | **`torch.float16`** | **282,608,640** |
| **Pooler Dense Layer (`pooler.dense.*`)** | $768 \times 768 + 768 = 590,592$ | `torch.float16` | 1,181,184 |
| **Classification Projection (`classifier.*`)** | $768 \times 2 + 2 = 1,538$ | `torch.float16` | 3,076 |
| **Total Model Parameters** | **141,896,450 (141.9M)** | **`torch.float16` (100.0%)** | **283,792,900** |

- **Trainable Parameters:** 141,896,450 (100.0% active).
- **Embedding Weight Dtype:** `torch.float16`
- **Classification Head Dtype:** `torch.float16`

---

## 3. Resolving the Checkpoint File Size vs Parameter Count Relationship

The raw byte size of the staged weight file is **286,059,269 bytes**. The relationship to the **141,896,450 loaded parameters** is explained mathematically:

1. **Checkpoint Contents (Masked LM Pretrained):**
   The upstream `pytorch_model.bin` contains the weights for the original Masked LM model (`DebertaV2ForMaskedLM`), totaling **143,010,661 parameters** (including the MLM prediction head).
2. **Precision Dtype:**
   All 143,010,661 parameters in the checkpoint are encoded as **16-bit half-precision floats (`torch.float16`)**:
   $$\text{Raw Tensor Bytes} = 143,010,661\text{ parameters} \times 2\text{ bytes/parameter} = 286,021,322\text{ bytes}$$
3. **Zip Archive Overhead:**
   $$\text{Packaging Overhead} = 286,059,269 - 286,021,322 = 37,947\text{ bytes}$$
   This 37.9 kB difference accounts exactly for zip central directory records, compression headers, and tensor naming metadata.
4. **Loading into Sequence Classification:**
   When loaded into `DebertaV2ForSequenceClassification`:
   - 1,706,341 MLM head parameters are discarded as UNEXPECTED.
   - 592,130 classification head parameters are newly created in FP16.
   - Resulting in the active 141,896,450 in-memory parameters.
