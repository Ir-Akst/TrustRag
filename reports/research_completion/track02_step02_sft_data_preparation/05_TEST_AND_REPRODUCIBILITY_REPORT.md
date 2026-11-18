# TrustRAG Track 2, Step 2: Test & Reproducibility Report

## 1. Quality Assurance Verification Gates

All quality gates were executed within the sandboxed environment using Python 3.14 on Linux x86_64.

### 1.1 Dedicated SFT Data Prep Unit Test Suite
Command:
```bash
PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest tests/unit/test_track02_step02_sft_data_prep.py -v
```
Result: **8/8 PASSED in 0.50s**
- `test_sft_record_schema_validation`: PASSED
- `test_sft_schema_rejects_extra_fields`: PASSED
- `test_record_counts_and_distributions`: PASSED
- `test_zero_leakage_between_train_and_val`: PASSED
- `test_zero_leakage_with_test_splits`: PASSED
- `test_retrieval_benchmarks_quarantined`: PASSED
- `test_provenance_and_target_validity`: PASSED
- `test_checksum_file_integrity`: PASSED

### 1.2 Full Unit Test Regression Suite
Command:
```bash
PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest tests/unit/ -q
```
Result: **693 passed in 24.43s** (0 regressions, 0 warnings).

### 1.3 Static Type Checking (`mypy`)
Commands:
```bash
/home/aditya/rags/.venv/bin/mypy src
/home/aditya/rags/.venv/bin/mypy tools/data_prep/prepare_sft_dataset.py tests/unit/test_track02_step02_sft_data_prep.py
```
Result:
- `src`: **Success: no issues found in 112 source files.**
- `tools/data_prep` and test: **Success: no issues found in 2 source files.**

### 1.4 Code Formatting and Linting (`ruff`)
Command:
```bash
/home/aditya/rags/.venv/bin/ruff check tools/data_prep/prepare_sft_dataset.py tests/unit/test_track02_step02_sft_data_prep.py
```
Result: **All checks passed!**

### 1.5 Bytecode Compilation (`compileall`)
Command:
```bash
/home/aditya/rags/.venv/bin/python -m compileall src tools/data_prep tests/unit/test_track02_step02_sft_data_prep.py
```
Result: **100% clean compilation without errors.**

---

## 2. Deterministic Reproduction Instructions

To reproduce the `sft_v1` dataset from scratch:

```bash
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=src /home/aditya/rags/.venv/bin/python tools/data_prep/prepare_sft_dataset.py \
    --data-dir data \
    --output-dir data/processed/sft_v1 \
    --seed 42 \
    --ragtruth-val-ratio 0.20
```

To verify cryptographic file hashes:
```bash
cd /home/aditya/rags/TrustRag-phase11/data/processed/sft_v1
sha256sum -c checksums.sha256
```

Expected output:
```text
dataset_manifest.json: OK
preprocessing_report.md: OK
schema.json: OK
train.jsonl: OK
validation.jsonl: OK
```

