# TrustRAG — Phase 11.1, Step 2.1: Dataset Integrity & Hyperparameter Configuration

## 1. Dataset Integrity & Partition Manifest

Both training and validation datasets reside in the audited SFT v2 directory structure. Preflight verified file integrity, partition sizes, and complete isolation from any test or unlabelled data.

| Dataset Split | Relative Path | Line Count | SHA-256 Digest |
| :--- | :--- | :--- | :--- |
| **Training Split** | `data/processed/sft_v2/nli/train.jsonl` | 10,815 | `b1777c7ac608d6d79171dbc4deaeb7bf5c4ba87acf83adbe53d63020524474ad` |
| **Validation Split** | `data/processed/sft_v2/nli/validation.jsonl` | 2,662 | `7601dd266edde160c51e1032150ea42c031131cb6be89c601637ad464121615c` |

---

## 2. Empirical Class Distribution & Imbalance Analysis

| Class Name | Label Index | Train Count | Train % | Val Count | Val % | Loss Weight |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`ENTAILMENT`** | 0 | 6,707 | 62.02% | 1,662 | 62.43% | 1.0 |
| **`CONTRADICTION`** | 1 | 1,420 | 13.13% | 356 | 13.37% | 3.5 |
| **`NEUTRAL`** | 2 | 2,688 | 24.85% | 644 | 24.19% | 1.5 |
| **Total** | — | **10,815** | **100.00%** | **2,662** | **100.00%** | — |

### Observations:
1. The training and validation splits display nearly identical marginal class proportions (~62.0% Entailment, ~13.1% Contradiction, ~24.9% Neutral).
2. The class weights $[1.0, 3.5, 1.5]$ inversely balance the minority Contradiction class ($\approx 3.5\times$ relative to Entailment) to drive recall without introducing artificial resampled distribution artifacts.

---

## 3. Serialization & Input Formatting

Input text is formatted using the evidence-preserving serialization strategy:
- **Premise Format:** `Premise: {premise}`
- **Hypothesis Format:** `Hypothesis: {hypothesis}`
- **Sequence Length Bounds:**
  - Maximum sequence length: 384 tokens
  - Minimum premise tokens: 64 tokens (guaranteed allocation to avoid premise starvation when hypothesis is long)
- **Tokenization:** DeBERTa-v3 SentencePiece tokenizer with offline local loading (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`).

---

## 4. Hyperparameter Matrix

| Hyperparameter | Value | Rationale |
| :--- | :--- | :--- |
| **Base Model Architecture** | DeBERTa-v3-small (12 layers, 768 hidden, 12 heads) | Offline local base weights |
| **Parameter Count** | 141,897,219 parameters (FP32) | CPU FP32 numerical stability |
| **Epochs** | 3 complete epochs | Full natural corpus convergence |
| **Batch Size (Per-Device)** | 1 sample | Minimizes peak CPU RAM footprint |
| **Gradient Accumulation** | 4 steps | Effective batch size = 4 |
| **Optimizer** | AdamW ($\beta_1=0.9, \beta_2=0.999, \epsilon=10^{-8}$) | Standard Transformer optimization |
| **Base Learning Rate** | $2.0 \times 10^{-5}$ | Validated fine-tuning rate |
| **Learning Rate Schedule** | Linear warmup (500 steps) followed by linear decay to 0 | Prevents catastrophic early gradient updates |
| **Weight Decay** | 0.01 | $L_2$ regularization |
| **Gradient Clipping** | Max norm 1.0 | Safeguards against gradient explosions |
| **Random Seed** | 42 | Full deterministic reproducibility |
| **CPU Worker Threads** | 16 threads | Optimized for host CPU thread allocation |
| **Watchdog Cutoff** | 100,000.0s (~27.78 hours) | Generous ceiling for complete 3-epoch execution |
| **RAM Abort Threshold** | $< 700.0\text{ MB}$ available | Host OS crash protection |
| **Swap Free Min** | $< 1,000.0\text{ MB}$ free | Prevents host hard lockups |
| **Swap Growth Abort** | $> 1,000.0\text{ MB}$ from baseline | Delta memory expansion limit |

