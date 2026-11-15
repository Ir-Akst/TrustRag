# TrustRAG — Track 2, Step 3.14: Multi-Chunk Dataset Partition Statistics

### 1. Empirical Multi-Chunk Breakdown

Across both splits using `MultiChunkNLIProcessor(max_seq_len=384, overlap=32, min_premise=64)`:

| Metric | Training Split (`train.jsonl`) | Validation Split (`validation.jsonl`) |
| :--- | :--- | :--- |
| **Total Original Examples** | 10,815 | 2,662 |
| **Total Generated Chunks** | **47,039** | **11,849** |
| **Average Chunks / Example** | 4.349 | 4.451 |
| **Max Chunks for Single Record** | 67 | 66 |
| **Single-Chunk Examples (Fit in 384)** | 1,431 (13.23%) | 342 (12.85%) |
| - *Single-Chunk ENTAILMENT* | 1,147 | 266 |
| - *Single-Chunk CONTRADICTION* | 62 | 26 |
| - *Single-Chunk NEUTRAL* | 222 | 50 |
| **Multi-Chunk Examples (>1 Chunk)** | 9,384 (86.77%) | 2,320 (87.15%) |
| - *Multi-Chunk ENTAILMENT* | 5,560 (27,178 chunks) | 1,396 (6,958 chunks) |
| - *Multi-Chunk CONTRADICTION* | 1,358 (7,412 chunks) | 330 (1,933 chunks) |
| - *Multi-Chunk NEUTRAL* | 2,466 (12,449 chunks) | 594 (2,958 chunks) |
| **Oversized Hypotheses (>317 tokens)** | 201 (1.86%) | 54 (2.03%) |

---

### 2. Supervision Viability Takeaway

- **Single-Chunk Examples (1,431 train / 342 val):** 100% of premise and hypothesis fit within a single 384-token window. Supervision is unambiguous and verified.
- **Multi-Chunk Examples (9,384 train / 2,320 val):** 86.77% of training examples require multiple chunks. They cannot be expanded into hard-supervised training pairs without introducing massive label noise.
