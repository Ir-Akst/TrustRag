# Phase 07 — Step 05: MSD Signal Ablation & Calibration Audit

**Execution Date:** 2026-11-12  
**Branch:** `phase-7` (`cc1961e`)  
**Dataset:** `backup_security_combined_test` (`data/benchmarks_backup/knowledge_poisoning/test.jsonl` `n=24` + `adversarial_robustness/test.jsonl` `n=40` = **`64` docs**, `35` benign / `29` attack, `seed=42`)  
**Machine-Readable Artifact:** `reports/evaluation/phase07_step05_msd_ablation.json`

---

## 1. Individual Signal Evaluation (D1–D6)

| Signal | Config Policy | Available (`n/64`) | ROC-AUC | PR-AUC | Prec | Rec | F1 | FPR | Clean Mean ± Std | Poison Mean ± Std | Verdict on Signal Utility |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| **F1 `perplexity`** | `disabled` | `0/64` | — | — | — | — | — | — | — | — | **`BLOCKED`** offline (no causal LM loaded) |
| **F2 `embedding_norm` (default)** | `require_configured` (`ref=None`) | `0/64` | 0.5000 | 0.4531 | 0.4531 | 1.0000 | 0.6237 | 1.0000 | — | — | Inactive without external clean norm reference |
| **F2 `embedding_norm` (TF-IDF opt-in)** | `allow_empirical_fallback` | `12/64` | **0.4704** | 0.4445 | 0.4423 | 0.7931 | 0.5679 | 0.8286 | — | — | Rejects `52/64` docs; worse than random on TF-IDF norms |
| **F3 `query_match`** | `tfidf_raw` + lex | `64/64` | **0.6670** | 0.6212 | 0.4531 | 1.0000 | 0.6237 | 1.0000 | `0.3115 ± 0.1306` | `0.2668 ± 0.1184` | Weak standalone separation (`+0.0447` clean gap) |
| **F4 `instruction_content`** | regex / obfuscation / flood | `64/64` | **0.7414** | 0.7171 | **1.0000** | 0.4828 | **0.6512** | **0.0000** | `1.0000 ± 0.0000` | `0.5448 ± 0.4753` | **Primary driver** (`14/14` instruction/DoS hits, `0` FP) |
| **F5 `consensus_deviation`** | pairwise cosine + polarity/num | `64/64` | **0.4586** | 0.4343 | 0.4167 | 0.5172 | 0.4615 | **0.6000** | `0.4700 ± 0.3919` | `0.5362 ± 0.3998` | Symmetrically penalizes BOTH clean & poisoned peers alone |
| **F6 `provenance`** | `provenance_priors={}` (`source_id` trace) | `64/64` | 0.5000 | 0.4531 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `0.7500 ± 0.0000` | `0.7500 ± 0.0000` | Zero variance across synthetic test corpus (`std=0.0`) |

---

## 2. Pairwise Signal Combinations (Active Signals `F3..F6`)

| Signal Pair | ROC-AUC | PR-AUC | F1 | Precision | Recall | FPR | Brier | ECE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `instruction_content + consensus_deviation` (`F4+F5`) | **0.8448** | 0.7828 | **0.6512** | **1.0000** | 0.4828 | **0.0000** | 0.1814 | 0.1909 |
| `query_match + instruction_content` (`F3+F4`) | 0.7798 | **0.7998** | **0.6512** | **1.0000** | 0.4828 | **0.0000** | **0.1774** | **0.1112** |
| `instruction_content + provenance` (`F4+F6`) | 0.7414 | 0.7171 | **0.6512** | **1.0000** | 0.4828 | **0.0000** | 0.2112 | 0.2150 |
| `query_match + provenance` (`F3+F6`) | 0.6670 | 0.6212 | 0.6517 | 0.4833 | 1.0000 | 0.8857 | 0.2453 | 0.1126 |
| `query_match + consensus_deviation` (`F3+F5`) | 0.5315 | 0.4771 | 0.7342 | 0.5800 | 1.0000 | 0.6000 | 0.3105 | 0.2608 |
| `consensus_deviation + provenance` (`F5+F6`) | 0.4586 | 0.4343 | 0.7342 | 0.5800 | 1.0000 | 0.6000 | 0.2958 | 0.2137 |

**Finding:** `F4 + F5` achieves the highest rank separation (**`ROC-AUC = 0.8448`**) because `F5` spreads pure factual conflicts below `0.85` while `F4` anchors overt attacks at the bottom (`<0.38`) — yet without `F4`, pairs (`F3+F5`, `F5+F6`) trigger `60%` false-positive rates!

---

## 3. Full Fusion & Leave-One-Signal-Out (LOO) Analysis

