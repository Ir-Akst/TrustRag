# 12 — Benchmark & Metrics Verification Audit

**Recomputation Sources:** [part4_metrics_and_phase10.json](file:///C:/Users/Dell/.gemini/antigravity/brain/9e1a4313-a77f-4ce1-9fae-83fef27597c4/scratch/part4_metrics_and_phase10.json), [part5_extras.json](file:///C:/Users/Dell/.gemini/antigravity/brain/9e1a4313-a77f-4ce1-9fae-83fef27597c4/scratch/part5_extras.json#L1340-L1389), [experiment_results.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/experiment_results.json)

---

## 1. Phase 10 Artifact Integrity Check (`100%` Mathematical Consistency)

Every `*_per_example.jsonl` log in `phase10_20261112T085610Z_phase11_remediated` (commit `e65bcc8`) and `phase10_20261112T073204Z_canonical_v2` (commit `1ceb29c`) was independently parsed and recomputed:
- **Sample Counts & Accuracies:** `100%` exact match (`acc_match = True` across all `21` dataset x system cells in both bundles).
- **Important Methodological Context:** These runs evaluated on synthetic `benchmarks_backup/` (`adv_rob` `n=40`, `kp` `n=24`) and sampled `boolq` (`clean_rag` `n=15`) with **SRM neural backends disabled** (`DeterministicFallbackBackend`) and extractive generation.

---

## 2. Recomputation Table + Wilson 95% CIs & McNemar Pairs (`phase11_remediated`)

| Dataset (`n`) | Baseline / Variant | Recomputed `acc` | Wilson 95% CI | Reported F1 | Reported FPR | Mean Lat (ms) | Notes / McNemar vs Static |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`adversarial_robustness` (`40`)** | `original_rag` | `0.5000` | `[0.352, 0.648]` | `0.0000` | `0.0000` | `2.5030` | Zero defense |
| `adversarial_robustness` (`40`) | `static_trustrag` | `0.7500` | `[0.5981, 0.8581]` | `0.6667` | `0.0000` | `4.6397` | Baseline |
| `adversarial_robustness` (`40`) | `adaptive_trustrag` | `0.8250` | `[0.6805, 0.9125]` | `0.7879` | `0.0000` | `4.4822` | `b=0, c=3` vs static (too few pairs for `p<0.05`) |
| `adversarial_robustness` (`40`) | `trustrag_no_g1` | `0.7500` | — | `0.6667` | `0.0000` | `4.3655` | Identical accuracy to `static` |
| `adversarial_robustness` (`40`) | **`trustrag_no_g2`** | **`0.5000`** | — | **`0.0000`** | `0.0000` | `5.3063` | Proves G2 drives all `adv_rob` gains |
| `adversarial_robustness` (`40`) | `trustrag_no_g3` / `no_srm` | `0.7500` | — | `0.6667` | `0.0000` | `2.059` / `4.545` | Zero marginal accuracy delta here |
| **`knowledge_poisoning` (`24`)** | `original_rag` | `0.5000` | — | `0.0000` | `0.0000` | `1.8009` | — |
| `knowledge_poisoning` (`24`) | `static_trustrag` | `0.5000` | `[0.3143, 0.6857]` | `0.0000` | `0.0000` | `4.5046` | No recall offline |
| `knowledge_poisoning` (`24`) | **`adaptive_trustrag`** | **`0.5000`** | `[0.3143, 0.6857]` | `0.5714` | **`0.6667`** | `4.5110` | **McNemar `b=8` static wins, `c=8` adaptive wins** (8 FP offset 8 TP; zero net accuracy gain) |
| **`clean_rag` (`15`)** | All `7` variants | `1.0000` | `[0.7961, 1.0000]` | `0.0000` | `0.0000` | `2.07 – 6.50` | `b=0, c=0`; small `n=15` (lower bound `79.6%`) |

---

## 3. G2 Ablations, G3 Unseen Probes, FilterRAG & External Benchmarks

- **G2 Ablations (`phase11_remediated`):** `full_g2_uncalibrated`, `without_F1_perplexity`, `without_F2_embedding_norm`, and `without_F3_query_match` all report identical **`F1 = 0.6512`, `FPR = 0.0`, `acc = 0.7656`**—confirming `F1`/`F2` are non-contributing offline.
- **G3 `canonical_v2` vs `phase11_remediated`:** `canonical_v2` failed `2/4` unseen probes (`acc = 0.50`, `macro_f1 = 0.50`); `remediated` tuned heuristics to reach `4/4` (`1.00`). Note `unseen_probes` contains only `4` total items.
- **FilterRAG Comparison (`filterrag_variants`):** `FilterRAG_Threshold`, `ML_FilterRAG`, and `Combined_MSD_FilterRAG` are explicitly labeled **`PROXY_ONLY`** (`mode=extractive_proxy`, no generative SLM). `ML_FilterRAG` achieved `ROC AUC = 0.2990`, `security_clean_fpr = 1.0`, while threshold/combined retained only `20%` of `clean_rag` (`clean_rag_fp = 60/75`).
- **Live External Runner (`run_all_external_benchmarks()`):**
  - `6/7 BLOCKED` (`0` records: `llm_aggrefact`, `rsb`, `halueval`, `natural_questions`, `hotpotqa`, `ms_marco`)
  - `1/7 PARTIALLY_READY` (`ragtruth`: **`5` records**, `acc = 0.60`, `f1 = 0.6667`, `fpr = 0.6667`, `parity_claimed = False`).

