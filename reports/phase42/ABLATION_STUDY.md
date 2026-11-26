# Five-Arm Controlled Component Ablation Study

**Protocol:** Fixed Phase 41 evaluation splits (`p41_g1_holdout.jsonl` $N=250$, `p41_firewall_holdout.jsonl` $N=140$, `p41_multilingual_holdout.jsonl` $N=270$, `p41_g3_holdout.jsonl` $N=120$), `seed=42`, frozen DeBERTa-v3-small CPU.

| Arm | G1 ADR | G1 ASR | G1 FPR | ML ADR | Boundary Leak | G3 Gate Acc | G3 Unsup Leak | G3 Con Recall | Time (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **1. Full TrustRAG** | **96.67%** | **3.33%** | 10.00% | **97.22%** | **0.00%** | **100.00%** | **0.00%** | **100.00%** | 4439.75 |
| **2. w/o G1 Semantic** | 36.67% | 63.33% | 5.00% | 86.11% | 0.00% | 100.00% | 0.00% | 100.00% | 937.15 |
| **3. w/o Boundary Enforcer** | 96.67% | 3.33% | 10.00% | 97.22% | **100.00%** | 100.00% | 0.00% | 100.00% | 3069.40 |
| **4. w/o Multilingual** | 96.67% | 3.33% | 10.00% | **66.67%** | 0.00% | 100.00% | 0.00% | 100.00% | 2972.21 |
| **5. w/o G3 Verifier** | 96.67% | 3.33% | 10.00% | 97.22% | 0.00% | **25.00%** | **100.00%** | **0.00%** | 3075.40 |

**Intervention Notes:** Each ablation isolated exactly one module (`SemanticAttackClassifier`, `GeneratorBoundaryEnforcer`, `MultilingualSemanticDefense`, or `EvidenceGroundedVerifier`) while keeping all other layers active.
