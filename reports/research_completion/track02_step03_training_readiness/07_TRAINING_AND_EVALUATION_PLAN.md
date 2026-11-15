# Track 2, Step 3.0: Neural Training, Validation & Evaluation Protocol

**Audit Date:** November 14, 2026  
**Auditor:** ML Infrastructure Auditor  

---

## 1. Objective Training Recipes

The training pipeline for actionable objectives (A, B, C) is structured around strict reproducibility and safety bounds:

### Recipe Matrix:

| Hyperparameter / Setting | Objective A: Binary Classification | Objective B: 3-Way NLI | Objective C: Fine-Grained Spans |
| :--- | :--- | :--- | :--- |
| **Base Architecture** | `microsoft/deberta-v3-small` | `microsoft/deberta-v3-small` | `microsoft/deberta-v3-base` |
| **Model Class** | `AutoModelForSequenceClassification` | `AutoModelForSequenceClassification` | `AutoModelForTokenClassification` |
| **Target Classes** | 2 (`[FAITHFUL, HALLUCINATED]`) | 3 (`[ENTAILMENT, NEUTRAL, CONTRADICTION]`) | 3 (`[O, B-HALL, I-HALL]`) |
| **Loss Function** | `BCEWithLogitsLoss` | `CrossEntropyLoss` (class-weighted) | Masked `CrossEntropyLoss` (`ignore_index=-100`) |
| **Initial Learning Rate** | $2.0 \times 10^{-5}$ | $3.0 \times 10^{-5}$ | $2.5 \times 10^{-5}$ |
| **LR Scheduler** | Linear warmup (10%) with cosine decay | Linear warmup (10%) with cosine decay | Linear warmup (10%) with cosine decay |
| **Physical Batch Size** | 8 | 8 | 4 |
| **Gradient Accumulation**| 2 steps (Effective Batch = 16) | 2 steps (Effective Batch = 16) | 4 steps (Effective Batch = 16) |
| **Weight Decay** | 0.01 | 0.01 | 0.01 |
| **Max Epochs** | 3 | 3 | 3 |
| **Evaluation Frequency** | Every 0.5 epoch | Every 0.5 epoch | Every 0.5 epoch |

---

## 2. Validation & Model Selection Strategy

1. **Split Isolation:**
   - Validation must strictly use the canonical `validation.jsonl` files from `data/processed/sft_v2/` (`binary`: 5,984 records, `nli`: 2,662 records, `spans`: 3,018 records).
   - Zero test-set leakage: Canonical evaluation benchmarks (RAGTruth test responses, HotpotQA validation, MS MARCO validation) remain strictly quarantined and isolated from the training loop.
2. **Checkpointing Protocol:**
   - Save checkpoint after each validation cycle if validation metric achieves a new optimum.
   - Maintain only the top-2 checkpoints (`save_total_limit = 2`) to preserve disk storage.

---

## 3. Evaluation Metrics & Success Criteria

Each objective specifies primary and secondary metrics aligned with TrustRAG's research goals:

| Objective | Primary Decision Metric | Secondary Diagnostic Metrics | Acceptance Target |
| :--- | :--- | :--- | :--- |
| **Objective A (Binary)** | **Validation Macro F1** | Accuracy, Precision, Recall, AUROC | Macro F1 $\ge 0.78$ |
| **Objective B (NLI)** | **Validation Balanced F1** | Class-wise F1 (Entailment, Contradiction, Neutral) | Macro F1 $\ge 0.75$, Contradiction F1 $\ge 0.70$ |
| **Objective C (Spans)** | **Character-Level Span F1** | Precision, Recall, Token-level F1 | Span F1 $\ge 0.65$ |

---

## 4. Stopping Criteria & Overfitting Mitigation

1. **Early Stopping:**
   - Monitor primary validation metric.
   - Patience = 3 evaluation intervals (1.5 epochs). If validation performance fails to improve by $\Delta \ge 0.005$, terminate training.
2. **Divergence Guard:**
   - If training loss increases for 2 consecutive logging steps or evaluates to `NaN`/`Inf`, immediately abort and rollback to previous valid checkpoint.

---

## 5. Hardware Threshold Fallback Protocols

If host memory or thermal constraints are breached during training, execute the following standardized fallbacks:

```
[ Condition: Resident Memory > 2.8 GB ]
       │
       ▼
Reduce physical batch size by 50% (e.g., 8 -> 4)
Double gradient accumulation steps (e.g., 2 -> 4)
       │
       ├─ Still > 2.8 GB? ──► Enable gradient_checkpointing = True
       │
       └─ Still > 2.8 GB? ──► Switch from Full Fine-Tuning to Linear Probe (Freeze base encoder)

[ Condition: Process CPU Thermal Throttling ]
       │
       ▼
Reduce OMP_NUM_THREADS from 6 to 4
Pin process priority via nice -n 10
```
