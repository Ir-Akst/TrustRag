# TrustRAG Track 2 — Step 3.15.1: Consolidated Watchdog & Evaluation Runtime Remediation Audit

**Role:** Independent ML Infrastructure Auditor and Adversarial Training Safety Reviewer  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch/HEAD:** `phase-11` @ `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`  
**Audit timestamp:** 2026-11-14T14:35:44Z  
**Resolves:** Step 3.15 Limitation L1

---

## ══════════════════════════════════════════════════════════════
## FINAL VERDICT
## ══════════════════════════════════════════════════════════════

> # `CONDITIONALLY_READY_WITH_LIMITATIONS`

**L1 is resolved by a CLI parameter change. No source modification required.**

After applying `--max-duration-seconds 36000`, zero blocking limitations remain.

**Training remains blocked.** This audit does NOT authorize training.

---

## 1. L1 Root Cause (Deepened Analysis)

The Step 3.15 audit correctly identified that `max_duration_seconds=3600` is too short.
This audit establishes the precise failure mode:

**The `watchdog.check()` is never called inside `evaluate()`.** The timer starts before
model loading (L648). The first `watchdog.check()` fires at training **step 1** (L762),
**after** the entire pre-training baseline evaluation completes.

```
Elapsed at first check() call:
  model load (~45–90 s) + data load (~2 s) + pre-train eval (~5,324 s) = ~5,371 s
  >> max_duration_seconds=3600  → TimeoutAbortError at STEP 1
```

**Effect:** Zero optimizer updates occur. No checkpoint is written. The run aborts cleanly.

---

## 2. Recommended Fix

| Parameter | Current | Recommended | Method |
|---|---|---|---|
| `max_duration_seconds` | 3,600 s | **36,000 s** | `--max-duration-seconds 36000` |

**Derivation:** Conservative total estimate 22,154 s × 1.5 safety factor = 33,231 s
→ round up to 10 h → 36,000 s.

| Previous suggestion (Step 3.15) | Refined recommendation (Step 3.15.1) |
|---|---|
| `--max-duration-seconds 21600` (6 h) | `--max-duration-seconds 36000` (10 h) |
| Insufficient by ~554 s under conservative timing | 13,846 s (3.8 h) buffer even at 4 s/sample |

---

## 3. Protected Asset Verification (Post-Audit)

| Asset | Status |
|---|---|
| `TrustRag-phase11` @ `aba5cc9d...` | ✅ VERIFIED |
| `TrustRag` Phase 10 @ `e65bcc80...` | ✅ VERIFIED |
| Binary pilot `472ea687...` | ✅ UNCHANGED |
| Failed NLI pilot `500832fa...` | ✅ UNCHANGED |
| Pretrained model checksums | ✅ ALL OK |

---

## 4. Watchdog Properties Summary

| Property | Status |
|---|---|
| Global timeout (3,600 s) | ⚠️ TOO SHORT → Fix: 36,000 s |
| Timer measures entire pipeline | ✅ By design |
| RAM guard (700 MB, 6,114 MB margin) | ✅ Adequate |
| Swap growth guard (1,000 MB limit) | ✅ Adequate |
| Swap minimum guard (1,000 MB, 1,828 MB margin) | ✅ Adequate |
| Atomic checkpoint on exception | ✅ Safe |
| No checkpoint on step-1 abort | ✅ Verified by code path |
| eval() timeout gap | ⚠️ Non-blocking known gap |

---

## 5. Test Results

| Suite | Passed | Skipped | Failed |
|---|---|---|---|
| `test_track02_step03_6_nli_training_runner.py` | 35 | 1 | 0 |
| `test_track02_step03_14_supervision_readiness.py` | 11 | 0 | 0 |
| **Combined** | **46** | **1** | **0** |

Targeted safety tests (watchdog × 4, checkpoint × 2): **6/6 PASS**.

---

## 6. Evaluation Protocol Verified

Pre-training and post-training evaluations are identical in all respects:
- Same `val_records` object (2,662 samples, imbalanced distribution)
- Same `encode_item()` → `evidence_preserving_tokenize()` with `max_seq_len=384`
- Same `NLI_LABEL_MAP` (ENT=0, CON=1, NEU=2)
- Same `compute_nli_metrics()` with Brier score and ECE
- Both use `model.eval()` + `torch.no_grad()`

Failed Step 3.8 checkpoint: used only as frozen reference — not loaded during Step 3.16.

---

## 7. Authorized Step 3.16 Invocation (Pending Explicit Authorization)

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /home/aditya/rags/.venv-train/bin/python \
  /home/aditya/rags/TrustRag-phase11/tools/training/train_nli_classifier.py \
  --authorize-nli-training \
  --output-dir /home/aditya/rags/models/trained/deberta-v3-small-nli-remediated \
  --report-dir /home/aditya/rags/TrustRag-phase11/reports/training_runs/step03_16 \
  --max-seq-len 384 \
  --max-train-samples 1000 \
  --max-val-samples 2662 \
  --learning-rate 2e-5 \
  --warmup-steps 100 \
  --seed 42 \
  --swap-growth-abort-mb 1000 \
  --max-duration-seconds 36000
```

> ⚠️ This invocation is provided for reference only.  
> **Training requires SEPARATE EXPLICIT AUTHORIZATION from the user.**  
> The `--authorize-nli-training` flag must be passed only after explicit authorization  
> for Step 3.16 is granted. This audit does not constitute that authorization.

---

## 8. Remaining Limitations (All Non-Blocking)

| ID | Issue | Severity |
|---|---|---|
| L2 | Thread oversubscription (16 vs 12 CPUs) | LOW |
| L3 | 1,000 steps = pilot, not convergence | SCIENTIFIC |
| L4 | 201 oversized hypotheses capped | DESIGN |
| L-NEW-A | eval() has no timeout guard | LOW |
| L-NEW-B | No mid-training checkpoint | LOW |
| L-NEW-C | Timing estimate uncertainty | LOW |

---
*Step 3.15.1 Runtime Audit — 2026-11-14T14:35:44Z*  
*READ-ONLY: No model training, backward passes, optimizer updates, or checkpoint modifications were performed.*
