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
- **Retrieval Date:** 2026-11-07T20:00:50.899248+00:00
- **Schema Version:** `1.0.0`
- **Preprocessing Version:** `1.0.0`

## Intended Use & Permissions
- Evaluating detector and guardrail resilience against targeted factual poisoning
- **Permitted for Training:** Yes
- **Permitted for Evaluation:** Yes

## Records and Split Statistics
- **Raw Records:** 150
- **Processed Records:** 150
- **Valid Records:** 150
- **Duplicate Records:** 0
- **Empty / Invalid Records:** 0
- **Split Seed:** 42

### Partition Sizes
- **train:** 104 records
- **val:** 22 records
- **test:** 24 records

## Files and Checksums
| Split | Split Type | Format | Records | Size (Bytes) | Relative Path | SHA-256 Checksum |
|---|---|---|---:|---:|---|---|
| train | custom | jsonl | 104 | 120586 | `train.jsonl` | `9283523628acef61...` |
| val | custom | jsonl | 22 | 25738 | `val.jsonl` | `f6ba03d383469122...` |
| test | custom | jsonl | 24 | 27668 | `test.jsonl` | `da58500da58f3c6f...` |

## Known Biases and Limitations
None documented.

## Preprocessing Pipeline
1. Safe NFKC Unicode normalization.
2. Safe horizontal whitespace collapse preserving paragraph boundaries, punctuation, and negation.
3. Empty record filtering.
4. SHA-256 content-hash generation and exact duplicate elimination.
5. Leakage-resistant grouped train/val/test splitting with zero group and hash overlaps.
