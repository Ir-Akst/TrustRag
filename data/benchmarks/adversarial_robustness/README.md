# Dataset Card: benchmark_adversarial_robustness

## Summary
- **Dataset Name:** `benchmark_adversarial_robustness`
- **Schema Record Type:** `SecurityRecord`
- **Source Identifier / URL:** trustrag/benchmarks/adversarial_robustness
- **Source Revision:** `Unspecified`
- **License:** `MIT`
- **Access Conditions:** `open`
- **Workflow Usage Category:** `SECURITY_BENCHMARK`
- **Split Type:** `custom`
- **Retrieval Date:** 2026-11-08T16:59:23.403204+00:00
- **Schema Version:** `1.0.0`
- **Preprocessing Version:** `1.0.0`

## Intended Use & Permissions
- Stress-testing RAG guardrails under compound and multi-modal adversarial injection
- **Permitted for Training:** Yes
- **Permitted for Evaluation:** Yes

## Records and Split Statistics
- **Raw Records:** 30
- **Processed Records:** 30
- **Valid Records:** 30
- **Duplicate Records:** 0
- **Empty / Invalid Records:** 0
- **Split Seed:** 42

### Partition Sizes
- **train:** 22 records
- **val:** 4 records
- **test:** 4 records

## Files and Checksums
| Split | Split Type | Format | Records | Size (Bytes) | Relative Path | SHA-256 Checksum |
|---|---|---|---:|---:|---|---|
| train | custom | jsonl | 22 | 25652 | `train.jsonl` | `4e782aeecde569e3...` |
| val | custom | jsonl | 4 | 4824 | `val.jsonl` | `2dbaf50a91422a47...` |
| test | custom | jsonl | 4 | 4586 | `test.jsonl` | `674d5c4da3034356...` |

## Known Biases and Limitations
None documented.

## Preprocessing Pipeline
1. Safe NFKC Unicode normalization.
2. Safe horizontal whitespace collapse preserving paragraph boundaries, punctuation, and negation.
3. Empty record filtering.
4. SHA-256 content-hash generation and exact duplicate elimination.
5. Leakage-resistant grouped train/val/test splitting with zero group and hash overlaps.
