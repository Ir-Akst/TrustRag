# TrustRAG — Track 2, Step 3.14: Scientific Limitations & Architectural Tradeoffs

1. **Absence of Premise Ground Truth in RAGTruth:**
   Because human annotators only labeled hallucination spans in candidate responses, ground-truth alignment between specific premise sentences and response claims does not exist. Any attempt to generate hard chunk labels requires heuristic inference, which injects unverified noise.

2. **Inapplicability of Hard-Supervised Chunk Training:**
   Naive chunk-level training corrupts ~80% of contradiction chunks and produces massive false-positive entailment targets. It must not be deployed.

3. **Oversized Hypothesis Truncation (201 Train / 54 Val):**
   1.86% of training records and 2.03% of validation records have hypotheses exceeding 317 tokens. These claims are truncated at 317 tokens to protect premise budget.

4. **Multi-Hop Evidence Fragmentation:**
   Cross-encoder chunking evaluates chunks independently. If a refuting argument requires combining premise facts residing in Chunk 1 and Chunk 5, chunk aggregation cannot synthesize this multi-hop deduction.

5. **Inference vs Training Decoupling:**
   The recommended deployment trains the model on single-window 384 example pairs and applies multi-chunk `CONTRADICTION_PRIORITY` aggregation at inference time. While practically effective, this introduces a minor distribution shift between single-window training context and chunked evaluation context.
