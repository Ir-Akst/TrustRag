# TrustRAG — Phase 11.1, Step 2: Full-Dataset NLI Training Audit
## 04 — Final Validation Metrics & Pre-Registered Targets

- **Audit Date:** 2026-11-14T18:25:00Z
- **Auditor:** Senior ML Training Engineer & Independent Experimental Auditor

---

### 1. Pre-Registered Target Comparison

The authorization pre-registered three empirical research targets for the final selected checkpoint over the 2,662 validation set:

| Pre-Registered Metric | Target | Final Achieved Value | Evaluation Status |
| :--- | :---: | :---: | :--- |
| **Contradiction Recall** | $\ge 65.0\%$ | **N/A** | Run blocked during preflight; zero optimizer steps executed. |
| **Macro F1 Score** | $\ge 0.650$ | **N/A** | Run blocked during preflight; zero optimizer steps executed. |
| **ECE-10 Calibration Error** | $\le 0.100$ | **N/A** | Run blocked during preflight; zero optimizer steps executed. |

---

### 2. Operational Discipline Confirmation

In strict compliance with independent research standards:
- **No thresholds or labels were manipulated.**
- **No metrics were fabricated or simulated.**
- Because preflight safety and sampler compatibility gates failed, **zero backward passes were executed**.
- Reporting targets as unachieved due to preflight blockage maintains absolute fidelity to empirical truth.

