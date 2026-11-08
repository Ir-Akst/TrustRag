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
- **Retrieval Date:** 2026-11-07T20:00:50.760138+00:00
- **Schema Version:** `1.0.0`
- **Preprocessing Version:** `1.0.0`

## Intended Use & Permissions
- Evaluating standard retrieval accuracy and answer generation quality without attacks
- **Permitted for Training:** Yes
- **Permitted for Evaluation:** Yes

## Records and Split Statistics
- **Raw Records:** 100
- **Processed Records:** 100
- **Valid Records:** 100
- **Duplicate Records:** 0
- **Empty / Invalid Records:** 0
- **Split Seed:** 42

### Partition Sizes
- **train:** 70 records
- **val:** 15 records
- **test:** 15 records

## Files and Checksums
| Split | Split Type | Format | Records | Size (Bytes) | Relative Path | SHA-256 Checksum |
|---|---|---|---:|---:|---|---|
| train | custom | jsonl | 70 | 66854 | `train.jsonl` | `bfc1759cd62e87da...` |
| val | custom | jsonl | 15 | 14559 | `val.jsonl` | `1077922658522def...` |
| test | custom | jsonl | 15 | 12298 | `test.jsonl` | `b78ab07ac036e9d2...` |

## Known Biases and Limitations
None documented.

## Preprocessing Pipeline
1. Safe NFKC Unicode normalization.
2. Safe horizontal whitespace collapse preserving paragraph boundaries, punctuation, and negation.
3. Empty record filtering.
4. SHA-256 content-hash generation and exact duplicate elimination.
5. Leakage-resistant grouped train/val/test splitting with zero group and hash overlaps.
