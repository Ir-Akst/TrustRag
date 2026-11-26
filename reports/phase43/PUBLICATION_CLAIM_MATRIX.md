# Final Publication Claim Matrix (Narrowed & Scientifically Defensible)

| Claim | Defensible Scope | Evidence |
|---|---|---|
| **Fail-Closed Generator-Boundary Containment** | **Claim Directly** | 0/90 leakage (0.00%, [0.00%, 4.09%]) vs 100% w/o `GeneratorBoundaryEnforcer`. |
| **G1 Semantic Generalization (Unquoted Queries)** | **Claim Directly** | 96.67% ADR (145/150) vs 36.67% w/o G1 Semantic; 0% FPR on unquoted educational/technical/analytical queries. |
| **G1 Benign Utility on Quoted SOC/CTI Logs** | **Narrow / Disclose Limitation** | 40%–80% FPR on raw quoted attacks, SOC incident reports, and CTI briefs. |
| **G3 Evidence Verification (Single-Passage Claims)** | **Claim Directly** | 100% release-gate accuracy ($N=120$–$140$) and 3%–8% leakage on RAGTruth `Summary`. |
| **G3 Abstractive Summary / Short-QA Recall** | **Narrow / Disclose Limitation** | 16% recall on RAGTruth `Summary` (88% abstention) and 10% raw / 52% wrapped recall on HaluEval. |
| **Batched Neural CPU Serving** | **Claim Directly** | 57 genuine DeBERTa `forward()` passes / 15 reqs; 838.94–963.35 ms warm mean (2.68x–3.07x faster vs Phase 39). |
