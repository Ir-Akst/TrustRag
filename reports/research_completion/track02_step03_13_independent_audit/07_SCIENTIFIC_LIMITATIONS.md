# TrustRAG — Track 2, Step 3.13: Scientific Limitations & Architectural Tradeoffs

1. **Token Coverage vs Semantic Grounding:**
   Achieving 100% premise token coverage guarantees that no premise tokens are dropped before the model, but it does NOT guarantee that the cross-encoder correctly interprets long-range dependencies spanning multiple chunks.

2. **Cross-Chunk Disconnection (No Multi-Hop Cross-Attention):**
   Each premise chunk $[P_k, H]$ is scored in isolation. If a claim requires synthesizing evidence where premise fact A is in Chunk 1 and premise fact B is in Chunk 4, standard chunk-level aggregation cannot jointly reason across them.

3. **Oversized Hypothesis Truncation (54 Records):**
   For 54 validation records with hypotheses exceeding 317 tokens, the hypothesis was truncated. While preserving premise context is necessary, claim information in the hypothesis tail is lost for these 54 examples.

4. **Inference Latency vs Precision Tradeoff:**
   Multi-chunk processing increases inference operations by ~4.45x (averaging 4.45 chunks per example). Deploying this on CPU requires caching or selective document routing.

5. **Lack of Downstream Experimental Calibration:**
   The aggregation policies have only been evaluated with mock probabilities and zero-training forward passes. Their actual effect on F1, precision, recall, and false-positive rates can only be established after a properly trained NLI model is evaluated.
