# TrustRAG — Track 1, Step 2.1: Independent Benchmark Metric Integrity Audit
## 07. Defects, Root Causes & Formal Corrections

### Defect Inventory

| Defect ID | Severity | Category | Description | Root Cause | Formal Correction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEF-01** | Medium | Metric Accounting | 436 records in RAGTruth and 19 records in HaluEval omitted from decisive coverage and abstention rate. | Script formulas only counted `SUPPORTED + CONTRADICTED` in decisive and `INSUFFICIENT + UNCERTAIN` in abstention, leaving `PARTIALLY_SUPPORTED` unpartitioned. | Formally partition into Strict Abstention (29.85% RAGTruth, 53.73% HaluEval) or Lenient Decisive (86.30% RAGTruth, 46.90% HaluEval). |
| **DEF-02** | Medium | Configuration | `strict_g3` executed with identical settings to `default_g3`. | `VerificationConfig` accepted and silently discarded non-existent fields `evidence_threshold` and `claim_threshold`. | Reclassify `strict_g3` as duplicate default run; configure `min_support_coverage=0.80` in future runs. |
| **DEF-03** | Low | Metric Terminology | Conflation of Classification False Positives (1,748) and False Contradictions (1,100). | Pipeline maps all non-supported verdicts to positive for hallucination in binary classification. | Explicitly report both: FPR = 99.49% (1,748/1,757) and FCR = 62.61% (1,100/1,757). |
| **DEF-04** | Low | Metric Reporting | MS MARCO denominator did not explicitly document handling of 341 unannotated queries. | Annotators selected 0 passages in v1.1 validation. | Report dual metrics: N=9,706 (standard protocol) and N=10,047 (conservative penalization). |

---

### Conclusion on Baseline Validity
None of the identified defects compromise the core scientific findings of Track 1 Step 2:
1. Zero False Supported Rate on RAGTruth (0 / 943) is **100% verified and true**.
2. 15.93% False Supported Rate on HaluEval (239 / 1,500) is **100% verified and true**.
3. High False Contradiction Rate (62.61% on RAGTruth) remains the core empirical rationale for Track 2 neural NLI models.
4. Top-10 candidate retrieval recall (98.76% HotpotQA, 97.68% MS MARCO) is **100% verified and true**.

The baseline does **NOT** need to be withdrawn. It is formally **`CONDITIONALLY_VERIFIED`** with the mathematical corrections established herein.
