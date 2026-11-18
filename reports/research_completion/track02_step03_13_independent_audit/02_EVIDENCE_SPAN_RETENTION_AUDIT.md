# TrustRAG — Track 2, Step 3.13: Evidence-Span Retention Audit

- **Validation Corpus:** `data/processed/sft_v2/nli/validation.jsonl` (2,662 records)
- **Ground Truth Source:** `data/processed/ragtruth/train.jsonl` (15,090 human-annotated records)
- **Population with Spans:** Exactly 1,000 validation records contain 1,482 annotated hallucination/conflict spans.

---

### 1. Independent Span Retention Recomputation

The auditor independently recomputed span survival across sequence lengths:

| Sequence Length | Fully Preserved Spans | Fully Preserved % | Partially Preserved Spans | Completely Lost Spans | Completely Lost % | Kept Span Tokens / Total | Token Retention % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MaxLen 128 (Step 3.8 Baseline)** | 410 / 1,482 | **27.67%** | 127 (8.57%) | 945 / 1,482 | **63.77%** | 4,846 / 19,383 | **25.00%** |
| **MaxLen 256** | 1,324 / 1,482 | **89.34%** | 45 (3.04%) | 113 / 1,482 | **7.62%** | 16,575 / 19,383 | **85.51%** |
| **MaxLen 384 (Step 3.10/3.12 Remediated)** | 1,468 / 1,482 | **99.06%** | 5 (0.34%) | 9 / 1,482 | **0.61%** | 19,042 / 19,383 | **98.24%** |
| **MaxLen 512 (Extended)** | 1,482 / 1,482 | **100.00%** | 0 (0.00%) | 0 / 1,482 | **0.00%** | 19,383 / 19,383 | **100.00%** |

---

### 2. Methodological & Technical Verification

- **Overlapping Spans:** Exactly 9 validation records have overlapping spans. Each span was treated as an independent ground-truth annotation unit. No double-counting occurs because span retention is reported as a fraction of valid annotated spans ($N = 1,482$), and token retention calculates union-level intersections.
- **Character Offset Alignment:** Offset mapping was executed with `add_special_tokens=False`. This eliminates separator and classification token shifts. Character offsets $[s_{start}, s_{end}]$ align directly to raw hypothesis string slicing.
- **Classification Boundaries:**
  - `FULLY_PRESERVED`: $n_{kept} = n_{total}$
  - `PARTIALLY_PRESERVED`: $0 < n_{kept} < n_{total}$
  - `COMPLETELY_LOST`: $n_{kept} = 0$
- **Empty / Invalid Offsets:** Handled gracefully. Zero negative or out-of-bounds offsets existed in the processed validation set.
- **Distinction Between Hypothesis Tokens and Evidence Spans:** The audit confirmed that the reported span retention measures the survival of annotated conflict character spans, not simply raw hypothesis token length.
