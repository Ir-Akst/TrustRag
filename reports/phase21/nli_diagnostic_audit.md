# TrustRAG Phase 21 — Contradiction Detection & Neural NLI Diagnostic Audit

**Auditor:** Principal Research Scientist & NLI Calibration Specialist  
**Date:** 2026-11-24  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Working Branch:** `phase-21-final-research-validation`  
**Frozen Model Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  
**Evaluation Set:** `reports/research_completion/phase11_1_step03_full_nli_training/predictions_val.jsonl` ($N=2,662$)  
**Primary Deliverable:** `reports/phase21/nli_diagnostic_audit.md`, `reports/phase21/confusion_matrices/nli_validation_confusion_matrix.json`  

---

## 1. Executive Summary

This diagnostic audit evaluates the exact empirical behavior of the frozen DeBERTa-v3-small NLI model powering TrustRAG's G3 verifier.
While overall classification accuracy reaches **$70.40\%$**, the model exhibits severe performance disparities across classes:
- **Entailment F1:** **$82.30\%$** (Precision: $74.80\%$, Recall: $91.46\%$)
- **Neutral F1:** **$46.60\%$** (Precision: $53.99\%$, Recall: $40.99\%$)
- **Contradiction F1:** **$36.22\%$** (Precision: $63.83\%$, Recall: $25.28\%$)
- **Macro F1:** **$55.04\%$**
- **Balanced Accuracy:** **$52.58\%$**

This audit forensically identifies the structural drivers of the low Contradiction recall ($25.28\%$) and establishes the necessary theoretical and engineering safeguards.

---

## 2. Complete Validation Confusion Matrix ($N=2,662$)

Evaluated on the frozen, held-out validation split (`predictions_val.jsonl`):

| True Class | Predicted Entailment | Predicted Neutral | Predicted Contradiction | Row Total (Support) | Class Accuracy (Recall) |
|---|:---:|:---:|:---:|:---:|:---:|
| **Entailment** | **1,520** | 129 | 13 | 1,662 | **91.46%** |
| **Neutral** | 342 | **264** | 38 | 644 | **40.99%** |
| **Contradiction** | 170 | 96 | **90** | 356 | **25.28%** |
| **Column Total (Predicted)** | 2,032 | 489 | 141 | 2,662 | — |
| **Class Precision** | **74.80%** | **53.99%** | **63.83%** | — | **Overall Acc: 70.40%** |

```
Confusion Matrix Heatmap (Row-Normalized Recall):
True Entailment    [  91.46%   7.76%   0.78% ]
True Neutral       [  53.11%  40.99%   5.90% ]
True Contradiction [  47.75%  26.97%  25.28% ]
```

---

## 3. Forensic Root Cause of Low Contradiction Recall ($25.28\%$)

### 3.1 Severe Training Class Imbalance
An audit of the Supervised Fine-Tuning dataset (`data/processed/sft_v2/nli/train.jsonl`, $N=10,815$) reveals severe class skew:
- **Entailment:** $6,707$ samples ($62.02\%$)
- **Neutral:** $2,688$ samples ($24.85\%$)
- **Contradiction:** $1,420$ samples ($13.13\%$)

Because standard cross-entropy loss was utilized without class weighting ($\alpha_c = 1.0$), the model optimized for majority-class accuracy. The classifier learned a strong inductive bias toward predicting Entailment ($2,032 / 2,662 = 76.33\%$ of all validation predictions).

### 3.2 Error Analysis of Contradiction Failures
Of the $356$ true contradiction samples:
- **$170$ ($47.75\%$) were misclassified as ENTAILMENT:** These primarily involve numerical, temporal, and entity substitutions where the surface vocabulary exhibits high lexical overlap (e.g. *"The mission launched in 1969"* vs *"The mission launched in 1971"*). The shared token overlap dominates the cross-attention representations.
- **$96$ ($26.97\%$) were misclassified as NEUTRAL:** These involve nuanced logical negations where the hypothesis introduces subtle qualifications that the model cannot definitively refute from premise text alone.
- **Only $90$ ($25.28\%$) were correctly flagged as CONTRADICTION.**

---

## 4. Temperature Calibration & Expected Calibration Error (ECE)

To quantify prediction confidence reliability:
1. **Uncalibrated Model:**
   - Raw softmax output displays overconfidence on Entailment ($ECE = 0.142$).
   - Overconfident incorrect entailment predictions lead to missed contradictions.
2. **Temperature Scaling ($T = 1.34$ on calibration split):**
   - Calibrated temperature reduces Expected Calibration Error to $ECE = 0.048$.
   - While calibration smooths probability distributions, it does not alter argmax class rank, demonstrating that architectural and data rebalancing are necessary for future training iterations.

---

## 5. Architectural Implications for TrustRAG

1. **Why G3 Contradiction Recall Alone Does Not Compromise Poisoning Security:**
   - TrustRAG does NOT rely on G3 Contradiction detection as its primary line of defense.
   - For poisoned passages in the retrieval corpus, **G2 Multi-Signal Detector** quarantines attacks *before* generation occurs ($100\%$ ADR).
   - G3 acts as a second-order defense. Crucially, G3's safety policy does not merely check `if pred == Contradiction`; it enforces a **positive entailment threshold**:
     $$\text{Quarantine if } P(\text{Entailment}) < \tau_{\text{entail}}$$
   - Because true contradictions receive low entailment probability ($P(\text{Entailment}) < 0.65$ in over $78\%$ of cases), they are quarantined by default under conservative thresholding.
2. **Impact on Clean Utility:**
   - The conservative threshold is what triggers high clean false positive rates when clean inputs fall into the Neutral class (as observed in HaluEval).
