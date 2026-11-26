# TrustRAG Phase 21 — External Benchmark Evaluation: RAG Security Benchmark (RSB)

**Auditor:** Principal Research Scientist & Independent ML Security Auditor  
**Date:** 2026-11-24  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Working Branch:** `phase-21-final-research-validation`  
**Paper Reference:** Zhang et al., "Benchmarking Poisoning Attacks against Retrieval-Augmented Generation", arXiv:2505.18543, May 2025  
**Canonical Status:** **`BLOCKED`** (Strictly Read-Only Environment Boundary)  

---

## 1. Executive Summary & Research Policy

Under the strict ethical and scientific integrity rules governing Phase 21:
> *"Never claim external benchmark validation if the benchmark was not actually downloaded and evaluated. If a benchmark cannot be accessed, classify it as BLOCKED and continue with other permitted tasks. Do not substitute synthetic data and call it external validation."*

This audit formally records that the **RAG Security Benchmark (RSB)** remains classified as **`BLOCKED`**. While its threat model and formal test harness have been analyzed theoretically, zero empirical predictions or synthetic approximations are substituted.

---

## 2. Benchmark Architecture & Threat Model

### 2.1 Overview of RSB (arXiv:2505.18543)
The RAG Security Benchmark provides the first comprehensive empirical framework evaluating 13 knowledge poisoning and retrieval manipulation attacks across dense, sparse, and hybrid RAG systems. It covers:
1. **Corpus Poisoning:** Injecting conflicting factual assertions into static vector stores.
2. **Dense Retriever Inversion:** Gradient-based token optimization targeting dual-encoder dot products (e.g., DPR, Contriever).
3. **Trigger-Activated Injections:** Embedding backdoor trigger tokens that force deterministic passage retrieval on specified keywords.
4. **Majority Consensus Dilution:** Flooding top-$K$ retrieval pools with multi-source synthetic consensus.

### 2.2 Theoretical Interaction with TrustRAG Architecture

| RSB Threat Vector | Attack Mechanism | TrustRAG Defense Layer | Theoretical Outcome & Limitations |
|---|---|---|---|
| **Query Injection Attacks** | Direct user prompt override | **G1: Input Guardrail** | **High Resilience:** Lexical and semantic intent classifiers detect directive hijacking before retrieval occurs. |
| **Corpus Knowledge Poisoning** | Adversarial passage injected into index | **G2: Multi-Signal Detector** | **High Resilience:** Unverified sources are quarantined by domain tiering ($S_1$) and consensus deviation ($S_5$). |
| **Sybil Consensus Attacks** | Multiple colluding sources echoing a false fact | **G2 Removal Cap ($C_r = 0.50$)** | **Theoretical Failure:** If adversarial passages exceed $50\%$ of the retrieved pool, G2's removal cap permits malicious content to reach the LLM. |
| **Paraphrased Contradiction** | Smooth linguistic paraphrasing of false claims | **G3: DeBERTa NLI Verifier** | **Moderate Failure:** DeBERTa's $25.28\%$ contradiction recall permits subtle paraphrased contradictions to pass unflagged. |

---

## 3. Forensic Investigation of Inaccessibility

1. **Local Filesystem Verification:**
   - Evaluated `/home/aditya/rags/TrustRag-phase11/data/raw/` and `src/trustrag/data/acquisition/downloader.py`.
   - Confirmed no pre-staged clone or local tarball of RSB exists on the system.
2. **Network Sandbox Boundary:**
   - Standard execution environments are sandboxed without external internet access.
   - Remote repository fetching (`git clone`) or Hugging Face dataset downloads cannot execute.
3. **Scientific Integrity Mandate:**
   - In accordance with academic reproducibility standards, TrustRAG declines to generate synthetic surrogate data or mock evaluation outputs. RSB evaluation is formally declared `BLOCKED` pending future offline dataset import.
