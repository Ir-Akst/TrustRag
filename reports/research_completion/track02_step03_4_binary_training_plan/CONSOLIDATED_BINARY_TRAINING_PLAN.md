# TrustRAG — Track 2, Step 3.4: Bounded Binary Classification Training Plan Consolidated Report

**Document ID:** `TRUSTRAG-TRACK02-STEP03-4-CONSOLIDATED`  
**Date:** 2026-11-14  
**Auditor Role:** Senior ML Infrastructure Engineer & Experimental Auditor  
**Overall Verdict:** `READY_FOR_EXPLICIT_TRAINING_AUTHORIZATION`  
**Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, Baseline HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Protected Baseline:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, UNTOUCHED)  
**Model Architecture:** `microsoft/deberta-v3-small` (141,896,450 parameters, FP32)  
**Dataset Path:** `data/processed/sft_v2/binary/` (26,054 train records, 5,984 val records)  

---

## 1. Executive Summary & Verdict

### Final Verdict: `READY_FOR_EXPLICIT_TRAINING_AUTHORIZATION`

Following the successful completion and independent verification of the Step 3.3 CPU feasibility pilot (which proved that 141.9M parameter DeBERTa forward, backward, and AdamW optimizer steps run stably on host CPU with ~2.37 GB peak RSS), this document delivers the **complete engineering preflight, experimental design, metric specification, and safety protocol** for a bounded 1,000-example training run.

### Key Preflight Confirmations:
1. **Model & Tokenizer Ready:** Pretrained weights (`microsoft/deberta-v3-small`, commit `a36c739020e01763fe789b4b85e2df55d6180012`) and `DebertaV2Tokenizer` are staged locally and verified offline.
2. **Dataset Remediated:** `data/processed/sft_v2/binary/` exhibits zero document leakage between train, validation, and test splits.
3. **Execution Scope Strictly Bounded:** Exactly **1,000 training examples** (500 FACTUAL, 500 HALLUCINATED) and **200 validation examples** (100 FACTUAL, 100 HALLUCINATED).
4. **Computational Feasibility:** Estimated run time is **19.7 minutes** on 4 CPU threads, well within the **30-minute safety limit**.
5. **Safety Abort Limit:** Immediate termination if available host physical RAM drops below **700 MB**.

---

## 2. Proposed Training Configuration Specification

| Hyperparameter / Setting | Value | Engineering Rationale |
|--------------------------|:-----:|-----------------------|
| **Objective** | Binary Classification | Detects factual vs. hallucinated responses. |
| **Model Class** | `DebertaV2ForSequenceClassification` | Pretrained encoder with 2-class classification head. |
| **Runtime Datatype** | `torch.float32` (FP32) | Required for numerical stability during CPU autograd backpropagation. |
| **Training Subset** | **1,000 examples** | Lines 1–1,000 of `binary/train.jsonl` (500 FACTUAL, 500 HALLUCINATED). |
| **Validation Subset** | **200 examples** | Lines 1–200 of `binary/validation.jsonl` (100 FACTUAL, 100 HALLUCINATED). |
| **Batch Size** | **1** | Maintains peak process RSS at ~2.37 GB, preserving $> 4.5	ext{ GB}$ host memory headroom. |
| **Max Sequence Length** | **128 tokens** | Padded/truncated sequence length accommodating query, evidence, and response. |
| **Total Steps** | **1,000 steps** | Exactly 1 epoch of the bounded training subset. |
| **Optimizer** | `AdamW` | Weight decay regularization on non-bias, non-norm weights. |
| **Base Learning Rate** | $2 	imes 10^{-5}$ (`2e-5`) | Stable learning rate for DeBERTa fine-tuning. |
| **Weight Decay** | $0.01$ | Standard L2 weight regularization. |
| **Warmup Steps** | $100$ steps ($10\%$) | Linear warmup prevents early classification-head gradient shock. |
| **Learning Rate Decay** | Linear decay to 0.0 | Promotes smooth parameter convergence. |
| **CPU Concurrency** | 4 threads | `torch.set_num_threads(4)` prevents thread contention on mobile CPU. |
| **Deterministic Seed** | 42 | Ensures exact reproducibility. |

---

## 3. Evaluation and Metrics Protocol

### Metric Suite:
- **Loss:** `torch.nn.CrossEntropyLoss` (tracked continuously on train; measured at step 0 and step 1,000 on validation).
- **Classification Performance:**
  - Accuracy: $(TP + TN) / (TP + TN + FP + FN)$
  - Balanced Accuracy: $rac{1}{2}(	ext{TPR} + 	ext{TNR})$
  - Precision, Recall, F1 for Class 0 (`FACTUAL`)
  - Precision, Recall, F1 for Class 1 (`HALLUCINATED`)
  - Macro F1: $rac{1}{2}(F1_0 + F1_1)$
  - 2x2 Confusion Matrix ($TP, FP, TN, FN$)
- **Abstention Policy:** Explicitly excluded. Classification is strictly binary.

---

## 4. Resource Safeguards and Execution Boundaries

```
[Available RAM Safety Limit]      >= 700 MB  (Abort if < 700 MB)
[Swap Growth Limit]               <= 500 MB  (Abort if swap drift > 500 MB)
[Execution Timeout Cutoff]        <= 30.0 min (1,800 s)
[Expected Compute Duration]       ~ 19.7 min (1,145 s train + 36 s val)
[Automated Retries]               ZERO (Fail fast on any resource failure)
```

---

## 5. Unresolved Prerequisites & Proposed Execution Command

### Unresolved Prerequisites Prior to Execution:
1. **Explicit User Authorization:** In accordance with track guidelines, full or bounded training requires explicit user approval.
2. **Implementation of Training Runner Script:** Implement `tools/training/train_binary_classifier.py` containing the verified data loader, 1,000-step training loop, metrics computation, and safety watchdog.

### Proposed Execution Command (Upon Explicit Authorization):
```bash
/home/aditya/rags/.venv-train/bin/python /home/aditya/rags/TrustRag-phase11/tools/training/train_binary_classifier.py     --train-file /home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/train.jsonl     --val-file /home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/validation.jsonl     --model-dir /home/aditya/rags/models/pretrained/deberta-v3-small     --max-train-samples 1000     --max-val-samples 200     --batch-size 1     --max-seq-len 128     --lr 2e-5     --weight-decay 0.01     --warmup-steps 100     --seed 42     --num-threads 4     --ram-abort-threshold-mb 700     --max-duration-seconds 1800     --output-dir /home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_step04_binary_training
```

---

## 6. Mandatory Explicit Statement

> **NO TRAINING WAS PERFORMED AND NO TRAINING AUTHORIZATION WAS GRANTED BY THIS PREFLIGHT AUDIT.**  
> Model weights and dataset records remain strictly unmodified. Execution is held pending explicit user authorization.
