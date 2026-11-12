# Phase 10 Experiment Summary (`phase10_20261112T085610Z_phase11_remediated`)

- **Git Commit:** `e65bcc8`
- **Config Hash:** `7ee49abbfe65ded1`
- **Seed:** `42`
- **Started:** `2026-11-12T08:56:10.458749+00:00`
- **Completed:** `2026-11-12T08:56:15.145851+00:00`

## Comparative Baselines

### Dataset: `knowledge_poisoning`
| Profile | n | Accuracy | Precision | Recall | F1 | FPR | ASR | Mean ms |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `original_rag` | 24 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 1.8009 |
| `static_trustrag` | 24 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 4.5046 |
| `adaptive_trustrag` | 24 | 0.5 | 0.5 | 0.6667 | 0.5714 | 0.6667 | 0.3333 | 4.511 |
| `trustrag_no_g1` | 24 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 4.384 |
| `trustrag_no_g2` | 24 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 4.2463 |
| `trustrag_no_g3` | 24 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 2.183 |
| `trustrag_no_srm` | 24 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 4.5202 |

### Dataset: `adversarial_robustness`
| Profile | n | Accuracy | Precision | Recall | F1 | FPR | ASR | Mean ms |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `original_rag` | 40 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 2.503 |
| `static_trustrag` | 40 | 0.75 | 1.0 | 0.5 | 0.6667 | 0.0 | 0.5 | 4.6397 |
| `adaptive_trustrag` | 40 | 0.825 | 1.0 | 0.65 | 0.7879 | 0.0 | 0.35 | 4.4822 |
| `trustrag_no_g1` | 40 | 0.75 | 1.0 | 0.5 | 0.6667 | 0.0 | 0.5 | 4.3655 |
| `trustrag_no_g2` | 40 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 5.3063 |
| `trustrag_no_g3` | 40 | 0.75 | 1.0 | 0.5 | 0.6667 | 0.0 | 0.5 | 2.0591 |
| `trustrag_no_srm` | 40 | 0.75 | 1.0 | 0.5 | 0.6667 | 0.0 | 0.5 | 4.5446 |

### Dataset: `clean_rag`
| Profile | n | Accuracy | Precision | Recall | F1 | FPR | ASR | Mean ms |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `original_rag` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 2.0672 |
| `static_trustrag` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 6.4978 |
| `adaptive_trustrag` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 6.4309 |
| `trustrag_no_g1` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 6.3995 |
| `trustrag_no_g2` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 6.0132 |
| `trustrag_no_g3` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 2.6075 |
| `trustrag_no_srm` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 6.4875 |
