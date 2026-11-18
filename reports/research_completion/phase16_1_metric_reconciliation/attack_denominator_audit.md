# TrustRAG Phase 16.1 — Forensic Audit 01: Attack Denominators & Category Breakdown Reconciliation

**Auditor:** Senior ML Evaluation Auditor and Statistical Reproducibility Specialist  
**Date:** 2026-11-19T00:37:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-16`  
**Reference Release Tag:** `trustrag-v1.0.0-rc1` (Commit: `531bff32745ede1bd1b38609cc6daf653d3eff24`)  
**Target Artifact Audited:** `reports/research_completion/phase16_independent_poisoning_validation/step04_security_utility_analysis.md`  
**Raw Source Dataset:** `data/raw/custom_security/raw_train.jsonl`  

---

## 1. Executive Summary & Audit Mandate

In the Phase 16 validation report (`step04_security_utility_analysis.md`), a headline discrepancy appeared between the global genuine attack denominator ($N_{\text{att}} = 875$) and the table breakdown across the 5 designated attack objectives, where the individual category sample sizes summed to $1,000$ ($250 + 250 + 125 + 125 + 250 = 1,000$).

This forensic audit inspected `data/raw/custom_security/raw_train.jsonl` line by line, traced every raw sample ID, mapped all attack categories, and resolved the discrepancy.

---

## 2. Raw Dataset Structure & Subtype Distribution

The authoritative raw evaluation dataset `data/raw/custom_security/raw_train.jsonl` (SHA-256: `823bca9639587ff7170530a67c2b35c54d959ee2007bdb554c3e50143c4dae00`) contains exactly **2,000 JSON lines**, partitioned into two contiguous blocks of 1,000 records each:

### 2.1 Block 1: Lines 1 to 1,000 (`clean_poison_label: "clean"`)
- Exactly 1,000 baseline records paired to queries, each with `metadata.pair_id` from `sec_pair_0000` to `sec_pair_0999`.
- Subtype distribution: Exactly 8 subtypes $\times$ 125 records each = 1,000 records.

### 2.2 Block 2: Lines 1,001 to 2,000 (`clean_poison_label: "poisoned"`)
- Exactly 1,000 records paired to the same queries and pair IDs (`sec_pair_0000` to `sec_pair_0999`).
- Subtype breakdown:

| Line Range | `attack_subtype` | Raw Label | Record Count | Genuine Semantic Nature |
|---|---|---|---:|---|
| 1001–1125 | `cryptographic_falsification` | `poisoned` | 125 | **Genuine Attack** (Targeted Knowledge Poisoning) |
| 1126–1250 | `medical_dosage_distortion` | `poisoned` | 125 | **Genuine Attack** (Targeted Knowledge Poisoning) |
| 1251–1375 | `financial_disinformation` | `poisoned` | 125 | **Genuine Attack** (Stealthy Factual Poisoning) |
| 1376–1500 | `direct_jailbreak_instruction` | `poisoned` | 125 | **Genuine Attack** (Explicit Prompt Injection) |
| 1501–1625 | `credential_exfiltration_payload` | `poisoned` | 125 | **Genuine Attack** (Explicit Prompt Injection) |
| 1626–1750 | `token_exhaustion_trigger` | `poisoned` | 125 | **Genuine Attack** (Trigger-Based Denial-of-Service) |
| 1751–1875 | `benign_instruction_control` | `poisoned` | 125 | **Clean Control Mislabeled as Poisoned** (Baking instructions) |
| 1876–2000 | `astrophysical_disinformation` | `poisoned` | 125 | **Genuine Attack** (Stealthy Factual Poisoning) |
| **Total** | **8 Subtypes** | | **1,000** | **875 Genuine Attacks + 125 Mislabeled Controls** |

---

## 3. Forensic Investigation of the $875$ vs $1,000$ Category Sum

### 3.1 Root Cause Identification
The apparent discrepancy between the 875 reported total attacks and the 1,000 category breakdown sum arose from two distinct factors:

1. **Double-Counting of `token_exhaustion_trigger` Across Objectives 3 and 4:**  
   In `step04_security_utility_analysis.md` (and `evaluate_campaign.py` lines 96–105), the five attack objectives were constructed as:
   - **Objective 1 (Targeted Knowledge Poisoning):** `cryptographic_falsification` ($125$) + `medical_dosage_distortion` ($125$) = **250**
   - **Objective 2 (Explicit Prompt Injection):** `direct_jailbreak_instruction` ($125$) + `credential_exfiltration_payload` ($125$) = **250**
   - **Objective 3 (Denial-of-Service Poisoning):** `token_exhaustion_trigger` = **125**
   - **Objective 4 (Trigger-Based Denial-of-Service):** `token_exhaustion_trigger` = **125**
   - **Objective 5 (Stealthy Factual Poisoning):** `financial_disinformation` ($125$) + `astrophysical_disinformation` ($125$) = **250**
   
   Summing the rows of this table yields:
   $$250 + 250 + 125 + 125 + 250 = \mathbf{1,000}$$
   
   However, Objective 3 and Objective 4 mapped to the **exact same 125 pair IDs** (`sec_pair_0625` to `sec_pair_0749`). The 125 samples were counted twice in the table presentation.

2. **The 125 Mislabeled `benign_instruction_control` Records:**  
   In Block 2 of `raw_train.jsonl`, lines 1,751–1,875 contain baking recipes (e.g. `"To bake sourdough, dissolve active starter in water..."`). These 125 records carry `"clean_poison_label": "poisoned"` in the raw JSON, but contain zero malicious or adversarial content.  
   If these 125 records were included in attack metrics, the attack denominator would be $875 + 125 = 1,000$. However, treating benign baking text as an attack would artificially distort security metrics.

---

## 4. Reconciled Attack Breakdown (Strict Zero-Overlap)

To eliminate double-counting and present statistically sound metrics, the evaluation suite must report both the **deduplicated genuine attack denominator** ($N=875$) and the objective-level breakdown without double-counting:

| Objective ID | Objective Title | Threat Subtypes | Unique Pair IDs | Sample Count ($N$) | Share of Attack Benchmark |
|---|---|---|---|---:|---:|
| **Obj 1** | Targeted Knowledge Poisoning | `cryptographic_falsification`, `medical_dosage_distortion` | `sec_pair_0000`–`sec_pair_0249` | 250 | 28.57% |
| **Obj 2** | Explicit Prompt Injection | `direct_jailbreak_instruction`, `credential_exfiltration_payload` | `sec_pair_0375`–`sec_pair_0624` | 250 | 28.57% |
| **Obj 3 & 4** | Denial-of-Service & Trigger DoS | `token_exhaustion_trigger` | `sec_pair_0625`–`sec_pair_0749` | 125 | 14.29% |
| **Obj 5** | Stealthy Factual Poisoning | `financial_disinformation`, `astrophysical_disinformation` | `sec_pair_0250`–`sec_pair_0374`, `sec_pair_0875`–`sec_pair_0999` | 250 | 28.57% |
| **Total** | **All Unique Attack Objectives** | **7 Attack Subtypes** | **875 Unique Pairs** | **875** | **100.0%** |

---

## 5. Audit Finding & Conclusion

- **True Attack Denominator:** Strictly **$N=875$** unique genuine attack samples.
- **Root Cause of Discrepancy:** Dual-assignment of `token_exhaustion_trigger` to both Objective 3 and Objective 4 in the presentation table ($125$ double-counted rows), combined with the historical presence of $125$ mislabeled benign baking records in Block 2.
- **Resolution Status:** Fully resolved and reconciled from raw JSON records.

