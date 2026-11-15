# Track 2, Step 3.1.1: Critical Pilot Validity Audit & Architecture Deconstruction

**Audit Date:** November 14, 2026  
**Auditor:** Independent ML Infrastructure Auditor  
**Inspected Artifacts:**
- `tools/evaluation/run_bounded_cpu_pilot.py`
- `tools/evaluation/run_cpu_smoke_tests.py`
- `reports/research_completion/track02_step03_1_cpu_environment/bounded_pilot_results.json`
- `reports/research_completion/track02_step03_1_cpu_environment/smoke_test_results.json`

---

## 1. Executive Summary of Pilot Inspection

The previous Step 3.1 completion report claimed that a 3-step CPU feasibility pilot had verified memory safety (peak RSS 420.6 MB) and throughput (78.1 tokens/sec) on the approved binary dataset.

An independent code-level and telemetry audit reveals that **the pilot did NOT evaluate the actual `microsoft/deberta-v3-small` target model or its tokenizer.** Instead, the pilot executed on a miniature 2-layer, 128-hidden-size toy substitute model with synthetic random token inputs. Consequently, the pilot functions as a **generic PyTorch CPU runtime smoke test**, and **cannot be used as an empirical feasibility benchmark for DeBERTa-v3-small.**

---

## 2. In-Depth Analysis of the Seven Pilot Questions

### Question 1: Was the actual `microsoft/deberta-v3-small` architecture loaded?
**Answer:** **NO.**  
**Evidence:** Citing `tools/evaluation/run_bounded_cpu_pilot.py`, lines 76–83:
```python
# tools/evaluation/run_bounded_cpu_pilot.py:76-83
cfg = DebertaV2Config(
    vocab_size=1000,
    hidden_size=128,
    num_hidden_layers=2,
    num_attention_heads=4,
    intermediate_size=256,
    num_labels=2,
)
```
Comparison with canonical `microsoft/deberta-v3-small`:
- **Target DeBERTa-v3-small:** 6 transformer layers, 768 hidden dimension, 12 attention heads, 3072 intermediate dimension, 128,100 SentencePiece vocabulary. **Total Parameters: 141,894,914 (141.89M)**.
- **Pilot Toy Substitute Model:** 2 transformer layers, 128 hidden dimension, 4 attention heads, 256 intermediate dimension, 1000 vocabulary. **Total Parameters: 475,522 (0.48M)**.
- **Architectural Discrepancy:** The target model is **298.4 times larger** in parameter count than the model evaluated in the pilot.

---

### Question 2: Were pretrained DeBERTa weights loaded?
**Answer:** **NO.**  
**Evidence:** Citing `tools/evaluation/run_bounded_cpu_pilot.py`, lines 55–57:
```python
# tools/evaluation/run_bounded_cpu_pilot.py:55-57
if not has_weights:
    print("[NOTICE] Pretrained weights for microsoft/deberta-v3-small are not staged locally.")
    print("[NOTICE] In accordance with offline policy, remote downloads are NOT initiated.")
    print("[NOTICE] Executing bounded architecture pilot with initialized DebertaV2Config to verify CPU tensor training loops.")
```
The model was instantiated from configuration with randomly initialized Gaussian weights (`DebertaV2ForSequenceClassification(cfg)`). Pretrained weights were neither present nor loaded.

---

### Question 3: Was a randomly initialized model, toy model, mock model or other substitute used?
**Answer:** **YES.**  
**Evidence:** A randomly initialized toy substitute model of 475,522 parameters was instantiated directly in memory without pretrained weights.

---

### Question 4: Were real records from `sft_v2/binary/train.jsonl` consumed?
**Answer:** **PARTIALLY (Metadata only; text was ignored).**  
**Evidence:** In lines 62–70, the script parsed the first 5 JSONL objects from `data/processed/sft_v2/binary/train.jsonl`. In lines 101–103, it extracted the metadata:
```python
# tools/evaluation/run_bounded_cpu_pilot.py:101-103
raw_label = rec["binary_label"]
numeric_label = label_map.get(raw_label, 0)
label_tensor = torch.tensor([numeric_label], dtype=torch.long)
```
However, the actual textual content (`question_or_claim`, `context_or_evidence`, `candidate_response`) was **never tokenized, formatted, or passed to the model**.

---

### Question 5: Were actual DeBERTa tokenizer and sequence-processing steps executed?
**Answer:** **NO.**  
**Evidence:** Citing lines 98–100:
```python
# tools/evaluation/run_bounded_cpu_pilot.py:98-100
seq_len = 64
input_ids = torch.randint(0, 1000, (1, seq_len), dtype=torch.long)
attention_mask = torch.ones((1, seq_len), dtype=torch.long)
```
The inputs were generated as synthetic uniform random integers. The `spm.model` SentencePiece tokenizer was neither loaded nor called. Text tokenization, subword segmentation, special token insertion (`[CLS]`, `[SEP]`), truncation, and padding were completely bypassed.

---

### Question 6: Does the reported 420.6 MB peak RSS include the target model and its tokenizer?
**Answer:** **NO.**  
**Evidence:** In `bounded_pilot_results.json`, the telemetry records:
- `initial_rss_mb`: `14.21 MB`
- `peak_rss_mb`: `420.6 MB`
- `rss_delta_mb`: `406.39 MB`
This 406.39 MB delta represents:
1. Python 3.10 runtime + imported PyTorch dynamic C++ libraries (~250–300 MB).
2. The 0.48M parameter toy model + gradients + AdamW states (~10–20 MB).
3. Minor memory buffer fragmentation.

The target `microsoft/deberta-v3-small` model requires:
- Model parameters (FP32): $141.9\text{M} \times 4\text{ bytes} \approx 568\text{ MB}$.
- Gradients (FP32): $\approx 568\text{ MB}$.
- AdamW optimizer states (FP32): $2 \times 568\text{ MB} \approx 1,136\text{ MB}$.
- SentencePiece vocabulary lookup table: $\approx 50\text{ MB}$.
- **Expected true resident memory for DeBERTa-v3-small:** **$\approx 1.5\text{ to }1.8\text{ GB}$**.  
The reported 420.6 MB is an artifact of the toy substitute.

---

### Question 7: Can the reported throughput be used to estimate DeBERTa training time?
**Answer:** **NO.**  
**Evidence:** The pilot reported throughput of **78.1 tokens/sec** based on an average step latency of 13.7 ms on a 0.48M parameter model at sequence length 64.  
The FLOPs per token for backward training are given by:
$$\text{FLOPs/token} \approx 6 \times P$$
- For the toy model ($P = 0.48\text{M}$): $\text{FLOPs/token} \approx 2.85\times 10^6$.
- For DeBERTa-v3-small ($P = 141.9\text{M}$): $\text{FLOPs/token} \approx 8.51\times 10^8$.
The computational work required for actual DeBERTa-v3-small is **$\approx 298$ times higher per token**. Projecting full training time from the toy pilot would underestimate training duration by two orders of magnitude.

---

## 3. Classification of the Step 3.1 Feasibility Pilot

Based on the empirical evidence:
> **Auditor Classification:** The Track 2 Step 3.1 pilot is officially classified as a **Generic PyTorch CPU Runtime Smoke Test**. It successfully proves that the CPU autograd and optimizer pipeline works on the host, but it does **NOT** establish empirical feasibility, true memory footprint, or throughput for `microsoft/deberta-v3-small`.
