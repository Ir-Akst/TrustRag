# TrustRAG Phase 11.1 NLI Training Safe Pause & Resume Audit

**Date:** 2026-11-16T01:03:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11` (`aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Campaign:** DeBERTa-v3-small 3-Way NLI Training Campaign  
**Final Status:** `SAFELY_PAUSED_RESUMABLE`  

---

## 1. Process Identification & Lifecycle

| Property | Value |
|---|---|
| **Host Process PID** | `13069` |
| **Wrapper Shell PID** | `13068` |
| **Antigravity Task ID** | `task-10254` |
| **Launch Time** | `Sun Nov 15 18:51:24 2026` |
| **Termination Time** | `Mon Nov 16 01:02:25 2026` |
| **Total Wall-Clock Runtime** | 6 hours 11 minutes |
| **Termination Signal** | `SIGTERM` (signal 15) gracefully handled |
| **Process Exit Code** | `0` (clean exit) |
| **Live State** | Fully exited; 0 residual processes |

---

## 2. Checkpoint Verification & Acceptance

The latest checkpoint was atomically saved at Step 1,000, and earlier checkpoints remain intact.

### A. Latest Checkpoint (`checkpoint_step_001000`)
- **Directory:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch/checkpoint_step_001000`
- **Creation Timestamp:** `2026-11-15T19:11:07Z` (00:41:07 local time)
- **Global Optimizer Step:** `1,000`
- **Epoch:** `1` of `3`
- **Last Consumed Sample Index:** `3,999` of `10,815`
- **Next Unconsumed Sample Index on Resume:** `4,000`
- **Gradient Accumulation Count at Checkpoint:** `0` (clean boundary, 0 pending gradients)
- **Learning Rate:** `1.775587e-05`
- **SHA-256 Integrity Verification:** **100% PASS** (`OK`)
- **Files Verified:**
  - `model.safetensors` (567,601,628 bytes)
  - `optimizer.pt` (1,135,263,947 bytes — 1 param group, 106 state dictionaries)
  - `scheduler.pt` (1,337 bytes)
  - `rng_state.pt` (14,455 bytes — PyTorch, NumPy, Python RNG states)
  - `checkpoint_meta.json` (1,468 bytes)
  - `checksums.sha256` (655 bytes)
  - `config.json` (1,096 bytes)
  - `tokenizer.json` (8,339,876 bytes)
  - `tokenizer_config.json` (536 bytes)

### B. Pointer & Prior Checkpoint
- **`latest_checkpoint.json`:** Verified pointing to `checkpoint_step_001000`.
- **`checkpoint_step_000500/`:** Verified intact with 100% SHA-256 integrity passing.

---

## 3. Resume Plan & Exact CLI Command

When authorized to resume, executing the command below will resume training seamlessly without restarting from step zero or duplicating samples:

```bash
cd /home/aditya/rags/TrustRag-phase11 && PYTHONPATH=. /home/aditya/rags/.venv-train/bin/python tools/training/train_nli_classifier.py \
  --authorize-nli-training \
  --model-dir /home/aditya/rags/models/pretrained/deberta-v3-small \
  --train-file /home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/train.jsonl \
  --val-file /home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/validation.jsonl \
  --output-dir /home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch \
  --resume-from-checkpoint /home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch/checkpoint_step_001000 \
  --report-dir /home/aditya/rags/TrustRag-phase11/reports/research_completion/phase11_1_step03_full_nli_training \
  --max-train-samples 10815 \
  --max-val-samples 2662 \
  --epochs 3 \
  --gradient-accumulation-steps 4 \
  --sampler-strategy sequential \
  --class-weights 1.0 3.5 1.5 \
  --save-predictions \
  --max-seq-len 384 \
  --min-premise-tokens 64 \
  --learning-rate 2e-5 \
  --warmup-steps 100 \
  --weight-decay 0.01 \
  --num-threads 10 \
  --interop-threads 1 \
  --checkpoint-every-steps 500 \
  --keep-last-n-checkpoints 2 \
  --ram-abort-threshold-mb 700.0 \
  --swap-free-min-mb 1000.0 \
  --max-process-rss-mb 4500.0 \
  --watchdog-consecutive-violations 3 \
  --seed 42 \
  --max-duration-seconds 86400.0
```

### Resume Execution Semantics
1. **Sample Fast-Forward:** Skips samples 0..3999 in 0.1s and begins training immediately at sample index 4000.
2. **Optimizer & RNG Continuity:** Restores AdamW first/second momentum tensors and exact RNG seeds.
3. **Step 0 Baseline Skip:** Restores Step 0 baseline evaluation metrics from metadata, avoiding a redundant 18-minute validation run.
4. **Remaining Workload:** 7,112 optimizer steps remaining out of 8,112 total (~14–16 CPU hours).

