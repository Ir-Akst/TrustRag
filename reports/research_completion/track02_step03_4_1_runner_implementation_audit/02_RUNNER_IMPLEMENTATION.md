# Track 2, Step 3.4.1 — Section 02: Runner Implementation Architecture

## 1. Script Architecture & Design

The runner script is located at:
`/home/aditya/rags/TrustRag-phase11/tools/training/train_binary_classifier.py`

### Module Layout:
1. **Configuration Dataclass (`TrainingConfig`):** Type-annotated parameters with sensible defaults.
2. **Watchdog Monitor (`WatchdogMonitor`):** Real-time host telemetry sampling on every step.
3. **Data Loading & Sampling (`load_binary_dataset`):** Implements `stratified_source_balanced` and `sequential` modes with record validation.
4. **Input Serialization (`serialize_binary_input`):**
   - Text A (Query and Evidence Context): `question_or_claim` + `" "` + `context_or_evidence`
   - Text B (Candidate Output Response): `candidate_response`
   - *Note: Avoids NLI premise/hypothesis terminology.*
5. **Evaluation Engine (`compute_binary_metrics`):** Strict arithmetic for accuracy, balanced accuracy, precision/recall/F1, and confusion matrix.
6. **Atomic Checkpoint Serializer (`save_checkpoint_atomic`):** Temporary directory creation followed by atomic directory move; protects base model directory from overwrite.
7. **Training Loop (`run_training_experiment`):**
   - Offline model & tokenizer instantiation.
   - Step 0 pre-training baseline validation.
   - Bounded 1,000-step training loop with per-step watchdog check.
   - Linear warmup (100 steps) + linear decay learning rate schedule.
   - Step 1,000 post-training validation.
   - Atomic checkpoint export.
8. **CLI Interface (`parse_args`):** Exposes all hyperparameters and memory thresholds.

---

## 2. Hyperparameter Specifications

- **Model Target:** `microsoft/deberta-v3-small` (141.9M params, FP32).
- **Classification Head:** 2-class linear projection head ($2 	imes 768$).
- **Batch Size:** 1.
- **Max Sequence Length:** 128 tokens.
- **Base Learning Rate:** $2 	imes 10^{-5}$ (`2e-5`).
- **Weight Decay:** $0.01$.
- **Warmup Steps:** 100 steps ($10\%$).
- **Total Training Steps:** Exactly 1,000 steps (1 epoch of the subset).
- **Optimizer:** `AdamW` $(eta_1=0.9, eta_2=0.999, \epsilon=10^{-8})$.
- **CPU Concurrency:** 4 threads pinned (`torch.set_num_threads(4)`).
- **Deterministic Seed:** 42.
