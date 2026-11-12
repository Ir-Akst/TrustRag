# 06 — Trust-Aware Retriever Audit

**Module:** [retriever.py](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/retrieval/retriever.py)
**Verdict:** `YELLOW` (**Readiness: `45%`**)

---

## 1. Executed Capabilities & Telemetry

Probed on BoolQ (`clean_rag/train.jsonl`, `n=70`) plus synthetic edge cases (`part2_subsystems.json`):

| Metric / Probe | Observed Value | Interpretation |
| :--- | :---: | :--- |
| Underlying Engine | `sklearn.feature_extraction.text.TfidfVectorizer` (1–2 word n-grams) + `compute_lexical_overlap` | Pure sparse bag-of-words / TF-IDF; zero dense embeddings |
| Vector Store / ANN Backend | **None** | Pure in-memory Python list + matrix |
| Index Persistence (`has_save_method` / `has_load_method`) | `False` / `False` | Ephemeral; corpus must be re-indexed every process start (`22.1 s` cold import init; `37.435 ms` to index 70 docs) |
| Query Latency (`n=70`, top-K) | `6.583 ms` | Fast in-memory sparse scoring for small corpora |
| Empty Query Behavior | `empty_query_trusted_count = 0` | Safely returns empty trusted list (`min_similarity` / non-matching guard) |
| Empty Corpus Behavior | `empty_corpus_trusted_count = 0` | Safely handles unindexed retriever |
| Duplicate `doc_id` Handling | `[('dup_1', {'tier': 1}), ('dup_1#1', {'tier': 2})]` | **Silent ID mutation** (`#1` suffix) instead of deduplication or error |

---

## 2. Structural & Research Gaps

1. **No Dense Semantic Search or FAISS:** Despite references in research specifications and optional dependencies (`requirements-hf.txt`), there are no sentence-transformer bi-encoders, no `faiss-cpu` ANN index, and no dense/sparse RRF fusion. Paraphrased queries that lack exact unigram/bigram overlap fail retrieval unless synonyms overlap (e.g., `boolq_retrieved_ids` in a cross-topic query returned `[]`, and `3/15` BoolQ E2E utility questions returned zero candidates / `ABSTAINED`).
2. **No Document Chunking or Metadata Pre-Filtering:** Entire passages are indexed flat as single entries without sliding-window chunking or pre-retrieval tenant/source ACL filters.
3. **Removal Cap Vulnerability in `retrieve_and_filter()`:** Retrieval enforces a global `removal_cap_ratio: 0.5` (`floor(K/2)` removed cap) across G2 `POISONED` candidates. When multiple poisoned documents co-occur at top-K (e.g., `04_poisoned_retrieval_instr` and `atk_duplicate_poison_3v1`), the cap either leaves `2/2` duplicate poison docs untouched (`04`) or keeps all `3` poison docs while dropping the clean document (`atk_duplicate_poison_3v1`).
4. **Silent Identifier Rewriting:** Duplicate IDs are mutated (`dup_1 -> dup_1#1`), corrupting provenance lineage and audit trace correlation if upstream callers supply colliding IDs.

