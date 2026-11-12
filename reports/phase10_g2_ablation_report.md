# TrustRAG Phase 10 — G2 Multi-Signal Detector Ablation & Calibration Report

**Evaluation Set:** `knowledge_poisoning` + `adversarial_robustness` test partitions (`n=64`, `29` attack / `35` clean)

## 1. Leave-One-Out Signal Ablations & Calibration

| Configuration | Accuracy | Precision | Recall | F1 | FPR | ROC-AUC | PR-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `full_g2_uncalibrated` | **0.7656** | **1.0000** | 0.4828 | 0.6512 | **0.0000** | 0.8315 | 0.8320 |
| `full_g2_train_calibrated` | 0.7188 | 0.6667 | **0.7586** | **0.7097** | 0.3143 | 0.8315 | 0.8320 |
| `without_F1_perplexity` | 0.7656 | 1.0000 | 0.4828 | 0.6512 | 0.0000 | 0.8315 | 0.8320 |
| `without_F2_embedding_norm` | 0.7656 | 1.0000 | 0.4828 | 0.6512 | 0.0000 | 0.8315 | 0.8320 |
| `without_F3_query_match` | 0.7656 | 1.0000 | 0.4828 | 0.6512 | 0.0000 | **0.8448** | 0.7828 |
| `without_F4_instruction_content` | **0.5156** | 0.4750 | 0.6552 | 0.5507 | **0.6000** | **0.5315** | **0.4771** |
| `without_F5_consensus_deviation` | 0.7656 | 1.0000 | 0.4828 | 0.6512 | 0.0000 | 0.7798 | 0.7998 |
| `without_F6_provenance_prior` | 0.6250 | 0.6087 | 0.4828 | 0.5385 | **0.2571** | 0.8315 | 0.8320 |

## 2. Signal Availability & Key Findings
- **Offline Availability (sample corpus):** `query_match` (`1.0`), `instruction_content` (`1.0`), `consensus_deviation` (`1.0`); `perplexity` (`0.0` — no causal LM), `embedding_norm` (`0.0` — no dense neural model), `provenance_prior` (`0.0` on unmapped provenance strings, fallback prior `0.75` in batch).
- **Dominant Signal (`F4`):** Removing `F4_instruction_content` collapses ROC-AUC from `0.8315` to `0.5315` and spikes FPR to `0.6000`.
- **Clean Protection (`F6`):** Removing `F6_provenance_prior` raises FPR from `0.0000` to `0.2571`.
- **Consensus (`F5`):** Removing `F5_consensus_deviation` drops ROC-AUC from `0.8315` to `0.7798`.
- **Calibration Trade-off:** Fitting `TrustCalibrator` strictly on `train` increases recall (`0.4828` -> `0.7586`, `F1=0.7097`) at the cost of `0.3143` FPR.
- **Adversarial Edge Cases:** On symmetric 50/50 factual substitution, both documents receive identical trust scores (`0.8997`), confirming the heuristic limit without causal LM/NLI; missing metadata yields `0.8148` without crashing. Removal cap (`<= 0.5`) remains enforced.
