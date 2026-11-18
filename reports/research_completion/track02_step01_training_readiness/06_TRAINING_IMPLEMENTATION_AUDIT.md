# TrustRAG — Track 2, Step 1: Independent Neural Training Readiness Audit
# 06 — Training Implementation, Codebase Architecture & Pipeline Audit

**Audit Objective:** Inspect the existing codebase to evaluate whether training entrypoints, PyTorch datasets, collators, loss functions, validation loops, checkpoint handlers, and experiment logging exist.

---

## 1. Codebase Training Infrastructure Inventory

A thorough audit of `src/`, `tools/`, `configs/`, and `tests/` was performed:

| Component / Routine | Expected Responsibility | Current Implementation State | Audit Status |
| :--- | :--- | :--- | :---: |
| **Training Entrypoint Script** | CLI script accepting config, seed, epochs, LR, output dir | **NON-EXISTENT** (0 training scripts found) | **BLOCKED** |
| **PyTorch Dataset Classes** | PyTorch `Dataset` parsing JSONL into input IDs & target labels | **NON-EXISTENT** (Only raw data loaders in `data/loaders/`) | **BLOCKED** |
| **Data Collator** | Padding sequences dynamically to batch max length with label masking | **NON-EXISTENT** | **BLOCKED** |
| **Loss Function Configuration** | Cross-entropy / ORPO loss with appropriate label smoothing | **NON-EXISTENT** | **BLOCKED** |
| **Optimizer & Scheduler** | AdamW with cosine decay and warmup steps | **NON-EXISTENT** | **BLOCKED** |
| **Checkpoint Management** | Saving top-K checkpoints by validation loss, resuming from state | **NON-EXISTENT** | **BLOCKED** |
| **Validation & Early Stopping** | Evaluating validation split every $N$ steps to halt overfitting | **NON-EXISTENT** | **BLOCKED** |
| **Tokenizer Persistence** | Saving tokenizer alongside model weights with identical special tokens | **NON-EXISTENT** | **BLOCKED** |
| **Training Config Schema** | Pydantic / YAML schema defining batch size, grad accum, LoRA rank | **NON-EXISTENT** | **BLOCKED** |
| **Evaluation Integration** | Running G3 verifier test on checkpoint outputs | Implemented in `tools/evaluation/run_track02_benchmarks.py` | **READY** |

---

## 2. Review of Existing SRM Modules in `src/trustrag/srm/`

The repository contains an SRM module suite developed during Phase 08 / Phase 10:
- `src/trustrag/srm/client.py`: Client orchestrating SRM invocation, fallback, and health checks.
- `src/trustrag/srm/backends.py`: Backend base classes, prompting logic (`_build_srm_prompt`), JSON parser (`_parse_srm_json`), and deterministic fallback (`DeterministicFallbackBackend`).
- `src/trustrag/srm/hf_local.py`: Local Hugging Face / PEFT inference backend.
- `src/trustrag/srm/registry.py`: Factory registry instantiating SRM backends.

### Key Architectural Findings:
1. **Strictly Inference-Only:** Every module in `srm/` is written solely for **inference, prompt construction, and response parsing**. None of these classes contain training loops, gradient calculations, backward passes, or optimizer updates.
2. **Missing Dependencies Fail Gracefully at Runtime:**
   - In `src/trustrag/srm/hf_local.py`:
     ```python
     @staticmethod
     def _import_optional_runtime() -> tuple[Any, Any, Any | None]:
         try:
             torch_mod = importlib.import_module("torch")
             transformers_mod = importlib.import_module("transformers")
         except ImportError as exc:
             raise ProviderError(
                 "hf_local SRM backend requires optional dependencies 'torch' and 'transformers', "
                 f"which are not installed in this environment: {exc}"
             ) from exc
     ```
   - When configured with `backend: "hf_local"`, the system raises `ProviderError` as expected, triggering the deterministic evidence fallback.
3. **No Training Configurations in `configs/`:**
   - `configs/` contains only runtime evaluation configs (`configs/evaluation/phase10_eval.yaml`).
   - No `train_srm.yaml`, `sft_config.yaml`, or `orpo_config.yaml` exists.

---

## 3. Engineering Requirements for Track 2 Training Harness

When hardware and libraries are provisioned, the following components must be implemented from scratch:

1. **`src/trustrag/training/dataset.py`:**
   - Implements `SRMDataset(torch.utils.data.Dataset)`.
   - Tokenizes `(document, claim)` pairs.
   - Applies `<think>` prompt templates and masks prompt tokens with `-100` so loss is only calculated over target reasoning tokens.
2. **`src/trustrag/training/config.py`:**
   - Defines `TrainingConfig(BaseModel)` with `extra="forbid"`.
   - Fields: `base_model_name`, `output_dir`, `learning_rate`, `batch_size`, `gradient_accumulation_steps`, `lora_r`, `lora_alpha`, `lora_dropout`, `max_seq_length`, `seed`.
3. **`tools/training/train_srm.py`:**
   - Main executable training pipeline.
   - Sets random seeds (`set_seed(42)`).
   - Initializes tokenizer, model, and PEFT LoRA adapter.
   - Instantiates Hugging Face `Trainer` / `SFTTrainer`.
   - Executes training, validation evaluation, model saving, and artifact export.

---

## 4. Implementation Audit Conclusion

The repository currently possesses **zero training code**. Training cannot be launched by invoking an existing script. A complete training harness must be authored before Track 2 model training can commence.

