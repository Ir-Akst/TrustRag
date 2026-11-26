# TrustRAG Phase 17 — Independent Public Benchmark Audit: RAG Security Benchmark (RSB)

**Auditor:** Principal Research Engineer & Independent ML Security Auditor  
**Date:** 2026-11-19T01:00:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-17-20-final-release`  
**Benchmark Reference:** Zhang et al., "Benchmarking Poisoning Attacks against Retrieval-Augmented Generation", arXiv:2505.18543  
**Status:** **`BLOCKED`**  

---

## 1. Executive Summary & Audit Mandate

Phase 17 mandates evaluating TrustRAG against independent public RAG poisoning benchmarks. The primary target evaluated herein is the RAG Security Benchmark (RSB, arXiv:2505.18543), which catalogs 13 poisoning attacks and 7 defenses across varied RAG architectures.

Per the absolute safety rules:
> *"Never claim external benchmark validation if the benchmark was not actually downloaded and evaluated. If a benchmark cannot be accessed, classify it as BLOCKED and continue with other permitted tasks. Do not substitute synthetic data and call it external validation."*

---

## 2. Investigation of Authoritative Source & Repository Availability

1. **Academic Paper Specification:**
   - **Reference:** Zhang et al., May 2025 (arXiv:2505.18543).
   - **Scope:** 13 attack objectives covering corpus poisoning, dense retriever manipulation, trigger injections, and conflicting factual consensus.
   - **License:** Pending Verification / Academic Research Reference Only.
2. **Repository & Download URL Inspection:**
   - Inspection of `src/trustrag/data/acquisition/downloader.py` (lines 78–82 and 723–730) confirms:
     ```python
     "rsb": {
         "paper": "arXiv:2505.18543",
         "access": "LOCAL_IMPORT_ONLY",
         "license": "Pending Verification",
     }
     ...
     if dataset_name == "rsb":
         return {
             "dataset_name": dataset_name,
             "status": "ACCESS_BLOCKED",
             "reason": "No public direct download URL or canonical Hugging Face repository exists. Academic paper arXiv:2505.18543 requires local research artifact import.",
             "license": info["license"],
             "paper": info["paper"],
         }
     ```
   - Inspection of `src/trustrag/data/loaders/rsb.py` confirms that an adapter interface is provided for local file ingestion (`RSBAdapter`), but remote acquisition raises an explicit `AcquisitionError`.
3. **Local Filesystem Audit:**
   - Exhaustive recursive search across the host environment (`/home/aditya/rags` and `/home/aditya`) identified zero pre-cached RSB test corpora or evaluation splits.
4. **Environment Sandbox Boundary:**
   - External network downloads and unauthorized web scraping are prohibited by execution sandbox constraints and safety rules.

---

## 3. Scientific Audit Finding

Because no local RSB dataset files exist on disk, no unauthenticated direct public download URL is hosted, and external network downloads are disabled:
- **Evaluation Status:** **`BLOCKED`**
- **Evaluation Protocol:** In strict compliance with research ethics, no synthetic or internally generated datasets were renamed or substituted to simulate RSB validation.
- **Action Plan:** The blocker is formally documented. Independent evaluation proceeds to available public benchmarks (RAGTruth, HaluEval) and advanced security red teaming.

