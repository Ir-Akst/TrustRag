# TrustRAG — Track 2, Step 3.9: Executive Failure Report & Root Cause Investigation

- **Date:** 2026-11-14T12:35:00Z
- **Role:** Senior ML Research Engineer, Independent Experimental Auditor
- **Repository:** `/home/aditya/rags/TrustRag-phase11` (`phase-11` @ `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)
- **Protected Baseline Repository:** `/home/aditya/rags/TrustRag` (`phase-10` @ `e65bcc80aac634900d1f8e343880fddf66cec168`, strictly immutable)
- **Investigated Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000` (Step 3.8 Checkpoint)
- **Pretrained Base:** `/home/aditya/rags/models/pretrained/deberta-v3-small` (FP32, 141.9M parameters, untouched)
- **Preserved Binary Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000` (byte-for-byte unchanged)
- **Final Verdict:** **`ROOT_CAUSE_IDENTIFIED`**

---

## Executive Summary

An adversarial forensic audit was conducted on the completed 1,000-optimizer-step DeBERTa-v3-small Evidence-Grounded 3-Way NLI pilot (`ENTAILMENT=0`, `CONTRADICTION=1`, `NEUTRAL=2`). The pilot finished all 1,000 optimization updates on CPU, but failed to learn three-class discriminative capability, exhibiting complete collapse on the ENTAILMENT class (predicting **0 Entailment**, **389 Contradiction**, and **2,273 Neutral** across 2,662 validation records) and causing validation cross-entropy loss to increase from **1.0898** (untrained head) to **2.4507** (trained checkpoint).

### Primary Verified Root Causes

1. **Catastrophic Recency Bias via Unshuffled Sequential Tail (Verified Finding):**
   In `load_nli_dataset()`, 1,000 samples were selected via a sequential one-pass scan until class caps were met (`counts[lbl] < targets[lbl]`). Because the training file is 62.0% Entailment (6,707 / 10,815), the target of 334 Entailment records was reached and exhausted at record index 705. Because no random shuffling was performed (`random.shuffle()` was omitted), the final **295 consecutive optimizer steps** (steps 706 through 1,000) contained **EXACTLY ZERO ENTAILMENT SAMPLES** (154 Contradiction, 141 Neutral). With batch size 1 and AdamW, 295 consecutive negative updates drove the Entailment logit $z_0$ down to an average of **-1.448** ($p_0 \approx 5.1\%$, max $p_0 = 10.3\%$ across all 2,662 validation samples), suppressing Entailment predictions to zero.

2. **Severe Context Truncation Blindness via `max_seq_len = 128` (Verified Finding):**
   The mean token length of (premise, hypothesis) cross-encoder pairs is **943.8 tokens** in the training partition and **638.0 tokens** in validation. Exactly **100.0% of training samples and 100.0% of validation samples exceeded the 128-token cutoff**. HuggingFace's default `longest_first` truncation sliced away the substantive evidence in structured premises (e.g. cutting off business attributes and user reviews at token ~64) and sliced away generated claims in hypotheses (cutting off at token ~64). In the RAGTruth benchmark, hallucination spans typically occur deep in generated responses against fine-grained factual evidence in premises. The model was systematically starved of the textual tokens required to determine entailment or factual contradiction.

3. **Mathematical Mechanism of Validation Loss Explosion (Verified Finding):**
   The validation loss increase from 1.0898 to 2.4507 was **NOT** caused by numerical instability, exploding gradients, or weight divergence. At Step 0, an untrained symmetric head predicted roughly uniform probabilities ($p \approx 0.33$), yielding $-\ln(1/3) \approx 1.09$. In the post-training evaluation, because 62.4% (1,662 / 2,662) of validation records are true Entailment, and the model's predicted probability for Entailment had been suppressed to $p_0 \approx 0.051$, the cross-entropy loss on those 1,662 samples exploded to $-\ln(0.051) \approx 2.97$, mechanically driving the dataset-wide average loss to 2.4507.

---

## Verdict Summary

| Investigation Domain | Finding | Verdict |
| :--- | :--- | :---: |
| **Label Mapping Integrity** | `ENTAILMENT=0`, `CONTRADICTION=1`, `NEUTRAL=2` consistent across data, model, and loss | **VERIFIED CLEAN** |
| **Pipeline & Optimization** | 1,000 optimizer steps completed, grad norm $\le 1.0$, LR decayed from 2e-5 to 0 | **VERIFIED EXECUTED** |
| **Class Collapse Origin** | Unshuffled sampling created 295-step unbroken non-Entailment tail; suppressed $z_0$ | **ROOT CAUSE VERIFIED** |
| **Information Truncation** | 100% of samples truncated by `max_seq_len=128`; evidence and claims severed | **ROOT CAUSE VERIFIED** |
| **Overall Assessment** | Full forensic diagnosis complete with mathematical proof and code trace | **ROOT_CAUSE_IDENTIFIED** |
