# Phase 29 — FilterRAG Methodological Reproduction Details

---

## 1. Algorithmic Breakdown of FilterRAG

FilterRAG calculates the Frequency-Density ($FD$) of a candidate passage $d_j$ relative to query $q_i$ and an intermediate answer $a_j$:

$$FD(d_j, q_i, a_j) = \frac{\sum_{w \in W_{relevant}} \text{count}(w, d_j)}{\text{len}(d_j)}$$

where $W_{relevant}$ contains keywords shared between the query and generated/extracted answer.

### The Two Evaluated Variants:
1. **FilterRAG-Threshold**:
   - A passage is pruned if $FD(d_j) < \epsilon$.
   - $\epsilon$ is chosen via grid search on the validation set to maximize F1. In our experiments, $\epsilon = 0.70$ was the optimal validation threshold.
2. **ML-FilterRAG**:
   - Constructs a 4-dimensional feature vector per passage:
     $$\mathbf{x}_j = [\text{FreqDensity}(d_j), \text{QueryMatch}(d_j), \text{RetrievalScore}(d_j), \text{TokenNorm}(d_j)]$$
   - A `LogisticRegression` classifier with balanced class weights is trained strictly on `train` splits and evaluated on `test`.

---

## 2. Experimental Integrity & Separation

- All FilterRAG experiments are isolated in `src/trustrag/evaluation/filterrag_experiment.py`.
- Production `configs/base.yaml` strictly keeps `msd.enable_freq_density: false`.
- Training data never leaks into evaluation splits (enforced via split guard exceptions in `MLFilterRAGModel.fit`).
