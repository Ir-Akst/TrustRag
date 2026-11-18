# TrustRAG — Track 2, Step 3.12: Ground-Truth Evidence Span Retention Audit

- **Annotated Ground Truth Source:** `data/raw/ragtruth/response.jsonl` & `data/processed/ragtruth/train.jsonl`
- **Validation Dataset:** `data/processed/sft_v2/nli/validation.jsonl` (2,662 records)
- **Span Population:** 1,000 validation records contain 1,482 annotated hallucination/conflict spans.

---

### Empirical Evidence Span Retention Across Sequence Lengths

| Sequence Length | Fully Preserved Spans | Fully Preserved % | Partially Preserved | Completely Lost Spans | Completely Lost % | Token Retention Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MaxLen 128 (Step 3.8 Baseline)** | 410 / 1,482 | **27.67%** | 127 (8.57%) | 945 / 1,482 | **63.77%** | **25.12%** |
| **MaxLen 256** | 1,324 / 1,482 | **89.34%** | 45 (3.04%) | 113 / 1,482 | **7.62%** | **85.51%** |
| **MaxLen 384 (Step 3.10 Remediated)** | 1,468 / 1,482 | **99.06%** | 5 (0.34%) | 9 / 1,482 | **0.61%** | **98.24%** |
| **MaxLen 512 (Extended)** | 1,482 / 1,482 | **100.00%** | 0 (0.00%) | 0 / 1,482 | **0.00%** | **100.00%** |

---

### Root Cause Confirmation

The direct span audit provides empirical proof for why Step 3.8 failed:
1. In Step 3.8 (`max_seq_len=128`), **63.77% of all annotated conflict spans were completely destroyed** before reaching the transformer layers.
2. Model parameters were forced to optimize cross-entropy loss against supervisory labels (`CONTRADICTION` or `NEUTRAL`) whose justifying evidence spans did not exist in the tokenized input.
3. In Step 3.10 and Step 3.12 (`max_seq_len=384` with hypothesis-preserving budget allocation), **99.06% of annotated conflict spans are fully retained**, with only 9 spans (0.61%) completely lost due to extreme hypothesis length.
4. Setting `max_seq_len=512` achieves **100.00% span retention** across the entire validation corpus.
