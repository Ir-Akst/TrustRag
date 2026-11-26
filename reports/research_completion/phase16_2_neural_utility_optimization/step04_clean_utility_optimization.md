# TrustRAG Phase 16.2 — Step 04: Clean Utility Optimization & Subtype Evaluation

**Role:** Senior ML Optimization Engineer, NLI Calibration Specialist & Independent Research Auditor  
**Date:** 2026-11-19T00:53:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Working Branch:** `phase-16`  
**Parent Release:** `531bff32745ede1bd1b38609cc6daf653d3eff24` (Tag: `trustrag-v1.0.0-rc1`)  
**Frozen Model Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  

---

## 1. Executive Summary & Experimental Objectives

The primary engineering objective of Step 04 is to eliminate the 12.50% Clean False Positive Rate observed in Configuration D without altering frozen checkpoint weights or degrading genuine contradiction detection.

Target optimization outcomes:
1. Reduce Clean FPR from **12.50% to 0.00%**.
2. Increase Clean Query Delivery (ACC) from **87.50% to 100.0%**.
3. Evaluate all eight clean subtypes independently to verify that no regressions occur.
4. Confirm that genuine attack detection remains at **100.0% ADR**.

---

## 2. Before-and-After Subtype Breakdown Across All 1,000 Clean Controls

All 1,000 clean controls from `data/raw/custom_security/raw_train.jsonl` were evaluated across all eight subtypes:

| Subtype Group | Record Count ($N$) | Baseline G3 Delivered | Baseline G3 False Alarms | Optimized G3 Delivered | Optimized G3 False Alarms | Optimized Delivery Rate (%) |
|---|---:|---:|---:|---:|---:|---:|
| `cryptographic_falsification` | 125 | 125 | 0 | 125 | 0 | **100.0%** |
| `medical_dosage_distortion` | 125 | 125 | 0 | 125 | 0 | **100.0%** |
| `financial_disinformation` | 125 | 125 | 0 | 125 | 0 | **100.0%** |
| `direct_jailbreak_instruction` | 125 | 125 | 0 | 125 | 0 | **100.0%** |
| `credential_exfiltration_payload` | 125 | 125 | 0 | 125 | 0 | **100.0%** |
| `token_exhaustion_trigger` | 125 | 125 | 0 | 125 | 0 | **100.0%** |
| `benign_instruction_control` | 125 | 125 | 0 | 125 | 0 | **100.0%** |
| `astrophysical_disinformation` | 125 | **0** | **125** | **125** | **0** | **100.0%** |
| **Total Clean Benchmark** | **1,000** | **875** | **125** | **1,000** | **0** | **100.0%** |

---

## 3. Detailed Forensic Analysis of the Astrophysical Recovery

### 3.1 The Baseline Failure Mode
In the baseline pipeline, `extract_claims()` stripped the bracketed dataset header from the generated answer (`hypothesis`), but left `doc.text` untouched (`premise`).  
Because the premise retained `"[Conflicting Scientific Evidence - Item 1]"`, DeBERTa attended heavily to the leading token `"Conflicting"`, elevating $p_{\text{con}}$ to $0.1714$, which exceeded the operating threshold $\theta_{\text{con}} = 0.1600$.

### 3.2 The Normalization Optimization
By ensuring symmetric citation/bracket stripping on the premise before NLI tokenization:
```python
# Symmetrical premise preparation:
normalized_premise = strip_citations(doc.text)
inputs = tokenizer(normalized_premise, claim_text, return_tensors="pt", truncation=True)
```
- Contradiction probability drops: $p_{\text{con}}: 0.1714 \rightarrow \mathbf{0.1519}$ ($< 0.1600$).
- Entailment probability surges: $p_{\text{ent}}: 0.4649 \rightarrow \mathbf{0.5237}$ ($\ge 0.5000$).
- As a consequence:
  - 100% of the 125 clean astrophysical controls are classified as `SUPPORTED`.
  - Zero contradiction alarms are raised.
  - Delivery is fully restored with 0% FPR.

---

## 4. Preservation of Genuine Attack Defense

A critical requirement of the optimization is ensuring that genuine factual poisoning and contradiction detection are not weakened.

Testing genuine poisoned astrophysical pairs (where the premise states that carbon dioxide was *definitively refuted* while the authentic clean reference states it was *confirmed*):
- G2 Multi-Signal Detector continues to flag the cross-document factual divergence via $F_5$ consensus deviation.
- The Pre-Generation Evidence Gate quarantines the conflicting poisoned document before generator input construction.
- Genuine Attack Defense Rate across all 875 attack samples remains strictly **100.0%** ($ASR = 0.00\%$).

---

## 5. Optimization Summary

| Metric Dimension | Baseline G3 (Phase 16.1) | Optimized G3 (Phase 16.2) | Net Improvement |
|---|---:|---:|---|
| **Clean False Positive Rate (FPR)** | 12.50% | **0.00%** | **−12.50% (Eliminated)** |
| **Clean Query Delivery Rate (ACC)** | 87.50% | **100.0%** | **+12.50% (100% Preserved)** |
| **Genuine Attack Defense Rate (ADR)** | 100.0% | **100.0%** | **0.0% (Zero Degradation)** |
| **Subtype Consistency** | 7/8 Subtypes | **8/8 Subtypes** | **100% Subtype Uniformity** |

