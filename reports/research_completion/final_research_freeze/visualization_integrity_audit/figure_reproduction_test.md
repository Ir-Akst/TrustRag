# TrustRAG — Figure Reproduction Test & Technical Verification Log

**Auditor:** Senior ML Systems Engineer & Reproducibility Auditor  
**Date:** 2026-11-19T03:05:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Dedicated Branch:** `phase-17-20-final-release`  
**Release Tag Candidate:** `trustrag-v1.0.0-rc1` (Commit: `531bff3`)  
**Output Directory:** `reports/research_completion/final_research_freeze/visualization_integrity_audit/`  

---

## 1. Executive Summary & Test Mandate

This document logs the live technical reproduction test of the entire TrustRAG visualization suite, verifying that every figure can be deterministically re-generated from its underlying CSV data and Python generation scripts without manual intervention.

---

## 2. Test Environment & Software Stack

- **Operating System:** Linux 6.x (x86_64)
- **Python Executable:** `/usr/bin/python3` (Python 3.11.2)
- **Matplotlib Version:** `3.11.2`
- **NumPy Version:** `2.4.4`
- **Pandas Version:** `2.3.3`
- **Configuration Directory:** `export MPLCONFIGDIR=/tmp/mplconfig`

---

## 3. Live Reproduction Command & Execution Log

The reproduction script was executed from the repository root:

```bash
cd /home/aditya/rags/TrustRag-phase11
export MPLCONFIGDIR=/tmp/mplconfig
/usr/bin/python3 reports/research_completion/final_research_freeze/figures/scripts/generate_publication_figures.py
```

### Execution Log Output:
```
Starting Publication-Quality Figure Generation Campaign...
Generated: figure_01_architecture_comparison (PNG 300 DPI, PDF, SVG)
Generated: figure_02_attack_defense (PNG 300 DPI, PDF, SVG)
Generated: figure_03_clean_utility (PNG 300 DPI, PDF, SVG)
Generated: figure_04_nli_confusion_matrix (PNG 300 DPI, PDF, SVG)
Generated: figure_05_classwise_metrics (PNG 300 DPI, PDF, SVG)
Generated: figure_06_calibration (PNG 300 DPI, PDF, SVG)
Generated: figure_07_cpu_latency (PNG 300 DPI, PDF, SVG)
Generated: figure_08_batch_throughput (PNG 300 DPI, PDF, SVG)
Generated: figure_09_memory_profile (PNG 300 DPI, PDF, SVG)
Generated: figure_10_redteam_heatmap (PNG 300 DPI, PDF, SVG)
Generated: figure_11_external_benchmarks (PNG 300 DPI, PDF, SVG)
Generated: figure_12_security_latency_tradeoff (PNG 300 DPI, PDF, SVG)
Generated: figure_13_research_progress (PNG 300 DPI, PDF, SVG)
Generated: figure_index.md
All 13 publication figures successfully created with CSVs, PNGs, PDFs, and SVGs.
```
- **Execution Return Code:** `0` (Success).
- **Execution Duration:** $5.82\text{ seconds}$.

---

## 4. Multi-Format Export & Resolution Verification

All 13 figures were verified across all three required export formats:

| Figure Base Name | CSV Data | Raster PNG | Vector PDF | Vector SVG | PNG Dimensions (Pixels) | Measured DPI (pHYs Chunk) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `figure_01_architecture_comparison` | YES | YES | YES | YES | $2,319 \times 1,594$ | **300.00 DPI** |
| `figure_02_attack_defense` | YES | YES | YES | YES | $2,810 \times 1,686$ | **300.00 DPI** |
| `figure_03_clean_utility` | YES | YES | YES | YES | $2,569 \times 1,426$ | **300.00 DPI** |
| `figure_04_nli_confusion_matrix` | YES | YES | YES | YES | $2,124 \times 1,692$ | **300.00 DPI** |
| `figure_05_classwise_metrics` | YES | YES | YES | YES | $2,363 \times 1,465$ | **300.00 DPI** |
| `figure_06_calibration` | YES | YES | YES | YES | $2,571 \times 1,501$ | **300.00 DPI** |
| `figure_07_cpu_latency` | YES | YES | YES | YES | $2,331 \times 1,325$ | **300.00 DPI** |
| `figure_08_batch_throughput` | YES | YES | YES | YES | $2,344 \times 1,388$ | **300.00 DPI** |
| `figure_09_memory_profile` | YES | YES | YES | YES | $2,228 \times 1,371$ | **300.00 DPI** |
| `figure_10_redteam_heatmap` | YES | YES | YES | YES | $3,222 \times 2,076$ | **300.00 DPI** |
| `figure_11_external_benchmarks` | YES | YES | YES | YES | $2,206 \times 1,492$ | **300.00 DPI** |
| `figure_12_security_latency_tradeoff` | YES | YES | YES | YES | $2,571 \times 1,434$ | **300.00 DPI** |
| `figure_13_research_progress` | YES | YES | YES | YES | $2,973 \times 1,757$ | **300.00 DPI** |

**Binary DPI Verification:** Python binary inspection of the PNG `pHYs` chunks confirmed `unit = 1` (meters) with pixel-per-meter values corresponding to strictly **300.00 DPI** ($x\_ppm \times 0.0254 = 300.00$).

---

## 5. Master Checksum Verification

Cryptographic verification was executed via `sha256sum -c sha256_verification.txt`:

```bash
cd /home/aditya/rags/TrustRag-phase11/reports/research_completion/final_research_freeze
sha256sum -c sha256_verification.txt
```

### Verification Result:
- **Total Files Audited:** 31 files (5 final reports, 1 index, 12 CSV datasets, 13 PNG images).
- **Match Status:** **`31 / 31 OK (100.0%)`**. Zero checksum mismatches.

---

## 6. Checkpoint & Model Immutability Verification

The frozen DeBERTa-v3-small checkpoint at `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` was re-verified against canonical `checksums.sha256`:
- `checkpoint_meta.json`: **OK**
- `config.json`: **OK**
- `model.safetensors` (`0464758a...`): **OK**
- `optimizer.pt`: **OK**
- `rng_state.pt`: **OK**
- `scheduler.pt`: **OK**
- `tokenizer.json`: **OK**
- `tokenizer_config.json`: **OK**

**Status:** Model checkpoint is 100% immutable and uncorrupted.

---

## 7. Reproduction Test Verdict

The visualization campaign is **100% technically reproducible, deterministic, and cryptographically verified**.

