# TrustRAG Track 2 — Step 3.16: Consolidated Remediated NLI Training Report

**Role:** Senior ML Infrastructure Engineer and Reproducibility Auditor  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Execution Timestamp:** 2026-11-14T16:32:14Z  

---

## ══════════════════════════════════════════════════════════════
## FINAL VERDICT
## ══════════════════════════════════════════════════════════════

> # **`TRAINING_COMPLETED_AWAITING_INDEPENDENT_AUDIT`**

Exactly one bounded NLI pilot training run (1,000 optimizer steps) was executed under authorized configuration. Training completed cleanly without watchdogs triggering. The resulting checkpoint is serialized atomically and verified.

---

## 1. Executive Metrics Overview

| Metric | Step 0 Baseline | Step 1,000 Final | Delta |
|---|---|---|---|
| **Accuracy** | 24.19% | **38.05%** | **+13.86%** (+57.3% rel) |
| **Balanced Accuracy** | 33.33% | **35.44%** | **+2.11%** (+6.3% rel) |
| **Macro F1** | 0.1299 | **0.2975** | **+0.1676** (+129.1% rel) |
| **Weighted F1** | 0.0943 | **0.3834** | **+0.2891** (+306.7% rel) |
| **Validation Loss** | 1.0883 | 1.1371 | +0.0488 |
| **Brier Score** | 0.6629 | **0.6614** | Improved |
| **ECE (10-bin)** | 0.1518 | **0.1304** | Improved |

---

## 2. Confusion Matrix

```
                  Predicted ENT   Predicted CON   Predicted NEU     Total
True ENTAILMENT             557             143             962      1662
True CONTRADICTION           85              16             255       356
True NEUTRAL                151              53             440       644
Total Predicted             793             212            1657      2662
```

---

## 3. Checkpoint Files

Directory: `/home/aditya/rags/models/trained/deberta-v3-small-nli-remediated`
- `config.json`: `38370396a4e2988a14226b6b8875766e660ab8bbd1374b9e23a6e0c7a05ef385`
- `model.safetensors`: `bb4c26bab4a147c2ad6bdae7ec8a1ecc56841ea56fc89922fd377fb5d70fe113`
- `tokenizer_config.json`: `1121ad33ecd98a97b2db184ce896546feb7555bebddf33a2dfe1b1a1077dc847`
- `tokenizer.json`: `e9ddd853a4a31023721c993458663f2019e3154a05dacf0d2b3c217e53d9bdc8`
- `training_meta.json`: `d673d317525d566c29cbccc1f67fc3a47fbbb767c7a812f6d4509afc6969243c`

---

## 4. Protected Asset Post-Execution Verification

All protected baseline commits and checkpoints confirmed unchanged:
- Binary Checkpoint: `472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b` ✅
- Failed NLI Checkpoint: `500832fa1b9b7c67c2c08d9e1f4d4c76d235d15fa9960d76e1e6e81c220a2f8a` ✅
- Phase 11 HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61` ✅
- Phase 10 HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168` ✅

---

## 5. Mandatory Stop Condition

**STOPPED.** Step 3.16 execution and reporting are complete. Standing by for Step 3.17 independent audit.

---
*Step 3.16 Execution Auditor — 2026-11-14T16:32:14Z*
