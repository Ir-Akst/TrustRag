# TrustRAG — Track 2, Step 3.7: NLI Dataset Revalidation Audit

## 1. Census Revalidation

Independent re-inspection of `data/processed/sft_v2/nli/`:

| Split | Records | ENTAILMENT | CONTRADICTION | NEUTRAL | Empty / Malformed | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Train** | 10,815 | 6,707 (62.0%) | 1,420 (13.1%) | 2,688 (24.9%) | 0 | **VERIFIED** |
| **Validation** | 2,662 | 1,662 (62.4%) | 356 (13.4%) | 644 (24.2%) | 0 | **VERIFIED** |
| **Total** | 13,477 | 8,369 (62.1%) | 1,776 (13.2%) | 3,332 (24.7%) | 0 | **VERIFIED** |

---

## 2. Partition Isolation & Leakage Checks

- **Example ID Leakage:** `len(train_ids ∩ val_ids) == 0` (**0 overlapping IDs**).
- **Document / Premise Leakage:** `len(train_doc_hashes ∩ val_doc_hashes) == 0` (**0 overlapping documents**).
- **Test Set Quarantine:** Canonical test files (`data/processed/halueval/test.jsonl` and `data/processed/ragtruth/test.jsonl`) remain completely unvisited and unreferenced.

---

## 3. Pilot Sampler Determinism

Evaluating `load_nli_dataset(..., max_samples=1000, strategy="stratified_class_balanced")`:
- **Total Selected Samples:** Exactly **1,000 records**.
- **Class Composition:**
  * `ENTAILMENT`: **334 records**
  * `CONTRADICTION`: **333 records**
  * `NEUTRAL`: **333 records**
- **Determinism:** Two independent execution passes generated identical SHA-256 sequence order hashes.
