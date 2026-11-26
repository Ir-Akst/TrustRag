# TrustRAG Phase 11.2 — Step 06: Clean RAG Dataset Discovery & Forensic Inventory

**Author:** Senior ML Evaluation Engineer & Independent Research Auditor  
**Date:** 2026-11-18  
**Repository:** `/home/aditya/rags/TrustRag-phase11` — Branch `phase-11`  
**Target Model:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`

---

## 1. Executive Summary & Objective

The objective of Step 06 is to establish an independent, non-adversarial clean RAG benchmark containing at least 1,000 valid query-evidence evaluation pairs to assess the real-world generalization of TrustRAG's frozen DeBERTa-v3-small NLI detector.

This document records the forensic discovery and quality-gate analysis of all candidate datasets available in the environment, specifically evaluating whether QA relevance labels can be defensibly mapped to NLI entailment ground truth without violating scientific integrity rules.

---

## 2. Systematic Candidate Discovery Matrix

| Dataset Candidate | Local Repository Path | Usable Query Count | Format & Task Type | Original License | Trustworthy NLI Ground Truth? | Verdict |
| :--- | :--- | :---: | :--- | :--- | :---: | :--- |
| **Natural Questions (NQ)** | `/home/aditya/rags/data/raw/natural_questions/` | 0 (lock file only) | Real Google search queries + Wikipedia | CC BY-SA 3.0 | ❌ Unavailable in offline sandbox | **REJECTED (UNAVAILABLE)** |
| **MS MARCO v1.1** | `data/raw/ms_marco/ms_marco_val_v1.1.parquet` | 10,047 | Real Bing search queries + Web passages | Microsoft Research Non-Commercial | ❌ Passage relevance only; no formal NLI labels | **REJECTED FOR NLI GROUND TRUTH** |
| **HotpotQA** | `data/raw/hotpotqa/hotpotqa_val_distractor.parquet` | 7,405 | Multi-hop Wikipedia QA | CC BY-SA 4.0 | ❌ Supporting fact indices only; no NLI labels | **REJECTED FOR NLI GROUND TRUTH** |
| **HaluEval QA** | `data/processed/halueval/test.jsonl` | 3,000 | ChatGPT-generated QA with hallucinations | MIT | ❌ Conflates contradiction with unmentioned info | **EXCLUDED (SUPERVISION GAP)** |
| **Clean RAG Baseline** | `data/benchmarks/clean_rag/` | 10 total (7 train, 1 val, 2 test) | BoolQ reading comprehension | CC BY-SA 3.0 | ❌ Statistically unviable ($N=10$), QA answers only | **REJECTED (INSUFFICIENT SAMPLE SIZE)** |
| **RAGTruth Held-out Test Split** | `data/processed/ragtruth/test.jsonl` | **2,700 total (2,536 valid NLI)** | LLM RAG responses across News, QA, Bio | MIT | ✅ Human character-span annotations | **ACCEPTED AS PRIMARY BENCHMARK** |

---

## 3. Deep Forensic Analysis of Prioritized Candidates

### 3.1 Candidate 1: Natural Questions (Google Research)
- **Investigation:** A comprehensive search of `/home/aditya/rags/` located only an empty lock file (`data_raw_natural_questions_google-research-datasets___natural_questions_default_0.0.0_...lock`).
- **Data Availability:** Zero raw records are cached or downloaded.
- **Offline Restriction:** Under strict audit constraints ("No external package installation or external downloads"), acquiring Natural Questions from external HuggingFace servers during this session is prohibited.
- **Finding:** Natural Questions is unavailable locally.

---

### 3.2 Candidate 2: MS MARCO (Microsoft Machine Reading Comprehension)
- **Local Path:** `/home/aditya/rags/TrustRag-phase11/data/raw/ms_marco/ms_marco_val_v1.1.parquet` (21.4 MB).
- **Volume:** 10,047 validation queries with 6–10 candidate passages each (~60,000 total passages).
- **Provenance & Nature:** Real-world non-adversarial Bing user queries paired with web-crawled passages.
- **Annotation Structure:**
  - `is_selected`: Binary flag ($1$ if human annotators selected the passage as containing the answer; $0$ otherwise).
  - `answers`: Free-form answer string authored by human annotators.
- **Audit of NLI Transferability (Relevance $\neq$ Entailment):**
  - *Audit Mandate:* "Do not claim that QA relevance labels automatically constitute NLI entailment labels. Do not infer that every relevant passage entails every answer claim."
  - *Failure Mode 1 (Selected Passages):* An annotator-selected passage (`is_selected == 1`) frequently contains only the core factual answer entity, while the human-authored answer includes conversational framing or commonsense synthesis not entailed by the passage.
  - *Failure Mode 2 (Unselected Passages):* A passage marked `is_selected == 0` is not guaranteed to be `NEUTRAL`. It may be:
    1. A redundant passage containing the exact same fact (annotator skipped it).
    2. A conflicting passage with differing numbers or dates (active `CONTRADICTION`).
    3. An irrelevant or unmentioned passage (`NEUTRAL`).
  - *Conclusion:* Automatically mapping `is_selected == 1` to `ENTAILMENT` and `is_selected == 0` to `NEUTRAL` constitutes pseudo-label fabrication and violates scientific audit standards. MS MARCO cannot serve as an NLI ground-truth benchmark without a dedicated human re-annotation campaign.

---

### 3.3 Candidate 3: HotpotQA Distractor Benchmark
- **Local Path:** `data/raw/hotpotqa/hotpotqa_val_distractor.parquet` (27.5 MB).
- **Volume:** 7,405 multi-hop questions.
- **Annotation Structure:** Annotations identify `supporting_facts` (sentences necessary for multi-hop reasoning) alongside distractor Wikipedia paragraphs.
- **Audit Finding:** Identical to MS MARCO: multi-hop sentence relevance does not equate to formal sentence-level directional entailment. Distractor paragraphs cannot be assumed neutral without verification.

---

### 3.4 Candidate 4: HaluEval QA Benchmark
- **Local Path:** `data/processed/halueval/test.jsonl` (3,000 samples).
- **Previous Audit Status:** Formally audited in Phase 11 Track 2 Step 2.2 (`G3_SUPERVISION_GAP_REPORT.md`).
- **Supervision Deficit:** HaluEval was synthesized via ChatGPT-based perturbation, frequently generating samples that blend unmentioned entity insertions with subtle factual conflicts. It lacks span-level human verification to distinguish pure Neutral from pure Contradiction.
- **Audit Finding:** Excluded to preserve 3-way NLI semantic integrity.

---

### 3.5 Candidate 5: RAGTruth Independent Held-out Test Split
- **Local Path:** `/home/aditya/rags/TrustRag-phase11/data/processed/ragtruth/test.jsonl` (16.9 MB).
- **Volume:** 2,700 total generation records across CNN/DailyMail (Summarization), PubMed (Bio-QA), and COVID-19 QA.
- **Provenance:** RAGTruth benchmark developed by ParticleMedia (published at ACL/EMNLP 2024).
- **Annotation Quality:** Exhaustive, character-level human span annotations by multiple independent trained raters with reported Fleiss' Kappa inter-annotator agreement $> 0.65$.
- **Independence & Contamination Audit:**
  - Phase 11.1 NLI training and validation splits (`data/processed/sft_v2/nli/train.jsonl` and `validation.jsonl`) were derived **strictly and exclusively** from `data/processed/ragtruth/train.jsonl`.
  - Forensic document hash matching verified:
    - Overlap with `sft_v2/nli/train.jsonl`: **0 documents (0.00%)**.
    - Overlap with `sft_v2/nli/validation.jsonl`: **0 documents (0.00%)**.
  - All 450 source documents in `ragtruth/test.jsonl` are completely disjoint from the training corpus.
- **Usable Evaluation Pairs:**
  - Filtering out 164 mixed cases (containing both conflict and baseless spans simultaneously) yields **2,536 valid 3-way NLI evaluation pairs**:
    - **`ENTAILMENT` (Human-verified Factual):** **1,757 pairs**
    - **`NEUTRAL` (Human-verified Baseless Info, no conflict):** **474 pairs**
    - **`CONTRADICTION` (Human-verified Semantic Conflict):** **305 pairs**
  - **Clean Evidence Pairs:** $1,757 + 474 = \mathbf{2,231}$ clean evidence evaluation pairs (substantially exceeding the $\ge 1,000$ target).

---

## 4. Benchmark Selection Conclusion

The **RAGTruth Independent Held-out Test Split** is formally selected as the authoritative clean RAG benchmark for Phase 11.2 Step 06. It satisfies every quality, licensing, independence, and human-ground-truth requirement, providing 2,231 clean evidence pairs and 305 contradiction control pairs on completely unseen source documents.

