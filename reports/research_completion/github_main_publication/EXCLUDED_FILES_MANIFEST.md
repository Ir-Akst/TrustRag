# Excluded Files Manifest

The following files and directories were strictly excluded from publication to preserve repository hygiene, security, and active training integrity.

| Pattern / Relative Path | Exclusion Reason |
| --- | --- |
| `data/` (563 MB) | Large raw and processed JSONL datasets (halueval, hotpotqa, ms_marco, ragtruth, sft_v1, sft_v2) |
| `models/trained/` | Model weights, PyTorch binaries, and optimizer checkpoints |
| `models/pretrained/` | Pretrained base weights (DeBERTa-v3-small) |
| `reports/research_completion/phase11_1_step03_full_nli_training/training_execution.log` | Mutable log actively being written by running background PID 13069 |
| `reports/research_completion/phase11_1_step03_full_nli_training/*` | In-progress training campaign reports (to be published upon campaign completion) |
| `tools/evaluation/generate_step03_16_reports.py.v1_backup` | Temporary / backup script file |
| `**/__pycache__/**` | Python bytecode cache |
| `**/*.pyc` | Compiled Python objects |
| `.venv/`, `.venv-train/` | Local virtual environments |
| `reports/research_completion/phase11_1_step03_full_nli_training/CHECKPOINT_RECOVERY_LOG.md` | Live training in-progress campaign directory (contains mutable logs) |
| `reports/research_completion/phase11_1_step03_full_nli_training/EPOCH_VALIDATION_METRICS.md` | Live training in-progress campaign directory (contains mutable logs) |
| `reports/research_completion/phase11_1_step03_full_nli_training/FINAL_EVALUATION_REPORT.md` | Live training in-progress campaign directory (contains mutable logs) |
| `reports/research_completion/phase11_1_step03_full_nli_training/PREFLIGHT_REPORT.md` | Live training in-progress campaign directory (contains mutable logs) |
| `reports/research_completion/phase11_1_step03_full_nli_training/PROTECTED_ASSET_INTEGRITY.md` | Live training in-progress campaign directory (contains mutable logs) |
| `reports/research_completion/phase11_1_step03_full_nli_training/RESOURCE_TELEMETRY.md` | Live training in-progress campaign directory (contains mutable logs) |
| `reports/research_completion/phase11_1_step03_full_nli_training/TRAINING_EXECUTION_REPORT.md` | Live training in-progress campaign directory (contains mutable logs) |
| `reports/research_completion/phase11_1_step03_full_nli_training/checksums.sha256` | Live training in-progress campaign directory (contains mutable logs) |
| `reports/research_completion/phase11_1_step03_full_nli_training/training_execution.log` | Live training in-progress campaign directory (contains mutable logs) |
| `tools/evaluation/generate_step03_16_reports.py.v1_backup` | Temporary/backup file |
