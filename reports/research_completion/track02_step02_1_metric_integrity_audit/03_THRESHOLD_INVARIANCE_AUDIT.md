# TrustRAG — Track 1, Step 2.1: Independent Benchmark Metric Integrity Audit
## 03. Threshold Invariance Audit

### 1. The Anomaly Under Audit
In Track 1 Step 2, `default_g3` and `strict_g3` were reported to achieve identical results:
- RAGTruth: 2,700 identical predictions.
- HaluEval: 3,000 identical predictions.
- Zero records changed decision between the two modes.

The Step 2 report attributed this to a "qualitative threshold invariance" of lexical matching across 0.60 vs 0.80 thresholds.

---

### 2. Forensic Code & Configuration Inspection

#### 2.1 Evaluator Code in `run_track02_benchmarks.py`:
```python
    # Baseline 2: Default Production G3 Verifier
    default_verifier = OutputEvidenceVerifier(VerificationConfig(enable_query_consistency=False))
    
    # Baseline 3: Strict Threshold G3 Verifier
    strict_config = VerificationConfig(
        enable_query_consistency=False,
        evidence_threshold=0.70,
        claim_threshold=0.75,
    )
    strict_verifier = OutputEvidenceVerifier(strict_config)
```

#### 2.2 Model Definition in `src/trustrag/config/engine_config.py`:
```python
class VerificationConfig(_ValidatedConfigModel):
    enabled: bool = Field(default=True)
    min_support_coverage: float = Field(default=0.65)
    min_relevance_for_check: float = Field(default=0.10)
    strict_numeric_matching: bool = Field(default=True)
    strict_negation_check: bool = Field(default=True)
    enable_query_consistency: bool = Field(default=True)
    min_query_consistency_score: float = Field(default=0.12)
    enable_reanswer: bool = Field(default=False)
    max_reanswer_attempts: int = Field(default=1)
    min_reanswer_trust_score: float = Field(default=0.6)
    reanswer_timeout_seconds: float = Field(default=5.0)
```

Notice that `evidence_threshold` and `claim_threshold` **do not exist** on `VerificationConfig`.

#### 2.3 Pydantic Model Behavior:
Because `_ValidatedConfigModel` inherits from Pydantic `BaseModel` without `extra="forbid"`, any unrecognized keyword arguments are **silently discarded**.

Inspection of the actual instantiated objects confirms:
```python
>>> default_verifier.config.model_dump() == strict_verifier.config.model_dump()
True
```
Both `default_verifier` and `strict_verifier` had identical `min_support_coverage = 0.65`.

---

### 3. Empirical Verification of Genuine Threshold Sensitivity

To verify whether the G3 verifier is truly sensitive to threshold changes when correctly configured, we evaluated a sample of 100 HaluEval records comparing `min_support_coverage = 0.65` vs `min_support_coverage = 0.80`:
- **Result:** **6 out of 100 records changed verdict** from `SUPPORTED` to `INSUFFICIENT_EVIDENCE`.
- **Conclusion:** G3 is genuinely sensitive to `min_support_coverage`. The Step 2 reported invariance was an artifact of passing non-existent config parameters that were silently ignored.

---

### 4. Audit Finding & Corrective Directive
- **Finding ID:** `DEF-02` (Silent Parameter Discard in Strict Evaluator Configuration).
- **Severity:** Medium (Reporting/Experimental configuration defect; does not invalidate the default production baseline).
- **Impact:** The claim in Step 2 reports that thresholds 0.6 and 0.8 produce identical results was invalid. The `strict_g3` baseline simply re-ran `default_g3`.
- **Correction:** The `strict_g3` results must be classified as a duplicate run of `default_g3` pending re-evaluation with `min_support_coverage=0.80`.
