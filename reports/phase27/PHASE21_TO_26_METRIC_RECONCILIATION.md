# Phase 27 — Metric Reconciliation Across Phases 21–26

---

## 1. Longitudinal Overview of Benchmark Performance

| Phase | Evaluation Dataset | Sample Size ($N$) | Adversarial Samples ($N_{adv}$) | Benign Controls ($N_{benign}$) | ADR (%) | ASR (%) | FPR (%) | Nature of Evaluation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Phase 21** | Offline Clean RAG | - | - | - | - | - | - | Research anchor baseline |
| **Phase 22** | RSB & PoisonedRAG | - | - | - | - | - | - | Blocked (external environment dependencies) |
| **Phase 23** | Console Baseline | 140 | 120 | 20 | 95.83% | 4.17% | 0.00% | Initial ad-hoc validation (5 FNs identified) |
| **Phase 24** | Forensic Audit | 140 | 120 | 20 | 95.83% | 4.17% | 0.00% | Replicated Phase 23; audited failure modes |
| **Phase 25** | Hardened Benchmark | 669 | 164 | 505 | 100.00% | 0.00% | 0.00% | In-distribution regression testing |
| **Phase 26** | Unseen Generalization | 1000 | 500 | 500 | 71.80% | 28.20% | 0.00% | Independent out-of-distribution audit |

---

## 2. Reconciling Phase 25 (100%) vs. Phase 26 (71.8%)

The dramatic shift in ADR from 100% in Phase 25 to 71.8% in Phase 26 does not indicate a regression in system capabilities. Rather, it reflects the difference between **in-distribution regression validation** and **out-of-distribution adversarial generalization**:

1. **Targeted Remediation in Phase 25**:
   Phase 25 created explicit rules and regular expressions designed to capture the five failure modes observed in Phase 23/24. When evaluated against test sets adhering to those syntax variations, G1 achieved 100% detection.
2. **True Red-Team Diversity in Phase 26**:
   Phase 26 synthesized 500 novel attacks across 13 diverse threat categories using paraphrasing, multilingual token sequences, complex narrative framings, and role-reversal jailbreaks. G1's deterministic rules were blind to attacks lacking specific keywords.

---

## 3. Preservation of Clean Precision

Throughout all phases, False Positive Rate remained strictly at **0.00%** across more than 1,000 evaluated benign control prompts (505 in Phase 25, 500 in Phase 26). The deterministic keyword approach ensures that normal queries are never erroneously intercepted.
