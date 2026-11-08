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
- **Retrieval Date:** 2026-11-07T20:00:51.197275+00:00
- **Schema Version:** `1.0.0`
- **Preprocessing Version:** `1.0.0`

## Intended Use & Permissions
- Stress-testing RAG guardrails under compound and multi-modal adversarial injection
- **Permitted for Training:** Yes
- **Permitted for Evaluation:** Yes

## Records and Split Statistics
- **Raw Records:** 250
- **Processed Records:** 250
- **Valid Records:** 250
- **Duplicate Records:** 0
- **Empty / Invalid Records:** 0
- **Split Seed:** 42

### Partition Sizes
- **train:** 174 records
- **val:** 36 records
- **test:** 40 records

## Files and Checksums
| Split | Split Type | Format | Records | Size (Bytes) | Relative Path | SHA-256 Checksum |
|---|---|---|---:|---:|---|---|
| train | custom | jsonl | 174 | 204936 | `train.jsonl` | `210710dae26ba3ff...` |
| val | custom | jsonl | 36 | 42290 | `val.jsonl` | `d7e5819b87cdf580...` |
| test | custom | jsonl | 40 | 47144 | `test.jsonl` | `24b20d20e2795400...` |

## Known Biases and Limitations
None documented.

## Preprocessing Pipeline
1. Safe NFKC Unicode normalization.
2. Safe horizontal whitespace collapse preserving paragraph boundaries, punctuation, and negation.
3. Empty record filtering.
4. SHA-256 content-hash generation and exact duplicate elimination.
5. Leakage-resistant grouped train/val/test splitting with zero group and hash overlaps.
