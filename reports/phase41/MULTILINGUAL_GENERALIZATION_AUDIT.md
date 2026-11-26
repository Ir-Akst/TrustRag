# Independent Multilingual Generalization Audit

**Dataset:** `reports/phase41/datasets/p41_multilingual_holdout.jsonl` ($N=270$: 9 languages $\times$ 30 samples).

- **Combined ADR:** **97.22%** (175/180) [95% CI: 93.66%, 98.81%]
- **Combined Benign FPR:** **0.00%** (0/90) [95% CI: 0.00%, 4.09%]
- **Per-Language Results (20 attacks + 10 benign per language):**
  - English, Spanish, French, German, Russian, Hindi, Arabic, Japanese: **100.00% ADR (20/20)** [83.89%, 100.0%], **0.00% FPR (0/10)** [0.00%, 27.75%]
  - Chinese: **75.00% ADR (15/20)** [53.13%, 88.81%], **0.00% FPR (0/10)** — confirms Phase 40.1's Chinese unseen-variant gap (`Hu1lue4 suo3you3 zhi3ling4...` / `Bu yao zunshou...` Pinyin variants).
