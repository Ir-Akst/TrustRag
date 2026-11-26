# Publication Claim Matrix

| Claim | Status | Supporting Evidence & Required Qualification |
|---|---|---|
| **Generator-Boundary Containment** | **Directly Supported** | 0/90 leakage (0.00%, 95% CI [0.00%, 4.09%]) vs 100% leakage without `GeneratorBoundaryEnforcer` (Arm 3). |
| **G1 Semantic Generalization** | **Supported on Tested Distributions** | 96.67% ADR (145/150) vs 36.67% without `G1 Semantic` (Arm 2); drops to 75–80% on adaptive evasions. |
| **Low-Latency Batched Neural G3** | **Directly Supported** | 57 genuine DeBERTa `forward()` passes / 15 reqs; 838.94 ms warm mean vs 2577.91 ms (Phase 39). |
| **G3 Hallucination Leakage Reduction** | **Requires Qualification** | 3.00% leakage on RAGTruth ($N=200$, vs 100% Vanilla), but 14.00% factual recall (high abstention) and 24.00% leakage / 10.00% recall on short-answer HaluEval ($N=200$). |
| **Multilingual Robustness** | **Supported on Limited Test Distributions** | 97.22% ADR vs 66.67% without `Multilingual` (Arm 4), but Chinese unseen variants = 75.00% and splits use cycled templates. |
| **Benign Quoted-Content Preservation** | **Unsupported / Known Gap** | 0% FPR on unquoted educational/technical queries, but 40–80% FPR on quoted attacks, SOC incident reports, and CTI briefs. |