| Configuration | ROC-AUC | Δ ROC-AUC vs Active-4 | PR-AUC | Prec | Rec | F1 | Δ F1 | FPR | Brier | ECE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Full Active-4 (`F3+F4+F5+F6`, Raw)** | **0.8315** | Baseline | **0.8320** | **1.0000** | 0.4828 | **0.6512** | Baseline | **0.0000** | **0.1750** | **0.1697** |
| **Active-4 + `platt-mixed-v1` Calibrated** | **0.8315** | `0.0000` | **0.8320** | 0.7000 | 0.4828 | 0.5714 | `-0.0798` | **0.1714** | 0.1828 | 0.1906 |
| **Active-4 + `F2_empirical_optin` (TF-IDF L2)** | **0.8039** | **`-0.0276`** | 0.8300 | 1.0000 | 0.4828 | 0.6512 | `0.0000` | 0.0000 | 0.1853 | 0.1523 |
| **LOO: `without_query_match` (`-F3`)** | **0.8448** | **`+0.0133`** | — | 1.0000 | 0.4828 | 0.6512 | `0.0000` | 0.0000 | 0.2101 | — |
| **LOO: `without_instruction_content` (`-F4`)** | **0.5315** | **`-0.3000`** | — | — | — | 0.7342 | `+0.0830` | **0.6000** | 0.2984 | — |
| **LOO: `without_consensus_deviation` (`-F5`)** | **0.7798** | **`-0.0517`** | — | 1.0000 | 0.4828 | 0.6512 | `0.0000` | 0.0000 | 0.1903 | — |
| **LOO: `without_provenance` (`-F6`)** | **0.8315** | `0.0000` | — | — | — | 0.5714 | **`-0.0798`** | **0.1714** | 0.1588 | — |

**Signal-Value Conclusions (Step 05 Mandate):**
1. **`F4` is essential** (`-0.3000` AUC on removal).
2. **`F5` adds genuine ranking value** (`-0.0517` AUC on removal) by flagging peer conflicts, though clean peers suffer symmetric conflict drops.
3. **TF-IDF `F3` slightly *degrades* ranking (`-0.0133` vs LOO without F3)** when `F4+F5+F6` are present, though it helps lower Brier error (`0.2101 -> 0.1750`).
4. **TF-IDF `F2_empirical` hurts rank separation (`-0.0276` AUC)** — Paper B requires real dense neural embeddings for `F2`, not unnormalized TF-IDF L2 norms.
5. **`F6` has zero discriminative AUC (`0.5000`), yet acts as an accidental positive intercept (`+0.75`)** whose removal exposes conflicted clean docs (`FPR 0.00 -> 0.1714`).
6. **`F1` remains unverified (`BLOCKED`) offline.**

---

## 4. Calibration, Threshold Sensitivity, Clean-vs-Poisoned Distributions & False Analysis

- **Distributions (`Active-4 Raw trust_score`):**
  - Clean (`n=35`): `mean = 0.8304`, `std = 0.1108`, `median = 0.8028`, `min = 0.6783`, `max = 0.9654`.
  - Poisoned (`n=29`): `mean = 0.5175`, `std = 0.2625`, `median = 0.7295`, `min = 0.1981`, `max = 0.8455`.
- **Calibration Regression (`platt-mixed-v1` on unseen `test n=64`):** While train-domain calibration targeted mixed clean+attack priors, on held-out `test`, `platt-mixed-v1` pushes clean `mean` from `0.8304 -> 0.8519` while widening `min` down to **`0.5770`**, pushing `6` clean `KNOWLEDGE_POISONING` docs below `0.60` (`FPR: 0.0000 -> 0.1714`, `Brier: 0.1750 -> 0.1828`, `ECE: 0.1697 -> 0.1906`).
- **Threshold Sensitivity (`raw trust_score < theta`, `n=64`):**
  - `theta = 0.20`: Prec `1.000`, Rec `0.1034`, F1 `0.1875`, FPR `0.000`.
  - **`theta in [0.30, 0.65]`:** Completely flat plateau (`Prec=1.0000`, `Rec=0.4828`, `F1=0.6512`, `FPR=0.0000`, `TP=14`, `FN=15`)! Because clean minimum (`0.6783`) and overt-poison maximum (`<0.30`) have a clean gap while subtle factual flips sit mixed in `[0.7295 .. 0.8455]`!
  - `theta = 0.70`: `Prec=0.6087`, `Rec=0.4828`, `F1=0.5385`, **`FPR=0.2571` (`9` clean FP)**.
  - `theta = 0.75`: `Prec=0.6667`, `Rec=0.7586`, `F1=0.7097`, **`FPR=0.3143` (`11` clean FP)**.
- **False-Negative & False-Positive Breakdown (at `poison_threshold=0.38`):**
  - **False Positives:** `0` at raw default `0.38` (`6` on `KNOWLEDGE_POISONING` clean peers under `platt-mixed-v1 < 0.60`).
  - **False Negatives (`15/29`, `FNR=51.7%`):** Exclusively **`KNOWLEDGE_POISONING` (`8/8` missed)** and **`CONFLICTING_EVIDENCE` (`7/7` missed)** — semantic factual lies with zero syntactic injection markers.

---

## 5. `BLOCKED` Ablation Reproducible Specification (`F1_perplexity` & Dense `F2_embedding_norm`)

To unblock F1 and neural F2 in Phase 08:
1. **F1 Spec:** Load causal LM `Qwen2.5-1.5B` or `GPT-2` locally (`device=cpu/cuda`); compute token-level perplexity `exp(-1/T sum log P(w_t | w_<t))` on `data/benchmarks_backup/clean_rag/train` (`N=70`) to freeze `perplexity_reference_mean` and `perplexity_reference_std`; pass `perplexity_callable` to `MultiSignalDetector`; sweep `weight_perplexity in {0.4, 0.8, 1.2}` on `backup/val` before locked test on `backup/test` (`n=64`).
2. **Dense F2 Spec:** Encode passages with `BAAI/bge-base-en-v1.5` or `all-MiniLM-L6-v2` (unnormalized embeddings); compute clean-corpus norm baseline `(mean, std)` on `train`; re-run LOO vs active-4 to measure whether real neural L2 norms avoid the `-0.0276` ROC-AUC regression observed with TF-IDF L2 norms.

