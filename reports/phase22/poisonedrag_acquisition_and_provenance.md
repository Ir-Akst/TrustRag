# TrustRAG Phase 22 — PoisonedRAG Benchmark Acquisition and Provenance Record

**Author:** Principal ML Research Scientist & Benchmark Evaluation Engineer  
**Date:** 2026-11-24  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Working Branch:** `phase-22-external-benchmark-validation`  
**Deliverable:** `reports/phase22/poisonedrag_acquisition_and_provenance.md`  

---

## 1. Executive Summary & Benchmark Overview

**PoisonedRAG** represents the landmark academic study of knowledge corruption attacks against Retrieval-Augmented Generation, presented at **USENIX Security 2025** (Zou et al., arXiv:2402.07867).

In Phase 21, PoisonedRAG was classified as `BLOCKED` due to execution sandbox boundaries. In Phase 22, the official author repository was acquired, verified, and integrated into TrustRAG's local evaluation pipeline.

---

## 2. Provenance & Dataset Specifications

- **Official Paper:** Zou et al., *"PoisonedRAG: Knowledge Corruption Attacks to Retrieval-Augmented Generation of Large Language Models"*, USENIX Security 2025 (arXiv:2402.07867).
- **Official Repository:** `https://github.com/sleeepeer/PoisonedRAG.git`
- **Acquisition Commit:** `69894e6`
- **Acquisition Timestamp:** `2026-11-24T04:13:50Z`
- **License:** MIT License (confirmed in `PoisonedRAG/LICENSE`)
- **Local Staging Path:** `data/raw/external_benchmarks/PoisonedRAG/results/adv_targeted_results/`
- **Preserved Artifacts:**
  - `hotpotqa.json` ($N=100$) (SHA-256: `64a7c126ec865bb6d0ad2eaefceb235e16ca61f67f08caee8542013824f1dc0b`)
  - `msmarco.json` ($N=100$) (SHA-256: `7d06637eefea902fbc13fae0aa4e4e96c429bb70a48a946280aa3cb4525d8001`)
  - `nq.json` ($N=100$) (SHA-256: `186594c7b8d4bb9f257d079ebfae859b665dfb1e428ab7756f76a086ea116669`)

---

## 3. Dataset Composition & Attack Taxonomy

| Benchmark Split | Target Queries ($N$) | Adv Texts per Query | Ground Truth Answers | Target Poisoned Answers | Total Adv Passages |
|---|:---:|:---:|:---:|:---:|:---:|
| **PoisonedRAG HotpotQA** | 100 | 5 | 100 | 100 | 500 |
| **PoisonedRAG MS-MARCO** | 100 | 5 | 100 | 100 | 500 |
| **PoisonedRAG NQ** | 100 | 5 | 100 | 100 | 500 |
| **TOTAL POISONEDRAG SUITE** | **300** | **5** | **300** | **300** | **1,500** |

Attack Properties:
1. **Target Query Selection:** Realistic user questions spanning multi-hop QA (HotpotQA), open-domain web search (MS-MARCO), and factual knowledge (NQ).
2. **Attacker-Chosen Target Answer:** Misinformation asserting false historical, numerical, or entity facts.
3. **Black-box Optimization:** Iterative adversarial text generation designed to maximize retriever dot-product ranking while retaining fluent English syntax.

---

## 4. Integrity Verdict

- **Authenticity:** All 300 test queries and 1,500 adversarial passages originate directly from the authors' official research distribution.
- **Zero Synthetic Replacement:** No replacement queries or fabricated attacks were introduced.
- **Acquisition Verdict:** **SUCCESSFULLY ACQUIRED & VERIFIED.**
