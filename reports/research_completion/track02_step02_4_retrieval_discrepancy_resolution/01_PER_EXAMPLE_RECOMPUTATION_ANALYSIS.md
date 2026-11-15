# TrustRAG — Track 1, Step 2.4: Retrieval Baseline Discrepancy Resolution
# 01 — Per-Example Recomputation Analysis & Mathematical Proof

**Primary Prediction Evidence:**
- HotpotQA: `reports/research_completion/track02_baseline_evaluation/predictions_hotpotqa_retrieval.jsonl` (7,405 records, SHA-256: `36c5629437fcbb7dbb89fc6b23b53f651040e255a7eeb30c53159a2e175d12ae`)
- MS MARCO: `reports/research_completion/track02_baseline_evaluation/predictions_msmarco_retrieval.jsonl` (9,706 records, SHA-256: `775703ccf0a01eb8537aec9721d1a66be42643decadc1212cca03b5a95eb27ad`)

---

## 1. HotpotQA Retrieval Mathematical Proof

### 1.1 Dataset Properties & Evaluation Structure
- **Dataset Split:** HotpotQA Validation Distractor Set (`hotpotqa_val_distractor.parquet`)
- **Total Evaluated Queries:** 7,405 ($N = 7,405$)
- **Skipped Queries:** 0
- **Candidate Pool:** 10 Wikipedia paragraphs per query (2 gold paragraphs, 8 negative distractor paragraphs).
- **Gold Label Definition:** Set of titles annotated in `supporting_facts.title`.

### 1.2 Metric Definitions
For query $i$ with gold titles $G_i$ ($|G_i| = 2$ in the vast majority of cases) and top-$k$ retrieved titles $R_{i, k}$:
$$\text{Recall@}k(i) = \frac{|G_i \cap R_{i, k}|}{|G_i|}$$
$$\text{MRR@10}(i) = \begin{cases} \frac{1}{\text{rank}_i} & \text{if first hit appears at rank } \le 10 \\ 0 & \text{otherwise} \end{cases}$$

### 1.3 Exact Recomputation from Per-Example Records
Direct evaluation across all 7,405 lines in `predictions_hotpotqa_retrieval.jsonl`:

| Metric | Sum Across All 7,405 Records | Exact Mean ($ \text{Sum} / 7405 $) | Rounded (4 Decimals) | Step 2.1 / 2.2 Reported | Step 2.3 Spurious Value | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Recall@1** | 3,076.0 | 0.415395003... | **0.4154** | 0.4154 | *0.5404* | **EXACT MATCH** |
| **Recall@5** | 6,059.0 | 0.818230925... | **0.8182** | 0.8182 | *0.7226* | **EXACT MATCH** |
| **Recall@10** | 7,313.5 | 0.987643484... | **0.9876** | 0.9876 | *0.7303* | **EXACT MATCH** |
| **MRR@10** | 6,638.8925 | 0.896541863... | **0.8965** | 0.8965 | *0.6179* | **EXACT MATCH** |

### 1.4 Alternative Formula Analysis (Why R@1 Cannot Mathematically Be 0.5404)
1. **Fraction of Gold Retrieved (Standard IR Multi-Label Recall):**
   - Because HotpotQA questions have 2 gold supporting paragraphs, at rank 1, at most 1 gold paragraph can be retrieved.
   - For queries with 2 gold titles, maximum possible Recall@1 is $1 / 2 = 0.50$.
   - A mean Recall@1 of **0.4154** indicates that for 6,152 out of 7,405 queries ($83.08\%$), the rank-1 retrieved paragraph was a gold supporting paragraph ($6152 \times 0.5 / 7405 = 0.415395$).
2. **Binary Hit Rate (Hit@1, at least one gold in top 1):**
   - Hit@1 = $\frac{6152}{7405} = \mathbf{0.8308}$ ($83.08\%$).
   - Hit@5 = $\mathbf{0.9841}$ ($98.41\%$).
   - Hit@10 = $\mathbf{0.9999}$ ($99.99\%$).
