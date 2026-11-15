# TrustRAG Research Completion — Track 1, Step 1: Split & Label Analysis

**Date**: 2026-11-13  
**Branch**: `phase-11`  
**Repository**: `/home/aditya/rags/TrustRag-phase11`  

---

## 1. Partitioning Strategy and Methodology

Research integrity requires strict preservation of test-set isolation:
1. **Canonical Pre-existing Splits**: When a benchmark defines official train/test splits (e.g. RAGTruth), native split assignments are preserved verbatim.
2. **Deterministic Partitioning**: When a benchmark does not specify explicit splits (e.g. HaluEval), a cryptographically seeded PRNG (`seed=42`) partitions records into disjoint 70% train, 15% validation, and 15% test splits.
3. **Cross-Split Leakage Prevention**: Cross-split document overlap checks ensure that the same knowledge text does not appear simultaneously in both training and test sets.

---

## 2. Detailed Split Breakdown

### RAGTruth
- **Total Canonical Records**: 17,790
- **Train Split**: 15,090 records (84.8%)
- **Validation Split**: 0 records (Native RAGTruth does not specify a distinct validation set; evaluation scripts draw from test or fold from train).
- **Test Split**: 2,700 records (15.2%)
- **Task Distribution**:
  - Question Answering (QA): ~6,000 records
  - Summarization: ~6,000 records
  - Data-to-Text: ~5,790 records
- **Label Distribution**:
  - `FACTUAL`: 10,126 records (56.9%)
  - `HALLUCINATED`: 7,664 records (43.1%)

### HaluEval
- **Total Canonical Records**: 20,000 claims (from 10,000 QA pairs)
- **Train Split**: 14,000 claims (70.0% — 7,000 factual, 7,000 hallucinated)
- **Validation Split**: 3,000 claims (15.0% — 1,500 factual, 1,500 hallucinated)
- **Test Split**: 3,000 claims (15.0% — 1,500 factual, 1,500 hallucinated)
- **Label Balance**:
  - `FACTUAL`: 10,000 claims (50.0%)
  - `HALLUCINATED`: 10,000 claims (50.0%)
  - Perfectly balanced baseline for threshold calibration and F1 evaluation.

### HotpotQA
- **Validation Split (Distractor subset)**: 7,405 multi-hop questions.
- **Answer Coverage**: 100% of records contain gold answers.
- **Supporting Fact Coverage**: 100% of records contain annotated passage titles for verification.

### MS MARCO
- **Validation Split (v1.1 subset)**: 10,047 web queries.
- **Answer Coverage**: Queries with human reference answers.
- **Passage Context**: Multiple candidate passages per query for retrieval evaluation.

---

## 3. Class Imbalance and Statistical Controls

- **Hallucination Evaluation**:
  - RAGTruth features a natural class imbalance (56.9% factual vs 43.1% hallucinated), accurately reflecting real-world LLM output distributions.
  - HaluEval provides a controlled, synthetic 50/50 balance suitable for measuring receiver operating characteristic (ROC) curves and balanced accuracy.
- **Metric Recommendations for Track 2 & 3**:
  - Primary defense metric: `False SUPPORTED Rate (FSR)` on hallucinated claims (must be minimized toward 0.0%).
  - Secondary verification metric: `Balanced Accuracy` and `F1 Score` to ensure factual claims are not over-rejected.

