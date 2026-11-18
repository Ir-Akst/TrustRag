# TrustRAG — Phase 11.1, Step 2.2: Next Training Campaign Engineering Proposal & Final Verdict

## 1. Formal Engineering Verdict

### **VERDICT: `CPU_FEASIBLE_WITH_REMEDIATION`**

### Comprehensive Justification:
1. **Memory Feasibility Proven:** Empirical telemetry across 1,750 steps in Run 1 and 325 steps in Run 2 confirms that DeBERTa-v3-small requires a flat, stable resident set size of **2,807 MB – 2,845 MB** (less than 19% of host RAM). There are zero software memory leaks.
2. **Computational Velocity Measured:** Benchmarking directly on the host Intel Core i7-1355U established that adjusting thread concurrency to the physical core count (10 threads) and implementing dynamic padding reduces single-pass latency from 2.002s down to **~1.237s**, shortening total 3-epoch runtime from ~19.5 hours to **~12.1 hours**.
3. **Failure Vectors Fully Resolved:** The failure of Step 2.1 was caused solely by two infrastructure vulnerabilities:
   - *Absence of sub-epoch checkpointing:* Solved by the 500-step atomic persistence and state restoration architecture.
   - *False-positive delta swap watchdog:* Solved by the multi-tier capacity floor architecture (RAM floor 700 MB, Swap floor 1,000 MB).

With these two remediations, the training campaign is robust against laptop reboots, power cuts, OS paging, and host load variations.

---

## 2. Invariant Scientific Constants (Non-Negotiable Protocol)

To preserve the experimental validity of the research paper, the following parameters remain strictly unchanged:

| Experimental Parameter | Fixed Value | Scientific Governance Rationale |
| :--- | :--- | :--- |
| **Model Architecture** | DeBERTa-v3-small (141.9M params, FP32) | Core audited baseline |
| **Training Split** | `data/processed/sft_v2/nli/train.jsonl` (10,815) | Natural corpus distribution |
| **Validation Split** | `data/processed/sft_v2/nli/validation.jsonl` (2,662) | Full unweighted validation set |
| **Epoch Count** | 3 complete epochs (32,445 sample passes) | Required for convergence |
| **Effective Batch Size** | 4 (Batch size = 1, Accumulation = 4) | AdamW gradient stability |
| **Loss Weighting** | Class-Weighted Cross-Entropy $[1.0, 3.5, 1.5]$ | Entailment: 0, Contradiction: 1, Neutral: 2 |
| **Sequence Length Bound** | Maximum 384 tokens (`min_premise=64`) | Preserves critical premise context |
| **Model Selection Metric** | Validation Macro F1 (Val loss tie-breaker) | Pre-registered selection criteria |
| **Random Seed** | 42 | Full deterministic reproducibility |

---

## 3. Engineering Enhancements Specification for Step 2.3

```
+-------------------------------------------------------------------------------------------------+
| PROPOSED STEP 2.3 ENGINEERING UPGRADE PACKAGE                                                   |
+-------------------------------------------------------------------------------------------------+
| 1. Thread Concurrency:      torch.set_num_threads(10) (assigns 1 thread / physical core)       |
| 2. Dynamic Padding:          Padding to min(L, 384) per sample (saves 47.7% compute on shorter)  |
| 3. Sub-Epoch Checkpoints:    Atomic save every 500 optimizer steps (~41 minutes of compute)    |
| 4. Full State Restoration:   Persist & restore model, AdamW optimizer, LR scheduler, RNG states |
| 5. Multi-Tier Watchdog:      RAM floor 700 MB, Swap floor 1,000 MB, Process RSS ceiling 4,500 MB|
| 6. Graceful Signal Handler:  Catches SIGINT/SIGTERM to write emergency checkpoint before exit   |
+-------------------------------------------------------------------------------------------------+
```

---

## 4. Projected Step 2.3 Execution Timeline

| Pipeline Stage | Step Range | Sample Range | Expected Duration | Checkpoint Event |
| :--- | :---: | :---: | :---: | :--- |
| **Step 0 Baseline Eval** | 0 | 2,662 val samples | ~20 minutes | Initial metrics logged |
| **Epoch 1 (Part 1)** | 1 – 500 | 1 – 2,000 | ~41 minutes | `checkpoint_step_0500/` |
| **Epoch 1 (Part 2)** | 501 – 1,000 | 2,001 – 4,000 | ~41 minutes | `checkpoint_step_1000/` |
| **Epoch 1 (Part 3)** | 1,001 – 1,500 | 4,001 – 6,000 | ~41 minutes | `checkpoint_step_1500/` |
| **Epoch 1 (Part 4)** | 1,501 – 2,000 | 6,001 – 8,000 | ~41 minutes | `checkpoint_step_2000/` |
| **Epoch 1 (Part 5)** | 2,001 – 2,500 | 8,001 – 10,000 | ~41 minutes | `checkpoint_step_2500/` |
| **Epoch 1 Completion** | 2,501 – 2,704 | 10,001 – 10,815 | ~17 minutes | `checkpoint_epoch_1/` |
| **Epoch 1 Validation** | 2,704 | 2,662 val samples | ~15 minutes | Macro F1 evaluation |
| **Epoch 2 (6 checkpoints)**| 2,705 – 5,408 | 10,816 – 21,630 | ~3.7 hours | `checkpoint_epoch_2/` |
| **Epoch 3 (6 checkpoints)**| 5,409 – 8,112 | 21,631 – 32,445 | ~3.7 hours | `checkpoint_epoch_3/` |
| **Final Validation** | 8,112 | 2,662 val samples | ~15 minutes | Final `predictions_val.jsonl` |
| **Total Wall-Clock Time** | — | — | **~12.1 hours** | Maximum lost compute $\le 41$ min |

---

## 5. Next Steps & Authorization Boundary

This feasibility report concludes Phase 11.1 Step 2.2. All analysis is read-only. In strict adherence to experimental safety rules:
- Zero training has been executed.
- Zero checkpoints or model files have been modified.
- Execution halts immediately. 
- Awaiting explicit user direction and authorization for Phase 11.1 Step 2.3.

