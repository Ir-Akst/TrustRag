# TrustRAG — Comprehensive Dataset Denominator & Sample Reconciliation Audit

**Auditor:** Senior Data Integrity Auditor & ML Reproducibility Specialist  
**Date:** 2026-11-19T03:02:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Dedicated Branch:** `phase-17-20-final-release`  
**Release Tag Candidate:** `trustrag-v1.0.0-rc1` (Commit: `531bff3`)  
**Output Directory:** `reports/research_completion/final_research_freeze/visualization_integrity_audit/`  

---

## 1. Executive Summary

A recurring source of ambiguity in ML security research stems from denominator conflation: pooling benign evaluation controls with genuine attack payloads, or conflating full corpus splits with balanced benchmark samples.

This audit forensically reconciles all dataset denominators, sample counts, exclusions, and partition overlaps across the 13 publication figures and their source datasets.

```
+---------------------------------------------------------------------------------------------------+
|                                 MASTER DENOMINATOR RECONCILIATION                                 |
+---------------------------------------------------------------------------------------------------+
|  1. Synthetic Security Corpus:     2,000 Total Records (1,000 Pairs)                              |
|     - Clean Controls:             1,000 Records (1,000 Pairs)                                     |
|     - Genuine Malicious Attacks:    875 Records (7 Subtypes x 125)                                |
|     - Benign Instruction Controls:  125 Records (Clean Imperative Prompts)                        |
|                                                                                                   |
|  2. Phase 18 Red-Team Corpus:       460 Total Attacks (15 Threat Categories)                      |
|     - Categories 1-13 & 15:          30 Instances Each (14 x 30 = 420)                            |
|     - Category 14 (Domain Misinfo):  40 Instances (10 Med, 10 Fin, 10 Sci, 10 Law)                |
|                                                                                                   |
|  3. External Benchmark Splits:                                                                    |
|     - RAGTruth (ACL 2024):         2,700 Total Split | 200 Balanced Sample in Figure 11           |
|     - HaluEval (EMNLP 2023):       3,000 Total Split | 200 Balanced Sample in Figure 11           |
|                                                                                                   |
|  4. DeBERTa SFT NLI Splits:                                                                       |
|     - Training Set (train.jsonl): 10,815 Records                                                 |
|     - Validation (val.jsonl):      2,662 Records (Figures 4, 5, 6)                                |
|     - Excluded During Pre-proc:    1,614 Records (Sanitized from Training)                        |
|     - Train/Val/Test Leakage:          0 Overlapping Pairs (0.00% Contamination)                   |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. In-Depth Reconciliation by Dataset & Figure

### 2.1 The Synthetic Security Benchmark: Reconciliation of $N=875$ vs. $N=1,000$
- **Raw File:** `data/raw/custom_security/raw_train.jsonl` (SHA-256: `823bca9639587ff7170530a67c2b35c54d959ee2007bdb554c3e50143c4dae00`).
- **Forensic Subtype Breakdown:**
  | Subtype Identifier | Total Records | Ground Truth Nature | Figure 1 Role | Figure 2 Role |
  |---|:---:|---|---|---|
  | `direct_jailbreak_instruction` | 125 | Explicit Malicious Jailbreak | Genuine Attack ($1/7$) | Category 1 ($N=125$) |
  | `credential_exfiltration_payload`| 125 | Exfiltration Directive | Genuine Attack ($2/7$) | *Omitted from plot* |
  | `token_exhaustion_trigger` | 125 | DoS Loop Trigger | Genuine Attack ($3/7$) | Category 8 ($N=125$) |
  | `medical_dosage_distortion` | 125 | Lethal Pharmaceutical Distortion | Genuine Attack ($4/7$) | Category 2 ($N=125$) |
  | `financial_disinformation` | 125 | Falsified Macroeconomic Rates | Genuine Attack ($5/7$) | Category 4 ($N=125$) |
  | `cryptographic_falsification` | 125 | Falsified Cryptographic Security | Genuine Attack ($6/7$) | Category 3 ($N=125$) |
  | `astrophysical_disinformation` | 125 | Falsified Orbital Discoveries | Genuine Attack ($7/7$) | Category 5 ($N=125$) |
  | `benign_instruction_control` | 125 | **Benign Imperative User Prompt** | **Clean Control** | *Omitted from plot* |
  | *(Phase 13 Duplicate Conflict)* | 125 | Near-Duplicate Scraped Mirror | *Stress Test Cohort* | Category 6 ($N=125$) |
  | *(Phase 13 Multi-doc 3v1)* | 125 | Collusive Consensus Inundation | *Stress Test Cohort* | Category 7 ($N=125$) |
- **Reconciliation Finding:**
  - In Figure 1, the primary denominator is correctly **$N=875$ genuine attacks** and **$N=1,000$ clean controls**.
  - In Figure 2, exactly 8 cohorts of $N=125$ each were plotted ($8 \times 125 = 1,000$). Credential Exfiltration was replaced by Phase 13 Duplicate Conflict ($N=125$) and Multi-doc 3v1 ($N=125$).
  - **Verdict:** Fully reconciled. The Figure 2 caption must clearly state that its $N=1,000$ represents 8 distinct evaluation cohorts, distinct from the canonical $N=875$ attack benchmark.

---

### 2.2 Phase 18 Red-Teaming Benchmark ($N=460$)
- **Raw File:** `reports/research_completion/final_independent_validation_and_release/raw_predictions/phase18_redteam_predictions.jsonl`.
- **Sample Distribution Verification:**
  - 14 Categories with $N=30$:
    1. Adaptive Prompt Injection ($N=30$)
    2. Multi-turn Context Manipulation ($N=30$)
    3. Cross-lingual Injection ($N=30$)
    4. Character Obfuscation ($N=30$)
    5. Paraphrased Factual Poisoning ($N=30$)
    6. Narrative Contradictions ($N=30$)
    7. Multi-doc Poisoning ($N=30$)
    8. Duplicate Source Poisoning ($N=30$)
    9. Sybil Varied Ratios ($N=30$)
    10. Majority Consensus Manipulation ($N=30$)
    11. Retrieval-Ranking Manipulation ($N=30$)
    12. Context Exhaustion ($N=30$)
    13. Citation Spoofing ($N=30$)
    15. Mixed Benign/Malicious Evidence ($N=30$)
  - 1 Category with $N=40$:
    14. Domain Misinformation ($N=40$: 10 Medicine, 10 Finance, 10 Science, 10 Law)
  - **Total Evaluations:** $14 \times 30 + 40 = \mathbf{460}$.
- **Reconciliation Finding:** Exact match. Figure 10 accurately plots all 460 instances without omissions or synthetic padding.

---

### 2.3 External Benchmarks: RAGTruth & HaluEval ($N=200$ Balanced)
- **Raw Sources:**
  - RAGTruth: `data/raw/ragtruth/response.jsonl` ($2,700$ records total).
  - HaluEval: `data/raw/halueval/qa_data.json` ($3,000$ records total).
- **Audit of Sample Selection:**
  - In Figure 11 and Phase 15 Step 03 (`step03_external_validation_report.md`), evaluation was conducted on a balanced sample of $N=200$ ($100$ `FACTUAL`, $100$ `HALLUCINATED`) for both datasets.
  - This balanced configuration was chosen to permit unbiased computation of Precision, Recall, and F1-score without base-rate distortions.
- **Reconciliation Finding:** Reconciled and verified.

---

### 2.4 DeBERTa SFT NLI Splits ($N=10,815$ Train, $N=2,662$ Validation)
- **Raw Files:** `data/processed/sft_v2/nli/train.jsonl` and `validation.jsonl`.
- **Audited Sample Counts:**
  - `train.jsonl`: Exactly $10,815$ records ($6,707$ Entailment, $2,688$ Neutral, $1,420$ Contradiction).
  - `validation.jsonl`: Exactly $2,662$ records ($1,662$ Entailment, $644$ Neutral, $356$ Contradiction).
  - `exclusion_manifest.json`: Exactly $1,614$ records excluded during preprocessing to prevent noisy label contamination.
- **Cross-Split Overlap & Leakage Audit:**
  - Cross-referencing normalized text hashes across SFT train, SFT val, Custom Security raw, Phase 18 red team, RAGTruth, and HaluEval confirmed **zero duplicate instances ($0.00\%$ leakage)**.
- **Figures 4, 5, 6 Verification:**
  - Evaluated on all $N=2,662$ validation records. Exact class support values ($1,662$ Entailment, $644$ Neutral, $356$ Contradiction) matched across all figures.

---

## 3. Denominator Audit Verdict

Every sample size, category denominator, and exclusion criterion across the 13 publication figures has been verified against the underlying datasets. All sample counts represent real, reproducible research cohorts.

