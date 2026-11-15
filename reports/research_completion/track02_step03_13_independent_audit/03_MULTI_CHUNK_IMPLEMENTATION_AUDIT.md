# TrustRAG — Track 2, Step 3.13: Multi-Chunk Implementation Audit

- **Component:** `tools/training/nli_multi_chunk.py`
- **Class:** `MultiChunkNLIProcessor`

---

### 1. Independent Verification of Reported Metrics

Independent execution across all 2,662 validation records yielded:

| Metric | Reported in Step 3.12 | Independently Measured | Status / Discrepancy Analysis |
| :--- | :--- | :--- | :--- |
| **Total Chunks (384 / Overlap 32)** | 11,845 | **11,849** | Minor prose delta: +4 chunks (+0.03%). JSON data matches 11,849. |
| **Average Chunks / Record (384)** | 4.450 | **4.451** | Verified. |
| **Max Chunks (384)** | 28 (prose) | **66** | Discrepancy: Outlier premise in RAGTruth requires 66 chunks. |
| **Total Chunks (512 / Overlap 64)** | 7,666 | **7,654** | Minor prose delta: -12 chunks (-0.15%). JSON data matches 7,654. |
| **Average Chunks / Record (512)** | 2.880 | **2.875** | Verified. |
| **Max Chunks (512)** | 18 (prose) | **740** | Extreme outlier document in validation set requires 740 chunks. |
| **Premise Token Coverage** | 100.00% | **100.00%** | **Verified (Unique Set).** 1,563,348 / 1,563,348 tokens covered. |
| **Hypothesis Token Coverage** | 99.45% | **99.45%** | **Verified.** 413,775 / 416,052 tokens covered. |
| **Overlap Overhead (384)** | 6.83% | **6.83%** | **Verified.** 293,984 redundant tokens / 4,305,618 total. |

---

### 2. Resolution of Coverage & Oversized Hypotheses Questions

1. **Does 100% Premise Coverage Count Duplicated Tokens?**
   - **No.** The auditor verified premise coverage by taking the mathematical set union of all token intervals $[\text{start}, \text{end})$ across all chunks belonging to an example:
     $$\bigcup_{k=1}^K [\text{premise\_token\_start}_k, \text{premise\_token\_end}_k) = [0, \text{orig\_premise\_len})$$
   - Exactly 1,563,348 unique premise tokens are present in the validation set, and all 1,563,348 are covered. Duplicated overlap tokens were excluded from the numerator.
2. **Why is Hypothesis Coverage 99.45% Instead of 100%?**
   - In cross-encoder processing, the available sequence budget at `max_seq_len=384` is $384 - 3 = 381$ tokens.
   - To prevent catastrophic omission of premise context, `MultiChunkNLIProcessor` enforces `min_premise_tokens=64`.
   - Therefore, the maximum allowable hypothesis budget is $381 - 64 = 317$ tokens.
   - In the validation dataset, exactly **54 records have hypotheses exceeding 317 tokens**. For these 54 records, the hypothesis is truncated to 317 tokens.
   - For all remaining 2,608 records (97.97%), 100% of the hypothesis is preserved in every chunk.
