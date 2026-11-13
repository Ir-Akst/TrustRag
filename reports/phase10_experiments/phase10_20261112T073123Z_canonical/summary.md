# Phase 10 Experiment Summary (`phase10_20261112T073123Z_canonical`)

- **Git Commit:** `1ceb29c`
- **Config Hash:** `7ee49abbfe65ded1`
- **Seed:** `42`
- **Started:** `2026-11-12T07:31:23.611556+00:00`
- **Completed:** `2026-11-12T07:31:26.559700+00:00`

## Comparative Baselines

### Dataset: `knowledge_poisoning`
| Profile | n | Accuracy | Precision | Recall | F1 | FPR | ASR | Mean ms |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `original_rag` | 24 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 0.5433 |
| `static_trustrag` | 24 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 1.4382 |
| `adaptive_trustrag` | 24 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | None | 1.3745 |
| `trustrag_no_g1` | 24 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 1.2856 |
| `trustrag_no_g2` | 24 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 1.373 |
| `trustrag_no_g3` | 24 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 0.8461 |
| `trustrag_no_srm` | 24 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 1.3828 |

### Dataset: `adversarial_robustness`
| Profile | n | Accuracy | Precision | Recall | F1 | FPR | ASR | Mean ms |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `original_rag` | 40 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 0.6141 |
| `static_trustrag` | 40 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 2.0113 |
| `adaptive_trustrag` | 40 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 1.6904 |
| `trustrag_no_g1` | 40 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 1.5789 |
| `trustrag_no_g2` | 40 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 1.416 |
| `trustrag_no_g3` | 40 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 0.9597 |
| `trustrag_no_srm` | 40 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 1.7245 |

### Dataset: `clean_rag`
| Profile | n | Accuracy | Precision | Recall | F1 | FPR | ASR | Mean ms |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `original_rag` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 2.0626 |
| `static_trustrag` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 6.6717 |
| `adaptive_trustrag` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 6.3817 |
| `trustrag_no_g1` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 5.9041 |
| `trustrag_no_g2` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 5.7583 |
| `trustrag_no_g3` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 3.2057 |
| `trustrag_no_srm` | 15 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | None | 6.1897 |
