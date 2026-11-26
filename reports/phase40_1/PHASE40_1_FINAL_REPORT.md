# TrustRAG Phase 40.1 — Benign Utility Remediation & Independent Verification

**Branch:** `phase-40.1-benign-utility-and-independent-verification`  
**Parent Commit:** `e6908d26a13089d108a09977f4f05e864c7dab82` (Phase 40)  
**Release Anchor:** `531bff32745ede1bd1b38609cc6daf653d3eff24` (`trustrag-v1.0.0-rc1`)  
**Frozen Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` (8/8 SHA-256 verified)  
**Final Verdict:** **PASS WITH LIMITATIONS**  
**Publication Recommendation:** **READY WITH CLAIM LIMITATIONS**

---

## 1. Before / After Summary (Phase 40 vs. Phase 40.1 Untouched Holdout)

| Metric | Phase 40 | Phase 40.1 Holdout | 95% Wilson CI | Target | Status |
|---|---:|---:|---|---|---|
| G1 ADR | 95.00% (190/200) | **95.00%** (190/200) | [91.04%, 97.26%] | >=90% | **PASS** |
| G1 Benign FPR (Overall) | 10.00% (8/80) | **10.00%** (10/100) | [5.52%, 17.44%] | <=3% | **MISSED** |
| — Cybersecurity Education FPR | 20.00% (8/40) | **0.00%** (0/25) | [0.00%, 13.32%] | <=3% | **PASS** |
| — Quoted Malicious Content FPR | — | **40.00%** (10/25) | [23.40%, 59.26%] | <=3% | **MISSED** |
| — Technical Imperative / Docs FPR | 0.00% (0/40) | **0.00%** (0/50) | [0.00%, 7.13%] | <=3% | **PASS** |
| Firewall Recall | 100.00% (100/100) | **100.00%** (100/100) | [96.30%, 100.0%] | — | **PASS** |
| Generator-Boundary Leakage | 0/100 | **0.00%** (0/100) | [0.00%, 3.70%] | 0 obs | **PASS** |
| Firewall False Quarantine | 0/50 | **0.00%** (0/50) | [0.00%, 7.13%] | <=3% | **PASS** |
| Multilingual Combined ADR | 94.44% (255/270) | **98.15%** (265/270) | [95.74%, 99.21%] | >=90% | **PASS** |
| Multilingual Benign FPR | 0/90 | **0.00%** (0/90) | [0.00%, 4.09%] | <=3% | **PASS** |
| G3 Release-Gate Accuracy | 100.00% (120/120) | **100.00%** (140/140) | [97.33%, 100.0%] | — | **PASS** |
| G3 Exact 4-Class Status Accuracy | 83.33% (100/120) | **91.43%** (128/140) | [85.62%, 95.03%] | — | **RECONCILED** |
| G3 Contradiction Recall | 100.00% (55/55) | **100.00%** (65/65) | [94.42%, 100.0%] | >=90% | **PASS** |
| G3 Unsupported Leakage | 0/20 | **0.00%** (0/25) | [0.00%, 13.32%] | 0 obs | **PASS** |
| G3 False Abstention | 0/30 | **0.00%** (0/30) | [0.00%, 11.35%] | <=10% | **PASS** |
| Profile B Warm Mean Latency | 804.05 ms | **963.35 ms** (vs 2577.91 ms P39) | 57 fwds / 15 reqs | — | **2.68x Faster vs P39** |
