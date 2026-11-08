# Dataset Card: boolq

## Summary
- **Dataset Name:** `boolq`
- **Schema Record Type:** `QueryRecord`
- **Source Identifier / URL:** google/boolq
- **Source Revision:** `Unspecified`
- **License:** `CC-BY-SA-3.0`
- **Access Conditions:** `open`
- **Workflow Usage Category:** `TRAINING`
- **Split Type:** `official`
- **Retrieval Date:** 2026-11-07T19:16:37.684465+00:00
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
- **validation:** 100 records

## Files and Checksums
| Split | Split Type | Format | Records | Size (Bytes) | Relative Path | SHA-256 Checksum |
|---|---|---|---:|---:|---|---|
| validation | official | jsonl | 100 | 93711 | `validation.jsonl` | `aaad91da64bb69f2...` |

## Known Biases and Limitations
Binary yes/no answers only

## Preprocessing Pipeline
1. Safe NFKC Unicode normalization.
2. Safe horizontal whitespace collapse preserving paragraph boundaries, punctuation, and negation.
3. Empty record filtering.
4. SHA-256 content-hash generation and exact duplicate elimination.
5. Leakage-resistant grouped train/val/test splitting with zero group and hash overlaps.
