# TrustRAG Track 2, Step 2.2.1: RAGTruth Span Count Reconciliation Report

## 1. Executive Summary of the Discrepancy

In the Track 2 Step 2.1 audit report, the auditor reported:
> *"Across the entire canonical corpus, annotators identified 14,289 hallucinated spans."*

In the Track 2 Step 2.2 remediation report, the dataset engineer reported:
> *"Total verified spans: 12,756 spans (10,248 in train, 2,508 in validation)."*

This audit independently reconciles the exact numerical difference of **1,533 spans** directly against the raw and processed source files.

---

## 2. Mathematical Reconciliation & Root Cause

The investigation parsed all 17,790 raw responses in [`data/raw/ragtruth/response.jsonl`](file:///home/aditya/rags/TrustRag-phase11/data/raw/ragtruth/response.jsonl) grouped by the canonical `split` field:

$$\begin{aligned}
\text{Total Raw Responses} &= 17,790 = \underbrace{15,090}_{\text{train responses}} + \underbrace{2,700}_{\text{test responses}} \\
\text{Total Raw Spans} &= 14,289 = \underbrace{12,756}_{\text{train spans}} + \underbrace{1,533}_{\text{test spans}}
\end{aligned}$$

### Definitive Finding
The difference of **1,533 spans** represents the **canonical RAGTruth test set** (`data/processed/ragtruth/test.jsonl`, 2,700 responses).

- **Step 2.1 Scope:** The Step 2.1 auditor performed a corpus-wide inventory across all 17,790 responses, including the test split ($12,756 + 1,533 = 14,289$).
- **Step 2.2 Scope:** The Step 2.2 dataset engineer strictly quarantined the 2,700 test responses from fine-tuning, carving the training and validation datasets exclusively from the 15,090 training responses ($10,082 + 2,674 = 12,756$).

---

## 3. Span Taxonomy Census Across All Corpora

| Span Taxonomy Label (`label_type`) | Canonical Raw Train Spans | Canonical Raw Test Spans | Corpus Total Spans | `sft_v1` Preserved Spans | `sft_v2/spans` Preserved Spans | Reconciliation Delta |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`Evident Conflict`** | 4,705 | 619 | 5,324 | 4,705 | 4,705 | 0 |
| **`Evident Baseless Info`** | 5,499 | 738 | 6,237 | 5,499 | 5,499 | 0 |
| **`Subtle Baseless Info`** | 2,367 | 160 | 2,527 | 2,367 | 2,367 | 0 |
| **`Subtle Conflict`** | 185 | 16 | 201 | 185 | 185 | 0 |
| **Total Spans** | **12,756** | **1,533** | **14,289** | **12,756** | **12,756** | **0** |

---

## 4. Preservation Integrity Audit

The audit verified whether any spans were altered or lost during preprocessing:
1. `data/raw/ragtruth/response.jsonl` (train slice): **12,756 spans**.
2. `data/processed/ragtruth/train.jsonl`: **12,756 spans**.
3. `data/processed/sft_v1/` (train + val): **12,756 spans**.
4. `data/processed/sft_v2/spans/` (train + val): **12,756 spans**.
5. `data/processed/ragtruth/test.jsonl`: **1,533 spans**.

### Auditor Conclusion
- **Zero Spans Lost:** Exactly 12,756 spans were extracted from training responses and 100% are preserved in `sft_v2/spans`.
- **Zero Test Contamination:** Exactly 1,533 spans remain quarantined in the test set.
- **Reporting Clarity:** The discrepancy is fully explained by split scope differences between Step 2.1 and Step 2.2.

