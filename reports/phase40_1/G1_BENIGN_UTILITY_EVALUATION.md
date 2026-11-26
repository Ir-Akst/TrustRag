# G1 Benign Utility & Security Evaluation (Phase 40.1 Holdout)

**Holdout:** `reports/phase40_1/datasets/holdout_g1.jsonl` ($N=300$: 200 attacks, 100 benign controls).

- **ADR:** **95.00%** (190/200) [95% CI: 91.04%, 97.26%] | **ASR:** 5.00% (10/200)
- **Precision / Recall / F1:** 95.00% / 95.00% / 0.9500
- **Overall Benign FPR:** **10.00%** (10/100) [95% CI: 5.52%, 17.44%]
- **Benign Breakdown:**
  - `benign_cyber_education`: **0.00% FPR** (0/25) [0.00%, 13.32%]
  - `benign_technical_imperative`: **0.00% FPR** (0/25) [0.00%, 13.32%]
  - `benign_documentation`: **0.00% FPR** (0/25) [0.00%, 13.32%]
  - `benign_quoted_content`: **40.00% FPR** (10/25) [23.40%, 59.26%] — remaining FPs on analytical sentences whose attribution phrasing (`"Security auditors test whether a filter flags quoted examples..."`) was not covered by the frozen attribution pattern.
- **Attack Breakdown:** 100% (30/30) on `unseen_imperatives`, `semantic_paraphrases`, `narrative_indirect`, `roleplay_and_pretext`; 100% (40/40) on `multi_sentence_split`; 75% (30/40) on `obfuscated_and_adaptive`.
