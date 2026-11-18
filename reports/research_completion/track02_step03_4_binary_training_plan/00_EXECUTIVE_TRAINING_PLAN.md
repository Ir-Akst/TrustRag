# Track 2, Step 3.4: Binary Classification Training Plan & Preflight — Executive Report

**Document ID:** `TRUSTRAG-TRACK02-STEP03-4-EXEC`  
**Date:** 2026-11-14  
**Auditor Role:** Senior ML Infrastructure Engineer & Experimental Auditor  
**Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Protected Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, UNTOUCHED)  
**Target Architecture:** `microsoft/deberta-v3-small` (141.9M parameters, FP32)  
**Dataset Target:** `data/processed/sft_v2/binary/` (26,054 train records, 5,984 val records)  

---

## 1. Final Preflight Verdict: `READY_FOR_EXPLICIT_TRAINING_AUTHORIZATION`

The prerequisite audits for Track 2 (Step 3.2.1 model staging audit, Step 3.3 full-architecture CPU feasibility pilot, and Step 3.3.1 independent audit) have established that the host runtime, model architecture, autograd reverse-mode graph, and dataset inputs are fully verified and stable.

This document establishes the **formal engineering specification and safety boundaries** for a strictly bounded 1,000-example training experiment.

### Key Preflight Determinations:
1. **Prerequisites 100% Satisfied:** Pretrained model weights, offline SentencePiece tokenizer, remediated zero-leakage binary dataset, and isolated `.venv-train` environment are authentic, complete, and verified.
2. **Strictly Bounded Scope:** Training is restricted to a **1,000-example subset** (500 FACTUAL, 500 HALLUCINATED), batch size 1, sequence length 128 tokens, and 1 epoch (1,000 optimizer steps).
3. **Execution Budget:** At steady-state CPU throughput (1.145 seconds/step), training requires **~19.1 minutes**, with validation (200 examples) requiring **~35.5 seconds**, totaling **~19.7 minutes** against a **30-minute hard cutoff**.
4. **Safety & Abort Watchdog:** Automatic termination if available host RAM drops below **700 MB** or if swap grows by $> 500	ext{ MB}$.
5. **Zero Training Commenced:** No model parameters have been updated, no optimizer state has been allocated, and no forward/backward passes have been run in this step.

---

## 2. Proposed Experiment Specifications at a Glance

| Parameter | Specification | Purpose / Rationale |
|-----------|:-------------:|---------------------|
| **Objective** | Binary Hallucination Classification | Discriminates grounded factual responses from unsupported hallucinations. |
| **Model** | `DebertaV2ForSequenceClassification` | Full 141.9M parameter DeBERTa-v3-small architecture (6 layers, 12 heads, 768 hidden). |
| **Backbone Weights** | Pretrained MLM Checkpoint | Loaded offline from local staging (`pytorch_model.bin`). |
| **Classification Head** | Newly Initialized | 2-class linear projection head ($2 	imes 768$) initialized with Gaussian $\sigma=0.02$. |
| **Precision** | `torch.float32` (FP32) | CPU tensor operations require FP32 for numerically stable autograd backpropagation. |
| **Training Subset** | **1,000 examples** | Perfectly balanced: 500 FACTUAL (50%) and 500 HALLUCINATED (50%). |
| **Validation Subset** | **200 examples** | Perfectly balanced: 100 FACTUAL (50%) and 100 HALLUCINATED (50%). Zero document overlap. |
| **Batch Size** | **1** | Restricts peak process RSS to ~2.37 GB, guaranteeing $> 4.5	ext{ GB}$ physical RAM safety margin. |
| **Max Sequence Length**| **128 tokens** | Covers the empirical distribution of question + context + response pairs. |
| **Optimizer** | AdamW (`lr=2e-5`, `weight_decay=0.01`) | Standard transformer fine-tuning optimizer with weight decay regularization. |
| **Learning Rate Schedule** | Linear Warmup (100 steps) + Decay | Mitigates initial gradient shock to the newly initialized classification head. |
| **Concurrency** | **4 CPU Threads** (`torch.set_num_threads(4)`) | Maximizes throughput while preventing thread-context thrashing across CPU cores. |
| **Timeout Watchdog** | **30 minutes (1,800 s)** | Enforces strict termination to protect host against hanging or thermal stalling. |
| **RAM Abort Limit** | **700 MB Available RAM** | Immediate shutdown if physical memory drops below safe operating limits. |

---

## 3. Explicit Engineering Statement

> **THIS TASK IS PLANNING AND PREFLIGHT ONLY.**  
> **NO TRAINING WAS PERFORMED AND NO TRAINING AUTHORIZATION WAS GRANTED BY THIS AUDIT.**  
> The model weights remain completely unmodified in local staging. Training execution requires explicit user authorization.
