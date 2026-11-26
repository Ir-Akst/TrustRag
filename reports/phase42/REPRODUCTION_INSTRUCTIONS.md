# Phase 42 Reproduction Instructions

- **Environment:** `/home/aditya/rags/.venv-phase15-clean10/bin/python` (Python 3.10.22, `torch 2.14.1+cpu`, `transformers 5.20.2`, `scikit-learn 1.7.2`, `numpy 2.2.6`, `scipy 1.15.3`).
- **Random Seed:** `42`.
- **Command:**
  ```bash
  cd /home/aditya/rags/TrustRag-phase11
  PYTHONPATH=src /home/aditya/rags/.venv-phase15-clean10/bin/python reports/phase42/scripts/run_phase42_experiments.py
  ```
- **Outputs:** `reports/phase42/STATISTICAL_ANALYSIS.json` and `reports/phase42/RAW_EXPERIMENT_RESULTS/*`.
