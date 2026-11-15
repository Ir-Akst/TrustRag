# TrustRAG — Track 2, Step 3.9: Dataset Serialization & Truncation Audit

## 1. Sequence Length Distribution

An empirical token length analysis was conducted using the DeBERTa-v3 tokenizer across training and validation splits:

| Partition | Total Inspected | Samples > 128 Tokens | Truncation Percentage | Max Tokens | Mean Tokens |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Train Split** | 1,000 | 1,000 | **100.0%** | 2,020 | **943.8** |
| **Validation Split** | 1,000 | 1,000 | **100.0%** | 1,690 | **638.0** |

---

## 2. Truncation Impact on Evidence and Conflict Spans

When `tokenizer(premise, hypothesis, max_length=128, truncation=True)` executes:
- Default truncation strategy is `longest_first`.
- Tokens are removed alternately from the longer sequence until total sequence length equals 128.
- For a typical record with 500 premise tokens and 350 hypothesis tokens:
  - Premise is cut from 500 down to ~64 tokens.
  - Hypothesis is cut from 350 down to ~64 tokens.

### Case Study: RAGTruth Record #3 (`nli_ragtruth_train_ragtruth_10001`)
- **Annotated Label:** `CONTRADICTION` (Span: `"While there is no dedicated parking lot, street parking and validated parking options are available."`)
- **Premise Evidence:** `'BusinessParking': {'garage': True, 'street': False, 'validated': False, 'lot': False, 'valet': False}`
- **Truncation Effect:**
  - In premise, tokenization truncated at token 64 (`'hours': {'Monday...`), discarding all parking attributes and review text.
  - In hypothesis, tokenization truncated at token 64, discarding the contradictory parking sentence entirely.
- **Result:** The model received only the business name and intro sentence. Neither the premise evidence nor the hypothesis contradiction survived truncation.

**Conclusion:** Setting `max_seq_len = 128` on document-grounded RAG tasks severely corrupted semantic validity, forcing the model to learn spurious label correlations rather than semantic reasoning.
