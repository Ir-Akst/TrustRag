# TrustRAG Research Completion — Track 1, Step 2: Retrieval Evaluation on MS MARCO

## 1. Summary of Results

Evaluation of `TrustAwareRetriever` candidate snippet re-ranking on MS MARCO v1.1 validation set.

- **Total Queries in Validation Split:** 10,047
- **Evaluated Queries:** 9706
- **Skipped Queries:** 341 *(Zero human-annotated relevant passages in v1.1)*
- **Candidate Pool per Query:** 6 to 10 candidate search snippets (mean 10.0)
- **Execution Time:** 65.16s
- **Throughput:** 149.0 queries/second

---

## 2. Re-ranking Retrieval Performance

| Metric | Score | Interpretation |
| :--- | :--- | :--- |
| **Recall@1** | **0.2311** | Selected passage ranked at rank 1 |
| **Recall@5** | **0.7592** | Selected passage ranked in top 5 |
| **Recall@10** | **0.9768** | Selected passage ranked in top 10 |
| **MRR@10** | **0.4626** | Mean Reciprocal Rank of relevant passage |

---

## 3. Detailed Handling of Skipped Queries

In MS MARCO v1.1 validation, 341 queries contain passages where `is_selected = 0` across all candidate entries (i.e. crowd annotators determined none of the retrieved search engine snippets answered the query). In accordance with standard TREC/MS MARCO evaluation protocols, queries without any ground-truth relevant passages cannot have a well-defined Recall or Reciprocal Rank and are excluded from ranking metric denominators.

---

## 4. Canonical Full-Corpus Status & Blockers

- **Status:** **`BLOCKED`**
- **Missing Artifact:** `Canonical 8.84M passage collection (collection.tsv / collection.tar.gz ~3.2 GB) and official qrels.dev.small.tsv`
- **Reason:** Canonical MS MARCO Passage Ranking evaluates retrieval over the complete 8.84 million passage collection. The current evaluation is restricted to re-ranking the candidate search snippets provided in the MS MARCO Q&A parquet dataset.
- **Remediation Path:** Downloading `collection.tar.gz` (~3.2 GB compressed, ~10 GB uncompressed) and building an index requires dedicated disk and memory capacity.
