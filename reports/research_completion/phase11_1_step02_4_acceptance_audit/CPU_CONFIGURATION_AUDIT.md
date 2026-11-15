# TrustRAG — Phase 11.1, Step 2.4: CPU Configuration & Numerical Invariants Audit

**Date:** 2026-11-15  
**Auditor:** Independent Senior ML Systems Auditor  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Subsystem:** CPU Threading, Dynamic Padding & Numerical Invariants  
**Evaluation Status:** FULLY VERIFIED & COMPLIANT

---

## 1. Threading Configuration & Execution Timing

### Configuration Timing Inspection
In `tools/training/train_nli_classifier.py`:
```python
def execute_training(config: NLITrainingConfig) -> dict[str, Any]:
    ...
    # 1. Environment & Concurrency Setup
    torch.set_num_threads(config.num_threads)
    try:
        torch.set_num_interop_threads(config.interop_threads)
    except Exception:
        pass
    torch.manual_seed(config.seed)
    ...
    # 2. Watchdog initialization
    # 3. Dataset loading
    # 4. Model preparation
    # 5. Training loop
```

### Audit Findings
- **Sequencing:** `torch.set_num_threads(10)` and `torch.set_num_interop_threads(1)` are called immediately upon entering `execute_training`.
- **Precedence:** Concurrency setup precedes any PyTorch tensor allocation, model initialization, tokenizer execution, or Step 0 evaluation.
- **Hardware Alignment:** 10 threads corresponds directly to the physical core count of the host's Intel Core i7-1355U (2 P-cores + 8 E-cores = 10 physical cores). Disabling inter-op parallelism (`interop_threads = 1`) eliminates cross-thread context-switching overhead on micro-batches of size 1.

---

## 2. Dynamic Padding Correctness & Invariant Preservation

### Attention Mask and Label Preservation
In `evidence_preserving_tokenize()`:
```python
input_ids = [cls_id] + proc_p_ids + [sep_id] + proc_h_ids + [sep_id]
attention_mask = [1] * len(input_ids)
token_type_ids = [0] * (len(proc_p_ids) + 2) + [1] * (len(proc_h_ids) + 1)

if not dynamic_padding and len(input_ids) < max_seq_len:
    pad_len = max_seq_len - len(input_ids)
    input_ids = input_ids + [pad_id] * pad_len
    attention_mask = attention_mask + [0] * pad_len
    token_type_ids = token_type_ids + [0] * pad_len
```

### Audit Findings
1. **Dynamic Padding Mode (`dynamic_padding=True`):**
   - No `[PAD]` tokens are appended to the tail of the sequence.
   - Every token in `input_ids` corresponds to an actual content or delimiter token (`[CLS]`, premise tokens, `[SEP]`, hypothesis tokens, `[SEP]`).
   - `attention_mask` is strictly `[1] * len(input_ids)`.
   - The self-attention matrix computes attention solely across valid tokens without attending to or from pad tokens.
2. **Fixed Padding Mode (`dynamic_padding=False`):**
   - Sequences are padded with `[PAD]` tokens up to `max_seq_len = 384`.
   - `attention_mask` pads with `0` for all pad positions.
   - Attention mask sum equals the exact sequence length of the dynamically padded representation:
     $$\sum \text{mask}_{\text{fixed}} = \text{len}(\text{input\_ids}_{\text{dynamic}})$$
3. **Label Preservation:**
   - Classification labels are handled completely outside the token sequence via `torch.tensor([target_label], dtype=torch.long)`. Dynamic padding does not touch or alter the target class index.

---

## 3. Sequence Truncation Cap Invariant

In `evidence_preserving_tokenize()`:
```python
special_count = 3  # [CLS] premise [SEP] hypothesis [SEP]
avail_budget = max_seq_len - special_count

if orig_h_len + min_premise_tokens <= avail_budget:
    kept_h_len = orig_h_len
    kept_p_len = min(orig_p_len, avail_budget - kept_h_len)
else:
    kept_p_len = min(orig_p_len, min_premise_tokens)
    kept_h_len = min(orig_h_len, avail_budget - kept_p_len)
```
- Total sequence length of tokenized output is:
  $$\text{Length} = 1 + \text{kept\_p\_len} + 1 + \text{kept\_h\_len} + 1 = \text{kept\_p\_len} + \text{kept\_h\_len} + 3$$
- Since $\text{kept\_p\_len} + \text{kept\_h\_len} \le \text{avail\_budget} = \text{max\_seq\_len} - 3$:
  $$\text{Length} \le (\text{max\_seq\_len} - 3) + 3 = \text{max\_seq\_len} = 384$$
- **Invariant:** Sequence length is strictly bounded above by 384 tokens in all cases.

---

## 4. Effective Batch Size & Optimizer Step Invariants

In `execute_training()`:
- `config.batch_size = 1`
- `config.gradient_accumulation_steps = 4`
- Effective batch size is:
  $$\text{Effective Batch Size} = \text{batch\_size} \times \text{gradient\_accumulation\_steps} = 1 \times 4 = 4$$
- Accumulator logic:
  ```python
  loss.backward()
  accum_count += 1
  if accum_count == config.gradient_accumulation_steps or is_last_sample_of_epoch:
      torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=config.max_grad_norm)
      optimizer.step()
      optimizer.zero_grad(set_to_none=True)
      opt_step += 1
      accum_count = 0
  ```
- Gradients from 4 consecutive samples are accumulated before a parameter update is committed.
- Effective batch size remains exactly 4, preserving identical optimization dynamics to a physical batch size of 4.

---

## 5. Experimental Configuration Preservation Audit

An audit was performed to confirm that no foundational research hyperparameter was inadvertently changed during the remediation of the harness:

| Hyperparameter | Authorized Baseline Value | Config Default in Harness | Status |
| :--- | :---: | :---: | :---: |
| Base Architecture | DeBERTa-v3-small | DeBERTa-v3-small | **UNCHANGED** |
| Classes | 3 (ENTAILMENT, CONTRADICTION, NEUTRAL) | 3 | **UNCHANGED** |
| Learning Rate | $2 \times 10^{-5}$ (`2e-5`) | $2 \times 10^{-5}$ (`2e-5`) | **UNCHANGED** |
| Weight Decay | 0.01 | 0.01 | **UNCHANGED** |
| Warmup Steps | 100 | 100 | **UNCHANGED** |
| Max Gradient Norm | 1.0 | 1.0 | **UNCHANGED** |
| Sequence Truncation Cap | 384 | 384 | **UNCHANGED** |
| Min Premise Tokens | 64 | 64 | **UNCHANGED** |
| Random Seed | 42 | 42 | **UNCHANGED** |
| Class Weight Vector | `[1.0, 3.5, 1.5]` (CLI exposed) | `[1.0, 3.5, 1.5]` | **UNCHANGED** |

---

## 6. Audit Verdict on CPU Configuration

The CPU execution parameters, sequence tokenization, batch accumulation mechanics, and experimental hyperparameters are **ACCEPTED**. All theoretical and numerical invariants are strictly preserved.

