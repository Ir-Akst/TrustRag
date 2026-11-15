# TrustRAG — Track 2, Step 3.6: Executive NLI Training Readiness Audit Report

- **Date:** 2026-11-14T06:08:20Z
- **Role:** Senior ML Infrastructure Engineer and Experimental Auditor
- **Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)
- **Protected Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, Strictly Untouched)
- **Pretrained Base:** `/home/aditya/rags/models/pretrained/deberta-v3-small` (FP32, 141.9M parameters)
- **Preserved Binary Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000` (Intact, Unchanged)
- **Objective:** Evidence-Grounded 3-Way Natural Language Inference (`ENTAILMENT=0`, `CONTRADICTION=1`, `NEUTRAL=2`)
- **NLI Dataset Path:** `data/processed/sft_v2/nli/` (10,815 train, 2,662 validation)
- **Final Readiness Verdict:** **`READY_FOR_EXPLICIT_TRAINING_AUTHORIZATION`**

---

## Executive Summary

Track 2 Step 3.6 completes the infrastructure preparation, dataset audit, runner implementation, and safety validation for Evidence-Grounded 3-Way Natural Language Inference (NLI) using DeBERTa-v3-small.

### Key Audit Findings

1. **Dataset Integrity & Provenance:**
   - **Training Set:** Exactly **10,815 records** (6,707 ENTAILMENT, 1,420 CONTRADICTION, 2,688 NEUTRAL).
   - **Validation Set:** Exactly **2,662 records** (1,662 ENTAILMENT, 356 CONTRADICTION, 644 NEUTRAL).
   - **Schema Compliance:** 100% compliant across mandatory fields (`example_id`, `source_dataset`, `source_id`, `split`, `premise`, `hypothesis`, `nli_label`, `conflict_types`, `span_count`, `source_provenance`).
   - **Zero Contamination:** Verified 0 duplicate example IDs, 0 train-validation document overlaps, and 0 test split exposures.
2. **Strict Semantic Mapping (No Silent Remapping):**
   - Direct contradictions (*Evident Conflict* / *Subtle Conflict*) are mapped strictly to `CONTRADICTION`.
   - Unsupported / baseless claims (*Evident Baseless Info* / *Subtle Baseless Info*) are mapped strictly to `NEUTRAL`.
   - Records with mixed conflict and baseless info (1,613 records) and ungrounded HaluEval pairs were quarantined into `exclusion_manifest.json` rather than arbitrarily remapped.
3. **Architecture & Runtime:**
   - Pretrained DeBERTa-v3-small backbone with a dedicated 3-class sequence classification head (`classifier.weight` [3, 768], `classifier.bias` [3]).
   - Total Parameters: **141,897,219** (141.9M). Runtime: FP32 on CPU.
   - 100% offline loading enforced (`HF_HUB_OFFLINE=1`, `local_files_only=True`).
4. **Dedicated Runner & Verification:**
   - Dedicated runner implemented in `tools/training/train_nli_classifier.py`.
   - Features: Deterministic 3-class balanced sampling, split isolation verification, real-time memory/swap watchdogs, atomic checkpointing with protected path overwrite guards, and an explicit authorization gate.
   - Test Suite: **21/21 unit tests passed** in `tests/unit/test_track02_step03_6_nli_training_runner.py`.
5. **Resource Feasibility:**
   - Host RAM: 6.5 GiB available (4.0 GiB buffer over estimated 2.45 GB peak RSS).
   - Swap: 3.4 GiB free.
   - Estimated runtime: ~21–25 minutes for a 1,000-step balanced pilot; ~3.6 hours for a full 10,815-step epoch.

**STOP NOTICE:** Zero training, backward passes, or optimizer steps were executed. A separate, explicit authorization will be required prior to any training execution.
