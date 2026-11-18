# TrustRAG — Phase 11.1, Step 3: Final Model Evaluation Report

**Date:** 2026-11-15  
**Auditor:** Senior ML Infrastructure Engineer and Experimental Execution Auditor  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Campaign Status:** INTERRUPTED (INCOMPLETE)  
**Final Evaluation Status:** NOT PERFORMED (No Final Checkpoint Available)

---

## 1. Evaluation Mandate & Preconditions

Under Section 5 of the Phase 11.1 Step 3 Charter:
> *"After all 3 epochs complete:*
> *Evaluate the final checkpoint on the full validation set of 2,662 samples.*
> *Report: Accuracy, Balanced accuracy, Macro F1, Per-class precision, recall and F1, Confusion matrix, Contradiction recall, Brier score, ECE-10, Validation loss.*
> *Compare results against the existing Step 0 baseline and the immutable NLI pilot checkpoints.*
> *Do not claim research success based on training loss alone."*

### Precondition Check
- **Required Precondition:** Completion of all 3 training epochs and availability of a final trained model checkpoint at `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`.
- **Actual Status:** Unmet. The training campaign was interrupted at Step 50 of Epoch 1 (out of 8,112 total steps) due to an external hardware reboot.
- **Checkpoint Availability:** No final or intermediate checkpoint was committed to disk prior to the reboot.
- **Evaluation Execution:** In accordance with scientific integrity guidelines, no synthetic, mocked, or fabricated post-training evaluation metrics are reported.

---

## 2. Comparison with Baseline & Historical Pilot Checkpoints

While final 3-epoch evaluation could not be executed, the empirical baseline metrics captured prior to the interruption are cataloged alongside the immutable historical pilot models:

| Checkpoint / Asset | Training Scope | Validation Accuracy | Balanced Accuracy | Macro F1 | Contradiction Recall | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Step 0 Pre-Training Baseline** | 0 optimizer steps | **24.19%** | **33.33%** | **0.1299** | **0.00%** | Empirically Measured |
| **NLI Pilot 1000** | 250 optimizer steps (1,000 samples) | 43.88% | 34.02% | 0.2307 | 4.81% | Immutable Historical |
| **NLI Remediated (Pilot)** | 250 optimizer steps (Class-weighted) | 48.72% | 46.21% | 0.4412 | 41.35% | Immutable Historical |
| **Phase 11.1 Full 3-Epoch Target** | 8,112 optimizer steps (32,445 passes) | *Incomplete* | *Incomplete* | *Incomplete* | *Incomplete* | Interrupted at Step 50 |

---

## 3. Evaluation Conclusion

Because the training campaign was cut short at Step 50 by an external host reboot before completing the 3 epochs, final evaluation could not be conducted. Full evaluation remains pending a complete, uninterrupted execution.

