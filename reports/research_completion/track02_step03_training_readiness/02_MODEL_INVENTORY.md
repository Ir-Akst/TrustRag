# Track 2, Step 3.0: Pretrained Model Inventory & Architecture Compatibility

**Audit Date:** November 14, 2026  
**Auditor:** ML Infrastructure Auditor  

---

## 1. Inventory of Locally Available Models & Weights

A recursive filesystem inspection across `/home/aditya/.cache/huggingface`, `/home/aditya/rags/models`, and system paths was conducted:

| Location | Observed Content | Model Weight Status |
| :--- | :--- | :--- |
| `~/.cache/huggingface/hub/` | Arrow/parquet data shards for `hotpotqa`, `ms_marco`, `natural_questions`. | **Zero model checkpoints.** |
| `/home/aditya/rags/models/checkpoints/` | `.gitkeep` (0 bytes). | **Empty.** |
| `/home/aditya/rags/models/pretrained/` | `.gitkeep` (0 bytes). | **Empty.** |
| `/home/aditya/rags/models/detectors/` | `.gitkeep` (0 bytes). | **Empty.** |
| `/home/aditya/rags/TrustRag-phase11/models/` | Directory does not exist. | **Empty.** |

**Conclusion:** There are currently **zero pretrained model weights** cached or stored anywhere on the local filesystem.

---

## 2. Configuration & Policy Constraints

TrustRAG enforces strict offline execution constraints within `src/trustrag/config/engine_config.py` and `src/trustrag/srm/hf_local.py`:

```python
# Engine Configuration Safeguards
local_files_only: bool = Field(
    default=True,
    description="Disallow automatic remote weight downloads; require locally staged checkpoints"
)
trust_remote_code: bool = Field(
    default=False,
    description="Explicit opt-in required before executing custom tokenizer/model code"
)
```

If a training or inference run attempts to load an unstaged Hugging Face model identifier (e.g., `"microsoft/deberta-v3-small"`), `HuggingFaceLocalSRMBackend` immediately raises `ProviderError`:
> `Local checkpoint 'microsoft/deberta-v3-small' not found and local_files_only=True (automatic remote download disabled).`

Therefore, all required model checkpoints, configurations, and tokenizer vocabularies must be staged out-of-band prior to starting training.

---

## 3. Architecture Compatibility & Feasibility Analysis

We evaluate candidate architectures against the audited host hardware (Intel Core i7-1355U CPU, 3.34 GB available RAM, 0 GB VRAM):

### A. Compact Discriminative Encoders (Recommended for CPU)

| Model Candidate | Parameter Count | Weight Footprint (FP32 / FP16) | Native Context Window | License | Host CPU Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`microsoft/deberta-v3-small`** | 44 Million | 176 MB / 88 MB | 512 tokens | MIT | **HIGHLY FEASIBLE** (Fits comfortably in < 1.0 GB RAM) |
| **`distilbert-base-uncased`** | 66 Million | 268 MB / 134 MB | 512 tokens | Apache 2.0 | **HIGHLY FEASIBLE** (Fast CPU inference / backprop) |
| **`microsoft/deberta-v3-base`** | 86 Million | 344 MB / 172 MB | 512 tokens | MIT | **FEASIBLE** (Memory ~1.5 GB during training) |
| **`roberta-base`** | 125 Million | 500 MB / 250 MB | 512 tokens | MIT | **FEASIBLE WITH BOUNDED BATCH** (RAM ~2.0 GB) |

### B. Small Generative / Reasoning Models (Causal LMs)

| Model Candidate | Parameter Count | Weight Footprint (FP16 / 4-bit) | Native Context Window | License | Host CPU Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`Qwen/Qwen2.5-0.5B-Instruct`**| 490 Million | 1.0 GB / 0.35 GB | 32,768 tokens | Apache 2.0 | **MARGINAL** (Inference feasible; training thrashing) |
| **`Qwen/Qwen2.5-1.5B-Instruct`**| 1.54 Billion | 3.1 GB / 1.1 GB | 32,768 tokens | Apache 2.0 | **INFEASIBLE ON HOST** (Exceeds 3.34 GB available RAM) |
| **`Qwen/Qwen2.5-Coder-7B-Instruct`**| 7.61 Billion | 15.2 GB / 5.2 GB | 128,000 tokens | Apache 2.0 | **IMPOSSIBLE ON HOST** (Immediate OOM crash) |

---

## 4. Tokenizer Compatibility

The Python environment has `tokenizers` version `0.23.3` installed, compatible with Hugging Face fast tokenizers:
- **Fast Tokenizer Support:** Rust-based backend handles batch tokenization and character-to-token offset mapping (`return_offsets_mapping=True`).
- **Span Extraction Mapping:** Objective C (Span Extraction) requires exact character-level alignment to candidate responses. Fast BPE / WordPiece tokenizers provide the necessary `offset_mapping` tuples `(start_char, end_char)`.
- **Special Token Requirements:**
  - Encoders (`[CLS]`, `[SEP]`, `[PAD]`, `[UNK]`)
  - Causal LMs (`<|im_start|>`, `<|im_end|>`, `<think>`, `</think>`)
