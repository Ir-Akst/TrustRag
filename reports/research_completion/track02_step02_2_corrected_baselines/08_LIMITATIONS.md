# TrustRAG Research Completion — Track 1, Step 2.2: Limitations & Next Steps

## 1. Limitations of Heuristic Lexical Verification
1. **The Paraphrase Tax:** On RAGTruth, 62.61% of factual claims are contradicted because TF-IDF token intersection drops when models use synonyms or syntactic inversions.
2. **Abstention Volume:** On HaluEval, short answers lack token density, triggering 53.10% to 56.50% abstentions.
3. **Blocked Open-Domain Retrieval:** Canonical multi-million passage collections (`hotpot_corpus.tsv`, `collection.tsv`) remain missing locally.

## 2. Readiness for Track 2 (Neural Verification)
Track 1 empirical baselines are complete, fully reconciled, and reproducible. TrustRAG is positioned to implement **Track 2: Neural Verification & Model Fine-Tuning** using cross-encoder NLI models to eliminate the paraphrase tax while maintaining $\le 9\%$ FSR.
