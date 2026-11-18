# TrustRAG — Track 2, Step 3.12: Scientific Limitations & Architectural Tradeoffs

1. **Independent Cross-Encoder Processing:**
   Multi-chunk processing evaluates premise chunks $[P_1, H], [P_2, H], \dots, [P_K, H]$ independently. While effective for localized conflict detection, it cannot perform cross-chunk multi-hop synthesis where premise evidence spanning $P_1$ and $P_3$ is jointly required to refute $H$.

2. **Inference Latency Scaling:**
   Average premise lengths in RAGTruth result in 4.45 chunks per sample at `max_seq_len=384`, increasing CPU inference compute by 4.45x. While acceptable for evaluation, deployment in real-time low-latency retrieval requires selective chunking or top-$k$ chunk filtering.

3. **Overlap Token Redundancy:**
   A 32-token overlap introduces 6.83% computational redundancy across chunks. This is necessary to avoid boundary splitting of critical multi-word entity mentions.

4. **Training Complexity:**
   Training directly on multi-chunk representations requires either chunk-level loss backpropagation with multiple-instance learning (MIL) or gradient accumulation across chunks, which increases training memory overhead.
