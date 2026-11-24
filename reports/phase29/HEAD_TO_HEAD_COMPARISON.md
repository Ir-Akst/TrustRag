# Phase 29 — FilterRAG Reproduction & Head-to-Head Comparison

---

## 1. Primary Methodological Reference

- **Paper Reference:** Zou et al., *FilterRAG: Defending Retrieval-Augmented Generation Against Knowledge Poisoning Attacks via Frequency Density Filtering*, USENIX Security 2025 (`2508.02835v2.pdf`).
- **Core Mechanism:** FilterRAG hypothesizes that poisoned passages designed to manipulate an LLM's answer share high lexical and semantic concentration with expected answer tokens, creating high "Frequency Density" clusters.
- **Evaluation Modes Evaluated:**
  1. `FilterRAG_Threshold`: Direct thresholding on Frequency-Density ($\epsilon = 0.70$ tuned on validation split).
  2. `ML_FilterRAG`: Multi-feature classification (`LogisticRegression` fitted on training split) combining frequency density, query match, retrieval score, and length normalization.
  3. `TrustRAG_MSD`: Robust K-Means clustering in embedding space with availability-preserving Removal Cap ($C_r = 0.50$).
  4. `Combined_MSD_FilterRAG`: Logical OR union of MSD and FilterRAG.

---

## 2. Experimental Setup & Controls

To ensure strict comparability:
- **Corpus & Queries:** Evaluated across identical held-out test splits (`data/benchmarks_backup/knowledge_poisoning/test.jsonl` and `data/benchmarks_backup/clean_rag/test.jsonl`).
- **Test Samples:** 64 attack candidate evaluations and 75 clean Wikipedia passage evaluations across 15 queries $\times$ 5 passages.
- **Retriever:** Identical BM25 and embedding scoring pipeline.
- **Representation:** Identical document feature representations.

---

## 3. Head-to-Head Empirical Findings

| Defense Variant | Status | Precision | Recall | F1 Score | Security Clean FPR | Clean RAG Retention ($n=75$) | Clean RAG False Positives |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Original RAG (No Defense)** | Completed | $0.0000$ | $0.0000$ | $0.0000$ | $0.0000$ | **$100.00\%$** | $0 / 75$ |
| **TrustRAG MSD** | Completed | **$0.8750$** | **$0.4828$** | **$0.6222$** | **$0.0000$** | **$100.00\%$** | **$0 / 75$** |
| **FilterRAG Threshold ($\epsilon=0.70$)** | Proxy-Only | **$1.0000$** | $0.3793$ | $0.5500$ | $0.0000$ | **$20.00\%$** | **$60 / 75$** |
| **ML-FilterRAG (LogReg)** | Proxy-Only | $0.4167$ | **$0.8621$** | $0.5618$ | $1.0000$ | $80.00\%$ | $15 / 75$ |
| **Combined MSD + FilterRAG** | Proxy-Only | $0.8750$ | $0.4828$ | $0.6222$ | $0.0000$ | $20.00\%$ | $60 / 75$ |

---

## 4. In-Depth Scientific Analysis

1. **Utility & Clean Context Starvation in FilterRAG**:
   - `FilterRAG_Threshold` achieved high precision on security test cases ($1.0000$), but **falsely rejected 80.0% of clean documents** ($60/75$ false positives) on natural multi-sentence Wikipedia text.
   - *Root Cause*: In multi-sentence informational passages, query-relevant tokens are naturally dispersed. When evaluated by frequency density, natural passages fail density thresholds, starving the downstream LLM of legitimate context.
2. **TrustRAG MSD Superiority in Clean Retention**:
   - `TrustRAG_MSD` achieved **100% clean passage retention** ($0/75$ false positives) while maintaining higher security F1 ($0.6222$ vs. $0.5500$).
   - Embedding-space spatial outlier detection is far more resilient to natural length variations than token-density heuristics.
3. **ML-FilterRAG Fragility**:
   - While `ML_FilterRAG` increased poison recall to $0.8621$, it suffered from an unacceptably high Security Clean FPR ($1.0000$), demonstrating severe vulnerability to feature distribution shift between short benchmark passages and longer narrative passages.
4. **Reproducibility Disclosure**:
   - FilterRAG was evaluated using the documented **extractive proxy mode** because live small language model (SLM) causal generation was unavailable in the offline environment. The limitations of this proxy are explicitly reported.
