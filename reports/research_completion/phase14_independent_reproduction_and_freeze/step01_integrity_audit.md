# TrustRAG Phase 14 — Step 01: Git, Artifact & Checkpoint Integrity Audit

**Role:** Independent Senior ML Research Auditor, RAG Security Engineer & Reproducibility Specialist  
**Date:** November 18, 2026  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Current Audit Branch:** `phase-14` (branched from `aba5cc9d`)  
**Frozen Model Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  
**Artifact Directory:** `reports/research_completion/phase14_independent_reproduction_and_freeze/`

---

## 1. Executive Summary

This independent audit rigorously examines the repository state, commit history, frozen model checkpoints, raw evaluation datasets, and experimental manifests across TrustRAG Phases 10, 11, 12, and 13.

### Core Audit Findings:
1. **Model Weights Immutability:** The frozen DeBERTa-v3-small checkpoint (`model.safetensors`) and all accompanying optimizer, scheduler, and tokenizer files match their original `checksums.sha256` bit-for-bit ($100\%$ integrity verified).
2. **Investigation of Phase 13 HEAD `aba5cc9d`:** While Phase 12 and 13 reports cited commit `aba5cc9d` as HEAD, forensic audit reveals that **665 lines of code across 12 files in `src/trustrag/` were active in the working directory as uncommitted modifications**. These include the core implementations of Neural G3 verification, multi-domain factual consistency matrices, 3-tier consensus resolution, and benchmark loaders.
3. **Dataset Provenance & Integrity:** `data/raw/custom_security/raw_train.jsonl` ($N=2,000$) is cleanly tracked in git with hash `823bca96...`. SFT v2 training and validation datasets match their official checksums ($100\%$).
4. **Phase 13 Manifest Discrepancy Discovered:** The JSON metric files in Phase 13 match their manifest hashes perfectly, but the 5 markdown reports in `phase13_generalization_and_hardening/` show updated hashes relative to `sha256_manifest.txt` due to post-manifest formatting updates ($04:19:26$ vs $04:19:56$).

---

## 2. Git History & Ancestry Audit

The commit history of `/home/aditya/rags/TrustRag-phase11` was traced from Phase 9 through Phase 14:

```
* aba5cc9d (HEAD -> phase-14, phase-13, phase-12, phase-11)
|   feat: complete Phase 11-13 remediations, reality audits, and project closure verification
* 8229aee8 phase-11(steps-04-09): audit, targeted remediation DEF-08..DEF-16, regression tests, and reports
* 5481d6aa phase-11(step-03): remediate DEF-01..DEF-07 with permanent regression tests and reports
* e65bcc8b (phase-10) phase-10: add evaluation harness, statistical validation, ablations, and research reports
* 1ceb29c9 (phase-9) phase-9(ui-deploy): add responsive SPA dashboard, integration tests, deployment config, and Phase 09 reports
```

### Forensic Analysis of Commit `aba5cc9d`:
- The Git log shows that `phase-11`, `phase-12`, and `phase-13` all point to commit `aba5cc9d`.
- **Finding:** Critical architectural features described in Phase 12 and Phase 13 reports were implemented directly in the working tree rather than isolated commits.
- **Uncommitted Modifications Discovered (12 files, +665 / -45 lines):**
  - `src/trustrag/verification/output_verifier.py` (+339 lines): Neural NLI integration, INT8 dynamic quantization loader, hybrid decision gating.
  - `src/trustrag/detection/signals.py` (+200 lines): Multi-domain antonym/polarity matrices, dimension/unit normalization, 3-tier consensus logic.
  - `src/trustrag/detection/msd.py` (+3 lines): Routing untrusted conflicting documents to `POISONED`.
  - `src/trustrag/config/engine_config.py` (+31 lines): VerificationConfig NLI parameters.
  - `src/trustrag/data/loaders/` (RAGTruth, HaluEval, HotpotQA, MS MARCO): Loader adaptors for benchmark evaluation.

---

## 3. Frozen NLI Checkpoint Cryptographic Audit

The reference checkpoint directory `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` was audited against its authoritative `checksums.sha256`:

