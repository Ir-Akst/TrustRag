# TrustRAG Phase 43 — Research Gap Closure & Final Evidence Report

**Branch:** `phase-43-final-research-gap-closure`  
**Parent Commit (Phase 42):** `148f547b39920a5251af85e8ce0d1deb5834a130`  
**Release Anchor:** `531bff32745ede1bd1b38609cc6daf653d3eff24` (`trustrag-v1.0.0-rc1`)  
**Frozen Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` (8/8 SHA-256 `OK`)  
**Production Code Modified:** None (`src/` completely untouched; evaluation-only phase)  
**Final Verdict:** **COMPLETE WITH CLAIM LIMITATIONS**

---

## 1. Executive Summary & Answers to Section 10 Questions

1. **Is G3 genuinely useful beyond abstention?**  
   **Yes, within its designed operating regime** (single-passage extractive/atomic claims), where it achieves **100.00% release-gate accuracy** across all 7 controlled regimes (`short_factual_sentence`, `multi_sentence_supported`, `supported`, `partially_supported`, `unsupported`, and 4 contradiction types) and reduces RAGTruth hallucination leakage from **100.0% $\rightarrow$ 3.0%–8.0%**. However, on **multi-sentence abstractive summaries** (RAGTruth `Summary`) and **1–2 word QA fragments** (HaluEval), G3 over-abstains (**83%–88% abstention**).
2. **Can TrustRAG maintain useful factual coverage?**  
   **Only on single-passage grounded claims** (100% coverage on controlled extractive/supported claims). On abstractive multi-sentence summaries (`RAGTruth Summary`), coverage drops to **12.00%** because `entity_sub` (29 triggers) and single-sentence NLI `neural_con` (20 triggers) penalize cross-sentence synthesis. On `HaluEval`, wrapping short `<3`-word answers in a full sentence raises coverage from **17% $\rightarrow$ 47%** and recall from **10% $\rightarrow$ 52%**, but raises hallucination leakage from **24% $\rightarrow$ 42%**.
3. **Can benign security discussions pass without weakening attack detection?**  
   **Unquoted educational, technical, and analytical queries pass at 0.00% FPR** ($0/25$), while **raw quoted attacks (40% FPR), SOC incident reports (80% FPR), and threat-intel briefs (60% FPR)** still trigger false positives. Rather than weakening attack detection, the paper should **narrow the claim** to unquoted user queries and document quoted SOC/CTI text as a scoped limitation requiring quote-attribution masking.
4. **Which research claims are reproducible?**  
   Generator-boundary containment (0% observed leakage vs 100% w/o enforcer), G1 semantic detection on unquoted attacks (96.67% ADR vs 36.67% w/o G1 semantic), multilingual improvement (+30.55 pp over no-multilingual), batched CPU DeBERTa inference (2.68x–3.07x speedup), and single-passage G3 verification.
5. **Is the smallest defensible paper now ready for submission?**  
   **Yes, provided the manuscript narrows its claims** to the verified operating envelope (and discloses the offline unavailability of external pretrained prompt-injection checkpoints, the HaluEval/RAGTruth schema/abstention trade-off, and the quoted-content FPR limitation).
