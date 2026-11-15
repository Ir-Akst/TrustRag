# TrustRAG Research Completion — Track 1, Step 2.2: Five-Outcome Accounting

## 1. Accounting Completeness & Assertion

Every record evaluated belongs to exactly one mutually exclusive outcome category:
1. `SUPPORTED` (Full evidence entailment)
2. `CONTRADICTED` (Explicit factual conflict / polarity clash)
3. `PARTIALLY_SUPPORTED` (Subset of predicate clauses grounded, but incomplete)
4. `INSUFFICIENT_EVIDENCE` (Evidence span relevance below threshold / ungrounded claims)
5. `UNCERTAIN` (Ambiguous semantic overlap or unresolvable temporal/numerical drift)

For every dataset and evaluation mode:
$$\text{Total Records} = \text{SUPPORTED} + \text{CONTRADICTED} + \text{PARTIALLY\_SUPPORTED} + \text{INSUFFICIENT\_EVIDENCE} + \text{UNCERTAIN}$$
This mathematical identity was asserted in code during execution with zero assertion failures.

---

## 2. Exhaustive Outcome Tables

### 2.1 RAGTruth Test Split (2,700 Records)
| Mode | SUPPORTED | CONTRADICTED | PARTIALLY_SUPPORTED | INSUFFICIENT_EVIDENCE | UNCERTAIN | Total Sum | Explicit Decisive Coverage | Strict Abstention Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **no_verification** | 2,700 (100%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | **2,700** | 100.00% | 0.00% |
| **default_g3** (0.65) | 9 (0.33%) | 1,885 (69.81%) | 436 (16.15%) | 280 (10.37%) | 90 (3.33%) | **2,700** | 70.15% (1,894) | 13.70% (370) |
| **strict_g3** (0.80) | 3 (0.11%) | 1,914 (70.89%) | 343 (12.70%) | 379 (14.04%) | 61 (2.26%) | **2,700** | 71.00% (1,917) | 16.30% (440) |

#### Cross-Tabulation by Ground Truth (Default vs Strict on RAGTruth):
- **FACTUAL (1,757 records):**
  - Default: SUP: 9, CONT: 1100, PART: 363, IE: 207, UNC: 78
  - Strict: SUP: 3, CONT: 1125, PART: 287, IE: 289, UNC: 53
- **HALLUCINATED (943 records):**
  - Default: SUP: 0, CONT: 785, PART: 73, IE: 73, UNC: 12
  - Strict: SUP: 0, CONT: 789, PART: 56, IE: 90, UNC: 8

---

### 2.2 HaluEval Test Split (3,000 Records)
| Mode | SUPPORTED | CONTRADICTED | PARTIALLY_SUPPORTED | INSUFFICIENT_EVIDENCE | UNCERTAIN | Total Sum | Explicit Decisive Coverage | Strict Abstention Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **no_verification** | 3,000 (100%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | **3,000** | 100.00% | 0.00% |
| **default_g3** (0.65) | 1,153 (38.43%) | 235 (7.83%) | 19 (0.63%) | 1,571 (52.37%) | 22 (0.73%) | **3,000** | 46.27% (1,388) | 53.10% (1,593) |
| **strict_g3** (0.80) | 1,050 (35.00%) | 235 (7.83%) | 20 (0.67%) | 1,675 (55.83%) | 20 (0.67%) | **3,000** | 42.83% (1,285) | 56.50% (1,695) |

#### Cross-Tabulation by Ground Truth (Default vs Strict on HaluEval):
- **FACTUAL (1,500 records):**
  - Default: SUP: 914, CONT: 13, PART: 0, IE: 559, UNC: 14
  - Strict: SUP: 914, CONT: 13, PART: 0, IE: 559, UNC: 14 *(Factual outcomes 100% preserved!)*
- **HALLUCINATED (1,500 records):**
  - Default: SUP: 239, CONT: 222, PART: 19, IE: 1012, UNC: 8
  - Strict: SUP: 136, CONT: 222, PART: 20, IE: 1116, UNC: 6 *(103 false-supported claims converted to abstentions!)*
