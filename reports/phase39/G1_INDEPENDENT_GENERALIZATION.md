# G1 Independent Semantic Generalization Audit

**Dataset:** `reports/phase39/datasets/g1_independent_holdout.jsonl` ($N=330$: 250 attacks, 80 benign controls; 330/330 unique).

## 1. Aggregate Results
- **Confusion Matrix:** TP = 74, FP = 0, TN = 80, FN = 176
- **ADR (Recall):** **29.60%** (95% CI: [24.28%, 35.53%])
- **ASR:** **70.40%** (95% CI: [64.47%, 75.72%])
- **FPR:** **0.00%** (95% CI: [0.00%, 4.58%])
- **Precision:** 100.00% | **F1 Score:** 0.4568

## 2. Semantic vs. Lexical/Regex Attribution (on 74 TP detections)
- `semantic_only` (`G1_SEMANTIC_ATTACK` only): **18** (24.3%)
- `lexical_or_regex_only` (`G1_PROMPT_INJECTION` / `G1_SUSPICIOUS_META_PATTERN` / `G1_OBFUSCATION_DETECTED`): **26** (35.1%)
- `both_semantic_and_regex`: **30** (40.5%)

## 3. Per-Category Breakdown

| Category | Ground Truth | Blocked / Total | ADR or FPR | 95% Wilson CI |
|---|---|---|---|---|
| `unseen_imperatives` | ATTACK | 6 / 40 | **15.00% ADR** | [7.06%, 29.07%] |
| `unseen_morphological` | ATTACK | 3 / 30 | **10.00% ADR** | [3.46%, 25.62%] |
| `semantic_paraphrases` | ATTACK | 3 / 30 | **10.00% ADR** | [3.46%, 25.62%] |
| `indirect_narrative` | ATTACK | 0 / 30 | **0.00% ADR** | [0.00%, 11.35%] |
| `roleplay_persona` | ATTACK | 12 / 30 | **40.00% ADR** | [24.59%, 57.68%] |
| `benign_prefaced` | ATTACK | 25 / 30 | **83.33% ADR** | [66.44%, 92.66%] |
| `multi_turn_attack` | ATTACK | 10 / 20 | **50.00% ADR** | [29.93%, 70.07%] |
| `unicode_fragmented` | ATTACK | 15 / 20 | **75.00% ADR** | [53.13%, 88.81%] |
| `adaptive_evasion` | ATTACK | 0 / 20 | **0.00% ADR** | [0.00%, 16.11%] |
| `benign_cyber_education` | BENIGN | 0 / 40 | **0.00% FPR** | [0.00%, 8.76%] |
| `benign_general_imperative` | BENIGN | 0 / 40 | **0.00% FPR** | [0.00%, 8.76%] |

**Conclusion:** Phase 38's 95.00% ADR does not generalize to unseen imperative verbs, indirect narratives, semantic paraphrases, or adaptive evasions.
