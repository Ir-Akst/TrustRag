# Dataset Card: benchmark_clean_rag

## Summary
- **Dataset Name:** `benchmark_clean_rag`
- **Schema Record Type:** `QueryRecord`
- **Source Identifier / URL:** trustrag/benchmarks/clean_rag
- **Source Revision:** `Unspecified`
- **License:** `CC-BY-SA-3.0`
- **Access Conditions:** `open`
- **Workflow Usage Category:** `VALIDATION`
- **Split Type:** `custom`
- **Retrieval Date:** 2026-11-08T16:59:23.293893+00:00
- **Schema Version:** `1.0.0`
- **Preprocessing Version:** `1.0.0`

## Intended Use & Permissions
- Evaluating standard retrieval accuracy and answer generation quality without attacks
- **Permitted for Training:** Yes
- **Permitted for Evaluation:** Yes

## Records and Split Statistics
- **Raw Records:** 10
- **Processed Records:** 10
- **Valid Records:** 10
- **Duplicate Records:** 0
- **Empty / Invalid Records:** 0
- **Split Seed:** 42

### Partition Sizes
- **train:** 7 records
- **val:** 1 records
- **test:** 2 records

## Files and Checksums
| Split | Split Type | Format | Records | Size (Bytes) | Relative Path | SHA-256 Checksum |
|---|---|---|---:|---:|---|---|
| train | custom | jsonl | 7 | 7374 | `train.jsonl` | `1bcd858846b4d2bd...` |
| val | custom | jsonl | 1 | 961 | `val.jsonl` | `fc3deaa37531393a...` |
| test | custom | jsonl | 2 | 1332 | `test.jsonl` | `0d53055226386817...` |

## Known Biases and Limitations
None documented.

## Preprocessing Pipeline
1. Safe NFKC Unicode normalization.
2. Safe horizontal whitespace collapse preserving paragraph boundaries, punctuation, and negation.
3. Empty record filtering.
4. SHA-256 content-hash generation and exact duplicate elimination.
5. Leakage-resistant grouped train/val/test splitting with zero group and hash overlaps.
