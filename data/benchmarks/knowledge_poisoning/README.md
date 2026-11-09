# Dataset Card: benchmark_knowledge_poisoning

## Summary
- **Dataset Name:** `benchmark_knowledge_poisoning`
- **Schema Record Type:** `SecurityRecord`
- **Source Identifier / URL:** trustrag/benchmarks/knowledge_poisoning
- **Source Revision:** `Unspecified`
- **License:** `MIT`
- **Access Conditions:** `open`
- **Workflow Usage Category:** `SECURITY_BENCHMARK`
- **Split Type:** `custom`
- **Retrieval Date:** 2026-11-08T16:59:23.326154+00:00
- **Schema Version:** `1.0.0`
- **Preprocessing Version:** `1.0.0`

## Intended Use & Permissions
- Evaluating detector and guardrail resilience against targeted factual poisoning
- **Permitted for Training:** Yes
- **Permitted for Evaluation:** Yes

## Records and Split Statistics
- **Raw Records:** 20
- **Processed Records:** 20
- **Valid Records:** 20
- **Duplicate Records:** 0
- **Empty / Invalid Records:** 0
- **Split Seed:** 42

### Partition Sizes
- **train:** 14 records
- **val:** 2 records
- **test:** 4 records

## Files and Checksums
| Split | Split Type | Format | Records | Size (Bytes) | Relative Path | SHA-256 Checksum |
|---|---|---|---:|---:|---|---|
| train | custom | jsonl | 14 | 16302 | `train.jsonl` | `7feaa0c7b69bef24...` |
| val | custom | jsonl | 2 | 2412 | `val.jsonl` | `46cbc33835181050...` |
| test | custom | jsonl | 4 | 4586 | `test.jsonl` | `674d5c4da3034356...` |

## Known Biases and Limitations
None documented.

## Preprocessing Pipeline
1. Safe NFKC Unicode normalization.
2. Safe horizontal whitespace collapse preserving paragraph boundaries, punctuation, and negation.
3. Empty record filtering.
4. SHA-256 content-hash generation and exact duplicate elimination.
5. Leakage-resistant grouped train/val/test splitting with zero group and hash overlaps.
