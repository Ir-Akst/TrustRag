# TrustRAG — Track 2, Step 3.7: Training Configuration & Runner Audit

## 1. Parameter Specification Audit

Audit of `NLITrainingConfig` and execution engine in `tools/training/train_nli_classifier.py` (`4e4b247edea5310b...`):

| Configuration Item | Specified Setting | Verification Finding | Compliance Status |
| :--- | :--- | :--- | :---: |
| **Backbone Path** | `/home/aditya/rags/models/pretrained/deberta-v3-small` | Exists locally, offline loading verified | **PASS** |
| **Numerical Precision** | FP32 (`torch.float32`) | Explicit `.float()` conversion verified | **PASS** |
| **Head Architecture** | 3-class linear projection (`[3, 768]`, `[3]`) | Verified dynamically in test suite | **PASS** |
| **Input Serialization** | `premise.strip(), hypothesis.strip()` | Verified, cross-encoder tokenization | **PASS** |
| **Sequence Length** | 128 tokens, `truncation=True`, `padding="max_length"` | Consistent with CPU feasibility pilot | **PASS** |
| **Optimizer** | `torch.optim.AdamW` | `lr=2e-5, weight_decay=0.01, betas=(0.9, 0.999)` | **PASS** |
| **LR Schedule** | Linear warmup (100 steps) + Linear decay | Verified lr update at each step | **PASS** |
| **Gradient Clipping** | `torch.nn.utils.clip_grad_norm_(..., max_norm=1.0)` | Active after backward pass | **PASS** |
| **Batch Size & Accum** | `batch_size=1`, `gradient_accumulation_steps=1` | 1 step = 1 sample = 1 optimizer update | **PASS** |
| **Training Budget** | 1,000 optimizer steps | Bounded loop `for step_idx in range(1000)` | **PASS** |
| **Checkpoint Path** | `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000` | Isolated new directory | **PASS** |
| **Atomic Serialization** | Temp dir `.tmp_*` -> rename | Prevents partial or corrupt checkpoints | **PASS** |
| **Authorization Gate** | Requires `--authorize-nli-training` flag | Verified: aborts immediately if absent | **PASS** |

---

## 2. Distinction: Steps vs. Batches vs. Epochs

To ensure complete clarity for auditing:
- **Optimizer Steps:** Exactly **1,000 steps**.
- **Batch Size:** 1 example per step.
- **Total Processed Training Examples:** 1,000 examples (balanced 334 / 333 / 333).
- **Full Epoch Equivalent:** 1,000 / 10,815 = **~0.092 epochs** (9.2% of full NLI training corpus).
