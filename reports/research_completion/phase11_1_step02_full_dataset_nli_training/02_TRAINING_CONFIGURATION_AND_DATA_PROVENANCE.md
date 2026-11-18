# TrustRAG — Phase 11.1, Step 2: Full-Dataset NLI Training Audit
## 02 — Training Configuration & Data Provenance Analysis

- **Audit Date:** 2026-11-14T18:25:00Z
- **Auditor:** Senior ML Training Engineer & Reproducibility Engineer

---

### 1. Architectural & Configuration Discrepancy Matrix

The requested authorization parameters were compared against the actual capabilities of the audited training harness (`tools/training/train_nli_classifier.py`):

| Parameter | User-Authorized Specification | Existing Runner Implementation | Compatibility Status |
| :--- | :--- | :--- | :--- |
| **Model Backbone** | DeBERTa-v3-small (141.9M) | `DebertaV2ForSequenceClassification` | ✅ COMPATIBLE |
| **Dataset Split** | Full `sft_v2/nli/train.jsonl` (10,815) | Configurable via `--train-file` | ❌ BLOCKED by sampler quota |
| **Epoch Count** | Exactly 3 complete epochs | **NOT IMPLEMENTED** (Only single-pass loop over `train_records`) | ❌ HARNESS MISMATCH |
| **Effective Batch Size** | Exactly 4 | **NOT IMPLEMENTED** (Hardcoded batch_size=1, accumulation=1) | ❌ HARNESS MISMATCH |
| **Total Optimizer Steps** | $\approx 8,111$ steps ($32,445 / 4$) | Hardcoded to `max_train_samples` (1 step per sample) | ❌ HARNESS MISMATCH |
| **Sequence Length** | 384 with hypothesis preservation | Supported via `evidence_preserving_tokenize` | ✅ COMPATIBLE |
| **Loss Function** | Class-weighted cross-entropy `[1.0, 3.5, 1.5]` | **NOT IMPLEMENTED** (Delegates to unweighted loss in HuggingFace `outputs = model(**kwargs)`) | ❌ HARNESS MISMATCH |
| **Sampling Strategy** | Audited Step 3.10 starvation-resistant | Hardcoded `strategy="stratified_class_balanced"` | ❌ MATHEMATICALLY INCOMPATIBLE |
| **Validation Frequency** | At each epoch (3 evaluations) | Hardcoded at Step 0 and Step final | ❌ HARNESS MISMATCH |
| **Checkpoint Selection** | Best validation Macro F1 | Hardcoded to save only at final step | ❌ HARNESS MISMATCH |
| **Validation Artifact** | `predictions_val.jsonl` (per-sample logits/probs) | **NOT IMPLEMENTED** (Only writes summary JSON) | ❌ HARNESS MISMATCH |

---

### 2. In-Depth Analysis of Sampler Failure & Double-Compensation

#### A. Mathematical Quota Failure
The audited function `load_nli_dataset(..., strategy="stratified_class_balanced")` in lines 380–408 of `train_nli_classifier.py` enforces equal class representation:
$$\text{target\_per\_class} = \frac{\text{max\_samples}}{3} = \frac{10,815}{3} = \mathbf{3,605\text{ samples per class}}$$
However, the physical file `data/processed/sft_v2/nli/train.jsonl` contains:
- `ENTAILMENT`: 6,707 samples (Sufficient)
- `NEUTRAL`: 2,688 samples (**Deficient**: 2,688 < 3,605)
- `CONTRADICTION`: 1,420 samples (**Critically Deficient**: 1,420 < 3,605)

When `load_nli_dataset` reaches the end of the file, it has gathered only 1,420 Contradictions and 2,688 Neutrals. Lines 407–408 immediately trigger:
```python
for c in ["ENTAILMENT", "CONTRADICTION", "NEUTRAL"]:
    if counts[c] != targets[c]:
        raise ValueError(f"Class {c} quota mismatch: expected {targets[c]}, got {counts[c]}")
```
**Conclusion:** `strategy="stratified_class_balanced"` **physically cannot load 10,815 samples**. The maximum balanced subset that can ever be drawn from this file without replacement is $1,420 \times 3 = \mathbf{4,260\text{ samples}}$. Loading all 10,815 samples requires changing to natural distribution (`strategy="sequential"`), which is currently hardcoded and inaccessible via CLI.

#### B. The Double-Compensation Pitfall
The authorization instructed:
> *"Use class-weighted cross-entropy with the proposed weights `[1.0, 3.5, 1.5]` ONLY after verifying the exact class ordering and confirming that the sampler/loss combination does not accidentally double-compensate the minority classes."*

Audit verification confirms:
1. In the natural training distribution, `CONTRADICTION` prevalence is $1,420 / 10,815 = \mathbf{13.13\%}$.
2. If `stratified_class_balanced` sampling is used, the sampler inflates `CONTRADICTION` to $33.33\%$ (a **$2.54\times$ artificial boost**).
3. If loss weights `[1.0, 3.5, 1.5]` (where Index 1 is Contradiction) are applied on top of this balanced stream:
   $$\text{Effective Weight}(\text{CONTRADICTION}) = 2.54 \times 3.5 = \mathbf{8.89\times \text{ relative to ENTAILMENT}}$$
4. This results in **severe double-compensation**, heavily skewing gradient updates, penalizing the natural majority class, and causing extreme false positive rates on Contradiction.
5. In accordance with Section 4 instructions (*"If the proposed combination is incompatible with the audited sampler or label mapping, STOP before training"*), training is **strictly blocked**.

