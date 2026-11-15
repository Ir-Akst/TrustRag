# TrustRAG Research Completion — Track 1, Step 2.2: Baseline Comparison

## 1. Safety vs Utility Frontier

The corrected baseline evaluations demonstrate how threshold tuning trades safety against coverage:

```
HaluEval Frontier:
  Unverified Baseline:    FSR = 100.0%  | Abstention =  0.0%  | Acc = 50.0%
  Default G3 (0.65):      FSR =  15.93% | Abstention = 53.10% | Acc = 72.50%
  Strict G3 (0.80):       FSR =   9.07% | Abstention = 56.50% | Acc = 75.93%
```

### Key Analytical Insights:
1. **Zero Hallucination Leaks on RAGTruth:** Under both default and strict thresholds, Strict FSR is exactly **0.0000** (0 / 943). TrustRAG consistently refuses to certify hallucinations on this complex benchmark.
2. **Strict Mode Safety Gains on HaluEval:** Elevating threshold to 0.80 successfully eliminates 103 hallucination leaks without causing a single additional false contradiction on factual claims ($FCR = 0.87\%$ for both).
3. **Retrieval Candidate Re-ranking Preserved:**
   - HotpotQA: Recall@1: 0.4154, Recall@5: 0.8182, Recall@10: 0.9876, MRR@10: 0.8965.
   - MS MARCO: Recall@1: 0.2311, Recall@5: 0.7592, Recall@10: 0.9768, MRR@10: 0.4626.
