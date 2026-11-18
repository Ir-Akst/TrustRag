# TrustRAG — Track 2, Step 3.4.3: Independent Binary Training Acceptance Audit Consolidated Report

**Document ID:** `TRUSTRAG-TRACK02-STEP03-4-3-CONSOLIDATED`  
**Date:** 2026-11-14  
**Auditor Role:** Independent ML Infrastructure and Experimental Auditor  
**Audit Scope:** Read-Only Independent Verification of Track 2 Step 3.4.2 Training Execution  
**Overall Verdict:** `INDEPENDENTLY_VERIFIED`  
**Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, Baseline HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Protected Baseline:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, **UNTOUCHED**)  
**Trained Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000`  

---

## 1. Executive Summary & Verdict

### Final Verdict: `INDEPENDENTLY_VERIFIED`

Following comprehensive adversarial auditing, offline checkpoint loading, inference smoke testing, and bit-level metric recomputation across the 200 validation samples, the Step 3.4.2 authorized binary classification training run is **`INDEPENDENTLY_VERIFIED`**.

The empirical evidence confirms that the training run was **completely authentic, mathematically sound, leak-free, and safe**:
1. **Checkpoint Authenticity:** The trained model loaded offline with all **141,896,450 parameters** intact in `torch.float32` runtime precision. The binary classification head ($2 \times 768$ weight, $2$ bias) produced finite logits on test-free inference inputs. Checkpoint SHA-256 hashes match reported values bit-for-bit.
2. **Exact Metric Reproduction:** Recomputing metrics on the 200-sample stratified validation set using the trained weights matched the reported Step 3.4.2 evaluation with zero discrepancy:
   - **Validation Accuracy:** `0.7600` (76.00%)
   - **Balanced Accuracy:** `0.7600` (76.00%)
   - **Macro F1 Score:** `0.7500`
   - **Validation Loss:** `0.5535`
   - **Confusion Matrix:** Exactly reproduced ($TN=96, FP=4, FN=44, TP=56$).
   - **Precision on Hallucinations:** Exactly `93.33%` (56/60).
3. **Dataset & Leakage Audit:** Verified the exact 1,000 training records (500 HaluEval, 500 RAGTruth; 250 FACTUAL, 250 HALLUCINATED per source) and 200 validation records (100 HaluEval, 100 RAGTruth; 50 FACTUAL, 50 HALLUCINATED per source). ID overlap between train and validation: **0**. Zero test data was accessed.
4. **Resource Safety Compliance:** Peak RSS was **2,444.55 MB**, host available RAM never dropped below **4,339 MB** (safety margin $> 3.6\text{ GB}$ above the 700 MB limit), swap drift was minimal ($+11.91\text{ MB}$), and wall-clock execution was **1,293.4 seconds** (~21.56 minutes against the 30-minute hard cutoff).
5. **Strict Boundary Conformance:** Zero training or optimizer steps were performed during this audit. Phase 10 baseline remains completely untouched.

---

## 2. Independent Metric Recomputation Matrix

| Metric | Reported Value (Step 3.4.2) | Recomputed Value (Audit) | Status |
|--------|:---------------------------:|:------------------------:|:------:|
| **Validation Loss** | `0.5535` | `0.5535` | **EXACT MATCH** |
| **Accuracy** | `76.00%` (0.7600) | `76.00%` (0.7600) | **EXACT MATCH** |
| **Balanced Accuracy** | `76.00%` (0.7600) | `76.00%` (0.7600) | **EXACT MATCH** |
| **Macro F1 Score** | `0.7500` | `0.7500` | **EXACT MATCH** |
| **Class 0 (Factual) Precision** | `68.57%` | `68.57%` | **EXACT MATCH** |
| **Class 0 (Factual) Recall** | `96.00%` | `96.00%` | **EXACT MATCH** |
| **Class 0 (Factual) F1** | `0.8000` | `0.8000` | **EXACT MATCH** |
| **Class 1 (Hallu) Precision** | `93.33%` | `93.33%` | **EXACT MATCH** |
| **Class 1 (Hallu) Recall** | `56.00%` | `56.00%` | **EXACT MATCH** |
| **Class 1 (Hallu) F1** | `0.7000` | `0.7000` | **EXACT MATCH** |

---

## 3. Confusion Matrix Reproduction

```
                       Actual Class
                    FACTUAL    HALLUCINATED
Predicted FACTUAL      96           44         (Total Predicted Factual = 140)
Predicted HALLU         4           56         (Total Predicted Hallu   = 60)
                     ------       ------
Actual Total          100          100         (Total = 200)
```

- True Negatives ($TN$): **96** (96% factual specificity).
- True Positives ($TP$): **56** (56% hallucination recall).
- False Positives ($FP$): **4** (4% false positive rate).
- False Negatives ($FN$): **44**.

---

## 4. Checkpoint Hashes & Architecture Verification

Stored in: `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000`

- `config.json`: `7cee3abbc6b9a3971c682867db8d16bb79eeaee218d544463bcc2433d82ff16d`
- `model.safetensors`: `472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b`
- `tokenizer_config.json`: `1121ad33ecd98a97b2db184ce896546feb7555bebddf33a2dfe1b1a1077dc847`
- `tokenizer.json`: `d87197028bcdd4a6c68dc03bd9b04e0956b0998daf7351345de21278a1c9249a`
- `training_meta.json`: `d1e91f1c47eb3858874173753a0cdd093e007f2be52b5bf4e2247f10fbd8d8c3`

Architecture verified: `DebertaV2ForSequenceClassification` with 141,896,450 parameters, 2-class head (`classifier.weight`: `[2, 768]`), loaded in `torch.float32`.

---

## 5. Mandatory Safety & Scope Statement

> **NO TRAINING WAS PERFORMED DURING THIS AUDIT.**  
> All investigations were strictly read-only. Phase 10 baseline, pretrained base model directory, and all processed dataset files remain completely untouched.
