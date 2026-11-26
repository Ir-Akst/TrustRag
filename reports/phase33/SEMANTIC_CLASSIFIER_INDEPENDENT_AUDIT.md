# Phase 33 Independent Audit: Semantic Classifier Architecture & Generalization

## 1. Classification Engine Reality: Hybrid or Learned?
An independent inspection of `src/trustrag/guardrails/semantic_classifier.py` confirms that `SemanticAttackClassifier` is **not a generalized neural model** (such as a BERT or RoBERTa embedding classifier), but rather an **interpretable, calibrated linear scoring classifier** over structured regex feature extractors with non-linear interaction terms.

### Mathematical Formulation
$$P(\text{attack} \mid x) = \sigma\left(\frac{b + \sum_{k} w_k \cdot f_k(x) + \sum_{i,j} w_{i,j} \cdot (f_i(x) \times f_j(x))}{T}\right)$$
- Base Logit: $b = -3.20$ ($\sigma(-3.20) \approx 0.0392$)
- Weights: $w_k \in [1.50, 2.80]$
- Interaction terms: `feat_action_x_target` ($w=2.80$), `feat_narrative_x_target` ($w=2.60$), `feat_roleplay_x_target` ($w=2.50$).

## 2. Generalization Reality: Lexical Patterns vs Semantic Understanding
While the architecture prevents false positives on benign queries ($0.0\%$ FPR), its feature extractors rely strictly on regular expression keyword groups.

### Empirical Holdout Test ($N=200$, 100 fresh attacks, 100 controls)
We tested fresh attacks using synonyms not included in `feat_action_override`:
- Unseen verbs: `"unshackle"`, `"jettison"`, `"overrule"`, `"waive"`, `"decouple"`, `"divest"`, `"disclaim"`, `"surrender"`, `"discard"`.
- Results:
  - **Adversarial Detection Rate (ADR):** **8.00%** (8/100 detected).
  - **Attack Success Rate (ASR):** **92.00%** (92/100 evaded detection).
  - **Clean Control FPR:** **0.00%** (0/100 falsely flagged).
  - **Precision:** 1.000, **Recall:** 0.080, **F1-Score:** 0.1481.

### Root Cause Analysis
Because the interaction terms require `feat_action_override` to be non-zero to activate the $+2.80$ interaction weight, any query that replaces the predefined verb list with a novel synonym fails to trigger the interaction weight. With only the target feature triggering, the logit remains:
$$-3.20 + 1.85 = -1.35 \implies \sigma(-1.35) \approx 0.2059 < 0.35 \text{ (ALLOW)}$$
The query is allowed through without flagging.

## 3. Scientific Recommendation
For Phase 34, TrustRAG should either:
1. Incorporate dense semantic sentence embeddings (e.g., MiniLM or DeBERTa embedding similarity) to evaluate semantic cosine proximity to known attack vectors.
2. Expand the lexical synonym dictionary using WordNet / LLM-generated synonym expansions.
