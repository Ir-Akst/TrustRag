# Track 2, Step 3.3.1 — Section 02: Model Architecture and Dataset Provenance Audit

## 1. Model Provenance & Full-Architecture Verification

- **Staged Model Directory:** `/home/aditya/rags/models/pretrained/deberta-v3-small`
- **Upstream Source:** `microsoft/deberta-v3-small`
- **Pinned Upstream Commit:** `a36c739020e01763fe789b4b85e2df55d6180012`
- **Offline Environment Verification:** Enforced via `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, and `local_files_only=True`. No network requests occurred.

### Independent Parameter Breakdown:
- **Total Parameters:** `141,896,450`
- **Backbone Parameters:** `141,304,320` across 102 tensor weights.
- **Head & Pooler Parameters:** `592,130` across 4 tensor weights:
  - `pooler.dense.weight` ($768 \times 768 = 589,824$)
  - `pooler.dense.bias` ($768$)
  - `classifier.weight` ($2 \times 768 = 1,536$)
  - `classifier.bias` ($2$)
- **Total Trainable Parameters:** `141,896,450` (100% active).
- **Runtime Dtype:** `torch.float32`. Checkpoint weights stored as `torch.float16` in `pytorch_model.bin` were correctly upcast to FP32 for CPU autograd.
- **Backbone Authenticity:** Confirmed. The model is NOT a toy substitute (such as the 0.48M model used in Step 3.1).

### Discrepancy Note (DISC-01):
The Step 3.3 report described autograd as running *"through all 12 transformer encoder blocks"*. Independent inspection of `config.json` confirms that `microsoft/deberta-v3-small` consists of **6 hidden layers** (`num_hidden_layers: 6`) with **12 attention heads** (`num_attention_heads: 12`). This is a minor descriptive confusion between layers and attention heads; the actual tensor graph executed all 6 layers without omission.

---

## 2. Dataset and Tokenizer Provenance Audit

- **Input File:** `data/processed/sft_v2/binary/train.jsonl` (26,054 records)
- **Schema Fields Tested:** `question_or_claim`, `context_or_evidence`, `candidate_response`, `binary_label`.
- **Tokenizer:** `DebertaV2Tokenizer` loaded from local SentencePiece model (`spm.model`, 128,001 tokens).
- **Format:** Pair encoding: `Premise = question + context`, `Hypothesis = candidate_response`.
- **Label Mapping:** `"FACTUAL"` $\to 0$, `"HALLUCINATED"` $\to 1$.

### Independent Token Reproduction:
The exact three records from lines 1–3 of `train.jsonl` were re-tokenized using the staged tokenizer:
1. `binary_halueval_train_halueval_0_factual` $\to$ **62 active tokens**
2. `binary_halueval_train_halueval_0_hallucinated` $\to$ **65 active tokens**
3. `binary_halueval_train_halueval_1000_factual` $\to$ **100 active tokens**

All active token counts, text fields, and label assignments match the reported telemetry bit-for-bit. Zero synthetic random token IDs were used.
