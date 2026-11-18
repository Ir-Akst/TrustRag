# TrustRAG — Track 2, Step 3.9: Root Cause & Engineering Recommendations

## 1. Verified Root Causes vs. Disproven Hypotheses

### Disproven Hypotheses
1. **Hypothesis: Label Mapping Inversion:**
   - *Status:* **DISPROVEN**.
   - *Evidence:* Code, config, model head, and evaluation decoding all map ENTAILMENT to 0, CONTRADICTION to 1, and NEUTRAL to 2.
2. **Hypothesis: Exploding Gradients or Numerical Divergence:**
   - *Status:* **DISPROVEN**.
   - *Evidence:* Gradient norm clipping at 1.0 prevented explosion. Final parameter norms remain stable ($\|W\| \approx 0.55$).
3. **Hypothesis: Dataset Corruption or Split Leakage:**
   - *Status:* **DISPROVEN**.
   - *Evidence:* Train and validation record counts and hash checks match Step 3.6/3.7 baselines with zero overlapping example IDs.

### Verified Root Causes
1. **Unshuffled Class-Capped Sampling Created 295-Step Unbroken Non-Entailment Tail:**
   - *Evidence:* In `train.jsonl`, Entailment is 62% of the dataset. Sequential iteration filled the 334-sample Entailment quota by record 705. Records 706–1000 had 0 Entailment samples. Because `random.shuffle()` was omitted, the model was subjected to 295 consecutive negative updates against class 0, pushing $z_0$ to -1.45 and reducing $p_0$ to 5.1%.
2. **Extreme Truncation via `max_seq_len = 128` Destroyed Semantic Distinctions:**
   - *Evidence:* 100% of train and validation samples exceed 128 tokens (mean lengths: 943.8 and 638.0). Default `longest_first` truncation cut critical contextual evidence and hallucination spans, rendering premises and hypotheses incomplete.

---

## 2. Engineering Recommendations for Subsequent Phases

> [!IMPORTANT]
> In accordance with the strict safety boundaries of Track 2 Step 3.9, no training is proposed or initiated automatically. These recommendations are documented strictly for future planning.

1. **Deterministic Random Shuffle After Balanced Selection:**
   When sampling a balanced subset, shuffle the selected records with a fixed seed before passing them to the training loop:
   ```python
   random.Random(seed).shuffle(selected)
   ```
   This guarantees that batches are identically and independently distributed (i.i.d.) across all 1,000 steps, preventing recency bias and class collapse.

2. **Increase Sequence Length and Support Smarter Truncation:**
   - Increase `max_seq_len` from 128 to 384 or 512.
   - For premise/hypothesis pairs, prioritize preserving the hypothesis and relevant premise spans (e.g. `truncation="only_first"` to truncate premise while keeping hypothesis intact, or context window chunking).

3. **Mini-Batching or Gradient Accumulation:**
   - Increase effective batch size from 1 to 8 or 16 using gradient accumulation (`gradient_accumulation_steps=8` or `16`).
   - Accumulating gradients across multiple classes averages out class-specific logit pushes and stabilizes AdamW momentum.
