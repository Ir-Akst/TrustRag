# TrustRAG Track 2 — Step 3.15: Consolidated Independent NLI Training Preflight Report

**Role:** Independent Senior ML Training Auditor, NLP Research Engineer & Adversarial Experimental Reviewer  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch/HEAD:** `phase-11` @ `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`  
**Audit timestamp:** 2026-11-14T14:15:20Z  
**Previous step verdict:** Step 3.14 → `CONDITIONALLY_READY_WITH_LIMITATIONS`

---

## ══════════════════════════════════════════════════════════════
## FINAL PREFLIGHT VERDICT
## ══════════════════════════════════════════════════════════════

> # `READY_FOR_EXPLICIT_TRAINING_AUTHORIZATION`

**with one mandatory configuration fix before execution (Limitation L1: extend watchdog timeout).**

This verdict does **NOT** authorize training. Training remains blocked by the
`config.authorized=False` default fence until the user explicitly grants authorization
for Step 3.16.

---

## 1. Repository & Protected Asset Integrity

| Asset | Expected | Actual | Status |
|---|---|---|---|
| `TrustRag-phase11` branch | `phase-11` | `phase-11` | ✅ |
| `TrustRag-phase11` HEAD | `aba5cc9d...` | `aba5cc9d...` | ✅ |
| `TrustRag` (Phase 10) HEAD | `e65bcc80...` | `e65bcc80...` | ✅ |
| Binary pilot SHA256 | `472ea687...` | `472ea687...` | ✅ UNCHANGED |
| Failed NLI pilot SHA256 | `500832fa...` | `500832fa...` | ✅ UNCHANGED |
| Pretrained model checksums | ALL OK | ALL OK | ✅ |

---

## 2. Supervision Policy

- **Example-level labels** (`nli_label` from JSONL) used exclusively. ✅
- **Chunk-level label training**: PROHIBITED and not implemented in training loop. ✅
- Multi-chunk used ONLY at inference time with `CONTRADICTION_PRIORITY` aggregation. ✅
- Label mapping: ENTAILMENT=0, CONTRADICTION=1, NEUTRAL=2. ✅

---

## 3. Dataset Statistics (Independently Verified)

| Split | ENT | CON | NEU | Total | Unique Docs |
|---|---|---|---|---|---|
| Train | 6,707 | 1,420 | 2,688 | 10,815 | 2,012 |
| Val | 1,662 | 356 | 644 | 2,662 | 503 |

**Split isolation:** 0 example_id overlap. 0 premise hash overlap. ✅

---

## 4. Serialization Configuration

| Parameter | Required | Configured | Status |
|---|---|---|---|
| `max_seq_len` | 384 | 384 | ✅ |
| `min_premise_tokens` | 64 | 64 | ✅ |
| Strategy | evidence_preserving | evidence_preserving | ✅ |
| Max hypothesis tokens | 317 | 317 (derived) | ✅ |
| Evidence retention | >99% | 99.06% | ✅ |

---

## 5. Sampling & Optimization

| Parameter | Configured | Status |
|---|---|---|
| Sampling strategy | stratified_class_balanced | ✅ |
| Seed | 42 (deterministic) | ✅ |
| Shuffle | True (post-selection) | ✅ |
| ENT/CON/NEU quota | 334/333/333 | ✅ |
| Starvation guard | max_absence=25 | ✅ |
| Optimizer | AdamW | ✅ |
| Learning rate | 2e-5 | ✅ |
| Weight decay | 0.01 | ✅ |
| Warmup steps | 100 | ✅ |
| LR schedule | Linear decay to 0 | ✅ |
| Gradient clipping | max_norm=1.0 | ✅ |
| Precision | FP32 | ✅ |

---

## 6. Safety Guards

