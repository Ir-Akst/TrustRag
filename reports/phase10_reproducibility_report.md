# TrustRAG Phase 10 — Reproducibility Report

## 1. Exact Reproduction Command
```bash
cd /home/aditya/rags/TrustRag
/home/aditya/rags/.venv/bin/python tools/run_phase10_benchmarks.py --seed 42 --run-tag canonical_v2
```

## 2. Recorded Run Metadata
- **Experiment ID:** `phase10_20261112T073204Z_canonical_v2`
- **Output Directory:** `reports/phase10_experiments/phase10_20261112T073204Z_canonical_v2/`
- **Artifacts Generated (Non-Overwriting):**
  - `bundle.json` (complete machine-readable results, SHA-256 dataset hashes, statistical CIs, and blocked flags)
  - `summary.md` (human-readable comparative tables)
  - `knowledge_poisoning_per_example.jsonl`
  - `adversarial_robustness_per_example.jsonl`
  - `clean_rag_per_example.jsonl`
- **Configuration File:** `configs/evaluation/phase10_eval.yaml` (`seed=42`, `offline=true`)
- **Config Hash:** `7ee49abbfe65ded1`
- **Git Commit:** `1ceb29c` (branched to `phase-10`)
