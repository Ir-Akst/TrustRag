# TrustRAG Phase 40 — Final Report

**Branch:** `phase-40-architectural-security-remediation`  
**Parent Commit:** `433e7f65abd17233dcaec363845fdb652d4692eb` (Phase 39 audit)  
**Release Anchor:** `531bff32745ede1bd1b38609cc6daf653d3eff24` (`trustrag-v1.0.0-rc1`)  
**Frozen Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` (8/8 SHA-256 verified)  
**Final Verdict:** **PASS WITH LIMITATIONS**  
**Publication Recommendation:** **READY WITH CLAIM LIMITATIONS**

---

## 1. Before / After Metrics (Phase 39 Baseline vs. Phase 40 Untouched Holdout)

| Metric | Phase 39 Baseline | Phase 40 Holdout | 95% Wilson CI | Target | Status |
|---|---:|---:|---|---|---|
| G1 Overall ADR | 29.60% (74/250) | **95.00%** (190/200) | [91.04%, 97.26%] | >=90% | **PASS** |
| G1 Unseen Imperatives ADR | 15.00% (6/40) | **100.00%** (30/30) | [88.65%, 100.0%] | >=85% | **PASS** |
| G1 Indirect Narrative ADR | 0.00% (0/30) | **100.00%** (30/30) | [88.65%, 100.0%] | >=85% | **PASS** |
| G1 Benign FPR | 0.00% (0/80) | **10.00%** (8/80) | [5.15%, 18.51%] | <=3% | **MISSED** |
| Firewall Recall | 45.45% (50/110) | **100.00%** (100/100) | [96.30%, 100.0%] | — | **PASS** |
| Generator-Boundary Leakage | 54.55% (60/110) | **0.00%** (0/100) | [0.00%, 3.70%] | 0 obs | **PASS** |
| Firewall False Quarantine | 0.00% (0/50) | **0.00%** (0/50) | [0.00%, 7.13%] | <=3% | **PASS** |
| Multilingual Combined ADR | 59.26% (160/270) | **94.44%** (255/270) | [91.04%, 96.60%] | >=90% | **PASS** |
| Multilingual Benign FPR | 2.22% (2/90) | **0.00%** (0/90) | [0.00%, 4.09%] | <=3% | **PASS** |
| G3 Gate Accuracy | 92.14% (129/140) | **100.00%** (120/120) | [96.90%, 100.0%] | — | **PASS** |
| G3 Contradiction Recall | 78.57% (55/70) | **100.00%** (55/55) | [93.47%, 100.0%] | >=90% | **PASS** |
| G3 Unsupported Leakage | 0.00% (0/20) | **0.00%** (0/20) | [0.00%, 16.11%] | 0 obs | **PASS** |
| G3 False Abstention | 17.14% (6/35) | **0.00%** (0/30) | [0.00%, 11.35%] | <=10% | **PASS** |
| Profile B Warm Mean Latency | 2577.91 ms | **804.05 ms** | 57 PyTorch fwds / 15 reqs | — | **3.2x Faster** |
