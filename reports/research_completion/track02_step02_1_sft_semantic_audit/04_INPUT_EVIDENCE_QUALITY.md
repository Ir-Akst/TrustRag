# TrustRAG Track 2, Step 2.1: Input and Evidence Quality Audit Report

## 1. Audit Methodology

This report evaluates the syntactic completeness, linguistic integrity, and input-target isolation of all 32,090 records in `data/processed/sft_v1/`.

The audit inspected:
- Field completeness across `example_id`, `source_dataset`, `source_id`, `split`, `question_or_claim`, `context_or_evidence`, `candidate_response`, `ground_truth_label`, `target`, and `target_provenance`.
- Length distributions and potential truncation anomalies.
- Target leakage: whether label indicators (e.g. `"SUPPORTED"`, `"CONTRADICTED"`, `"GROUNDED"`, `"HALLUCINATED"`) or serialized JSON targets were leaked into model input fields.
- Duplicate and near-duplicate instances.

---

## 2. Field Completeness and Missing Value Census

Every line of `data/processed/sft_v1/train.jsonl` (26,072 lines) and `data/processed/sft_v1/validation.jsonl` (6,018 lines) was parsed using strict JSON decoders:

| Field Checked | Train Missing Count | Val Missing Count | Train Empty String Count | Val Empty String Count | Compliance Rate |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `example_id` | 0 | 0 | 0 | 0 | 100.00% |
| `source_dataset` | 0 | 0 | 0 | 0 | 100.00% |
| `source_id` | 0 | 0 | 0 | 0 | 100.00% |
| `split` | 0 | 0 | 0 | 0 | 100.00% |
| `question_or_claim` | 0 | 0 | 0 | 0 | 100.00% |
| `context_or_evidence`| 0 | 0 | 0 | 0 | 100.00% |
| `candidate_response` | 0 | 0 | 0 | 0 | 100.00% |
| `ground_truth_label` | 0 | 0 | 0 | 0 | 100.00% |
| `target` | 0 | 0 | 0 | 0 | 100.00% |
| `target_provenance` | 0 | 0 | 0 | 0 | 100.00% |

**Auditor Finding:** **Zero missing, null, or empty fields across all 32,090 records.**

---

## 3. Length Distribution & Truncation Inspection

Character length distributions across input components:

| Component | Split | Minimum Chars | Mean Chars | Median Chars | Maximum Chars | Truncation Risk |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Question / Prompt** | Train | 20 | 1,244.8 | 1,120 | 10,709 | None (Prompts intact) |
| **Question / Prompt** | Validation | 22 | 1,399.6 | 1,180 | 10,719 | None |
| **Context / Evidence** | Train | 75 | 1,273.1 | 1,142 | 10,654 | None (Articles intact) |
| **Context / Evidence** | Validation | 89 | 1,413.4 | 1,201 | 10,664 | None |
| **Candidate Response** | Train | 1 | 392.7 | 312 | 4,007 | 1 short outlier |
| **Candidate Response** | Validation | 2 | 421.2 | 340 | 2,334 | None |

### Outlier Inspection: Minimum Candidate Length
In training, a single record (`sft_ragtruth_train_ragtruth_14201`) has a candidate response length of 1 character:
- *Candidate:* `"."`
- *Context:* Full news article.
- *Source Task:* Abstractive summarization where the generating model produced a degenerate single period.
- *Annotator Annotation:* Annotated with empty span (factual/empty generation).

---

## 4. Input-Target Leakage Verification

An adversarial scan was performed across all `question_or_claim`, `context_or_evidence`, and `candidate_response` fields to detect accidental label leakage:

| Potential Leakage Pattern | Occurrences in Train Inputs | Occurrences in Val Inputs | Leakage Detected? |
| :--- | :---: | :---: | :---: |
| `"verdict":` | 0 | 0 | **NO** |
| `"grounding_status":` | 0 | 0 | **NO** |
| `"GROUNDED"` | 0 | 0 | **NO** |
| `"HALLUCINATED"` | 0 | 0 | **NO** |
| Target JSON serialization leaks | 0 | 0 | **NO** |
| Preprocessor metadata tags (`__label__`, etc.) | 0 | 0 | **NO** |

**Auditor Finding:** **Zero label leakage.** Model inputs do not contain preprocessor metadata or hints regarding target classification.

---

## 5. Duplicate and Near-Duplicate Analysis

### 5.1 Full Record Duplicates
- Full record duplicate check: **0 duplicates across all 32,090 records.** Every record is distinct in its metadata, identifiers, and annotations.

### 5.2 Content Triplet Duplicates `(question, context, candidate)`
- **Train Split:** 26,027 unique triplets out of 26,072 records (38 duplicate triplet groups involving 83 records).
- **Validation Split:** 6,003 unique triplets out of 6,018 records (15 duplicate triplet groups involving 30 records).

### Investigation of Duplicate Triplets
- *Root Cause:* In RAGTruth, the benchmark creators evaluated multiple distinct large language models (e.g. GPT-4, Claude-2, LLaMA-2-70B) on identical prompts and source documents. In several cases, multiple models generated identical responses (e.g. *"Unable to answer based on given passages."* or standard summary openings).
- *Auditor Assessment:* These are legitimate, distinct model evaluation records from the upstream benchmark, correctly assigned unique `example_id`s (`ragtruth_12427` vs `ragtruth_12428`). They do not represent preprocessor duplication bugs.

