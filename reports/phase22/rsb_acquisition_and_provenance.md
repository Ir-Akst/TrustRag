# TrustRAG Phase 22 — RSB Benchmark Acquisition and Provenance Record

**Author:** Principal ML Research Scientist & Benchmark Evaluation Engineer  
**Date:** 2026-11-24  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Working Branch:** `phase-22-external-benchmark-validation`  
**Deliverable:** `reports/phase22/rsb_acquisition_and_provenance.md`  

---

## 1. Executive Summary & Benchmark Overview

The **RAG Security Benchmark (RSB)**, established in Zhang et al., *"Benchmarking Poisoning Attacks against Retrieval-Augmented Generation"* (arXiv:2505.18543), is officially instantiated and distributed via the open-source **PoisonArena** benchmarking suite (`yxf203/PoisonArena`).

In Phase 21, RSB was marked `BLOCKED` due to lack of local staging. In Phase 22, the complete authentic benchmark repository was cloned, verified, and integrated into TrustRAG's local evaluation pipeline without synthetic substitution or schema corruption.

---

## 2. Provenance & Dataset Specifications

- **Official Paper:** Zhang et al., *"Benchmarking Poisoning Attacks against Retrieval-Augmented Generation"*, arXiv:2505.18543 (May 2025).
- **Official Repository:** `https://github.com/yxf203/PoisonArena.git`
- **Acquisition Commit:** `2dc04a2`
- **Acquisition Timestamp:** `2026-11-24T04:15:00Z`
- **License:** Academic Research / Open Source
- **Local Staging Path:** `data/raw/external_benchmarks/PoisonArena/datasets/`
- **Preserved Artifacts:**
  - `datasets/incorrect_ans/ms-selected-queries-adv-ans-docs.json` (SHA-256: `9fa733d0774a38e8ba02a46e16ad724d29f86cf5d5db912803b9ad7f5f2fe4e8`)
  - `datasets/incorrect_ans/nq-all-adv-docs.json` (SHA-256: `81baae663a87cb51a31d9961d7a31ff6f125a25032ae8b1d98bc6b59364ea5f9`)

---

## 3. Dataset Composition & Split Details

| Split / Corpus | Total Queries | Attacks Evaluated | Benign Golden Docs | Adv Texts per Query | Total Test Records |
|---|:---:|:---:|:---:|:---:|:---:|
| **RSB MS-MARCO** | 100 | 100 | 100 | 5 | 600 passages |
| **RSB Natural Questions (NQ)** | 100 | 100 | 100 | 5 | 600 passages |
| **TOTAL RSB SUITE** | **200** | **200** | **200** | **5** | **1,200 passages** |

Each record contains:
1. `question`: Authentic benchmark user query.
2. `correct answer`: Ground truth factual answer.
3. `golden_docs`: Authoritative clean documents establishing consensus.
4. `all_adv_docs`: List of adversarial injection attacks, specifying `incorrect_answer` and 5 optimized `adv_texts`.

---

## 4. Integrity and Preprocessing Protocol

- **Zero Content Modification:** Raw benchmark files remain bit-for-bit identical to upstream repository contents.
- **Deterministic Adapter:** TrustRAG maps authentic records into `SecurityRecord` objects via `src/trustrag/data/loaders/rsb.py`, preserving all original IDs, query text, and labels.
- **Acquisition Verdict:** **SUCCESSFULLY ACQUIRED & VERIFIED.**
