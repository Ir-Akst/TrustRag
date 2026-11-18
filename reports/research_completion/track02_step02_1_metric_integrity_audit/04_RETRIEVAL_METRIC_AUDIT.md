# TrustRAG — Track 1, Step 2.1: Independent Benchmark Metric Integrity Audit
## 04. Retrieval Metric Audit

### 1. Retrieval Verification Summary

Independent recomputation was performed on [predictions_hotpotqa_retrieval.jsonl](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_baseline_evaluation/predictions_hotpotqa_retrieval.jsonl) (7,405 queries) and [predictions_msmarco_retrieval.jsonl](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_baseline_evaluation/predictions_msmarco_retrieval.jsonl) (9,706 queries).

| Dataset | Queries Evaluated | Queries Skipped | Recall@1 | Recall@5 | Recall@10 | MRR@10 | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **HotpotQA** | 7,405 | 0 | **0.4154** | **0.8182** | **0.9876** | **0.8965** | **VERIFIED EXACT** |
| **MS MARCO** | 9,706 | 341 | **0.2311** | **0.7592** | **0.9768** | **0.4626** | **VERIFIED EXACT** |

---

### 2. Independent Verification of HotpotQA Retrieval

- **Total Queries:** 7,405
- **Candidate Pool Size:** 10 passages per query (2 gold Wikipedia paragraphs, 8 distractor paragraphs).
- **Gold Label Source:** Mapped from `supporting_facts.title` directly to `context.title`.
- **Data Leakage Check:** Clean. Only `query` is passed to `TrustAwareRetriever.retrieve_candidates()`. Neither answer text nor gold supporting paragraph indices leak into retrieval scoring.
- **Analysis of Sub-1.0 Recall@10 (182 queries):**
  - For 182 queries, Recall@10 was 0.5 (1 of 2 gold paragraphs retrieved).
  - **Mechanism:** `TrustAwareRetriever` prunes candidates with TF-IDF score $\le 0.0$. In multi-hop bridge questions (e.g. Query `5a8c7595554299585d9e36b6`), the second supporting paragraph shares zero lexical token overlap with the initial question and is only reachable via entity links in the first paragraph.
  - This confirms standard multi-hop retrieval behavior and verifies the correctness of the metric computation.

---

### 3. Independent Verification of MS MARCO Retrieval

- **Total Queries in Parquet:** 10,047
- **Evaluated Queries:** 9,706
- **Skipped Queries:** 341
- **Reason for 341 Skipped Queries:**
  - Inspection of `data/raw/ms_marco/ms_marco_val_v1.1.parquet` confirms that exactly 341 queries have `is_selected = 0` for all candidate passages.
  - In MS MARCO v1.1 crowdsourced annotations, these queries represent search queries where annotators found no candidate search snippet that answered the question.
  - In information retrieval evaluation protocols (TREC, MS MARCO official leaderboard), queries with zero relevant judgments have undefined Recall and MRR and are excluded from metric denominators.
- **Dual-Denominator Metric Reporting:**
  - **Over Evaluated Queries ($N=9,706$, Standard Protocol):**
    - Recall@1: 0.2311
    - Recall@5: 0.7592
    - Recall@10: 0.9768
    - MRR@10: 0.4626
  - **Over Total Queries ($N=10,047$, Penalizing Unannotated Queries as Zero):**
    - Recall@1: 0.2233
    - Recall@5: 0.7334
    - Recall@10: 0.9437
    - MRR@10: 0.4469

---

### 4. Re-ranking vs Full-Corpus Retrieval Distinction

The candidate-pool results must never be conflated with open-domain first-stage retrieval:
- **HotpotQA:** Re-ranking was evaluated over 10 candidates. Full-corpus retrieval over 5.23 million Wikipedia passages remains `BLOCKED` due to missing raw passage dump `hotpot_corpus.tsv` (~2.5 GB compressed).
- **MS MARCO:** Re-ranking was evaluated over 6–10 search snippets. Full-corpus retrieval over 8.84 million passages remains `BLOCKED` due to missing `collection.tsv` (~3.2 GB compressed).