| Guard | Implementation | Tested | Status |
|---|---|---|---|
| Authorization fence (`authorized=False`) | ✅ | ✅ PASS | ✅ |
| Protected path overwrite guard | ✅ | ✅ PASS | ✅ |
| Test-set access prohibition | ✅ | ✅ PASS | ✅ |
| RAM watchdog (700 MB abort) | ✅ | ✅ PASS | ✅ |
| Swap growth watchdog (1,000 MB limit) | ✅ | ✅ PASS | ✅ |
| Wall-clock watchdog (3,600 s) | ✅ | ✅ PASS | ⚠️ TOO SHORT |
| Offline mode (HF_HUB_OFFLINE=1) | ✅ | — | ✅ |
| Atomic checkpoint serialization | ✅ | — | ✅ |

---

## 7. Test Suite Results

| Suite | Total | Passed | Skipped | Failed |
|---|---|---|---|---|
| `test_track02_step03_6_nli_training_runner.py` | 36 | 35 | 1 | 0 |
| `test_track02_step03_14_supervision_readiness.py` | 11 | 11 | 0 | 0 |
| **Combined** | **47** | **46** | **1** | **0** |

Skipped test: `test_prepare_nli_model_architecture` (requires model weight loading).
All safety-critical tests pass.

---

## 8. Resource Feasibility

| Resource | Available | Estimated Need | Margin | Status |
|---|---|---|---|---|
| RAM | 5,796 MB available | ~2,600 MB RSS | ~3,196 MB | ✅ |
| Free swap | 2,631 MB | <500 MB growth | 1,631 MB above guard | ✅ |
| Wall clock | 3,600 s limit | ~15,060 s (~251 min) | ⚠️ INSUFFICIENT | **FIX REQUIRED** |
| CPU threads | 12 logical | 16 configured | Oversubscribed | ⚠️ Performance only |

---

## 9. Remaining Limitations

| ID | Issue | Severity | Action Required |
|---|---|---|---|
| **L1** | Watchdog timeout 3,600 s << estimated 15,060 s total run time | HIGH | **Increase `max_duration_seconds` to 21,600 before Step 3.16** |
| L2 | `num_threads=16` oversubscribes 12 logical CPUs | LOW | Optional: reduce to 10–12 |
| L3 | 1,000 steps is a pilot, not full convergence | SCIENTIFIC | Accepted by design |
| L4 | 201 train / 54 val oversized hypotheses capped at 317 tokens | DESIGN | Accepted |
| L6 | RAM guard may trigger under concurrent system load | MEDIUM | Monitor before launch |

---

## 10. Recommended Training Invocation (Step 3.16, After Authorization)

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
  --swap-growth-abort-mb 1000
```

> ⚠️ **L1 fix required:** Add `--max-duration-seconds 21600` to the invocation above,
> OR accept that the watchdog will abort the run at 60 minutes (before Step 1,000 eval).

---

## 11. Comparison with Previous Step Verdicts

| Step | Verdict |
|---|---|
| Step 3.11 (Independent Audit) | `INDEPENDENTLY_VERIFIED_WITH_LIMITATIONS` |
| Step 3.12 (Remediation) | `EVIDENCE_RETENTION_REMEDIATED` |
| Step 3.13 (Independent Audit) | `INDEPENDENTLY_VERIFIED_WITH_LIMITATIONS` |
| Step 3.14 (Supervision Readiness) | `CONDITIONALLY_READY_WITH_LIMITATIONS` |
| **Step 3.15 (This Preflight)** | **`READY_FOR_EXPLICIT_TRAINING_AUTHORIZATION`** |

---

## 12. Immutability Post-Audit Confirmation

All protected assets verified unchanged at audit conclusion:
- Binary pilot `472ea687...` ✅
- Failed NLI pilot `500832fa...` ✅
- Phase 10 HEAD `e65bcc80...` ✅
- Pretrained model checksums ✅

---
*Step 3.15 Independent Preflight Audit — 2026-11-14T14:15:20Z*  
*This audit is read-only. No model training, backward passes, or checkpoint modifications were performed.*
