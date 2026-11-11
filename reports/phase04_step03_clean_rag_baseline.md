# TrustRAG Phase 04 — Step 3: Clean RAG Baseline Evaluation

**Date:** 2026-11-11  
**Dataset:** `clean_rag` (Real BoolQ validation records; active `data/benchmarks/clean_rag` + larger Phase 02 snapshot `data/benchmarks_backup/clean_rag`)  
**Configurations Compared (Identical Retrieval/Generator Settings):**
- **Original RAG Baseline:** `tfidf_extractive` (`top_k=5`, `max_context_docs=3`, `max_sentences_per_doc=2`, `seed=42`, G1/G2/G3/SRM disabled)
- **Full TrustRAG:** Identical retrieval & generator parameters with G1, G2 MSD, G3 Verification, and deterministic SRM fallback active

---

## 1. Observed Baseline Metrics

### 1.1 Active Frozen Benchmark (`data/benchmarks/clean_rag`)

| Configuration | Split ($N$) | P@1 | P@5 | R@1 | R@5 | MRR | Top-1 Rel. | GT Doc Hit | GT Overlap | Faithfulness | Abstention | Mean Tokens (In/Out) | Mean Lat (ms) | p95 Lat (ms) | QPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Original RAG** | `test` (2) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.2046 | 1.0000 | 0.6190 | 1.0000 | 0.0000 | 63.0 / 30.5 | 1.84 | 1.97 | 544.60 |
| **Full TrustRAG** | `test` (2) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.2046 | 1.0000 | 0.6190 | 1.0000 | 0.0000 | 63.0 / 30.5 | 4.42 | 4.71 | 226.35 |
| **Original RAG** | `train` (7) | 1.0000 | 0.9286 | 1.0000 | 1.0000 | 1.0000 | 0.2649 | 1.0000 | 0.4719 | 0.8571 | 0.0000 | 124.3 / 60.7 | 2.12 | 2.85 | 472.33 |
| **Full TrustRAG** | `train` (7) | 1.0000 | 0.9286 | 1.0000 | 1.0000 | 1.0000 | 0.2649 | 1.0000 | 0.4719 | 0.8571 | 0.0000 | 124.3 / 60.7 | 6.09 | 8.20 | 164.25 |

### 1.2 Larger Phase 02 Snapshot (`data/benchmarks_backup/clean_rag`)

| Configuration | Split ($N$) | P@1 | P@5 | R@1 | R@5 | MRR | Top-1 Rel. | GT Doc Hit | GT Overlap | Faithfulness | Abstention | Mean Tokens (In/Out) | Mean Lat (ms) | p95 Lat (ms) | QPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Original RAG** | `test` (15) | 0.7333 | 0.5356 | 0.7333 | 0.8000 | 0.7667 | 0.1839 | 0.8000 | 0.4134 | 0.7333 | 0.2000 | 118.7 / 74.4 | 2.74 | 4.76 | 365.42 |
| **Full TrustRAG** | `test` (15) | 0.7333 | 0.5356 | 0.7333 | 0.8000 | 0.7667 | 0.1839 | 0.8000 | 0.4180 | 0.7333 | 0.2000 | 118.0 / 74.1 | 6.63 | 12.81 | 150.91 |
| **Original RAG** | `train` (70) | **0.8714** | 0.3752 | **0.8714** | **0.9286** | **0.8940** | 0.2527 | **0.9143** | 0.3240 | 0.6571 | 0.0143 | 245.8 / 145.2 | 7.68 | 15.33 | 130.16 |
| **Full TrustRAG** | `train` (70) | 0.7571 | 0.3610 | 0.7571 | 0.8571 | 0.7945 | 0.2361 | 0.8286 | 0.3036 | 0.6429 | 0.0143 | 256.6 / 146.1 | 19.98 | 37.72 | 50.04 |

- **Execution Accounting:** `failed_examples = 0`, `invalid_examples = 0`, `skipped_examples = 0` across all 8 runs.

---

## 2. Scientific Findings & Honest Interpretation

1. **Boolean Exact Match (`0.0000` across all runs):** `AnswerGenerator` operates in deterministic `extractive` mode, returning verbatim evidence sentences (`"<sentence> [doc_id]"`) rather than `"yes"`/`"no"` strings. Therefore, Boolean exact-match accuracy cannot be satisfied without a downstream generative QA/LLM head, and we measure retrieval accuracy (`P@K`, `R@K`, `MRR`), ground-truth document citation (`GT Doc Hit`), passage lexical overlap, and evidence faithfulness instead.
2. **Utility Preservation vs. Trust Re-ranking Tradeoff:**
   - On `test` ($N=2$ active, $N=15$ backup), Full TrustRAG preserves **100% of Original RAG's retrieval and faithfulness metrics** (`P@1=0.7333`, `MRR=0.7667`, `Faithfulness=0.7333`).
   - On the denser 70-document `train` corpus, TrustRAG exhibits a measurable ranking utility cost (`P@1`: `0.8714` $\rightarrow$ `0.7571`, `-11.4 pp`; `R@5`: `0.9286` $\rightarrow$ `0.8571`, `-7.1 pp`). This arises because `TrustAwareRetriever` blends `trust_weight=0.45` into candidate scoring (`(1 - 0.45) * rel + 0.45 * trust`), allowing marginally higher-trust distractors to displace the highest-relevance clean document when TF-IDF scores are close.
3. **Computational Overhead:** Enabling full defenses increases mean per-query latency from `2.74 ms` $\rightarrow$ `6.63 ms` (`2.42x` on backup `test`, $N=15$) and `7.68 ms` $\rightarrow$ `19.98 ms` (`2.60x` on backup `train`, $N=70$).

---

## 3. Step 3 Acceptance Verdict

- [x] Clean RAG baseline metrics calculated without G1/G2/G3 interventions.
- [x] Sample counts, failures (`0`), and invalid predictions (`0`) explicitly accounted for.
- [x] Model configuration (`tfidf_extractive`) documented and held fixed across baseline vs. TrustRAG comparisons.
- [x] Results fully reproducible (`seed=42`, JSON/CSV artifacts exported to `reports/evaluation/`).

**Step 3 Status:** **PASS** — Ready to proceed to Step 4 (Knowledge Poisoning Evaluation).

