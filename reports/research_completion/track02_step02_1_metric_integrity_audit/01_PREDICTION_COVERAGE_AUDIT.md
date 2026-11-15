# TrustRAG — Track 1, Step 2.1: Independent Benchmark Metric Integrity Audit
## 01. Prediction Coverage Audit

### 1. Scope & Methodology
A 100% census was performed across all prediction JSONL files and raw/processed dataset files:
- [predictions_ragtruth.jsonl](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_baseline_evaluation/predictions_ragtruth.jsonl) (3,632,742 bytes)
- [predictions_halueval.jsonl](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_baseline_evaluation/predictions_halueval.jsonl) (1,703,722 bytes)
- [predictions_hotpotqa_retrieval.jsonl](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_baseline_evaluation/predictions_hotpotqa_retrieval.jsonl) (4,332,544 bytes)
- [predictions_msmarco_retrieval.jsonl](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_baseline_evaluation/predictions_msmarco_retrieval.jsonl) (2,741,483 bytes)

---

### 2. RAGTruth Record Census & Outcome Accounting

- **Input Test Split Records (`data/processed/ragtruth/test.jsonl`):** 2,700
- **Unique Input IDs:** 2,700
- **Prediction File Records (`predictions_ragtruth.jsonl`):** 2,700
- **Unique Prediction IDs:** 2,700
- **Missing IDs:** 0
- **Extra IDs:** 0
- **Invalid / Null / Corrupt Outputs:** 0

#### Complete Exhaustive Outcome Table (2,700 records):
| Ground Truth Label | G3 Output Verdict | Overall Status | Recorded Failure Type | Count | % of Split | Evaluation Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FACTUAL` | `CONTRADICTED` | `CONTRADICTED` | `FALSE_CONTRADICTION` | 1,100 | 40.74% | False Contradiction (Utility Error) |
| `FACTUAL` | `PARTIALLY_SUPPORTED` | `PARTIALLY_SUPPORTED` | `None` | 363 | 13.44% | Factual claim partially matched |
| `FACTUAL` | `INSUFFICIENT_EVIDENCE` | `UNVERIFIED` | `INSUFFICIENT_EVIDENCE_ON_FACTUAL` | 207 | 7.67% | Abstention on factual claim |
| `FACTUAL` | `UNCERTAIN` | `UNCERTAIN` | `INSUFFICIENT_EVIDENCE_ON_FACTUAL` | 78 | 2.89% | Abstention on factual claim |
| `FACTUAL` | `SUPPORTED` | `VERIFIED` | `None` | 9 | 0.33% | True Negative (Correctly Verified Factual) |
| `HALLUCINATED` | `CONTRADICTED` | `CONTRADICTED` | `None` | 785 | 29.07% | True Positive (Hallucination Caught) |
| `HALLUCINATED` | `PARTIALLY_SUPPORTED` | `PARTIALLY_SUPPORTED` | `None` | 73 | 2.70% | Hallucination partially matched |
| `HALLUCINATED` | `INSUFFICIENT_EVIDENCE` | `UNVERIFIED` | `None` | 73 | 2.70% | Hallucination safely rejected / unverified |
| `HALLUCINATED` | `UNCERTAIN` | `UNCERTAIN` | `None` | 12 | 0.44% | Hallucination safely rejected / uncertain |
| `HALLUCINATED` | `SUPPORTED` | `VERIFIED` | `FALSE_SUPPORTED` | **0** | **0.00%** | **False Supported (Zero Safety Leaks)** |
| **Total** | | | | **2,700** | **100.00%** | **Zero Unaccounted Records** |

---

### 3. HaluEval Record Census & Outcome Accounting

- **Input Test Split Records (`data/processed/halueval/test.jsonl`):** 3,000
- **Unique Input IDs:** 3,000
- **Prediction File Records (`predictions_halueval.jsonl`):** 3,000
- **Unique Prediction IDs:** 3,000
- **Missing IDs:** 0
- **Extra IDs:** 0
- **Invalid / Null / Corrupt Outputs:** 0

#### Complete Exhaustive Outcome Table (3,000 records):
| Ground Truth Label | G3 Output Verdict | Overall Status | Recorded Failure Type | Count | % of Split | Evaluation Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FACTUAL` | `SUPPORTED` | `VERIFIED` | `None` | 914 | 30.47% | True Negative (Correctly Verified Factual) |
| `FACTUAL` | `INSUFFICIENT_EVIDENCE` | `UNVERIFIED` | `INSUFFICIENT_EVIDENCE_ON_FACTUAL` | 559 | 18.63% | Abstention on factual claim |
| `FACTUAL` | `UNCERTAIN` | `UNCERTAIN` | `INSUFFICIENT_EVIDENCE_ON_FACTUAL` | 14 | 0.47% | Abstention on factual claim |
| `FACTUAL` | `CONTRADICTED` | `CONTRADICTED` | `FALSE_CONTRADICTION` | 13 | 0.43% | False Contradiction (Utility Error) |
| `HALLUCINATED` | `INSUFFICIENT_EVIDENCE` | `UNVERIFIED` | `None` | 1,012 | 33.73% | True Positive (Safely Rejected Unverified) |
| `HALLUCINATED` | `SUPPORTED` | `VERIFIED` | `FALSE_SUPPORTED` | 239 | 7.97% | False Supported (Safety Leak) |
| `HALLUCINATED` | `CONTRADICTED` | `CONTRADICTED` | `None` | 222 | 7.40% | True Positive (Hallucination Caught) |
| `HALLUCINATED` | `PARTIALLY_SUPPORTED` | `PARTIALLY_SUPPORTED` | `None` | 19 | 0.63% | Hallucination partially matched |
| `HALLUCINATED` | `UNCERTAIN` | `UNCERTAIN` | `None` | 8 | 0.27% | True Positive (Safely Rejected Uncertain) |
| **Total** | | | | **3,000** | **100.00%** | **Zero Unaccounted Records** |
