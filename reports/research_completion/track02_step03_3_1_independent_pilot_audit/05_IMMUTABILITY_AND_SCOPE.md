# Track 2, Step 3.3.1 — Section 05: Immutability and Scope Audit

## 1. Dataset Immutability Verification

All 18 dataset files across `data/processed/sft_v2/` were independently audited against their SHA-256 checksums:

- `data/processed/sft_v2/binary/` (5/5 files OK):
  - `dataset_manifest.json`: `6cb54641c888d3824bb884d5df3324a35016e7dd7ce606e1b73e5bf7d02ff86e`
  - `exclusion_manifest.json`: `2f0da64a2ba437f1912a76f238b7250ea546ba8c919d363ef80fece789539f16`
  - `schema.json`: `3d8429f56e9c93a90729ee9449f2b87fcf39369974249a21e7d0cf0c0347ee63`
  - `train.jsonl`: `28014e3000632d4fc02e088a24d5ba7e5be156173d19ebf4a0a4c28424269d03`
  - `validation.jsonl`: `0a80e1ec608d002a0a2df3358055609ee35b3be79f17066929e79870be5f60cb`
- `data/processed/sft_v2/nli/` (5/5 files OK)
- `data/processed/sft_v2/spans/` (5/5 files OK)
- `data/processed/sft_v2/g3_readiness/` (3/3 files OK)
- Historical baseline `data/processed/sft_v1/` (5/5 files OK)

Zero dataset modifications occurred.

## 2. Baseline & Model Immutability

- Protected baseline `/home/aditya/rags/TrustRag` remains on branch `phase-10`, commit `e65bcc80aac634900d1f8e343880fddf66cec168`, untouched.
- Staged pretrained model files in `/home/aditya/rags/models/pretrained/deberta-v3-small` remain 100% bit-for-bit identical to the staging manifest.
- No temporary checkpoints were written into the repository.
