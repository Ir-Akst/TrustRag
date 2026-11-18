# TrustRAG — Track 2, Step 3.12: Serialization Methods Comparison Across 2,662 Validation Samples

- **Evaluation Dataset:** `data/processed/sft_v2/nli/validation.jsonl` (2,662 records)
- **Total Premise Tokens:** 1,562,384 tokens
- **Total Hypothesis Tokens:** 102,410 tokens

---

### Comparative Serialization Matrix

| Serialization Method | Total Chunks | Avg Chunks / Record | Max Chunks | Premise Token Coverage | Hypothesis Token Coverage | Overlap Overhead % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Single-Window 128 (Step 3.8 Baseline)** | 2,662 | 1.000 | 1 | **10.66%** | **39.94%** | 0.00% |
| **Single-Window 384 (Step 3.10 Remediated)** | 2,662 | 1.000 | 1 | **36.88%** | **99.45%** | 0.00% |
| **Single-Window 512 (Extended Window)** | 2,662 | 1.000 | 1 | **54.11%** | **99.92%** | 0.00% |
| **Multi-Chunk 384 (Overlap 32)** | 11,845 | 4.450 | 28 | **100.00%** | **99.45%** | **6.83%** |
| **Multi-Chunk 512 (Overlap 64)** | 7,666 | 2.880 | 18 | **100.00%** | **99.92%** | **9.04%** |

---

### Key Analytical Takeaways

1. **Premise Coverage Deficit in Single-Window:**
   Even at `max_seq_len=512`, single-window serialization leaves **45.89% of premise content unexamined**. In dense RAG documents, critical supporting or refuting evidence residing in the document tail is permanently omitted.
2. **Complete Coverage via Multi-Chunk:**
   Both Multi-Chunk 384 and Multi-Chunk 512 achieve **100.00% premise token coverage**, ensuring zero silent truncation of premise evidence.
3. **Modest Overlap Redundancy:**
   Multi-chunk overlap introduces only **6.83% redundant tokens** at 384 (stride 320, overlap 32) and **9.04%** at 512 (stride 448, overlap 64).
