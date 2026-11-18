# TrustRAG Research Completion — Track 1, Step 1: Blocked Datasets Audit

**Date**: 2026-11-13  
**Branch**: `phase-11`  
**Repository**: `/home/aditya/rags/TrustRag-phase11`  

---

## 1. Principles of Honest Reporting

In accordance with strict research integrity standards:
- **No Mock Metrics**: TrustRAG never reports synthetic numbers or fabricated performance when a dataset is absent or blocked.
- **Explicit Block Classification**: If an external benchmark cannot be downloaded due to licensing gates, missing repositories, or environmental limits, its status is explicitly reported as `ACCESS_BLOCKED` or `NOT DOWNLOADED`.

---

## 2. Blocked Dataset Diagnostics

### 1. LLM-AggreFact
- **Status**: `ACCESS BLOCKED`
- **Official Repository**: `https://huggingface.co/datasets/lytang/LLM-AggreFact`
- **License**: Creative Commons Attribution-NoDerivatives 4.0 International (CC-BY-ND-4.0)
- **Root Cause**:
  1. The repository is configured as **GATED** on the Hugging Face Hub.
  2. Access requires an authenticated Hugging Face account to accept the data use agreement on the web portal.
  3. Automated API requests without a valid `HF_TOKEN` environment variable return HTTP 401/403.
- **Usage Restrictions**:
  - CC-BY-ND explicitly forbids derivative works.
  - The dataset cannot be used for fine-tuning or neural training; it is restricted to evaluation only.
- **Unblocking Instructions**:
  1. Navigate to `https://huggingface.co/datasets/lytang/LLM-AggreFact`.
  2. Log in and submit the access request agreement.
  3. Export your token in the local shell: `export HF_TOKEN="hf_..."`.
  4. Run `trustrag acquire llm_aggrefact`.

---

### 2. RSB (RAG Security Bench)
- **Status**: `ACCESS BLOCKED`
- **Reference**: arXiv:2505.18543 ("RAG Security Bench")
- **License**: Pending verification
- **Root Cause**:
  1. No public, canonical Hugging Face repository or direct download URL exists for RSB.
  2. The benchmark authors have released the methodology via preprint, but canonical data distribution remains pending.
- **Usage Restrictions**:
  - Evaluation and adversarial robustness testing only; forbidden for neural training.
- **Unblocking Instructions**:
  1. When research collaborators or paper authors provide the official JSONL data files, import them locally using:
     ```python
     from trustrag.data.acquisition.local import LocalFileImporter
     importer = LocalFileImporter(raw_base_dir="data/raw/rsb")
     importer.import_file("path/to/rsb_attack_records.jsonl", dataset_name="rsb")
     ```
  2. The implemented `RSBAdapter` will automatically validate and transform imported records into `SecurityRecord` objects.

---

### 3. Natural Questions (NQ) — Deferred Download
- **Status**: `NOT DOWNLOADED`
- **Official Repository**: `https://huggingface.co/datasets/google-research-datasets/natural_questions`
- **License**: CC-BY-SA-3.0
- **Reason for Deferral**:
  - Full canonical train set comprises 287 parquet shards totaling ~40 GB compressed.
  - Validation set comprises 7,830 examples in 9 parquet shards totaling ~1.2 GB compressed.
  - Due to environment disk and bandwidth limits, automatic bulk acquisition of full NQ was deferred in Step 1.
- **Adapter Readiness**:
  - `NaturalQuestionsAdapter` is fully implemented and tested with streaming support and local file import capabilities.

