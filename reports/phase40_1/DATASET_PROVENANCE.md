# Phase 40.1 Dataset Provenance & Integrity

All Phase 40.1 holdout datasets were generated via `reports/phase40_1/scripts/generate_phase40_1_holdout.py` **after** freezing `src/` (Stage 6):
- `holdout_g1.jsonl` ($N=300$: 200 adversarial, 100 benign across 4 benign categories)
- `holdout_firewall.jsonl` ($N=150$: 100 malicious across 6 categories, 50 benign)
- `holdout_multilingual.jsonl` ($N=360$: 9 languages $\times$ 40 samples)
- `holdout_g3.jsonl` ($N=140$: 30 supported, 20 partially supported, 25 unsupported, 65 contradicted)
