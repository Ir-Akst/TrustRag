# TrustRAG — Phase 11.1, Step 3: Epoch Validation Metrics Report

**Date:** 2026-11-15  
**Auditor:** Senior ML Infrastructure Engineer and Experimental Execution Auditor  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Validation Split:** `data/processed/sft_v2/nli/validation.jsonl` (2,662 active examples)  
**Reporting Status:** Step 0 Baseline Captured; Subsequent Epochs Incomplete Due to Reboot

---

## 1. Summary of Evaluation Schedule

The experimental protocol specified four formal evaluation passes over the full validation set of 2,662 samples:
1. **Step 0 Pre-Training Baseline:** Executed prior to first gradient update.
2. **Epoch 1 Evaluation:** Scheduled at Step 2,704 (Not reached due to reboot at Step 50).
3. **Epoch 2 Evaluation:** Scheduled at Step 5,408 (Not reached).
4. **Epoch 3 Final Evaluation:** Scheduled at Step 8,112 (Not reached).

---

## 2. Step 0 Pre-Training Baseline Metrics

Evaluated across all 2,662 validation examples using the offline initialized DeBERTa-v3-small model with classification head prior to any training updates:

| Metric | Measured Value | Standard Random Baseline | Prior-Matched Random |
| :--- | :---: | :---: | :---: |
| **Validation Loss** | **1.0883** | $\ln(3) \approx 1.0986$ | - |
| **Raw Accuracy** | **0.2419 (24.19%)** | 33.33% | 46.62% |
| **Balanced Accuracy** | **0.3333 (33.33%)** | 33.33% | 33.33% |
| **Macro F1 Score** | **0.1299** | 0.3333 | 0.3333 |
| **Contradiction Recall** | **0.0000 (0.00%)** | 33.33% | 15.60% |
| **Entailment Recall** | **1.0000 (100.0%)** | 33.33% | 62.43% |
| **Neutral Recall** | **0.0000 (0.00%)** | 33.33% | 21.97% |

### Analysis of Step 0 Baseline
- The randomly initialized 3-class classification head exhibited an initial Entailment bias ($y=0$), predicting Entailment across the entire validation split.
- Because the validation split contains 24.19% Entailment examples under this specific indexing, raw accuracy is exactly 24.19%, with balanced accuracy at 33.33% and zero recall for Contradiction and Neutral classes.
- This establishes the strict, empirical pre-training baseline against which future trained checkpoints must be judged.

---

## 3. Subsequent Epoch Validations

Due to the physical system restart at Step 50 of Epoch 1, validation passes for Epoch 1, Epoch 2, and Epoch 3 were not reached.

