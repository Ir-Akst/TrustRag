# G2 Sybil & Retrieval Defense Audit

**Auditor:** Principal RAG Architect & Distributed Systems Security Auditor  
**Suite:** Coordinated Multi-Attacker Sybil Benchmark ($K=10$, Removal Cap $=5$)

---

## 1. Audit Scope & Experimental Setup

We tested the G2 Multi-Signal Detector (MSD) against coordinated Sybil attacks across 6 poisoning ratios (10%, 20%, 40%, 50%, 60%, 80%), executing 20 trials per ratio (120 total retrieval trials, 1,200 evaluated passages).

The attack simulates multiple colluding attacker personas (`attacker_alpha`, `attacker_beta`, etc.) injecting high-similarity passages containing prompt injection instructions.

---

## 2. Empirical Findings

### Removal & Residual Metrics by Poisoning Ratio:

| Poison Ratio | Poison Injected | Poison Detected | Poison Pruned | Residual Poison | Clean Presented | Clean Retained | Removal Rate | Clean Retention | 95% Wilson CI (Removal) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **10%** | 20 | 20 | 20 | **0** | 180 | 180 | **100.0%** | **100.0%** | $[83.89\%, 100.00\%]$ |
| **20%** | 40 | 40 | 40 | **0** | 160 | 160 | **100.0%** | **100.0%** | $[91.24\%, 100.00\%]$ |
| **40%** | 80 | 80 | 80 | **0** | 120 | 120 | **100.0%** | **100.0%** | $[95.42\%, 100.00\%]$ |
| **50%** | 100 | 100 | 100 | **0** | 100 | 100 | **100.0%** | **100.0%** | $[96.30\%, 100.00\%]$ |
| **60%** | 120 | 120 | 100 | **20** | 80 | 80 | **83.33%** | **100.0%** | $[75.65\%, 88.94\%]$ |
| **80%** | 160 | 160 | 100 | **60** | 40 | 40 | **62.50%** | **100.0%** | $[54.79\%, 69.63\%]$ |

---

## 3. Removal Cap Policy Analysis

1. **Perfect Containment Below 50%:** At poisoning ratios up to 50%, G2 prunes 100% of injected passages without falsely pruning any legitimate documents.
2. **Cap Engagement at 60%+:** The removal cap ($\lfloor K/2 \rfloor = 5$) engages when 6 or 8 poisoned passages are returned. It limits pruning to 5 items to protect retrieval availability and prevent total context starvation.
3. **Downstream Quarantine Handoff:** Passages that bypass the cap retain low trust scores and are quarantined by G3 / output verification, ensuring that poisoned text is not incorporated into the final response unvetted.
