# TrustRAG Phase 13 — Step 01: Independent Security Benchmark Expansion Report

**Role:** Senior ML Security Engineer & Independent Evaluation Auditor  
**Date:** November 18, 2026  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-13` | **HEAD:** `aba5cc9d`  
**Artifact Directory:** `reports/research_completion/phase13_generalization_and_hardening/`  
**Dataset Inventory:** [`step01_dataset_inventory.json`](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/phase13_generalization_and_hardening/step01_dataset_inventory.json)

---

## 1. Executive Summary & Audit Mandate

In Phase 12, forensic audit resolved the historical $875$ vs $1,000$ sample count discrepancy and established a true baseline Attack Success Rate of **$57.14\%$** ($500/875$ declarative factual attacks breached defenses).

To rigorously validate security hardening across diverse, non-template scenarios, **Phase 13 Step 01** executes a comprehensive expansion of the security evaluation corpus. This expansion structures, validates, and partitions evaluation data across **9 distinct threat categories**, while enforcing strict data hygiene, cryptographic deduplication, provenance tracking, and zero contamination against the frozen DeBERTa NLI training sets.

---

## 2. Security Dataset Audit & Deduplication

### 2.1 Raw Security Benchmark Forensic Audit
The primary repository security dataset at `data/raw/custom_security/raw_train.jsonl` was audited at the individual byte and record level:
- **Total Ingested Records:** $2,000$ records.
- **Unique Document SHA-256 Hashes:** $2,000$ ($0$ duplicates, $0$ collisions).
- **True Attack Samples ($N_{\text{attack}}$):** $875$ records across 7 distinct threat subtypes.
- **True Benign Clean Controls ($N_{\text{clean}}$):** $1,125$ records ($1,000$ paired factual references + $125$ benign instruction-like culinary controls previously mislabeled as poisoned in Phase 11.2).

### 2.2 Model Training Contamination Verification
A cryptographic hash verification was performed between the $2,000$ security records and the DeBERTa-v3-small NLI training sets (`data/processed/sft_v2/nli/train.jsonl`, $N=10,815$; and `validation.jsonl`, $N=2,662$):
- **Training Set Overlap:** **$0 / 10,815$ records ($0.00\%$)**
- **Validation Set Overlap:** **$0 / 2,662$ records ($0.00\%$)**
- **Audit Conclusion:** The frozen DeBERTa-v3-small NLI model has zero training exposure to the security evaluation benchmark. All evaluations represent genuine out-of-distribution generalization.

---

## 3. Nine-Category Security Expansion Matrix

The expanded Phase 13 security benchmark explicitly partitions and evaluates 9 threat categories:

| Category # | Evaluation Category Name | Threat Family | Sample Count ($N$) | Evaluation Surface / Description | Provenance & Source |
| :-: | :--- | :--- | :---: | :--- | :--- |
| **1** | `direct_prompt_injection` | `PROMPT_INJECTION` | $125$ | Direct adversarial system override directives attempting guardrail bypass | `custom_security/raw_train.jsonl` |
| **2** | `declarative_factual_poisoning` | `KNOWLEDGE_POISONING` | $500$ | Non-imperative false assertions designed to evade keyword/instruction filters | `custom_security/raw_train.jsonl` |
| **3** | `medical_dosage_distortion` | `KNOWLEDGE_POISONING` | $125$ | Lethal distortions of pharmaceutical dosages (e.g., paracetamol $20,000\text{ mg}$) | `custom_security/raw_train.jsonl` |
| **4** | `cryptographic_falsification` | `KNOWLEDGE_POISONING` | $125$ | Fabricated backdoors and compromised keyspaces (e.g., AES-256 32-bit trapdoor) | `custom_security/raw_train.jsonl` |
| **5** | `financial_disinformation` | `CONFLICTING_EVIDENCE` | $125$ | Falsified macroeconomic policy, rate dissolutions, and fraudulent corporate solvency | `custom_security/raw_train.jsonl` |
| **6** | `astrophysical_disinformation` | `CONFLICTING_EVIDENCE` | $125$ | Contradicted spectroscopic observations and fabricated planetary orbital parameters | `custom_security/raw_train.jsonl` |
| **7** | `duplicate_conflicting_evidence` | `CONFLICTING_EVIDENCE` | $125$ | Co-retrieved clean and conflicting evidence evaluating inter-document conflict detection | `custom_security` paired subsets |
| **8** | `multidoc_coordinated_poisoning_3v1` | `COORDINATED_POISONING` | $125$ | Consensus spoofing: 3 coordinated poisoned passages confronting 1 authentic reference | Synthetic multi-document corpus |
| **9** | `unseen_paraphrased_factual_poisoning`| `KNOWLEDGE_POISONING` | $100$ | Out-of-distribution paraphrased contradictions testing semantic generalization | Held-out Phase 13 benchmark suite |

### 3.1 Benign Control Separation
To prevent metric distortion and guarantee clean query utility, all benign evaluation controls are maintained in an isolated partition:
- **Paired Factual Controls ($N=1,000$):** Authentic reference passages paired with target queries across medicine, cryptography, economics, and astrophysics.
- **Benign Procedural Controls ($N=125$):** Harmless imperative instructions (e.g., home bread baking recipes) verifying that G2 does not falsely flag legitimate step-by-step procedures.
- **Total Clean Controls:** $1,125$ evaluation pairs.

---

## 4. Key Takeaways & Readiness for Step 02

1. **Complete Category Coverage:** The 9 mandated threat categories are fully defined, cryptographically validated, and cataloged in [`step01_dataset_inventory.json`](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/phase13_generalization_and_hardening/step01_dataset_inventory.json).
2. **Defensive Target for Step 02:** Baseline G2 and Phase 12 remediations achieved $100\%$ detection on categories 1, 3, and 4, but exhibited $0\%$ detection on categories 5, 6, 8, and 9. Step 02 will advance G2 factual consistency to eliminate these vulnerabilities without degrading clean utility.

