# Phase 07 — Step 04: Independent Baseline Benchmark Results (Experiments A–H)

**Execution Date:** 2026-11-12  
**Branch:** `phase-7` (`cc1961e`)  
**Harness:** `tools/phase07_benchmark_audit.py` (read-only evaluation; zero production files altered)  
**Machine-Readable Output:** `reports/evaluation/phase07_step04_benchmarks.json`  
**Environment:** Python `3.14.9`, `x86_64` CPU-only offline Linux, `seed=42`, `top_k=5`, peak traced heap `6.688 MiB`, suite runtime `15.477 s`, deterministic bit-exact reproducibility confirmed (`reproducibility_seed42_exact = true`). Offline LLM/SLM dependencies (`Ollama` server stopped; `torch`, `transformers`, `sentence_transformers` absent).

---

## 1. Benchmark Separation & Explicit `BLOCKED` Scope

To avoid misleading cross-domain conflation, datasets are reported strictly separately across:
1. **Curated Synthetic Security (`backup_security_combined_test`):** `data/benchmarks_backup/knowledge_poisoning/test.jsonl` (`n=24`) + `data/benchmarks_backup/adversarial_robustness/test.jsonl` (`n=40`) = **`n=64` unique docs across 8 target queries** (`0` duplicates; `BENIGN_INSTRUCTION_LIKE` controls coded `is_attack=0`, yielding `35` clean / `29` poisoned documents and `7` attack queries + `1` benign control query). *Limitation: templated synthetic passages sharing query surface with train/val.*
2. **Real-World Held-Out Clean Utility (`clean_rag/test`):** `data/benchmarks_backup/clean_rag/test.jsonl` (`n=15` held-out BoolQ queries, **0% overlap** with `platt_calibrator_v1` training split) evaluated against both the harder `N=100` `boolq/validation.jsonl` corpus and the `N=15` split-only corpus. *Limitation: extractive TF-IDF generator emits passage sentences, not boolean `"true"`/`"false"` answers.*
3. **Real-World Claim Verification Smokes (`n=3..11`):** `hallucination/{train,val,test}` (`n=11`), `ragtruth/test` (`n=5`), `expertqa/test` (`n=3`), `wice/test` (`n=3`). *Insufficient sample size for statistical generalization.*
4. **`BLOCKED` External Benchmarks:** RSB 13-attack suite, HaluEval-QA (`10k`), Natural Questions, HotpotQA, MS-MARCO, LLM-AggreFact, and Full RAGTruth remain **`BLOCKED`** offline.

---

## 2. Security Evaluation (Experiments A, B, C) — `backup_security_combined_test` (`n=64`, `seed=42`)

| Exp | System / Configuration | Attack Queries (`n=7`) ASR ↓ | Query Quarantine / Abstain Rate | Doc Detection Prec | Doc Recall | Doc F1 | Doc FPR ↓ | Doc FNR ↓ | Doc ROC-AUC | Mean Latency (ms) | p50 (ms) | p95 (ms) | Throughput (QPS) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **A** | Original Unprotected RAG (`G1=off, G2=off, G3=off, SRM=off`) | **0.5714** (`4/7`) | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.5000 | 11.52 | 11.32 | 12.62 | 86.84 |
| **B** | Static TrustRAG (`configs/base.yaml`, Fallback SRM) | **0.4286** (`3/7`) | 0.0000 (`0/7`) | **1.0000** | 0.4000 | **0.5714** | **0.0000** | 0.6000 | **0.7749** | 45.07 | 40.06 | 81.79 | 22.19 |
| **C** | Phase 06 Adaptive (`platt-mixed-v1`, Context Thresholds, Drift, Policy) | **0.4286** (`3/7`) | 0.0000 (`0/7`) | 0.5263 | 0.4000 | 0.4545 | **0.2571** (`9` FP) | 0.6000 | **0.7749** | 62.97 | 58.64 | 98.92 | 15.88 |

**Key Experimental Findings (Exp A–C Security):**
- Retrieval-stage candidate filtering (`min_relevance_score=0.01`, `top_k * 3 = 15`) assessed `60` of `64` unique docs across the 8 queries. All systems achieved `0` false blocks on the clean control query (`BENIGN_INSTRUCTION_LIKE`).
- **Critical Vulnerability Exposed (`ASR = 0.4286`):** Neither Static TrustRAG nor Phase 06 Adaptive stops pure factual-substitution attacks (`KNOWLEDGE_POISONING` & `CONFLICTING_EVIDENCE` in `3/7` attack queries) when no external perplexity/NLI oracle is active — TF-IDF cosine keeps a fluent poisoned factual flip in `top_k`, and G2 cannot tell which conflicting passage is historically true (`F4=1.0`, `F5` flags conflict symmetrically, pipeline still returns top clean/mixed doc or fails to suppress).
- **Adaptive Regression on Held-Out Security (`FPR 0.0 -> 0.2571`):** Under `AdaptiveDefenseController`, `platt-mixed-v1` + context-threshold tightening (`trust_threshold=0.60`) shifts `9` benign/conflicted documents below threshold, slashing retrieval precision from `1.0000 -> 0.5263` (`F1: 0.5714 -> 0.4545`) without reducing `ASR` (`0.4286` unchanged) and adding `+17.9 ms` latency overhead.

