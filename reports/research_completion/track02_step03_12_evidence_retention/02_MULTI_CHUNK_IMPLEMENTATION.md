# TrustRAG — Track 2, Step 3.12: Multi-Chunk Serialization Architecture & Aggregator Implementation

- **Component Location:** `tools/training/nli_multi_chunk.py`
- **Core Abstractions:** `MultiChunkNLIProcessor`, `PremiseChunk`, `ChunkMetadata`, `ChunkAggregator`, `EvidenceSpanRetentionAuditor`

---

### Architectural Principles

1. **Hypothesis Invariance:**
   In cross-encoder NLI, breaking a claim across chunks destroys the claim's semantic proposition. Therefore, `MultiChunkNLIProcessor` guarantees that the **complete hypothesis is replicated intact in every chunk**.

2. **Sliding Window Chunking:**
   Long document premises are partitioned with configurable token stride and overlap (default: `max_seq_len=384`, `overlap=32`, `min_premise_tokens=64`).
   - Window budget: `budget = max_seq_len - 3 - len(hypothesis_ids)`
   - Stride: `stride = budget - overlap`
   - Every chunk contains deterministic character offsets `[premise_char_start, premise_char_end]` and token offsets `[premise_token_start, premise_token_end]`.

3. **Deterministic Chunk Identifiers:**
   Each chunk is assigned an immutable traceable identifier:
   `chunk_id = f"{example_id}_chunk_{chunk_index}"`

4. **Chunk Prediction Aggregation Policies:**
   `ChunkAggregator` implements 5 formal policies for reconciling chunk predictions:
   - `CONTRADICTION_PRIORITY`: If *any* chunk detects contradiction with confidence $\ge \tau_{conflict}$, the claim is falsified. Essential for RAG hallucination detection.
   - `MAX_CONFIDENCE`: Selects the chunk prediction with highest softmax probability.
   - `AVERAGE_PROBABILITIES`: Computes mean probability distribution $\frac{1}{K} \sum_{k=1}^K P(y|c_k)$ across all $K$ chunks.
   - `MAJORITY_VOTE`: Discrete modal class voting across chunks.
   - `INSUFFICIENT_EVIDENCE_GUARD`: If maximum confidence across chunks fails to exceed uncertainty threshold $\tau$, outputs `INSUFFICIENT_EVIDENCE`.
