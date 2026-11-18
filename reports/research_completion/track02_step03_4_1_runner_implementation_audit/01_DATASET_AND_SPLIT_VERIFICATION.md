# Track 2, Step 3.4.1 — Section 01: Dataset Selection and Sampling Audit

## 1. Ordering and Source Grouping Audit

An independent inspection of `data/processed/sft_v2/binary/train.jsonl` (26,054 records) revealed the physical line distribution:
- **Lines 1 to 13,982:** `halueval` (13,982 records)
  - Canonical right answers (`FACTUAL`): 6,991 records
  - Canonical hallucinated answers (`HALLUCINATED`): 6,991 records
- **Lines 13,983 to 26,054:** `ragtruth` (12,072 records)
  - `FACTUAL`: 6,707 records
  - `HALLUCINATED`: 5,365 records

### Adversarial Finding:
The preliminary Step 3.4 plan proposed taking lines 1–1,000 sequentially. While lines 1–1,000 are perfectly balanced (500 FACTUAL, 500 HALLUCINATED), they represent **100% HaluEval** and **0% RAGTruth**. A model trained exclusively on lines 1–1,000 would fail to learn evidence-grounding patterns specific to RAGTruth's multi-document summary and question-answering domains.

---

## 2. Engineered Sampling Strategies

To solve this without modifying the audited dataset files, the runner implements two deterministic selection modes:

### Strategy A: `stratified_source_balanced` (Default & Recommended)
- **Training Subset (1,000 examples):**
  - `halueval`: 500 examples (250 FACTUAL, 250 HALLUCINATED)
  - `ragtruth`: 500 examples (250 FACTUAL, 250 HALLUCINATED)
  - Total: **1,000 examples (500 FACTUAL, 500 HALLUCINATED)**
  - Source Balance: **50% HaluEval, 50% RAGTruth**
- **Validation Subset (200 examples):**
  - `halueval`: 100 examples (50 FACTUAL, 50 HALLUCINATED)
  - `ragtruth`: 100 examples (50 FACTUAL, 50 HALLUCINATED)
  - Total: **200 examples (100 FACTUAL, 100 HALLUCINATED)**
  - Source Balance: **50% HaluEval, 50% RAGTruth**

### Strategy B: `sequential` (Baseline Option)
- Selects the first N lines sequentially (Lines 1–1,000 from train; Lines 1–200 from val).
- Available via `--sampling-strategy sequential` if strict historical continuity with Step 3.3 is desired.

---

## 3. Leakage & Split Verification

- **ID Overlap:** Checked via `verify_split_isolation(train_records, val_records)`. Overlapping `example_id` values immediately raise `SecurityViolationError`.
- **Test Set Protection:** Target paths with `'test'` in the filename or records with `split='test'` are immediately rejected with `SecurityViolationError`.