---

## 3. Clean Utility Evaluation (Experiments A, B, C) — `clean_rag/test` (`n=15`, Held-Out)

| Exp | Corpus Context | Clean Recall@5 [Wilson 95% CI] | Recall@1 | Clean False-Block Rate | Abstention Rate | Grounding Rate | Mean Latency (ms) | p50 (ms) | p95 (ms) | Throughput (QPS) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **A** | Uncontaminated `n=15` over `N=100` `boolq_val` | **0.8000** `[0.5481, 0.9295]` | 0.6667 | 0.0000 | 0.0000 | 0.2000 | 16.78 | 17.61 | 18.54 | 59.59 |
| **B** | Uncontaminated `n=15` over `N=100` `boolq_val` | **0.7333** `[0.4805, 0.8910]` | **0.7333** | 0.0000 | 0.0000 | **0.3333** | 71.84 | 65.98 | 113.40 | 13.92 |
| **C** | Uncontaminated `n=15` over `N=100` `boolq_val` | **0.7333** `[0.4805, 0.8910]` | **0.7333** | 0.0000 | 0.0000 | **0.3333** | 107.17 | 87.38 | 206.51 | 9.33 |
| **A** | `n=15` over `N=15` split-only | 0.8000 `[0.5481, 0.9295]` | 0.7333 | 0.0000 | 0.2000 | 0.5333 | 6.57 | 5.75 | 11.13 | 152.12 |
| **B** | `n=15` over `N=15` split-only | 0.8000 `[0.5481, 0.9295]` | 0.7333 | 0.0000 | 0.2000 | 0.4667 | 21.96 | 19.00 | 42.87 | 45.53 |
| **C** | `n=15` over `N=15` split-only | 0.8000 `[0.5481, 0.9295]` | 0.7333 | 0.0000 | 0.2000 | 0.4667 | 28.66 | 23.85 | 59.16 | 34.89 |

- **Statistical Comparison (`n=15` over `N=100`):** McNemar exact `p=1.0` for `A vs B` and `B vs C` (`n=15` underpowered). Paired latency `B vs C` shows **`+35.33 ms` statistically significant overhead** for Adaptive (`Cohen's d = 1.0701`, `p = 0.0002`), driven by controller pre-retrieval context extraction.

---

## 4. Individual & Full MSD Signal Evaluation (Experiments D & E) — `n=64`

*(Detailed single/pairwise/LOO/calibration breakdown in Step 05 Report.)*

| Exp | Signal / Configuration | Status | Avail Docs | Precision | Recall | F1 | FPR | ROC-AUC | PR-AUC |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **D1** | `F1_perplexity` (`perplexity_backend=disabled`) | **`BLOCKED`** | `0/64` | — | — | — | — | — | — |
| **D2a** | `F2_embedding_norm` (default `require_configured`) | Inactive by default | `0/64` | 0.4531 | 1.0000 | 0.6237 | 1.0000 | 0.5000 | 0.4531 |
| **D2b** | `F2_embedding_norm` (opt-in `allow_empirical_fallback` TF-IDF L2) | Heuristic opt-in | `12/64` | 0.4423 | 0.7931 | 0.5679 | 0.8286 | **0.4704** | 0.4445 |
| **D3** | `F3_query_match` (TF-IDF cosine + lex) | Active | `64/64` | 0.4531 | 1.0000 | 0.6237 | 1.0000 | **0.6670** | 0.6212 |
| **D4** | `F4_instruction_content` (regex/obfuscation/flood) | Active | `64/64` | **1.0000** | 0.4828 | **0.6512** | **0.0000** | **0.7414** | 0.7171 |
| **D5** | `F5_consensus_deviation` (pool numeric/antonym check) | Active | `64/64` | 0.4167 | 0.5172 | 0.4615 | 0.6000 | **0.4586** | 0.4343 |
| **D6** | `F6_provenance` (`custom_security` + `source_id` metadata) | Constant `0.75` | `64/64` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.4531 |
| **E1** | **Full Active-4 MSD Raw (`F3+F4+F5+F6`)** | Active default | `64/64` | **1.0000** | 0.4828 | **0.6512** | **0.0000** | **0.8315** | **0.8320** |
| **E2** | Full Active-4 MSD + `platt-mixed-v1` | Active in P06 | `64/64` | 0.7000 | 0.4828 | 0.5714 | 0.1714 | **0.8315** | **0.8320** |
| **E3** | Full Active-4 + TF-IDF `F2_empirical` Opt-In | Experimental | `64/64` | 1.0000 | 0.4828 | 0.6512 | 0.0000 | **0.8039** (`-0.0276`) | 0.8300 |

