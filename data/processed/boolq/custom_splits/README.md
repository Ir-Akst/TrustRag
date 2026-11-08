# Dataset Card: boolq

## Summary
- **Dataset Name:** `boolq`
- **Schema Record Type:** `QueryRecord`
- **Source Identifier / URL:** google/boolq
- **Source Revision:** `Unspecified`
- **License:** `CC-BY-SA-3.0`
- **Access Conditions:** `open`
- **Workflow Usage Category:** `VALIDATION`
- **Split Type:** `custom`
- **Retrieval Date:** 2026-11-07T19:17:14.427540+00:00
- **Schema Version:** `1.0.0`
- **Preprocessing Version:** `1.0.0`

## Intended Use & Permissions
- Research evaluation and defense benchmarking
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
- **custom_test:** 15 records
- **custom_train:** 70 records
- **custom_val:** 15 records

## Files and Checksums
| Split | Split Type | Format | Records | Size (Bytes) | Relative Path | SHA-256 Checksum |
|---|---|---|---:|---:|---|---|
| custom_test | custom | jsonl | 15 | 12298 | `custom_test.jsonl` | `b78ab07ac036e9d2...` |
| custom_train | custom | jsonl | 70 | 66854 | `custom_train.jsonl` | `bfc1759cd62e87da...` |
| custom_val | custom | jsonl | 15 | 14559 | `custom_val.jsonl` | `1077922658522def...` |

## Known Biases and Limitations
Binary yes/no answers only

## Preprocessing Pipeline
1. Safe NFKC Unicode normalization.
2. Safe horizontal whitespace collapse preserving paragraph boundaries, punctuation, and negation.
3. Empty record filtering.
4. SHA-256 content-hash generation and exact duplicate elimination.
5. Leakage-resistant grouped train/val/test splitting with zero group and hash overlaps.
