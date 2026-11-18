# TrustRAG — Track 2, Step 3.10: Token Length & Truncation Audit

## 1. Empirical Token Length Distributions

Measured across all 10,815 training records and all 2,662 validation records using the DeBERTa-v3 tokenizer:

| Split | Element | Min | p25 | Median | Mean | p75 | p90 | p95 | p99 | Max |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Train** | Premise | 141 | 346.5 | 500.0 | 575.4 | 729.0 | 979.0 | 1,203.6 | 1,759.0 | 2,187 |
| **Train** | Hypothesis | 1 | 106.0 | 146.0 | 153.2 | 190.0 | 250.0 | 279.0 | 339.0 | 467 |
| **Train** | Combined Pair | 165 | 473.0 | 647.0 | 731.6 | 918.0 | 1,187.0 | 1,415.0 | 1,963.0 | 2,516 |
| **Val** | Premise | 155 | 369.3 | 502.0 | 587.3 | 751.0 | 1,008.0 | 1,210.0 | 1,871.0 | 2,124 |
| **Val** | Hypothesis | 6 | 108.0 | 149.0 | 156.3 | 195.0 | 254.9 | 276.9 | 347.4 | 770 |
| **Val** | Combined Pair | 173 | 484.0 | 657.0 | 746.6 | 950.0 | 1,201.0 | 1,390.0 | 2,043.1 | 2,471 |

---

## 2. Truncation Comparison Across Candidate Sequence Lengths

Evaluated on the full 2,662-sample validation split:

### Strategy 1: Naive `longest_first` (Step 3.8 Baseline Strategy)
| Max Length | Premise Truncation % | Samples with Trunc Premise | Hypothesis Truncation % | Samples with Trunc Hyp |
| :---: | :---: | :---: | :---: | :---: |
| **128** | 89.0% | 100.0% | **61.3%** | **94.6%** |
| **256** | 76.2% | 98.4% | **27.8%** | **63.4%** |
| **384** | 60.7% | 87.0% | **9.7%** | **25.9%** |
| **512** | 45.3% | 70.8% | **2.4%** | **9.8%** |

### Strategy 2: Remediated `evidence_preserving_tokenize` (Hypothesis Priority)
| Max Length | Premise Retention % | Avg Kept Premise Tokens | Hypothesis Retention % | Samples with Trunc Hyp |
| :---: | :---: | :---: | :---: | :---: |
| **128** | 11.1% | ~64 tokens | 38.1% | 94.8% |
| **256** | 19.0% | ~110 tokens | 90.1% | 26.6% |
| **384** | **36.9%** | **~225 tokens** | **99.5%** | **2.0%** |
| **512** | **54.1%** | **~330 tokens** | **99.9%** | **0.0%** |

**Recommendation:** `max_seq_len = 384` under `evidence_preserving_tokenize` achieves optimal trade-off: **99.5% hypothesis retention** with only 2.0% of hypotheses touched, while providing 225 premise tokens for grounding context.