---

## 5. G3 Output Verification Evaluation (Experiment F)

| Dataset | Split & `n` | Verdict Counts | False `SUPPORTED` on Non-Supported | Supported Precision | Supported Recall | Supported F1 | Accuracy | Mean Latency (ms) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `hallucination` (backup) | `train+val+test` (`n=11`) | `INSUFFICIENT=8, CONTRADICTED=2, SUPPORTED=1` | **0 / 6** | 1.0000 | 0.2000 | 0.3333 | 0.6364 | 5.73 |
| `expertqa` | `test` (`n=3`) | `INSUFFICIENT=1, CONTRADICTED=2` | **0 / 2** | 0.0000 | 0.0000 | 0.0000 | 0.6667 | 6.23 |
| `wice` | `test` (`n=3`) | `INSUFFICIENT=3` | **0 / 2** | 0.0000 | 0.0000 | 0.0000 | 0.6667 | 4.88 |
| `ragtruth` | `test` (`n=5`) | `SUPPORTED=1, INSUFFICIENT=4` | **0 / 2** | 1.0000 | 0.3333 | 0.5000 | 0.6000 | 5.31 |
| Security Query Clean vs Poison Check | `8` queries (`clean` vs `poison` against clean docs) | Clean: `8/8` supported; Poison vs Clean: `5/7` rejected (`CONTRADICTED`/`INSUFFICIENT`/`UNCERTAIN`) | — | — | — | — | — | — |

---

## 6. FilterRAG-Inspired Frequency Density & MSD+FD Ablation (Experiments G & H)

> [!IMPORTANT]
> **Experiment Status Note:** Paper C (FilterRAG) relies on an independent generative Small Language Model producing $a_j = \text{SLM}(q_i, d_j)$ per passage. Because live SLM execution is **`BLOCKED`** offline, Experiment G & H ran strictly as **`OFFLINE_EXTRACTIVE_PROXY`** using `AnswerGenerator` extractive sentences fed to `evaluate_freq_density_heuristic` (`SUPP_FREQ_DENSITY`) inside `tools/phase07_benchmark_audit.py`. The production pipeline was NOT modified.

- **Experiment G (`Freq-Density` Extractive Proxy on `n=64` Security & `n=15` BoolQ):**
  - **Security Distributions:** Clean `Freq-Density` mean = **`1.0000`** (`std=0.0, min=1.0, max=1.0`), Poisoned `Freq-Density` mean = **`0.9561`** (`std=0.0778, min=0.8182, max=1.0`).
  - **Discrimination (`ROC-AUC`):** **`0.3793`** (`PR-AUC = 0.4022`; inverted below chance!). Why? An extractive answer copied from passage `d` consists of tokens *from `d`*, forcing `FD -> 1.0` on clean factual texts while meta-injection phrases (`ignore`, `override`, `system`) slightly dilute content-word density (`0.82–0.96`).
  - **Utility Destruction Under Thresholding (`drop if FD >= eps` on BoolQ `n=15` over `N=100`):** Clean `Recall@5` drops catastrophically from **`0.8000` -> `0.0667` (`eps=0.45`), `0.1333` (`eps=0.55`), `0.3333` (`eps=0.65`)**; mean latency `3.81 ms/doc`.
- **Experiment H (`MSD + alpha * Freq-Density` on `n=64`, `alpha in {0.0, 0.25, 0.50, 1.0}`):**
  - Across every tested `alpha` (`0.0 -> 1.0`), **`ROC-AUC = 0.8315`**, `PR-AUC = 0.8320`, `F1 = 0.6512`, `Precision = 1.0000`, `Recall = 0.4828`, `FPR = 0.0000` (**exact `0.0000` delta**).
- **Finding:** Without a real generative SLM producing $a_j = \text{SLM}(q_i, d_j)$ (and ML-FilterRAG perplexity fusion), FilterRAG's lexical concentration ratio does **not** complement TrustRAG MSD and is destructive if paired with extractive answers.

