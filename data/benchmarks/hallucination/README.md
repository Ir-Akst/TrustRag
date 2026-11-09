# Dataset Card: benchmark_hallucination

## Summary
- **Dataset Name:** `benchmark_hallucination`
- **Schema Record Type:** `ClaimVerificationRecord`
- **Source Identifier / URL:** trustrag/benchmarks/hallucination
- **Source Revision:** `Unspecified`
- **License:** `MIT`
- **Access Conditions:** `open`
- **Workflow Usage Category:** `VALIDATION`
- **Split Type:** `custom`
- **Retrieval Date:** 2026-11-08T16:59:23.371966+00:00
- **Schema Version:** `1.0.0`
- **Preprocessing Version:** `1.0.0`

## Intended Use & Permissions
- Evaluating MSD and reasoning-model claim verification accuracy
- **Permitted for Training:** Yes
- **Permitted for Evaluation:** Yes

## Records and Split Statistics
- **Raw Records:** 11
- **Processed Records:** 11
- **Valid Records:** 11
- **Duplicate Records:** 0
- **Empty / Invalid Records:** 0
- **Split Seed:** 42

### Partition Sizes
- **train:** 7 records
- **val:** 1 records
- **test:** 3 records

## Files and Checksums
| Split | Split Type | Format | Records | Size (Bytes) | Relative Path | SHA-256 Checksum |
|---|---|---|---:|---:|---|---|
| train | custom | jsonl | 7 | 3760 | `train.jsonl` | `e2377a69cc64238e...` |
| val | custom | jsonl | 1 | 523 | `val.jsonl` | `a2bb0fbef7fed92f...` |
| test | custom | jsonl | 3 | 1551 | `test.jsonl` | `fc6a74dd7e88de89...` |

## Known Biases and Limitations
None documented.

## Preprocessing Pipeline
1. Safe NFKC Unicode normalization.
2. Safe horizontal whitespace collapse preserving paragraph boundaries, punctuation, and negation.
3. Empty record filtering.
4. SHA-256 content-hash generation and exact duplicate elimination.
5. Leakage-resistant grouped train/val/test splitting with zero group and hash overlaps.
