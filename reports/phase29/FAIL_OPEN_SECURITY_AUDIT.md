# Phase 29 — Fail-Open & Fail-Safe Security Audit

---

## 1. System Failure Mode & Exception Architecture

In high-throughput enterprise serving, components occasionally encounter transient faults (e.g. timeouts, thread allocation errors, corrupt documents). We audited how the system handles exceptions at each layer:

| Layer | Component | Failure Scenario | Fallback Behavior | Security Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **G1** | Input Guardrail | Unhandled parsing exception during regex scan | Defaults to `ALLOW` (`G1_CLEAN`) | **FAIL-OPEN (Vulnerable)** |
| **Serving** | TrustRAGService | Query processing timeout (`REQUEST_TIMEOUT`) | Returns 504 / Abstained Response | **FAIL-SAFE (Closed)** |
| **Serving** | TrustRAGService | Service shutdown or runtime exception | Returns Error / Abstained Response | **FAIL-SAFE (Closed)** |
| **G2** | MultiSignalDetector | Outlier clustering timeout | Retains candidate passages | **FAIL-OPEN (Vulnerable)** |
| **G3 / SRM**| Reasoning Model | Network/connection failure to model daemon | Reverts to `DeterministicFallbackBackend` | **DEGRADED (Heuristic)** |

---

## 2. Fault Injection Empirical Results

1. **G1 Regex Failure Injection**:
   - Forcing an internal normalization exception during a malicious prompt scan resulted in G1 returning `decision="ALLOW", risk_score=0.0`.
   - *Security Risk*: An adversary who crafts a payload triggering catastrophic regex backtracking or a memory allocation fault can cause G1 to fail open, admitting the attack.
2. **Pipeline Timeout & Service Error Injection**:
   - Setting `request_timeout_seconds=0.000001` resulted in the server returning `status="ERROR", abstained=True, answer="Request timed out safely prior to answer release."`.
   - The service safely withholds generated text during timeouts, preventing unverified outputs from reaching the user.