| Checkpoint File | Authoritative SHA-256 | Recomputed SHA-256 | Verification Status |
| :--- | :--- | :--- | :---: |
| `model.safetensors` | `0464758a2cd31260b44af96093dd52c2824a8305278d136ec438c87ee2b92313` | `0464758a2cd31260b44af96093dd52c2824a8305278d136ec438c87ee2b92313` | **VERIFIED (100% MATCH)** |
| `checkpoint_meta.json` | `0bd573e73a940c4146e54be751a47237aa6b9c72a3800cd921d879dca108ee09` | `0bd573e73a940c4146e54be751a47237aa6b9c72a3800cd921d879dca108ee09` | **VERIFIED (100% MATCH)** |
| `config.json` | `38370396a4e2988a14226b6b8875766e660ab8bbd1374b9e23a6e0c7a05ef385` | `38370396a4e2988a14226b6b8875766e660ab8bbd1374b9e23a6e0c7a05ef385` | **VERIFIED (100% MATCH)** |
| `optimizer.pt` | `9a2fd299dd3961fdf66532f12c1bf9ff06365dcb6957e0bcc50487d6b9792ac7` | `9a2fd299dd3961fdf66532f12c1bf9ff06365dcb6957e0bcc50487d6b9792ac7` | **VERIFIED (100% MATCH)** |
| `rng_state.pt` | `437b2e84b3fc90e6bc22ef0a043a986cf6124d523be0962df7a988a44d452e12` | `437b2e84b3fc90e6bc22ef0a043a986cf6124d523be0962df7a988a44d452e12` | **VERIFIED (100% MATCH)** |
| `scheduler.pt` | `1d78acdcfbbbb16e77bbe7752380688630dfe37fa53954279a7d69d3ad41e648` | `1d78acdcfbbbb16e77bbe7752380688630dfe37fa53954279a7d69d3ad41e648` | **VERIFIED (100% MATCH)** |
| `tokenizer.json` | `e9ddd853a4a31023721c993458663f2019e3154a05dacf0d2b3c217e53d9bdc8` | `e9ddd853a4a31023721c993458663f2019e3154a05dacf0d2b3c217e53d9bdc8` | **VERIFIED (100% MATCH)** |
| `tokenizer_config.json`| `1121ad33ecd98a97b2db184ce896546feb7555bebddf33a2dfe1b1a1077dc847` | `1121ad33ecd98a97b2db184ce896546feb7555bebddf33a2dfe1b1a1077dc847` | **VERIFIED (100% MATCH)** |

**Conclusion:** The frozen NLI model checkpoint is completely intact and has not been retrained, touched, or modified.

---

## 4. Dataset Integrity & Manifest Verification

### 4.1 Evaluation & Training Datasets:
- `data/raw/custom_security/raw_train.jsonl`: SHA-256 `823bca9639587ff7170530a67c2b35c54d959ee2007bdb554c3e50143c4dae00` ($N=2,000$ lines, zero git diff).
- `data/processed/sft_v2/nli/train.jsonl`: SHA-256 `b1777c7ac608d6d79171dbc4deaeb7bf5c4ba87acf83adbe53d63020524474ad` ($100\%$ match).
- `data/processed/sft_v2/nli/validation.jsonl`: SHA-256 `7601dd266edde160c51e1032150ea42c031131cb6be89c601637ad464121615c` ($100\%$ match).

### 4.2 Phase 13 Deliverable Manifest Audit:
All Phase 13 JSON metric files match their recorded SHA-256 digests in `sha256_manifest.txt`:
- `step01_dataset_inventory.json`: `d0440df7...` (MATCH)
- `step02_g2_results.json`: `2bd778a4...` (MATCH)
- `step03_g3_metrics.json`: `d25a0b46...` (MATCH)
- `step04_end_to_end_metrics.json`: `e696f182...` (MATCH)

**Report Hash Discrepancy Note:** The 5 markdown reports in `reports/research_completion/phase13_generalization_and_hardening/` were modified at $04:19:56$ (30 seconds after `sha256_manifest.txt` was written at $04:19:26$) during final report formatting. Their current hashes have been captured in [`step01_hash_verification.json`](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/phase14_independent_reproduction_and_freeze/step01_hash_verification.json).

