# G1 Benign Utility Attribution Analysis

From `reports/phase42/RAW_EXPERIMENT_RESULTS/quoted_fpr_results.json` ($N=120$):

| Category | Total | Blocked | Rate (95% CI) | Semantic | Multilingual | Heuristic |
|---|---:|---:|---|---:|---:|---:|
| `benign_security_education` | 25 | 0 | **0.00%** [0.00%, 13.32%] | 0 | 0 | 0 |
| `benign_quoted_attacks` | 25 | 10 | **40.00%** [23.40%, 59.26%] | 0 | 0 | 20 |
| `benign_incident_reports` | 25 | 20 | **80.00%** [60.87%, 91.14%] | 10 | 5 | 20 |
| `benign_threat_intel` | 25 | 15 | **60.00%** [40.74%, 76.60%] | 15 | 5 | 5 |
| `malicious_instructions` | 20 | 20 | **100.00% ADR** [83.89%, 100.0%] | 20 | 5 | 5 |

**Recommendation:** Narrow the paper's G1 benign-utility claim to unquoted educational, technical, and analytical user queries (0% FPR), and explicitly scope SOC incident reports / CTI briefs containing raw quoted payloads as future work requiring quote-attribution masking.
