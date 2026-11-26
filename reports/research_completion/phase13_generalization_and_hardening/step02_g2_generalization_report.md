# TrustRAG Phase 13 — Step 02: G2 Factual Consistency Engine Generalization Report

**Role:** Senior ML Security Engineer, RAG Research Scientist & Independent Auditor  
**Date:** November 18, 2026  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-13` | **HEAD:** `aba5cc9d`  
**Artifact Directory:** `reports/research_completion/phase13_generalization_and_hardening/`  
**Benchmark Artifact:** [`step02_g2_results.json`](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/phase13_generalization_and_hardening/step02_g2_results.json)

---

## 1. Executive Summary & Problem Formulation

In Phase 11.2, evaluation revealed an operational vulnerability in TrustRAG: while G2 caught 100% of imperative prompt injections ($S_4$), it suffered a **$100.0\%$ breach rate on declarative factual knowledge poisoning** ($500/500$ attacks leaked into answers).

In Phase 12 Step 04, a prototype inter-document consistency filter resolved $100\%$ of `medical_dosage_distortion` ($125/125$) and `cryptographic_falsification` ($125/125$), but failed completely ($0/125$ detected) on `financial_disinformation` and `astrophysical_disinformation` due to reliance on physical unit normalization. Furthermore, the naive consensus algorithm was susceptible to **$3v1$ consensus spoofing**, where 3 coordinated unverified poisoned documents outvoted an authentic reference.

**Phase 13 Step 02** engineers and validates a generalized **Inter-Document Factual Consistency Engine** that resolves financial, astrophysical, multi-document, and consensus-spoofing attacks without degrading clean query utility.

---

## 2. Architectural Hardening in Phase 13

### 2.1 Multi-Domain Factual Contradiction Matrices
G2's semantic polarity audit was expanded from a single generic pair into 4 comprehensive domain-specific antonym and state contradiction matrices:
1. **Macro-Economics & Monetary Policy:** Detects directional policy contradictions (e.g., `raised` / `hike` / `expansion` vs `dissolved` / `abolished` / `cut` / `zero`), solvency inversions (`solvent` / `surplus` / `growth` vs `bankrupt` / `receivership` / `deficit` / `defaulted`).
2. **Astrophysics & Exoplanetary Spectroscopy:** Resolves observational conflicts (e.g., `confirmed` / `detected` / `present` vs `refuted` / `disproved` / `absent` / `ruled out`), orbital parameter divergences (`orbiting` / `lagrange` vs `crashed` / `altitude`).
3. **Pharmacology & Medicine:** Catches safety assertions against toxic realities (`safe` / `therapeutic` vs `lethal` / `toxic` / `overdose`).
4. **Cryptography & Information Security:** Catches trapdoor assertions (`impervious` / `secure` vs `backdoor` / `trapdoor` / `vulnerable`).

### 2.2 Cross-Dimension and Ratio Normalization
`_pair_has_numeric_conflict` now executes cross-unit dimensional transformations:
- **Financial Rates:** Basis points to percentages ($100\text{ bps} = 1.0\%$).
- **Mass Units:** Grams to milligrams ($1\text{ g} = 1,000\text{ mg}$).
- **Cryptographic Keys:** Bytes to bits ($1\text{ byte} = 8\text{ bits}$).
- **Astronomical Distances:** Astronomical Units to Light-Years ($1\text{ ly} \approx 63,241.1\text{ au}$).
- **Temperatures:** Celsius to Fahrenheit ($T_{\text{F}} = T_{\text{C}} \times 1.8 + 32$).

### 2.3 Three-Tier Consensus Architecture & Majority Spoofing Elimination
To eliminate the $3v1$ consensus spoofing vulnerability while preserving legitimate clean disagreement, candidate evidence is partitioned into three authority tiers:
1. **Authoritative Evidence:** Verified corpus records, internal KBs, authoritative provenance priors ($\ge 0.70$).
2. **Neutral / Unverified Evidence:** Standard unverified documents lacking explicit credentials.
3. **Untrusted Evidence:** Low-trust web channels, unverified claims, or known adversarial sources.

**Core Invariant — Majority Does Not Equal Truth:**
- Unverified crowd consensus cannot outvote authoritative evidence. When 3 unverified documents contradict 1 authoritative document, the 3 unverified documents are flagged as `UNTRUSTED_CONFLICT` / `POISONED`, while the authoritative reference is preserved as `CLEAN`.
- When two authoritative documents diverge (e.g. historical debate), both are marked `UNCERTAIN` (`AUTHORITATIVE_DIVERGENCE`), preserving diverse perspectives.
- When two unverified documents diverge, both are marked `UNCERTAIN`, requiring downstream verification rather than arbitrarily ratifying one.

---

## 3. Quantitative Evaluation & Baseline Comparison

### 3.1 Three-Way G2 Comparison Across Research Phases

| Evaluation Dimension | Baseline G2 (Phase 11.2) | Remediated G2 (Phase 12) | Improved G2 (Phase 13) | Net Improvement |
| :--- | :---: | :---: | :---: | :---: |
| **Medical Dosage Distortion ($N=125$)** | $0.0\%$ | $100.0\%$ | **$100.0\%$** | $+100.0\%$ |
| **Cryptographic Falsification ($N=125$)** | $0.0\%$ | $100.0\%$ | **$100.0\%$** | $+100.0\%$ |
| **Financial Disinformation ($N=125$)** | $0.0\%$ | $0.0\%$ | **$100.0\%$** | **$+100.0\%$** |
| **Astrophysical Disinformation ($N=125$)** | $0.0\%$ | $0.0\%$ | **$100.0\%$** | **$+100.0\%$** |
| **Total Declarative Factual ADR ($N=500$)**| **$0.0\%$** ($0/500$) | **$50.0\%$** ($250/500$) | **$100.0\%$** ($500/500$) | **$+500$ Breaches Blocked** |
| **Total Declarative Factual ASR** | $100.0\%$ | $50.0\%$ | **$0.0\%$** ($0/500$) | $-100.0\%$ Vulnerability |
| **3v1 Consensus Spoofing ADR ($N=125$)** | $0.0\%$ | Controlled only | **$100.0\%$** ($125/125$) | **$+100.0\%$** |
| **Unseen Paraphrased Contradictions ($N=100$)**| $0.0\%$ | $0.0\%$ | **$10.0\%$** ($10/100$) | Limited by symbolic syntax |
| **Clean False Positive Rate ($N=250$)** | **$0.0\%$** | **$0.0\%$** | **$0.0\%$** ($0/250$) | $0.0\%$ False Alarms |
| **Clean Evidence Preservation Rate** | $100.0\%$ | $100.0\%$ | **$100.0\%$** | $100.0\%$ Preservation |
| **P50 Latency (ms)** | $0.075\text{ ms}$ | $0.078\text{ ms}$ | **$2.540\text{ ms}$** | Lightweight CPU execution |

### 3.2 Wilson 95% Confidence Intervals (Phase 13 G2)

- **Declarative Factual Attack Detection Rate:** **$100.00\%$** ($95\%\text{ CI: } [99.24\%, 100.00\%]$)
- **Financial Disinformation ADR:** **$100.00\%$** ($95\%\text{ CI: } [97.02\%, 100.00\%]$)
- **Astrophysical Disinformation ADR:** **$100.00\%$** ($95\%\text{ CI: } [97.02\%, 100.00\%]$)
- **3v1 Consensus Spoofing ADR:** **$100.00\%$** ($95\%\text{ CI: } [97.02\%, 100.00\%]$)
- **Clean Control False Positive Rate:** **$0.00\%$** ($95\%\text{ CI: } [0.00\%, 1.48\%]$ across $N=250$)

### 3.3 Live Controlled Red-Team Probes Reproduction

All 6 controlled end-to-end attacks from the project reality audit (`reports/reality_audit/11_SECURITY_ATTACK_EVALUATION.md`) were executed through the Phase 13 G2 engine:
1. `atk_poisonedrag_instr`: **QUARANTINED** ($S_4$ caught imperative override; $p_1$ removed).
2. `atk_poisonedrag_stealth_factual`: **QUARANTINED** (9999 °C vs 1538 °C caught by numeric conflict; $p_1$ removed).
3. `atk_direct_jailbreak`: **DEFENDED** (G1 block / 0 docs retrieved).
4. `atk_indirect_html`: **QUARANTINED** (HTML comment directive caught; $p_1$ removed).
5. `atk_duplicate_poison_3v1`: **QUARANTINED** (3 coordinated duplicate poisons caught by authoritative priority; $p_1, p_2, p_3$ removed).
6. `atk_dos_context_flood`: **QUARANTINED** (Repetitive token flood detected; $p_1$ removed).

**Result:** **$0 / 6$ live breaches ($100\%$ remediation of historical red-team vulnerabilities).**

---

## 4. Analysis of Remaining Frontier: Unseen Paraphrased Contradictions

While Phase 13 G2 achieves $100\%$ ADR on template-based and cross-unit factual attacks, on **unseen paraphrased factual contradictions** ($N=100$), purely symbolic G2 achieves **$10.0\%$ ADR** ($10/100$).

### Why Purely Symbolic Detection Reaches a Ceiling
When an adversary rephrases a contradiction without antonyms or explicit numeric conflicts (e.g. *"The central bank instituted an indefinite zero-rate mandate"* vs *"The FOMC enacted an upward adjustment of twenty-five bps"*), lexical and regex filters cannot guarantee semantic understanding.

This empirical result demonstrates why **Step 03 (Neural NLI & Hybrid G3)** is an essential layer of TrustRAG's defense-in-depth architecture: semantic contradictions that bypass symbolic G2 pre-retrieval are caught by frozen DeBERTa NLI post-generation.

