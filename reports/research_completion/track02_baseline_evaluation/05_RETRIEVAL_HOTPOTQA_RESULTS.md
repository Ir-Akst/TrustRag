# TrustRAG Research Completion — Track 1, Step 2: Retrieval Evaluation on HotpotQA

## 1. Summary of Results

Evaluation of `TrustAwareRetriever` candidate re-ranking on 7,405 validation queries of the HotpotQA distractor benchmark.

- **Evaluated Queries:** 7405
- **Candidate Pool per Query:** 10 (2 gold paragraphs, 8 distractor paragraphs)
- **Execution Time:** 57.75s
- **Throughput:** 128.2 queries/second

---

## 2. Re-ranking Retrieval Performance

| Metric | Score | Interpretation |
| :--- | :--- | :--- |
| **Recall@1** | **0.4154** | At least one gold paragraph ranked #1 |
| **Recall@5** | **0.8182** | At least one gold paragraph ranked in top 5 |
| **Recall@10** | **0.9876** | At least one gold paragraph ranked in top 10 (out of 10) |
| **MRR@10** | **0.8965** | Mean Reciprocal Rank across candidate pool |

---

## 3. Canonical Full-Corpus Status & Blockers

- **Status:** **`BLOCKED`**
- **Missing Artifact:** `Canonical 5.23M Wikipedia passage archive (hotpot_corpus.tsv, ~2.5 GB)`
- **Reason:** Canonical open-domain HotpotQA evaluation requires querying across the complete 5.23 million English Wikipedia article corpus. Only the distractor candidate benchmark (`hotpot_val_distractor.parquet`) was acquired in Track 1, Step 1.
- **Remediation Path:** To execute full-corpus retrieval evaluation, the multi-gigabyte Wikipedia corpus dump must be downloaded, indexed using an inverted index (e.g., BM25/Lucene) or vector index (HNSW/FAISS), and evaluated on memory-sufficient infrastructure.
