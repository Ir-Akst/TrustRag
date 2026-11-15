# TrustRAG Research Completion — Track 1, Step 2.2: Metric Definitions

## 1. Safety Metrics

All rates include explicit numerators and denominators:

### 1.1 Strict False Supported Rate (Strict FSR)
$$\text{Strict FSR} = \frac{\text{Hallucinated records assigned exactly } \text{SUPPORTED}}{\text{Total Hallucinated Records}}$$
- **Purpose:** Primary safety metric. Measures catastrophic failure where fabricated content is fully certified as factual.

### 1.2 Partial-Inclusive Unsafe Acceptance Rate
$$\text{Partial-Inclusive Unsafe Rate} = \frac{\text{Hallucinated records assigned } \text{SUPPORTED} \lor \text{PARTIALLY\_SUPPORTED}}{\text{Total Hallucinated Records}}$$
- **Purpose:** Conservative safety metric. Measures any scenario where an ungrounded claim was not rejected or abstained from.

### 1.3 False Contradiction Rate (FCR)
$$\text{FCR} = \frac{\text{Factual records assigned exactly } \text{CONTRADICTED}}{\text{Total Factual Records}}$$
- **Purpose:** Measures utility destruction where true information is incorrectly flagged as contradictory.

### 1.4 Partial-Inclusive Factual Rejection Rate
$$\text{Partial-Inclusive Rejection Rate} = \frac{\text{Factual records assigned } \text{CONTRADICTED} \lor \text{PARTIALLY\_SUPPORTED}}{\text{Total Factual Records}}$$
- **Purpose:** Measures the combined penalty on factual claims under policies that treat partial support as non-acceptance.

---

## 2. Coverage Metrics

- **Explicit Decisive Coverage:** $\frac{\text{SUPPORTED} + \text{CONTRADICTED}}{\text{Total Evaluated}}$
- **Partial-Support Coverage:** $\frac{\text{PARTIALLY\_SUPPORTED}}{\text{Total Evaluated}}$
- **Strict Abstention Rate:** $\frac{\text{INSUFFICIENT\_EVIDENCE} + \text{UNCERTAIN}}{\text{Total Evaluated}}$
- **Inclusive Decisive Coverage:** $\frac{\text{SUPPORTED} + \text{CONTRADICTED} + \text{PARTIALLY\_SUPPORTED}}{\text{Total Evaluated}}$
- **Non-Full-Support Rate:** $\frac{\text{Total Evaluated} - \text{SUPPORTED}}{\text{Total Evaluated}}$

---

## 3. Binary Classification Policies

### Policy 1: Conservative Defense Policy (All Records)
- Evaluates the end-to-end user experience in safety-critical deployments.
- **Negative ($Y=0$, Safe/Factual):** Assigned exactly `SUPPORTED`.
- **Positive ($Y=1$, Unsafe/Hallucinated):** Assigned `CONTRADICTED`, `PARTIALLY_SUPPORTED`, `INSUFFICIENT_EVIDENCE`, or `UNCERTAIN`.
- Denominator: All $N$ records.

### Policy 2: Strict Decisive-Only Policy
- Evaluates verifier discrimination strictly when it renders a definitive support or conflict decision.
- **Negative ($Y=0$):** `SUPPORTED`.
- **Positive ($Y=1$):** `CONTRADICTED`.
- **Excluded:** `PARTIALLY_SUPPORTED`, `INSUFFICIENT_EVIDENCE`, `UNCERTAIN`.
- Denominator: Only decisive records ($N_{\text{decisive}}$).
