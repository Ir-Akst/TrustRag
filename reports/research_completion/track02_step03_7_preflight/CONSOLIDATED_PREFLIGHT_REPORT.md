# TrustRAG — Track 2, Step 3.7: Consolidated NLI Pre-Flight Verification Report

> **Consolidated Master Report**  
> **Task:** Track 2, Step 3.7: Final Pre-Flight Verification & Bounded NLI Pilot Authorization  
> **Auditor Role:** Senior ML Infrastructure Engineer, Independent Experimental Auditor  
> **Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
> **Protected Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`)  
> **Pretrained Model Base:** `/home/aditya/rags/models/pretrained/deberta-v3-small`  
> **Preserved Binary Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000`  
> **Final Readiness Verdict:** **`READY_FOR_EXPLICIT_TRAINING_AUTHORIZATION`**

---



## Executive Summary

This independent pre-flight audit confirms that all training infrastructure, dataset splits, architectural configurations, resource watchdogs, safety gates, and evaluation protocols are in complete alignment for the bounded 1,000-optimization-step DeBERTa-v3-small NLI training pilot.

### Key Pre-Flight Verifications

1. **Repository & Baseline Immutability:**
   - Primary repo `phase-11` is clean at expected commit `aba5cc9`.
   - Protected Phase 10 baseline at `/home/aditya/rags/TrustRag` remains strictly untouched at commit `e65bcc8`.
   - Checksum audit confirms 100% byte-for-byte fidelity with Step 3.6 manifest.
2. **Dataset Isolation & Determinism:**
   - Training split: Exactly 10,815 records (6,707 ENTAILMENT, 1,420 CONTRADICTION, 2,688 NEUTRAL).
   - Validation split: Exactly 2,662 records (1,662 ENTAILMENT, 356 CONTRADICTION, 644 NEUTRAL).
   - Zero ID overlap, zero document/premise overlap, and zero test split exposure.
   - Deterministic 3-class balanced sampling verified: Exactly 334 ENTAILMENT, 333 CONTRADICTION, 333 NEUTRAL for the 1,000-step budget.
3. **Training Engine & Safety Guards:**
   - Runner `tools/training/train_nli_classifier.py` is fully verified across 21/21 unit tests.
   - Hardware watchdogs active: Abort on RAM < 700 MB, swap growth > 500 MB, or timeout > 1,800s.
   - Hard execution gate: Training cannot start without explicit user authorization flag (`--authorize-nli-training`).
4. **Evaluation Protocol:**
   - Validation is scheduled on the **original imbalanced validation split** (2,662 records), enabling accurate measurement against natural RAGTruth distribution and baseline predictors.
5. **Resource Headroom:**
   - Available Host RAM: **5.3 GiB** (+2.85 GiB buffer over estimated peak RSS of 2.45 GB). Free Swap: **3.9 GiB**.

---

## Decision & Next Action

**Final Decision: `READY_FOR_EXPLICIT_TRAINING_AUTHORIZATION`**

Unresolved Issues: **0**  
Risk Level: **Low** (All safety watchdogs and path guards active)

**STOP:** Execution is halted. Training will only proceed upon receipt of your explicit authorization command for Track 2 Step 3.8.


---



## 1. Repository State Verification

| Repository Target | Path | Active Branch | HEAD Commit | Audit Status |
| :--- | :--- | :---: | :---: | :---: |
| **Primary Project** | `/home/aditya/rags/TrustRag-phase11` | `phase-11` | `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61` | **MATCH_EXPECTED** |
| **Protected Baseline** | `/home/aditya/rags/TrustRag` | `phase-10` | `e65bcc80aac634900d1f8e343880fddf66cec168` | **STRICTLY_UNTOUCHED** |

---

## 2. Checkpoint Hash Cross-Verification (vs Step 3.6 Audit Manifest)

### Pretrained Snapshot (`microsoft/deberta-v3-small`)
- Location: `/home/aditya/rags/models/pretrained/deberta-v3-small`
- `config.json` SHA-256: `b0bb1caf90a50aa67d1085130508dfbf8646ac5a11928305e280b07a36e100ae` (**VERIFIED**)
- `pytorch_model.bin` SHA-256: `d4b0ebcc7799a2c2dde1a39199cb0ed709f2c6b63a48b8c05133b77955f271a9` (**VERIFIED**)
- `tokenizer_config.json` SHA-256: `3f3978e0c036f2c2588cac34a6047cbb0af0b0dc1814254e291028529805496d` (**VERIFIED**)
- `spm.model` SHA-256: `c679fbf93643d19aab7ee10c0b99e460bdbc02fedf34b92b05af343b4af586fd` (**VERIFIED**)

### Accepted Binary Classifier Checkpoint (`deberta-v3-small-binary-pilot1000`)
- Location: `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000`
- `model.safetensors` SHA-256: `472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b` (**IMMUTABLE_PRESERVED**)
- `config.json` SHA-256: `7cee3abbc6b9a3971c682867db8d16bb79eeaee218d544463bcc2433d82ff16d` (**IMMUTABLE_PRESERVED**)
- `tokenizer.json` SHA-256: `d87197028bcdd4a6c68dc03bd9b04e0956b0998daf7351345de21278a1c9249a` (**IMMUTABLE_PRESERVED**)

### Protected Path Overwrite Guard Audit
The runner `tools/training/train_nli_classifier.py` actively checks target output directories against:
1. `/home/aditya/rags/models/pretrained/deberta-v3-small`
2. `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000`
3. `/home/aditya/rags/TrustRag`
Any save operation targeting these paths raises a fatal `SecurityViolationError`.


