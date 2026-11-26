# Quoted Malicious Content FPR Root-Cause Analysis

**Dataset:** `reports/phase42/datasets/quoted_fpr_benchmark.jsonl` ($N=120$: 100 benign across 4 categories, 20 malicious).

| Category | Total | Blocked | Rate (95% CI) | `sem_fired` | `ml_fired` | `heur_fired` |
|---|---:|---:|---|---:|---:|---:|
| `benign_security_education` | 25 | 0 | **0.00%** [0.00%, 13.32%] | 0 | 0 | 0 |
| `benign_quoted_attacks` | 25 | 10 | **40.00%** [23.40%, 59.26%] | 0 | 0 | 20 |
| `benign_incident_reports` | 25 | 20 | **80.00%** [60.87%, 91.14%] | 10 | 5 | 20 |
| `benign_threat_intel` | 25 | 15 | **60.00%** [40.74%, 76.60%] | 15 | 5 | 5 |
| `malicious_instructions` | 20 | 20 | **100.00% ADR** [83.89%, 100.0%] | 20 | 5 | 5 |

**Root Cause:** Overall benign FPR on this stress benchmark is **45.00%** ($45/100$, [35.61%, 54.76%]) because:
1. `match_threat_patterns` (`heur_fired`) inspects raw quoted strings unless `_attribution_pat` matches the exact phrasing (`benign_quoted_attacks`).
2. `SemanticAttackClassifier` (`sem_fired`) scores quoted payloads inside SOC incident reports and CTI briefs without masking attributed quotes.
**Proposed Future Remediation (Not Applied in Phase 42):** Add a unified quote-attribution parser upstream of both `SemanticAttackClassifier` and `match_threat_patterns` covering SOC/CTI/audit-log verbs (`observed`, `contained`, `blocked string`, `incident`, `threat intelligence`, `CTI`, `TTP`).
