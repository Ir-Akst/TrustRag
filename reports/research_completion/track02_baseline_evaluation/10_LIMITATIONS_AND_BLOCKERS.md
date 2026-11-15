# TrustRAG Research Completion — Track 1, Step 2: Limitations & Blockers

## 1. Catalog of Methodological Limitations

### 1.1 Lexical & Heuristic Verifier Boundaries
- **Paraphrase Blindness:** The baseline G3 verifier cannot recognize semantic equivalence under lexical variance, causing a 62.61% False Contradiction Rate on RAGTruth.
- **Negation & Entity Resolution:** Heuristic polarity rules handle simple prefixes ("not", "never") but struggle with implicit contradictions (e.g. "declined" vs "accepted").
- **Ultra-Short Claim Sensitivity:** Single-word or short noun-phrase answers in QA benchmarks (e.g. HaluEval) often trigger `INSUFFICIENT_EVIDENCE` abstentions.

### 1.2 Evaluation Scope Limitations
- **Distractor Re-ranking vs Open-Domain Search:** HotpotQA and MS MARCO were evaluated strictly as candidate re-ranking tasks over pre-filtered pools of 10 candidates per query. This measures re-ranking precision but does not measure full corpus first-stage retrieval recall.

---

## 2. Infrastructure & Data Blockers

| Blocker ID | Affected Component | Required Artifact | Status | Impact / Workaround |
| :--- | :--- | :--- | :--- | :--- |
| **BLK-01** | Full-Corpus HotpotQA Retrieval | `hotpot_corpus.tsv` (5.23M passages, ~2.5 GB compressed) | **BLOCKED** | Distractor candidate pool re-ranking evaluated; full-corpus indexing deferred to dedicated indexing infrastructure. |
| **BLK-02** | Full-Corpus MS MARCO Retrieval | `collection.tsv` (8.84M passages, ~3.2 GB compressed) | **BLOCKED** | Search snippet candidate re-ranking evaluated; full-corpus indexing deferred. |
| **BLK-03** | G1 Adversarial Evaluation on Benchmarks | Benchmark datasets with prompt-injection labels | **NOT_EVALUABLE** | Canonical QA datasets have no injection labels. Validated via 680-test dedicated security test suite. |
| **BLK-04** | G2 Poisoning Evaluation on Benchmarks | RSB (arXiv:2505.18543) / Poisoned passage corpora | **BLOCKED / PENDING** | RSB distribution remains pending public release. |

---

## 3. Concrete Action Plan for Track 2

1. **Neural NLI Integration:** Incorporate cross-encoder NLI models into the G3 pipeline to eliminate lexical false contradictions.
2. **Multi-Scale Verification:** Combine lexical screening for fast rejection with neural entailment for nuanced claims.
3. **Dedicated Retrieval Indexing:** Stage multi-gigabyte passage collections on storage volumes configured for vector/BM25 indexing.
