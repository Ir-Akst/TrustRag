# TrustRAG Phase 10 — Isolated FilterRAG Evaluation Report

**Run ID:** `phase10_20261112T073204Z_canonical_v2` | **Seed:** `42` | **Isolation:** `MSDConfig.enable_freq_density = False` (production untouched)  
**Evaluation Mode:** `extractive_proxy` (`slm_available = False`; **SLM component `BLOCKED`**)

| Variant | Status | ROC-AUC | PR-AUC | Precision | Recall | F1 | Sec Clean FPR | Clean RAG Retention (`n=75`) | Clean RAG FP |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Original_RAG` | `COMPLETED` | 0.5000 | 0.4531 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | **1.0000** | 0 |
| `TrustRAG_MSD` | `COMPLETED` | **0.8315** | **0.8320** | **1.0000** | 0.4828 | **0.6512** | 0.0000 | **1.0000** | 0 |
| `FilterRAG_Threshold` (`eps=0.70`) | `PROXY_ONLY` | 0.6897 | 0.6606 | 1.0000 | 0.3793 | 0.5500 | 0.0000 | **0.2000** | **60** |
| `ML_FilterRAG` | `PROXY_ONLY` | 0.2990 | 0.3710 | 0.4167 | 0.8621 | 0.5618 | 1.0000 | 0.8000 | 15 |
| `Combined_MSD_FilterRAG` | `PROXY_ONLY` | 0.8315 | 0.8320 | 1.0000 | 0.4828 | 0.6512 | 0.0000 | **0.2000** | **60** |

**Key Finding:** Under the extractive Frequency Density proxy (`slm_available=False`), `FilterRAG_Threshold` severely harms clean retrieval retention (`0.2000`, `60/75` clean documents falsely rejected), whereas `TrustRAG_MSD` preserves `1.0000` clean retention (`0` false positives). Live SLM-based FilterRAG reproduction remains **BLOCKED** offline.
