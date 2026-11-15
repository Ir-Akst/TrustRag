# TrustRAG — Track 2, Step 3.13: Chunk Aggregation Engine Audit

- **Component:** `ChunkAggregator` in `tools/training/nli_multi_chunk.py`

---

### 1. Mathematical Implementation of Policies

The auditor inspected the source code for all five aggregation policies:

1. **`CONTRADICTION_PRIORITY`:**
   - Evaluates:
     $$P_{contra}^{max} = \max_{k \in [1, K]} P(y = \text{CONTRADICTION} \mid c_k)$$
   - If $P_{contra}^{max} \ge \tau_{conflict}$ (default 0.50) or if any chunk is labeled `CONTRADICTION`, the entire example is classified as `CONTRADICTION`.
   - If no contradiction exists, checks for entailment: if $\exists k: \hat{y}_k = \text{ENTAILMENT}$, outputs `ENTAILMENT`.
   - Otherwise outputs `NEUTRAL`.
   - *Audit Verdict:* Correctly implements an asymmetric falsification filter essential for RAG safety.
2. **`MAX_CONFIDENCE`:**
   - Selects $k^* = \arg\max_k (\max_{j \in [0, 2]} P(y = j \mid c_k))$.
   - Outputs $\hat{y}_{k^*}$.
3. **`AVERAGE_PROBABILITIES`:**
   - Computes normalized mixture distribution:
     $$\bar{P}(y = j) = \frac{1}{K} \sum_{k=1}^K P(y = j \mid c_k)$$
   - Outputs $\arg\max_j \bar{P}(y = j)$.
   - *Audit Check on Statistical Independence:* Averaging probabilities does NOT assume statistical independence; it acts as an arithmetic ensemble mixture.
4. **`MAJORITY_VOTE`:**
   - Discrete voting across chunk argmax labels: $\text{mode}(\hat{y}_1, \dots, \hat{y}_K)$.
5. **`INSUFFICIENT_EVIDENCE_GUARD`:**
   - Rejects predictions where $\max_k \max_j P(y = j \mid c_k) < \tau_{uncertainty}$ (default 0.34). Returns `INSUFFICIENT_EVIDENCE`.

---

### 2. Edge-Case Handling & Scientific Status

- **Empty Chunks:** Returns `INSUFFICIENT_EVIDENCE` with status `EMPTY_CHUNKS`.
- **Single Chunk:** Bypasses aggregation loop and returns single-chunk prediction directly.
- **Deterministic Output:** All policies are deterministic with zero stochastic behavior.
- **Scientific Limitation:** Aggregation is purely algorithmic. It has not been calibrated or optimized against downstream task metrics using fine-tuned weights.
