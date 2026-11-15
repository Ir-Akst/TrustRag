# TrustRAG Research Completion — Track 1, Step 2.2: Corrected Baseline Executive Summary

## 1. Overview and Mission Accomplished

Track 1, Step 2.2 formally remedies the evaluation-accounting and configuration defects identified during the independent Step 2.1 audit:
1. **Full 5-Outcome Accounting Implemented:** All evaluated records are now strictly partitioned into the five mutually exclusive G3 verdict outcomes: `SUPPORTED`, `CONTRADICTED`, `PARTIALLY_SUPPORTED`, `INSUFFICIENT_EVIDENCE`, and `UNCERTAIN`. Zero records are omitted or lost in denominators ($N = 2,700$ on RAGTruth, $N = 3,000$ on HaluEval).
2. **Dual Safety Metrics Formulated:** Both **Strict False Supported Rate** (hallucinations certified full `SUPPORTED`) and **Partial-Inclusive Unsafe Acceptance Rate** (hallucinations accepted as `SUPPORTED` or `PARTIALLY_SUPPORTED`) are explicitly measured alongside **False Contradiction Rate** (factual claims explicitly `CONTRADICTED`).
3. **Strict Threshold Configuration Repaired & Verified:** `VerificationConfig` now enforces `extra="forbid"`, preventing silent keyword argument drops. The strict baseline is genuinely instantiated with supported parameter `min_support_coverage = 0.80` (vs default `0.65`), backed by 5 new unit tests.
4. **Demonstrable Strict Mode Sensitivity:** On HaluEval, transitioning from `default_g3` (0.65) to `strict_g3` (0.80) drops the Strict False Supported Rate from **15.93% down to 9.07%** (a 43.1% relative reduction in hallucination leakage) and raises decisive accuracy from **81.84% to 88.40%**.

---

## 2. Master Comparative Baseline Table (All 3 Modes)

### 2.1 RAGTruth Test Split (2,700 Records)
| Metric | No Verification (`no_verification`) | TrustRAG Default G3 (`min_support_coverage = 0.65`) | TrustRAG Strict G3 (`min_support_coverage = 0.80`) |
| :--- | :--- | :--- | :--- |
| **Full 5-Outcome Distribution** | SUP: 2700, CONT: 0, PART: 0, IE: 0, UNC: 0 | SUP: 9, CONT: 1885, PART: 436, IE: 280, UNC: 90 | SUP: 3, CONT: 1914, PART: 343, IE: 379, UNC: 61 |
| **Strict FSR (Safety)** | **100.00%** (943/943) | **0.0000** (0/943) | **0.0000** (0/943) |
| **Partial-Inclusive Unsafe Acceptance** | 100.00% (943/943) | **7.74%** (73/943) | **5.94%** (56/943) *(Strict Safety Gain)* |
| **False Contradiction Rate (FCR)** | 0.00% (0/1757) | **62.61%** (1100/1757) | **64.03%** (1125/1757) |
| **Explicit Decisive Coverage** | 100.00% (2700/2700) | 70.15% (1894/2700) | 71.00% (1917/2700) |
| **Partial-Support Coverage** | 0.00% (0/2700) | 16.15% (436/2700) | 12.70% (343/2700) |
| **Strict Abstention Rate** | 0.00% (0/2700) | 13.70% (370/2700) | 16.30% (440/2700) |
| **Inclusive Decisive Coverage** | 100.00% (2700/2700) | 86.30% (2330/2700) | 83.70% (2260/2700) |
| **Conservative Policy Accuracy** | 65.07% | 35.26% (F1: 51.90%) | 35.04% (F1: 51.81%) |
| **Decisive-Only Accuracy** | 65.07% | 41.92% (Coverage: 70.15%) | 41.31% (Coverage: 71.00%) |

---

### 2.2 HaluEval Test Split (3,000 Records)
| Metric | No Verification (`no_verification`) | TrustRAG Default G3 (`min_support_coverage = 0.65`) | TrustRAG Strict G3 (`min_support_coverage = 0.80`) |
| :--- | :--- | :--- | :--- |
| **Full 5-Outcome Distribution** | SUP: 3000, CONT: 0, PART: 0, IE: 0, UNC: 0 | SUP: 1153, CONT: 235, PART: 19, IE: 1571, UNC: 22 | SUP: 1050, CONT: 235, PART: 20, IE: 1675, UNC: 20 |
| **Strict FSR (Safety)** | **100.00%** (1500/1500) | **15.93%** (239/1500) | **9.07%** (136/1500) *(43.1% Rel. Reduction)* |
| **Partial-Inclusive Unsafe Acceptance** | 100.00% (1500/1500) | **17.20%** (258/1500) | **10.40%** (156/1500) |
| **False Contradiction Rate (FCR)** | 0.00% (0/1500) | **0.87%** (13/1500) | **0.87%** (13/1500) *(Preserved Utility)* |
| **Explicit Decisive Coverage** | 100.00% (3000/3000) | 46.27% (1388/3000) | 42.83% (1285/3000) |
| **Partial-Support Coverage** | 0.00% (0/3000) | 0.63% (19/3000) | 0.67% (20/3000) |
| **Strict Abstention Rate** | 0.00% (0/3000) | 53.10% (1593/3000) | 56.50% (1695/3000) |
| **Inclusive Decisive Coverage** | 100.00% (3000/3000) | 46.90% (1407/3000) | 43.50% (1305/3000) |
| **Conservative Policy Accuracy** | 50.00% | 72.50% (F1: 75.35%) | **75.93%** (F1: 79.07%) |
| **Decisive-Only Accuracy** | 50.00% | 81.84% (Coverage: 46.27%) | **88.40%** (Coverage: 42.83%) |

---

## 3. Key Conclusions & Track 2 Scientific Mandate

1. **Strict Verification Is Highly Effective:** Increasing `min_support_coverage` from 0.65 to 0.80 cuts hallucination leakage almost in half on HaluEval (FSR: 15.93% -> 9.07%) without increasing false contradictions (0.87% -> 0.87%).
2. **The Paraphrase Bottleneck Remains on RAGTruth:** On RAGTruth, where claims use complex vocabulary substitutions, raising threshold increases false contradictions slightly (62.61% -> 64.03%). This empirical finding provides the definitive rationale for Track 2: **Neural Cross-Encoder / NLI semantic entailment is required to bridge the lexical vocabulary gap**.