3. **Complete Recall (All gold in top-k):**
   - All@1 = $0.0000$ (cannot retrieve 2 documents in top 1).
   - All@5 = $0.6524$ ($65.24\%$).
   - All@10 = $0.9754$ ($97.54\%$).

Neither Hit Rate nor Complete Recall equals 0.5404. The number 0.5404 is completely foreign to this dataset's distribution.

---

## 2. MS MARCO Retrieval Mathematical Proof

### 2.1 Dataset Properties & Evaluation Structure
- **Dataset Split:** MS MARCO v1.1 Validation Set (`ms_marco_val_v1.1.parquet`)
- **Total Queries in Parquet:** 10,047
- **Skipped Queries:** 341 (Queries where `is_selected` is all zeros; no passage answers query).
- **Evaluated Queries:** 9,706 ($N_{\text{eval}} = 9,706$)
- **Candidate Pool:** 6 to 10 web passages per query (annotated candidates in MS MARCO v1.1).

### 2.2 Exact Recomputation from Per-Example Records
Direct evaluation across all 9,706 lines in `predictions_msmarco_retrieval.jsonl`:

#### Standard Evaluated-Queries Protocol ($N = 9,706$):

| Metric | Sum Across 9,706 Records | Exact Mean ($ \text{Sum} / 9706 $) | Rounded (4 Decimals) | Step 2.1 / 2.2 Reported | Step 2.3 Spurious Value | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Recall@1** | 2,243.2821 | 0.231123233... | **0.2311** | 0.2311 | *0.3229* | **EXACT MATCH** |
| **Recall@5** | 7,368.3503 | 0.759154162... | **0.7592** | 0.7592 | *0.4430* | **EXACT MATCH** |
| **Recall@10** | 9,481.0834 | 0.976827055... | **0.9768** | 0.9768 | *0.4571* | **EXACT MATCH** |
| **MRR@10** | 4,489.9880 | 0.462599216... | **0.4626** | 0.4626 | *0.3725* | **EXACT MATCH** |

#### Total-Queries Protocol ($N = 10,047$, Penalizing 341 Unannotated Queries as Zero):

| Metric | Sum Across Records | Mean Over Total ($ \text{Sum} / 10047 $) | Rounded (4 Decimals) | Step 2.1 Audit Verified |
| :--- | :---: | :---: | :---: | :---: |
| **Recall@1** | 2,243.2821 | 0.2232788... | **0.2233** | 0.2233 |
| **Recall@5** | 7,368.3503 | 0.7333881... | **0.7334** | 0.7334 |
| **Recall@10** | 9,481.0834 | 0.9436730... | **0.9437** | 0.9437 |
| **MRR@10** | 4,489.9880 | 0.4468983... | **0.4469** | 0.4469 |

---

## 3. Discrepancy Synthesis & Conclusion

1. **Prediction File Veracity:** The per-example prediction files `predictions_hotpotqa_retrieval.jsonl` and `predictions_msmarco_retrieval.jsonl` are 100% authentic, internally consistent, and arithmetically verified against ground-truth labels.
2. **True Canonical Metrics:**
   - **HotpotQA:** Recall@1 = **0.4154**, Recall@5 = **0.8182**, Recall@10 = **0.9876**, MRR@10 = **0.8965**.
   - **MS MARCO:** Recall@1 = **0.2311**, Recall@5 = **0.7592**, Recall@10 = **0.9768**, MRR@10 = **0.4626**.
3. **Spurious Step 2.3 Numbers Expunged:** The spurious values reported in Step 2.3 (`0.5404`, `0.7226`, `0.7303`, `0.6179` and `0.3229`, `0.4430`, `0.4571`, `0.3725`) have been identified as an artifact transcription defect and removed.

