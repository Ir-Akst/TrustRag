# TrustRAG — Track 2, Step 3.14: Chunk-Level Label Assignment Policy & Evaluation

### 1. Analysis of Naive Label Inheritance

If example-level labels are copied to all generated chunks:
- In Training: 1,358 multi-chunk CONTRADICTION examples generate **7,412 chunks** (avg 5.46 chunks per example).
- An empirical contradiction fact is typically concentrated in a single 1-2 sentence evidence span (~30-60 tokens).
- Therefore, in a 5-chunk document, **only 1 chunk contains the refuting premise fact**, while 4 chunks contain benign, non-contradictory context.
- Naive copying forces 4 chunks to be labeled `CONTRADICTION`, generating **~5,900 false-positive contradiction training targets**.
- Similarly, for 5,560 multi-chunk ENTAILMENT examples generating **27,178 chunks**, copying `ENTAILMENT` forces irrelevant background paragraphs to be treated as entailing the claim.

---

### 2. Conservative Chunk Supervision Policy Matrix

| Original Example Label | Proposed Chunk Label | Feasibility | Scientific Verdict |
| :--- | :--- | :--- | :--- |
| **CONTRADICTION** | Copy to all chunks | False negative signal | **STRICTLY PROHIBITED (Corrupts ~80% of chunks)** |
| **CONTRADICTION** | Label chunk with localized span `CONTRADICTION`, others `NEUTRAL` | Requires premise span mapping | **UNSUPPORTED (Premise spans do not exist in RAGTruth)** |
| **ENTAILMENT** | Copy to all chunks | Spurious grounding | **STRICTLY PROHIBITED (Teaches hallucinated entailment)** |
| **ENTAILMENT** | Label supporting chunk `ENTAILMENT`, others `NEUTRAL` | Requires premise span mapping | **UNSUPPORTED (Positive premise spans unannotated)** |
| **NEUTRAL** | Copy to all chunks | Semantically valid | **CONDITIONALLY ACCEPTABLE (Whole doc lacks evidence)** |

---

### 3. Training Architecture Comparison

1. **Supervised Chunk Pairs (Hard Labels):** **REJECTED.** Severe supervisory noise (~80% in contradiction).
2. **Multiple-Instance Learning (MIL):** Structurally valid (treats chunks as a bag, backpropagating through $\max_k P(\text{CONTRADICTION}|c_k)$), but requires custom pooling heads, gradient accumulation, and unverified training dynamics.
3. **Single-Window 384 Training with Inference Aggregation (RECOMMENDED):**
   - Train the cross-encoder on clean example pairs using Step 3.10 remediated single-window 384 (preserving 99.06% of annotated spans, balanced sampling, starvation guards).
   - Deploy multi-chunk serialization strictly at inference / verification time via `CONTRADICTION_PRIORITY`.
