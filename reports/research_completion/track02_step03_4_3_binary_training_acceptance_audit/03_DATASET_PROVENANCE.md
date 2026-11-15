# Track 2, Step 3.4.3 — Section 03: Dataset Provenance and Leakage Audit

## 1. Split Census and Distribution Audit

- **Training Subset:** Exactly 1,000 records from `data/processed/sft_v2/binary/train.jsonl`.
  - `halueval`: 500 records (250 FACTUAL, 250 HALLUCINATED)
  - `ragtruth`: 500 records (250 FACTUAL, 250 HALLUCINATED)
  - Total: 500 FACTUAL (50.0%), 500 HALLUCINATED (50.0%).
- **Validation Subset:** Exactly 200 records from `data/processed/sft_v2/binary/validation.jsonl`.
  - `halueval`: 100 records (50 FACTUAL, 50 HALLUCINATED)
  - `ragtruth`: 100 records (50 FACTUAL, 50 HALLUCINATED)
  - Total: 100 FACTUAL (50.0%), 100 HALLUCINATED (50.0%).

---

## 2. Document & Example Leakage Audit

- **Example ID Overlap:**
  $$\text{Intersection}(\text{Train IDs}, \text{Val IDs}) = \emptyset \quad (|\text{Overlap}| = 0)$$
- **Test Set Protection:**
  - Neither the training script nor the evaluation loops targeted `test.jsonl`.
  - Zero test records were accessed during training or validation.
- **Dataset File Hashes:**
  - `train.jsonl` (SHA-256: `28014e3000632d4fc02e088a24d5ba7e5be156173d19ebf4a0a4c28424269d03`)
  - `validation.jsonl` (SHA-256: `0a80e1ec608d002a0a2df3358055609ee35b3be79f17066929e79870be5f60cb`)
  Both files remain 100% bit-for-bit unchanged from their remediated baseline.
