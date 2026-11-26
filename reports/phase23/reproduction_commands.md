# TrustRAG Phase 23: Reproduction Commands & Audit Guide

This document lists the exact bash commands required to independently reproduce all Phase 23 evaluation metrics, launch the Operations Console, verify checksums, and run unit tests.

---

## 1. Environment Verification

```bash
cd /home/aditya/rags/TrustRag-phase11
git checkout phase-23-live-malicious-prompt-validation

# Verify git anchor release commit
git rev-parse trustrag-v1.0.0-rc1^{commit}
# Expected: 531bff32745ede1bd1b38609cc6daf653d3eff24
```

---

## 2. Frozen DeBERTa Checkpoint SHA-256 Verification

```bash
cd /home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch
sha256sum -c checksums.sha256
# Expected output: All 8 files OK
```

---

## 3. Launch Operations Console Backend

```bash
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=.:src /home/aditya/rags/.venv-phase15-clean10/bin/python src/trustrag/api/server.py \
  --port 8000 \
  --corpus-path data/benchmarks/clean_rag/train.jsonl
```

---

## 4. Run Automated End-to-End Live Verification

In a separate terminal (while server is running on port 8000):

```bash
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=.:src /home/aditya/rags/.venv-phase15-clean10/bin/python tools/evaluation/run_phase23_e2e_verification.py
# Expected output: E2E Audit Complete: 15/15 passed (100.0%)
```

---

## 5. Run Comprehensive 13-Category Red-Team Evaluation

```bash
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=.:src /home/aditya/rags/.venv-phase15-clean10/bin/python tools/evaluation/run_phase23_redteam_evaluation.py
# Expected output:
# Total Evaluated: 140 (Adversarial: 120, Benign: 20)
# Attack Detection Rate (ADR): 95.83% (95% CI: [90.62%, 98.21%])
# Attack Success Rate (ASR):   4.17% (95% CI: [1.79%, 9.38%])
# Clean False Positive Rate:   0.00% (95% CI: [0.0%, 16.11%])
# Clean Delivery Rate:        100.00% (95% CI: [83.89%, 100.0%])
# Precision: 100.00% | Recall: 95.83% | F1: 97.87%
# Latency P50: 0.129 ms | P95: 1.15 ms | P99: 1.653 ms
```

---

## 6. Run Unit & Regression Tests

```bash
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=.:src /home/aditya/rags/.venv-phase15-clean10/bin/pytest tests/unit/ -k "test_phase_05 or test_guardrail" --tb=short -q
# Expected output: 24 passed in ~2s
```

---

## 7. Deliverables Verification

```bash
ls -la reports/phase23/
# Expected artifacts:
# - PHASE23_FINAL_REPORT.md
# - ui_activation_report.md
# - malicious_prompt_detection_audit.md
# - false_negative_analysis.md
# - security_remediation_report.md
# - red_team_results.csv
# - confusion_matrix.json
# - per_category_metrics.csv
# - latency_results.json
# - e2e_test_results.json
# - checkpoint_integrity.json
# - reproduction_commands.md
# - raw_predictions/phase23_redteam_predictions.jsonl
```

