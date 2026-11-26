# Independent G1 Security & Benign Utility Audit

**Dataset:** `reports/phase41/datasets/p41_g1_holdout.jsonl` ($N=250$: 150 attacks, 100 benign controls; 250/250 unique).  
**Command:** `PYTHONPATH=src /home/aditya/rags/.venv-phase15-clean10/bin/python reports/phase41/scripts/run_phase41_audit.py`

- **Confusion Matrix:** TP=145, FP=10, TN=90, FN=5
- **ADR (Recall):** **96.67%** (145/150) [95% CI: 92.43%, 98.57%] | **ASR:** 3.33% (5/150)
- **Precision / F1:** 93.55% / 0.9508
- **Overall Benign FPR:** **10.00%** (10/100) [95% CI: 5.52%, 17.44%]
- **Semantic vs. Heuristic Attribution (on 145 TP):**
  - `semantic_only` (`G1_SEMANTIC_ATTACK`): **90** (62.1%)
  - `multi_signal`: **55** (37.9%)
  - `heuristic_only`: **0** (0.0%)
- **Category Breakdown:**
  - `direct_injection`, `unseen_imperatives`, `narrative_roleplay`, `paraphrase_and_multi`, `indirect_override`: **25/25 (100.00%)**
  - `adaptive_obfuscated_fragmented`: **20/25 (80.00%)** [60.87%, 91.14%]
  - `benign_cyber_education`, `benign_technical_docs`, `benign_analytical`: **0/25 FP (0.00%)**
  - `benign_quoted_content`: **10/25 FP (40.00%)** [23.40%, 59.26%] — confirms Phase 40.1 finding.
