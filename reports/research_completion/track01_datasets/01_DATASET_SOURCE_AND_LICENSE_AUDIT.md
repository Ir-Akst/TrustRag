# TrustRAG Research Completion — Track 1, Step 1: Dataset Source & License Audit

**Date**: 2026-11-13  
**Branch**: `phase-11`  
**Repository**: `/home/aditya/rags/TrustRag-phase11`  

---

## 1. Overview

Research evaluation in TrustRAG must maintain strict legal and academic license compliance. Under no circumstances may evaluation-only datasets with restrictive terms (such as `CC-BY-ND` or proprietary research licenses) be commingled with neural model training pipelines.

This audit establishes the official origin, license type, usage permissions, and paper citation for each of the seven target benchmarks.

---

## 2. Dataset License and Usage Inventory

### 1. RAGTruth
- **Official Source**: `https://github.com/ParticleMedia/RAGTruth`
- **Citation**: Niu et al., "RAGTruth: A Hallucination Detection Benchmark for Retrieval-Augmented Generation", ACL/EMNLP 2024.
- **License**: MIT License
- **Permitted for Training**: YES (permissive open-source license allows research modeling and fine-tuning).
- **Permitted for Evaluation**: YES.
- **Notes**: Contains paired model responses across QA, Summarization, and Data-to-Text with word- and sentence-level hallucination span annotations.

### 2. HaluEval
- **Official Source**: `https://github.com/RUCAIBox/HaluEval` / `pminervini/HaluEval` (Hugging Face)
- **Citation**: Li et al., "HaluEval: A Large-Scale Hallucination Evaluation Benchmark for Large Language Models", EMNLP 2023.
- **License**: MIT License / Apache-2.0
- **Permitted for Training**: YES.
- **Permitted for Evaluation**: YES.
- **Notes**: 10,000 QA pairs generated via ChatGPT prompting paired with human-grounded Wikipedia passages, yielding 20,000 balanced evaluation claims (10,000 factual, 10,000 hallucinated).

### 3. HotpotQA
- **Official Source**: `https://huggingface.co/datasets/hotpotqa/hotpot_qa`
- **Citation**: Yang et al., "HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering", EMNLP 2018.
- **License**: Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA-4.0).
- **Permitted for Training**: YES (with attribution and copyleft preservation if derivatives are redistributed).
- **Permitted for Evaluation**: YES.
- **Notes**: Multi-hop question answering dataset requiring cross-document reasoning with explicit sentence-level supporting fact annotations.

### 4. MS MARCO
- **Official Source**: `https://huggingface.co/datasets/microsoft/ms_marco`
- **Citation**: Nguyen et al., "MS MARCO: A Human Generated MAchine Reading COmprehension Dataset", CoRR 2016.
- **License**: Microsoft Research License / CC-BY-4.0 (for dataset subsets).
- **Permitted for Training**: YES (Non-commercial research use).
- **Permitted for Evaluation**: YES.
- **Notes**: Large-scale real-world queries from Bing search logs with human-annotated answers and passage relevance labels.

### 5. Natural Questions (NQ)
- **Official Source**: `https://huggingface.co/datasets/google-research-datasets/natural_questions`
- **Citation**: Kwiatkowski et al., "Natural Questions: A Benchmark for Question Answering Research", TACL 2019.
- **License**: Creative Commons Attribution-ShareAlike 3.0 Unported (CC-BY-SA-3.0).
- **Permitted for Training**: YES.
- **Permitted for Evaluation**: YES.
- **Notes**: Canonical QA benchmark based on real Google search queries paired with full Wikipedia articles, annotated with long answers (paragraphs) and short answers.

### 6. LLM-AggreFact
- **Official Source**: `https://huggingface.co/datasets/lytang/LLM-AggreFact`
- **Citation**: Tang et al., "LLM-AggreFact: A Multi-Task Benchmark for Hallucination Detection in Large Language Models", 2024.
- **License**: Creative Commons Attribution-NoDerivatives 4.0 International (CC-BY-ND-4.0).
- **Permitted for Training**: **NO** (Strictly forbidden: CC-BY-ND prohibits the creation or distribution of derivative models trained on the dataset).
- **Permitted for Evaluation**: YES (Evaluation only; zero model parameter updates allowed).
- **Access Type**: **GATED** (Requires user to sign into Hugging Face Hub, accept agreement terms, and provide `HF_TOKEN`).

### 7. RSB (RAG Security Bench)
- **Official Source**: Academic paper arXiv:2505.18543 ("RAG Security Bench: Benchmarking Prompt Injection and Knowledge Poisoning Attacks in RAG Systems").
- **Citation**: Research pre-print arXiv:2505.18543 (2025).
- **License**: Pending verification (No public license text published yet).
- **Permitted for Training**: **NO** (Security attack records must not be leaked into training sets).
- **Permitted for Evaluation**: YES (Evaluation and adversarial robustness benchmarking only).
- **Access Type**: **LOCAL IMPORT ONLY** (No public canonical HF repo or direct download link exists; local import adapter provided).

---

## 3. Strict License Enforcement Policy

TrustRAG's `DatasetUsageValidator` (`src/trustrag/data/isolation.py`) automatically intercepts any dataset accessed during training workflows:
- If a dataset marked `permitted_for_training=False` (e.g. `LLM-AggreFact` or `RSB`) is passed to a training pipeline, a `UsageIsolationError` is raised immediately.
- This guarantees zero contamination of defense model weights by evaluation-only benchmarks.

