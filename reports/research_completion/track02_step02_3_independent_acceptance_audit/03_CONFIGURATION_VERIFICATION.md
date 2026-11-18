# TrustRAG — Track 1, Step 2.3: Independent Corrected Baseline Acceptance Audit
# 03 — Configuration Schema Enforcement & Sensitivity Verification

**Audit Scope:**
1. Schema verification of `VerificationConfig` in `src/trustrag/verification/config.py`.
2. Validation behavior for unknown / deprecated parameters (`extra="forbid"` vs legacy `extra="ignore"`).
3. Parameter consumption in `OutputEvidenceVerifier` (`min_support_coverage`).
4. Sensitivity proof on synthetic test cases and 5,700 real benchmark records.

---

## 1. Schema Definition & `extra="forbid"` Verification

### 1.1 Source Code Inspection
File: `src/trustrag/verification/config.py` (lines 14–46)

```python
class VerificationConfig(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )
    enabled: bool = True
    min_support_coverage: float = Field(default=0.65, ge=0.0, le=1.0)
    min_relevance_for_check: float = Field(default=0.10, ge=0.0, le=1.0)
    strict_numeric_matching: bool = True
    strict_negation_check: bool = True
    enable_query_consistency: bool = False
```

### 1.2 Independent Negative Test Execution
The following adversarial probe was executed to confirm that passing legacy, hallucinated, or misspelled kwargs raises `ConfigurationError`:

```python
from trustrag.verification.config import VerificationConfig
from trustrag.core.exceptions import ConfigurationError

# Attempting to instantiate with legacy fields that caused silent failure in Step 2:
try:
    VerificationConfig(evidence_threshold=0.80)
    assert False, "Should have raised ConfigurationError!"
except ConfigurationError as e:
    print(f"Correctly caught: {e}")
```

**Result:** `ConfigurationError: Validation error in VerificationConfig: 1 validation error for VerificationConfig: evidence_threshold Extra inputs are not permitted [type=extra_forbidden]`  
**Verification:** Confirmed. The schema actively rejects invalid configurations instead of silently discarding them.

---

## 2. Parameter Wiring in `OutputEvidenceVerifier`

### 2.1 Consumption Trace
In `src/trustrag/verification/output_verifier.py`:
- In `__init__`, the verifier assigns `self._config = config`.
- In `_verify_claim_evidence(self, claim, evidence)`:
  ```python
  required_coverage = self._config.min_support_coverage
  if coverage < required_coverage:
      status = VerificationStatus.UNVERIFIED
      verdict = G3Verdict.INSUFFICIENT_EVIDENCE
      explanation = f"Similarity alone insufficient: ... coverage {coverage:.2f} < {required_coverage:.2f}"
  ```
- The configured value is strictly referenced during the claim-to-evidence coverage check.

---

## 3. Empirical Sensitivity Verification

### 3.1 Controlled Single-Example Synthetic Verification
To confirm that `min_support_coverage` actively dictates the decision threshold, a synthetic claim with support coverage $c = 0.70$ was passed to both verifiers:

1. **Default Verifier (`min_support_coverage = 0.65`):**
   - Condition: $0.70 \ge 0.65$
   - Verdict: `SUPPORTED`
2. **Strict Verifier (`min_support_coverage = 0.80`):**
   - Condition: $0.70 < 0.80$
   - Verdict: `INSUFFICIENT_EVIDENCE` (Abstained)

**Result:** Verified. The verdict shifts deterministically from `SUPPORTED` to `INSUFFICIENT_EVIDENCE`.

### 3.2 Real Benchmark Record Sensitivity Census

The per-example prediction files for `default_g3` (0.65) and `strict_g3` (0.80) were compared record-by-record:

#### RAGTruth Test Split (2,700 records):
- **Records with different verdicts between Default and Strict:** **145 records** (5.37% of dataset)
  - `SUPPORTED` $\to$ `INSUFFICIENT_EVIDENCE`: 6 records
  - `PARTIALLY_SUPPORTED` $\to$ `INSUFFICIENT_EVIDENCE`: 93 records
  - `CONTRADICTED` / `UNCERTAIN` shifts: 46 records
  - Total Abstention Increase: $+70$ records ($370 \to 440$, $+18.9\%$ relative)
  - Partial Unsafe Acceptance: Reduced from 73 to 56 ($23.3\%$ relative risk reduction)

#### HaluEval Test Split (3,000 records):
- **Records with different verdicts between Default and Strict:** **108 records** (3.60% of dataset)
  - **Hallucinated records converted from `SUPPORTED` to `INSUFFICIENT_EVIDENCE`:** **103 records**
  - **Factual records converted from `SUPPORTED` to `INSUFFICIENT_EVIDENCE`:** **0 records**
  - False Supported Count on Hallucinations: Dropped from 239 down to 136 (**43.10% relative reduction**)
  - False Contradiction Count on Factual Claims: Invariant at exactly 13 / 1500 (**0.87%**)

### 3.3 Verification Conclusion
The Step 2 defect (threshold invariance caused by inactive parameter) has been completely and demonstrably remediated. The parameter `min_support_coverage` is rigorously enforced, active in the code, and produces meaningful, safety-enhancing sensitivity across both benchmark datasets.

