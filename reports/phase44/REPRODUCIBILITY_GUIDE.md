# Phase 44 — Reproducibility Guide

## 1. Environment & Immutable Anchors
- **Repository:** `/home/aditya/rags/TrustRag-phase11`
- **Branch:** `phase-44-final-remediation-publication-freeze`
- **Parent Commit:** `9d6874e7ca65d5eb5e1440ab1205a7dffdf36cc1`
- **Release Anchor:** `531bff32745ede1bd1b38609cc6daf653d3eff24` (`trustrag-v1.0.0-rc1`)
- **Python Environment:** `/home/aditya/rags/.venv-phase15-clean10/bin/python`
- **Frozen Model:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`

## 2. Verify Model & Git Integrity
```bash
cd /home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch
sha256sum -c checksums.sha256

cd /home/aditya/rags/TrustRag-phase11
git merge-base --is-ancestor 531bff32745ede1bd1b38609cc6daf653d3eff24 HEAD
```

## 3. Run Unit & Regression Test Suites
```bash
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=src:. /home/aditya/rags/.venv-phase15-clean10/bin/pytest \
  tests/test_phase_04_suites.py \
  tests/unit/test_phase_40_security_regression.py \
  tests/unit/test_phase_40_1_regression.py \
  tests/unit/test_phase_44_remediation.py -q

PYTHONPATH=src:. /home/aditya/rags/.venv-phase15-clean10/bin/pytest tests/unit/ -q
```

## 4. Reproduce Phase 44 Evaluation (`STATISTICAL_RESULTS.json`)
```bash
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=src /home/aditya/rags/.venv-phase15-clean10/bin/python \
  reports/phase44/scripts/run_phase44_evaluation.py
```

## 5. Verify Artifact Checksums
```bash
cd /home/aditya/rags/TrustRag-phase11
sha256sum -c reports/phase44/ARTIFACT_SHA256_MANIFEST.txt
```

