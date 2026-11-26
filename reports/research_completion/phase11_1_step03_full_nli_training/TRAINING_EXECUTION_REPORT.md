# TrustRAG — Phase 11.1, Step 3: Training Execution Report

**Date:** 2026-11-15  
**Role:** Senior ML Infrastructure Engineer and Experimental Execution Auditor  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11`  
**Commit HEAD:** `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`  
**Execution Campaign:** Phase 11.1 Full NLI 3-Epoch Training Campaign  
**Target Output Directory:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  
**Campaign Status:** INTERRUPTED BY EXTERNAL HARDWARE REBOOT  
**Execution Outcome:** Incomplete (50 of 8,112 optimizer steps executed; 0 complete epochs)

---

## 1. Execution Campaign Configuration

The authorized training campaign was launched with pre-registered parameters:
- **Architecture:** DeBERTa-v3-small (141,897,219 parameters in FP32)
- **Pretrained Source:** `/home/aditya/rags/models/pretrained/deberta-v3-small`
- **Training Corpus:** `data/processed/sft_v2/nli/train.jsonl` (10,815 natural distribution examples)
- **Validation Corpus:** `data/processed/sft_v2/nli/validation.jsonl` (2,662 active examples)
- **Target Epochs:** 3
- **Micro-Batch Size:** 1
- **Gradient Accumulation Steps:** 4 (Effective batch size = 4)
- **Total Optimizer Steps Planned:** 8,112 steps (2,704 steps/epoch)
- **Total Forward+Backward Passes Planned:** 32,445 passes
- **Optimizer:** AdamW ($\beta_1=0.9, \beta_2=0.999, \epsilon=10^{-8}$)
- **Learning Rate:** $2 \times 10^{-5}$ with linear warmup over 100 steps and linear decay
- **Weight Decay:** 0.01
- **Loss Function:** Class-Weighted Cross-Entropy `[1.0, 3.5, 1.5]` (ENTAILMENT=0, CONTRADICTION=1, NEUTRAL=2)
- **Sequence Truncation / Padding:** Evidence-preserving tokenization with dynamic padding up to 384 tokens
- **CPU Concurrency:** 10 intra-op threads, 1 inter-op thread
- **Checkpoint Schedule:** Periodic atomic checkpointing every 500 optimizer steps

---

## 2. Execution Chronology & Telemetry Milestones

### 2.1 Initialization & Preflight Telemetry
- **Start Timestamp:** 2026-11-15 17:22:00 IST
- **Preflight Host Telemetry:**
  - Available Host RAM: 6,410.2 MB (Safe floor: 700.0 MB)
  - Process RSS: 221.0 MB (Ceiling: 4,500.0 MB)
  - Free Swap: 5,183.4 MB (Safe floor: 1,000.0 MB)
  - Used Swap: 816.6 MB
- **Dataset Ingestion:** 10,815 training records and 2,662 validation records ingested and split isolation confirmed in 0.15s.
- **Model Initialization:** DeBERTa-v3-small head initialized in FP32 offline mode.

### 2.2 Step 0 Pre-Training Baseline Validation
Prior to entering the training loop, the initialized model underwent Step 0 baseline evaluation across all 2,662 validation examples:
- **Evaluation Throughput:** 2,662 inferences completed in ~650 seconds (~4.1 inferences/sec).
- **Validation Loss:** 1.0883
- **Validation Accuracy:** 0.2419 (24.19%)
- **Balanced Accuracy:** 0.3333 (33.33%)
- **Macro F1:** 0.1299
- **Contradiction Recall:** 0.0000

### 2.3 Training Loop Entry (Epoch 1)
- **Post-Validation Baseline Telemetry:**
  - Available RAM: 5,568.6 MB
  - Process RSS: 1,212.1 MB
  - Swap Used: 817.8 MB
  - Free Swap: 5,182.2 MB
- **Training Progression to Step 50:**
  - Micro-batches processed: 200 samples
  - Optimizer update steps: 50 steps
  - Step 50 Loss: 0.9976
  - Rolling Loss (last 50 steps): 1.0886
  - Learning Rate: $9.80 \times 10^{-6}$ (progressing through linear warmup)
  - Process RSS: 2,711.8 MB (well below 4,500 MB ceiling)
  - Available RAM: 4,103.4 MB (well above 700 MB floor)
  - Elapsed Execution Time: 1,096.8 seconds (~18.28 minutes)
  - Watchdog Telemetry: 0 threshold violations, 0 consecutive warnings.

---

## 3. Hardware Interruption & Termination Event

At approximately 17:44 IST (12:14 UTC), an external unhandled host shutdown/reboot occurred:
- **Uptime Audit at Session Restoration:** System reported `17:48:32 up 4 min`.
- **Nature of Interruption:** Complete physical machine restart.
- **Watchdog State Prior to Interruption:** The internal WatchdogMonitor did **not** trigger an abort. Memory (4,103 MB available) and process RSS (2,711 MB) were operating safely within all threshold boundaries.
- **Last Logged Step:** Step 50 / 8,112 in Epoch 1.

---

## 4. Execution Metrics Summary

| Metric | Target / Planned | Achieved Before Interruption | Completion Rate |
| :--- | :---: | :---: | :---: |
| **Total Epochs** | 3 | 0 complete (stopped at Epoch 1) | 0.0% |
| **Training Samples Consumed** | 32,445 | 200 samples | 0.62% |
| **Optimizer Steps** | 8,112 | 50 steps | 0.62% |
| **Step 0 Baseline Evaluation** | 1 pass (2,662 samples) | 1 pass completed | 100.0% |
| **Interim Epoch Validations** | 3 passes | 0 passes | 0.0% |
| **Elapsed Wall-Clock Time** | ~43,554s (~12.1h) | 1,096.8s (~18.3 min) | 2.52% |

Raw execution log preserved in: [training_execution.log](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/phase11_1_step03_full_nli_training/training_execution.log)

