# Git and Checkpoint Integrity Verification

## 1. Commit and Branch Ancestry
- Parent Commit: `ea06ff7f48a7c7d0e69cc567ea79acc146e6a79f`
- Phase 36 Commit Message: `Phase 36: semantic generalization, document firewall and evidence utility remediation`
- New Audit Branch: `phase-37-independent-security-validation`
- Working Tree Status: Clean prior to audit; only `reports/phase37/` deliverables added.

## 2. Release Anchor & Tag Verification
- Release Commit: `531bff32745ede1bd1b38609cc6daf653d3eff24` (Verified intact)
- Annotated Tag: `trustrag-v1.0.0-rc1` (Verified intact)

## 3. Checkpoint SHA256 Verification
All 8 files in `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` verified bit-exact via `sha256sum -c checksums.sha256`:
- `checkpoint_meta.json`: OK
- `config.json`: OK
- `model.safetensors`: OK
- `optimizer.pt`: OK
- `rng_state.pt`: OK
- `scheduler.pt`: OK
- `tokenizer.json`: OK
- `tokenizer_config.json`: OK
