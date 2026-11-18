# TrustRAG Track 2, Step 2.2: Test & Reproducibility Report

## 1. Quality Assurance Verification Gates

All verification gates were executed within the sandboxed environment using Python 3.14 on Linux x86_64.

### 1.1 Dedicated SFT Remediation Unit Test Suite
Command:
```bash
PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest tests/unit/test_track02_step02_2_sft_remediation.py -v
```
Result: **8/8 PASSED in 1.17s**
- `test_binary_dataset_schema_and_counts`: PASSED
- `test_binary_dataset_zero_document_leakage`: PASSED
- `test_binary_exclusion_manifest`: PASSED
- `test_nli_dataset_labels_and_mapping_rules`: PASSED
- `test_nli_exclusions`: PASSED
- `test_span_dataset_exact_character_offsets`: PASSED
- `test_g3_gap_specification_and_no_fabricated_records`: PASSED
- `test_sft_v2_all_checksums_pass`: PASSED

### 1.2 Baseline Regression Verification (`sft_v1`)
Command:
```bash
PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest tests/unit/test_track02_step02_sft_data_prep.py -v
```
Result: **8/8 PASSED in 0.63s** (confirms `sft_v1` baseline was untouched and remains 100% compliant).

### 1.3 Static Type Checking (`mypy`)
Command:
```bash
/home/aditya/rags/.venv/bin/mypy tools/data_prep/prepare_sft_v2_remediated.py tests/unit/test_track02_step02_2_sft_remediation.py
```
Result: **Success: no issues found in 2 source files.**

### 1.4 Code Formatting and Linting (`ruff`)
Command:
```bash
/home/aditya/rags/.venv/bin/ruff check tools/data_prep/prepare_sft_v2_remediated.py tests/unit/test_track02_step02_2_sft_remediation.py
```
Result: **All checks passed!**

### 1.5 Bytecode Compilation (`compileall`)
Command:
```bash
/home/aditya/rags/.venv/bin/python -m compileall tools/data_prep/prepare_sft_v2_remediated.py tests/unit/test_track02_step02_2_sft_remediation.py
```
Result: **100% clean compilation without errors.**

---

## 2. Deterministic Reproduction Instructions

To reproduce all four `sft_v2` datasets from scratch:

```bash
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=src /home/aditya/rags/.venv/bin/python tools/data_prep/prepare_sft_v2_remediated.py \
    --data-dir data \
    --output-base-dir data/processed/sft_v2 \
    --seed 42 \
    --val-ratio 0.20
```

To verify cryptographic file hashes across all subdirectories:
```bash
cd /home/aditya/rags/TrustRag-phase11
(cd data/processed/sft_v2/binary && sha256sum -c checksums.sha256)
(cd data/processed/sft_v2/nli && sha256sum -c checksums.sha256)
(cd data/processed/sft_v2/spans && sha256sum -c checksums.sha256)
(cd data/processed/sft_v2/g3_readiness && sha256sum -c checksums.sha256)
```

Expected output for each subdirectory:
```text
dataset_manifest.json: OK
exclusion_manifest.json: OK
schema.json: OK
train.jsonl: OK
validation.jsonl: OK
```

