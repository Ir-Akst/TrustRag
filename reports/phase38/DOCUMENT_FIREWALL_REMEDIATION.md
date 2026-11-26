# Workstream B — Document Firewall & Generator-Boundary Hardening

## 1. Problem Diagnosis
Phase 37 revealed 33.33% generator boundary leakage because indirect prompt injections disguised as academic citations () or developer role headers () were treated as benign passage content.

## 2. Engineering Changes
- Added  in .
- Added  pattern targeting spoofed conversational role prefixes.
- Added  targeting administrative and system override notices.

## 3. Empirical Results
- Total evaluated: =150$ (00$ attacks, 0$ controls).
- Detection Recall: **100.00%** (00/100$) [95% CI: 96.30%, 100.00%].
- Generator Boundary Leakage: **0.00%** (bash/100$) [95% CI: 0.00%, 3.70%].
- False Quarantine Rate: **0.00%** (bash/50$) [95% CI: 0.00%, 7.13%].
- Utility Retention on Benign Technical Docs: **100.00%**.