---



## 1. Census Revalidation

Independent re-inspection of `data/processed/sft_v2/nli/`:

| Split | Records | ENTAILMENT | CONTRADICTION | NEUTRAL | Empty / Malformed | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Train** | 10,815 | 6,707 (62.0%) | 1,420 (13.1%) | 2,688 (24.9%) | 0 | **VERIFIED** |
| **Validation** | 2,662 | 1,662 (62.4%) | 356 (13.4%) | 644 (24.2%) | 0 | **VERIFIED** |
| **Total** | 13,477 | 8,369 (62.1%) | 1,776 (13.2%) | 3,332 (24.7%) | 0 | **VERIFIED** |

---

## 2. Partition Isolation & Leakage Checks

- **Example ID Leakage:** `len(train_ids ∩ val_ids) == 0` (**0 overlapping IDs**).
- **Document / Premise Leakage:** `len(train_doc_hashes ∩ val_doc_hashes) == 0` (**0 overlapping documents**).
- **Test Set Quarantine:** Canonical test files (`data/processed/halueval/test.jsonl` and `data/processed/ragtruth/test.jsonl`) remain completely unvisited and unreferenced.

---

## 3. Pilot Sampler Determinism

Evaluating `load_nli_dataset(..., max_samples=1000, strategy="stratified_class_balanced")`:
- **Total Selected Samples:** Exactly **1,000 records**.
- **Class Composition:**
  * `ENTAILMENT`: **334 records**
  * `CONTRADICTION`: **333 records**
  * `NEUTRAL`: **333 records**
- **Determinism:** Two independent execution passes generated identical SHA-256 sequence order hashes.


---



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


---



## 1. Validation Dataset Policy

In accordance with strict auditor standards:
- **Validation Dataset:** The **ORIGINAL IMBALANCED VALIDATION SPLIT** (`data/processed/sft_v2/nli/validation.jsonl`, N=2,662) will be used for both Step 0 baseline evaluation and Step 1,000 final post-training evaluation.
- **Non-Distortion:** The balanced training sampler is strictly forbidden from being applied to the validation set.

---

## 2. Mandatory Metric Suite

1. **Overall Performance:**
   - Classification Accuracy
   - Balanced Accuracy (Macro Average of Class Recalls)
   - Macro F1 Score
   - Weighted F1 Score
   - Cross-Entropy Validation Loss
2. **Per-Class Metrics (ENTAILMENT, CONTRADICTION, NEUTRAL):**
   - Precision
   - Recall
   - F1 Score
   - Support
3. **Confusion Analysis:**
   - Complete 3×3 Confusion Matrix `cm[true_idx][pred_idx]`
   - **False Entailment Analysis:** True CONTRADICTION or NEUTRAL incorrectly classified as ENTAILMENT (Type I acceptance of ungrounded text).
   - **False Contradiction Analysis:** True ENTAILMENT or NEUTRAL incorrectly classified as CONTRADICTION (Type I false alarm).
   - **Neutral-vs-Contradiction Confusion:** Mutual confusion between unsupported additions and direct factual conflicts.
4. **Calibration & Reliability:**
   - Multi-class Brier Score: $\frac{1}{N} \sum_{i=1}^N \sum_{c=1}^3 (p_{ic} - y_{ic})^2$
   - Expected Calibration Error (ECE, 10 equal bins)

---

## 3. Comparison Baselines (Imbalanced Validation N=2,662)

| Baseline Model | Accuracy | Balanced Acc | Macro F1 | Weighted F1 | Note |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Majority Class (Always Entailment)** | **62.43%** | 33.33% | 0.2562 | 0.4800 | Predicts label 0 for all instances |
| **Uniform Random Guessing (1/3)** | 33.33% | 33.33% | 0.3333 | 0.3333 | Equal chance across classes |
| **Stratified Class Prior Guessing** | 46.62% | 33.33% | 0.3333 | 0.4662 | Samples from validation prior |


---



## 1. Host Resource Telemetry

- **Available Physical RAM:** **5.3 GiB** (Total: 15 GiB)
- **Free Swap Space:** **3.9 GiB** (Total: 5.9 GiB)
- **Available Disk Space:** **45 GiB** on `/home/aditya/rags`
- **CPU Concurrency:** 16 execution threads available.

---

## 2. Watchdog Thresholds & Safety Mechanisms

| Watchdog Condition | Safety Threshold | Trigger Action | Test Suite Status |
| :--- | :---: | :--- | :---: |
| **Minimum Available RAM** | **< 700.0 MB** | Immediate `ResourceAbortError` abort | **TESTED & PASS** |
| **Maximum Swap Growth** | **> 500.0 MB** | Immediate `ResourceAbortError` abort | **TESTED & PASS** |
| **Minimum Free Swap** | **< 1,000.0 MB** | Immediate `ResourceAbortError` abort | **TESTED & PASS** |
| **Wall-Clock Timeout** | **> 1,800.0 s (30 min)** | Immediate `TimeoutAbortError` abort | **TESTED & PASS** |

---

## 3. Resource Projection for 1,000-Step Pilot

- **Estimated Peak RSS:** **~2,450 MB** (~2.45 GB).
- **Physical RAM Buffer:** **+2.85 GiB** headroom above peak RSS.
- **Estimated Runtime:** **~21 - 25 minutes** (based on measured ~1.2s/step in Step 3.4.2).
- **Disk Footprint for Checkpoint:** ~570 MB (safely within 45 GiB free disk).


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

