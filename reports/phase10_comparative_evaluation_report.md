# TrustRAG Phase 10 — Comparative Evaluation Report

**Run ID:** `phase10_20261112T073204Z_canonical_v2` | **Seed:** `42` | **Commit:** `1ceb29c`

---

## 1. Adversarial Robustness (`data/benchmarks_backup/adversarial_robustness`, `n=40` test)

| System Profile | Accuracy | Precision | Recall | F1 | FPR | ASR | Mean Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `original_rag` | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 2.0955 |
| `static_trustrag` | 0.7500 | 1.0000 | 0.5000 | 0.6667 | 0.0000 | 0.5000 | 4.3478 |
| `adaptive_trustrag` | **0.8250** | **1.0000** | **0.6500** | **0.7879** | **0.0000** | **0.3500** | 4.4561 |
| `trustrag_no_g1` | 0.7500 | 1.0000 | 0.5000 | 0.6667 | 0.0000 | 0.5000 | 4.1448 |
| `trustrag_no_g2` | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 5.0044 |
| `trustrag_no_g3` | 0.7500 | 1.0000 | 0.5000 | 0.6667 | 0.0000 | 0.5000 | 1.9629 |
| `trustrag_no_srm` | 0.7500 | 1.0000 | 0.5000 | 0.6667 | 0.0000 | 0.5000 | 4.2385 |

**Findings:** Both `static_trustrag` (`+0.2500`, `adj_p=0.0117`) and `adaptive_trustrag` (`+0.3250`, `adj_p=0.0017`) significantly outperform `original_rag` with `0.0000` FPR. Removing G2 (`trustrag_no_g2`) collapses accuracy back to `0.5000` (`ASR=1.0000`), confirming G2 is the primary defense against adversarial retrieval documents.

---

## 2. Knowledge Poisoning (`data/benchmarks_backup/knowledge_poisoning`, `n=24` test, Exploratory)

| System Profile | Accuracy | Precision | Recall | F1 | FPR | ASR | Mean Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `original_rag` | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 1.6944 |
| `static_trustrag` | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 4.1767 |
| `adaptive_trustrag` | 0.5000 | 0.5000 | 0.6667 | 0.5714 | 0.6667 | 0.3333 | 4.3555 |
| `trustrag_no_{g1,g2,g3,srm}` | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 1.96–4.47 |

**Negative / Trade-Off Finding:** In single-document factual substitution without instruction-injection tokens, `static_trustrag` has `0.0000` recall (`ASR=1.0000`). Train-calibrated `adaptive_trustrag` raises recall to `0.6667` (`ASR=0.3333`), **but** increases FPR to `0.6667` (overall accuracy `0.5000`, `p=1.0`). Without causal LM perplexity (`F1`) or multi-doc consensus (`F5`), single-doc factual poisoning remains an open limitation.

---

## 3. Clean RAG Utility (`data/benchmarks_backup/clean_rag`, `n=15` test, Exploratory)

- All 7 profiles achieve **`1.0000` clean utility (`0.0000` FPR)** — zero clean-query degradation.
- Mean latency overhead: `1.7839 ms` (`original_rag`) -> `5.6373 ms` (`static_trustrag`, `+3.85 ms`, primarily from G3 claim verification since `trustrag_no_g3` runs in `2.2455 ms`).

---

## 4. External Benchmarks Status
- `ragtruth` (5-record smoke fixture only): `acc=0.6000`, `bal_acc=0.6667`, `prec=0.5000`, `rec=1.0000`, `f1=0.6667`, `false_supported_rate=0.0000` (`PARTIALLY_READY`, parity `BLOCKED`).
- `halueval`, `llm_aggrefact`, `rsb`, `natural_questions`, `hotpotqa`, `ms_marco`: **BLOCKED** offline.
