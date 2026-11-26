# Multilingual Regression Validation (Phase 40.1)

**Holdout:** `reports/phase40_1/datasets/holdout_multilingual.jsonl` ($N=360$: 9 languages $\times$ 40 samples).

- **Combined ADR:** **98.15%** (265/270) [95% CI: 95.74%, 99.21%]
- **Combined Benign FPR:** **0.00%** (0/90) [95% CI: 0.00%, 4.09%]
- **Per-Language Results:**
  - English, Spanish, French, German, Russian, Hindi, Arabic, Japanese: **100.00% ADR (30/30)**, **0.00% FPR (0/10)**
  - Chinese: **83.33% ADR (25/30)**, **0.00% FPR (0/10)** (5 unseen paraphrase/Pinyin variants missed)
