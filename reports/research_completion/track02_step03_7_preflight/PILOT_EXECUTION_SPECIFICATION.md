# TrustRAG — Track 2: Bounded 1,000-Step NLI Pilot Execution Specification

> **STANDBY SPECIFICATION — NOT AN AUTHORIZATION TO EXECUTE**  
> This specification defines the exact, unmodifiable execution parameters for the proposed 1,000-step NLI training pilot.

---

## 1. Experiment Overview

- **Target Architecture:** `microsoft/deberta-v3-small` (FP32)
- **Objective:** Evidence-Grounded 3-Way Natural Language Inference (`ENTAILMENT=0`, `CONTRADICTION=1`, `NEUTRAL=2`)
- **Optimization Budget:** Exactly **1,000 optimizer steps** (1 sample per step, batch size 1).
- **Training Sampler:** Deterministic `stratified_class_balanced` (334 Entailment, 333 Contradiction, 333 Neutral).
- **Validation Dataset:** Original imbalanced validation split (`data/processed/sft_v2/nli/validation.jsonl`, N=2,662).
- **Optimizer:** `AdamW(lr=2e-5, weight_decay=0.01, betas=(0.9, 0.999), eps=1e-8)`.
- **LR Schedule:** Linear warmup (100 steps) + Linear decay to 0.0.
- **Gradient Clipping:** Max norm = 1.0.
- **Sequence Length:** 128 tokens (`max_length=128`, `truncation=True`).
- **Network Mode:** 100% Offline (`HF_HUB_OFFLINE=1`).

---

## 2. Checkpoint Management

- **Input Model Snapshot:** `/home/aditya/rags/models/pretrained/deberta-v3-small` (Read-Only)
- **Output Checkpoint Directory:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000` (Isolated)
- **Preserved Checkpoints:**
  * `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000` (**STRICTLY IMMUTABLE**)
  * `/home/aditya/rags/TrustRag` Phase 10 Baseline (**STRICTLY IMMUTABLE**)

---

## 3. Required CLI Invocation (Upon User Authorization)

```bash
/home/aditya/rags/.venv-train/bin/python tools/training/train_nli_classifier.py \
    --authorize-nli-training \
    --max-train-samples 1000 \
    --max-val-samples 2662 \
    --learning-rate 2e-5 \
    --warmup-steps 100 \
    --weight-decay 0.01 \
    --seed 42
```
