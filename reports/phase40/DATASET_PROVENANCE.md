# Dataset Provenance & Split Hygiene

- **Development Corpora (Used for `semantic_sec_v3.pkl` & `multilingual_sec_v3.pkl`):**
  - `reports/phase40/datasets/g1_dev_corpus.jsonl` ($N=82$: 47 attacks, 35 benign)
  - `reports/phase40/datasets/multilingual_dev_corpus.jsonl` ($N=56$: 36 attacks, 20 benign)
- **Untouched Evaluation Holdouts (Generated via `generate_phase40_holdout.py` after freezing `src/`):**
  - `holdout_g1.jsonl` ($N=280$)
  - `holdout_firewall.jsonl` ($N=150$)
  - `holdout_multilingual.jsonl` ($N=360$)
  - `holdout_g3.jsonl` ($N=120$)
- **Hygiene:** Zero Phase 39 holdout examples were used for tuning or training.
