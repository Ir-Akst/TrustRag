# 03 — P1 Data Integrity, Verification Accuracy, and Calibration Report

**Date:** 2026-11-13  
**Auditor:** Independent Adversarial Verification Team  
**Scope:** Verification of P1.4 (Offline Dataset Loaders), P1.5 (G3 Linguistic Verifier Fixes), and P1.6 (Adaptive Calibration)  
**Evidence File:** `evidence/p1_probe_output.json` (SHA256: `152aec6e5a5f89e04ac17df22b5a1939eb10afdf205a49c698684f5f52235238`)

---

## 1. P1.4: Offline Dataset Loader Short-Circuit Timing

### Issue Description
When benchmark loaders were invoked with `offline=True` while raw cache directories (`data/raw/<dataset>`) were empty, the underlying Hugging Face `load_dataset` helper executed repeated HTTP HEAD requests to `huggingface.co`, causing 30–60 second test timeouts and execution hangs in sandboxed or air-gapped environments.

### Independent Verification Probe
Direct instantiation and execution of dataset adapters with `offline=True` against non-existent local raw caches:
- `NaturalQuestionsAdapter(offline=True)`
- `HotpotQAAdapter(offline=True)`
- `MSMarcoAdapter(offline=True)`

### Verification Findings
```
Dataset             Elapsed Time   Exception Raised      Message
NaturalQuestions    0.156 s        AcquisitionError      Dataset unavailable in offline mode. No cached version found.
HotpotQA            0.000 s        AcquisitionError      Dataset unavailable in offline mode. No cached version found.
MSMarco             0.000 s        AcquisitionError      Dataset unavailable in offline mode. No cached version found.
```
- All loaders short-circuit deterministically in **< 0.20 seconds**.
- No external network requests or hang periods occurred.
- **Verdict: PASS (Closed)**.

---

## 2. P1.5: G3 Output Verifier Accuracy & Semantic Enhancements

### A. Phrased Unit Equivalence & Token Normalization
- **Issue:** Original G3 implementation evaluated lexical overlap before unit conversion. Comparing `1000 mg per day` in evidence against `1 g daily` in the claim yielded coverage `0.60 < 0.65`, resulting in false `INSUFFICIENT_EVIDENCE`.
- **Remediation:** Integrated `_FREQ_PERIOD_SYNONYMS` (e.g., `daily` <-> `{"day", "daily", "per", "a"}`) and dimension-aware scalar mapping (`_normalize_to_dimension`).
- **Independent Probe Results:**
  1. Claim: `"The patient took 1 g daily of medication."`  
     Evidence: `"Clinical record confirms the patient was administered 1000 mg per day of medication."`  
     **Result:** **SUPPORTED** (Claim coverage: `1.00`, Verdict: `SUPPORTED`).
  2. Claim: `"Daily fluid intake is capped at 1 L per day."`  
     Evidence: `"Daily fluid intake is capped at 1000 ml daily."`  
     **Result:** **SUPPORTED** (Claim coverage: `1.00`, Verdict: `SUPPORTED`).
  3. Claim: `"The dose was 500 mg per day."`  
     Evidence: `"The prescribed dose was 2000 mg daily."`  
     **Result:** **CONTRADICTED** (Conflicting numeric scalar detected).
- **Verdict: PASS (Closed)**.

### B. Coordinated Clauses Multi-Document Verification
- **Issue:** In `01_clean_factual`, when evaluating the claim `"Pure water freezes at 0 °C and boils at 100 °C."`, evidence document A stated only boiling point (`100 °C`), while evidence document B stated both freezing and boiling points. Document A's absence of freezing point was falsely flagged as a numeric contradiction.
- **Remediation:** Added `_thermal_properties_disjoint` and `required_predicate_text` checks so missing independent predicates across distinct documents do not trigger false contradictions unless properties overlap.
- **Independent Probe Results:**
  - Evaluated claim against `doc_nist` (boiling only) + `doc_wiki` (freezing & boiling).
  - Verdict: **SUPPORTED** (Status: `VERIFIED`, total claims: 1, supported: 1, contradicted: 0).
- **Verdict: PASS (Closed)**.

### C. Vague / Hedged Text Provenance Gating
- **Issue:** Extractive circularity in previous versions allowed generated answers with speculative or hedged phrasing (`perhaps`, `some variable vague factors`) to be verified as `SUPPORTED` simply because they lexically matched unverified evidence with unknown provenance.
- **Remediation:** Integrated `_VAGUE_HEDGE_RE` pattern check at `src/trustrag/verification/output_verifier.py` (lines 2505–2515), explicitly rejecting hedged assertions supported exclusively by unverified documents with provenance `UNKNOWN` or `NONE`.
- **Independent Probe Results:**
  - Claim: `"Perhaps some variable vague factors possibly affected the trial outcome."`
  - Evidence: Same text with `provenance="UNKNOWN"`.
  - Verdict: **INSUFFICIENT_EVIDENCE** (Status: `UNVERIFIED`).
  - Explanation: *"Claim asserts speculative or hedged statements supported exclusively by unverified evidence with unknown provenance; cannot certify as SUPPORTED."*
- **Verdict: PASS (Closed)**.

---

## 3. P1.6: Adaptive Calibration Alignment

### Issue Description
In Phase 08 / Reality Audit 16, `platt_calibrator_v1.json` exhibited high clean false-positive rates (`0.50`–`0.67`) on the `knowledge_poisoning` benchmark because Platt scaling weights had been fitted without active `F1` (perplexity) and `F2` (embedding norm) feature backends.

### Independent Verification Probe
Inspected calibrator files in `configs/adaptive/` and default configurations:
- `configs/adaptive/temperature_calibrator_v1.json`:
  - `calibrator_type`: `"temperature"`
  - `temperature`: `0.64315401`
  - Validated clean FPR: `0.00%` across canonical benchmark evaluation.
- Default calibrator parameter in `src/trustrag/pipeline/cli.py` line 34 points to `temperature_calibrator_v1.json`.
- `platt_calibrator_v1.json` remains available with neutral prior bias `0.0` for experimental evaluation.

### Verification Findings
- Temperature calibration provides smooth, monotonic probability mapping without inflating clean false positives.
- **Verdict: PASS (Closed)**.

---

## 4. Summary Table

| Sub-Gate | Target | Result | Evidence File Reference |
|:---|:---|:---:|:---|
| P1.1 | G3 Phrased Unit Equivalence | **PASS** | `p1_probe_output.json:P1_1_g3_phrased_units` |
| P1.2 | G3 Coordinated Clauses Verification | **PASS** | `p1_probe_output.json:P1_2_g3_coordinated_clauses` |
| P1.3 | G3 Vague / Hedged Provenance Gating | **PASS** | `p1_probe_output.json:P1_3_g3_vague_provenance_gating` |
| P1.4 | Offline Loader Short-Circuit Timing | **PASS** | `p1_probe_output.json:P1_4_dataset_loader_short_circuit` |
| P1.5 | Adaptive Calibrator Selection | **PASS** | `p1_probe_output.json:P1_5_calibration_alignment` |

