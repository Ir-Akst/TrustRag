# Phase 10 Experiment Summary (`phase10_20261112T073204Z_canonical_v2`)

- **Git Commit:** `1ceb29c`
- **Config Hash:** `7ee49abbfe65ded1`
- **Seed:** `42`
- **Started:** `2026-11-12T07:32:04.330160+00:00`
- **Completed:** `2026-11-12T07:32:08.545671+00:00`

## Comparative Baselines

### Dataset: `knowledge_poisoning`
| Profile | n | Accuracy | Precision | Recall | F1 | FPR | ASR | Mean ms |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `original_rag` | 24 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 1.6944 |
| `static_trustrag` | 24 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 4.1767 |
| `adaptive_trustrag` | 24 | 0.5 | 0.5 | 0.6667 | 0.5714 | 0.6667 | 0.3333 | 4.3555 |
| `trustrag_no_g1` | 24 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 4.4735 |
| `trustrag_no_g2` | 24 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 4.2044 |
| `trustrag_no_g3` | 24 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 1.963 |
| `trustrag_no_srm` | 24 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 4.1204 |

### Dataset: `adversarial_robustness`
| Profile | n | Accuracy | Precision | Recall | F1 | FPR | ASR | Mean ms |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `original_rag` | 40 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 2.0955 |
| `static_trustrag` | 40 | 0.75 | 1.0 | 0.5 | 0.6667 | 0.0 | 0.5 | 4.3478 |
| `adaptive_trustrag` | 40 | 0.825 | 1.0 | 0.65 | 0.7879 | 0.0 | 0.35 | 4.4561 |
| `trustrag_no_g1` | 40 | 0.75 | 1.0 | 0.5 | 0.6667 | 0.0 | 0.5 | 4.1448 |
| `trustrag_no_g2` | 40 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 5.0044 |
| `trustrag_no_g3` | 40 | 0.75 | 1.0 | 0.5 | 0.6667 | 0.0 | 0.5 | 1.9629 |
| `trustrag_no_srm` | 40 | 0.75 | 1.0 | 0.5 | 0.6667 | 0.0 | 0.5 | 4.2385 |

### Dataset: `clean_rag`
| Profile | n | Accuracy | Precision | Recall | F1 | FPR | ASR | Mean ms |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `original_rag` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 1.7839 |
| `static_trustrag` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 5.6373 |
| `adaptive_trustrag` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 5.8188 |
| `trustrag_no_g1` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 5.5735 |
| `trustrag_no_g2` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 5.2295 |
| `trustrag_no_g3` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 2.2455 |
| `trustrag_no_srm` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 5.7428 |
