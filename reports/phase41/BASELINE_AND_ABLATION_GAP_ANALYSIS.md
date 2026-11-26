# Baseline and Ablation Gap Analysis

## 1. Existing Baselines & Ablations in Repository
- **Phase 04 Step 3 (`reports/phase04_step03_clean_rag_baseline.md`):** Clean RAG baseline (`tfidf_extractive`).
- **Phase 04 Step 9 (`reports/phase04_step09_ablation_study.md`):** Controlled 7-arm ablation (`E1–E7`, $N=58$) on Phase 04 (`v0.4` deterministic architecture).
- **Phase 29 (`reports/phase29/HEAD_TO_HEAD_COMPARISON.md`):** `TrustRAG_MSD` vs `FilterRAG_Threshold` / `ML-FilterRAG` on passage filtering ($N=75$).

## 2. Missing Experiments Required for Publication
1. **Post-Phase 40/40.1 Component Ablations:** No ablation isolates `SemanticAttackClassifier v3` vs regex-only, `GeneratorBoundaryEnforcer` vs G2 MSD alone, `MultilingualSemanticDefense v3` vs base G1, or G3 functional-role/tolerance rules vs raw DeBERTa NLI.
2. **External Defense Baselines:** No head-to-head comparison on Phase 40.1/41 holdouts against published prompt-injection/RAG defenses (e.g., DeBERTa-prompt-injection-v2, LlamaGuard, Spotlighting-only, or Perplexity filtering).
