# Phase 27 — Dataset Provenance & Integrity Audit

---

## 1. Overview of Evaluated Datasets

All evaluation datasets used across Phases 25, 26, and 27 are stored in `data/benchmarks/` and have been cryptographically verified.

| Dataset Name | Relative Path | Sample Count | SHA-256 Checksum | Origin / Provenance |
| :--- | :--- | :--- | :--- | :--- |
| `phase26_adversarial_generalization` | `data/benchmarks/phase26_adversarial_generalization.jsonl` | 500 | `4b68480aebe21f3fce6007e6ce140c94a28f73dd49969542a230752533261ea6` | Phase 26 Red-Team Synthesis (13 categories) |
| `phase26_benign_controls` | `data/benchmarks/phase26_benign_controls.jsonl` | 500 | `47a9fe0b396f4fc9ffb19f6a5d447a192bb3b33da2e673ba7e6db69b59637b56` | Phase 26 Enterprise Benign Queries (10 domains) |
| `phase25_adversarial_evaluation` | `data/benchmarks/phase25_adversarial_evaluation.jsonl` | 164 | `6bf45cbcf7047f08b53cf5dbbb7a79f3df934f5521c752c0f644b9b9423c914b` | Phase 25 Curated Remediation Set |
| `phase25_benign_controls` | `data/benchmarks/phase25_benign_controls.jsonl` | 505 | `7a0c83dff4bca81c15c2ec85800ec9a41e974bc2799307c087e35b7582522765` | Phase 25 Clean Enterprise Controls |
| `clean_rag_train` | `data/benchmarks/clean_rag/train.jsonl` | 2000 | `76e651e089270e53a33909ea2b8e390c9b7f5835b1d428bfbce900f6b4991191` | Clean RAG anchor corpus |

---

## 2. Integrity Verification

All datasets are immutable text files in JSON Lines (`.jsonl`) format. The SHA-256 checksums recorded above match the actual files on disk with zero divergence.
