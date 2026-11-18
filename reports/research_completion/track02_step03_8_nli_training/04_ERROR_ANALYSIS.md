# TrustRAG — Track 2, Step 3.8: Fine-Grained Error Analysis

## 1. Critical Failure Modes

### False Entailment (Type I Acceptance of Hallucinations)
- **Total False Entailments:** **0** instances (0.00% of non-entailed samples).
  * True Contradictions misclassified as Entailment: **0 / 356** (0.00%)
  * True Neutral (Baseless additions) misclassified as Entailment: **0 / 644** (0.00%)
- **Implication:** The model is more prone to accepting unsupported claims (Neutral) as Entailment than accepting direct contradictions, mirroring findings from Track 2 Step 3.5.

### False Contradiction (Type I False Alarm)
- **Total False Contradictions:** **321** instances.
  * True Entailment misclassified as Contradiction: **251 / 1,662** (15.10%)
  * True Neutral misclassified as Contradiction: **70 / 644** (10.87%)

### Neutral vs. Contradiction Mutual Confusion
- **Total Mutual Confusions:** **358** instances.
  * Neutral predicted as Contradiction: **70**
  * Contradiction predicted as Neutral: **288**
- **Analysis:** Disentangling pure omissions from conflicting facts is an inherently challenging semantic task. The 1,000-step pilot shows initial separation capability, but full-scale training with sequence length 512 is recommended to further reduce this mutual ambiguity.
