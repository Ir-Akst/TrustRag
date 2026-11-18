# Track 2, Step 3.2: Offline Loading & Inference Verification Test

**Audit Date:** November 14, 2026  
**Auditor:** Senior ML Infrastructure Engineer  
**Harness Script:** `tools/evaluation/verify_offline_deberta_loading.py`  
**Execution Environment:** `/home/aditya/rags/.venv-train/bin/python`  

---

## 1. Offline Containment Protocol

The verification test was executed under complete network isolation:
- `os.environ["HF_HUB_OFFLINE"] = "1"`
- `os.environ["TRANSFORMERS_OFFLINE"] = "1"`
- Explicit invocation with `local_files_only=True` on all loader APIs.
- Outbound network requests were strictly prevented by both environment flags and the execution sandbox.

---

## 2. Tokenizer Offline Loading & Encoding Verification

| Parameter | Observed Telemetry | Status |
| :--- | :--- | :--- |
| **Tokenizer Class** | `transformers.models.deberta_v2.tokenization_deberta_v2.DebertaV2Tokenizer` | ✅ **PASSED** |
| **Vocabulary Size** | `128,001` pieces | ✅ **PASSED** |
| **Load Latency** | `202.9 ms` | ✅ **PASSED** |
| **Sample Input Text** | `"TrustRAG verifies evidence grounding in retrieved passages."` | Processed |
| **Tokenized Output** | `['[CLS]', '▁Trust', 'RAG', '▁verifies', '▁evidence', '▁grounding', '▁in', '▁retrieved', '▁passages', '.', '[SEP]']` | Valid Unigrams |
| **Roundtrip Exact Match** | True (`tokenizer.decode(encoded, skip_special_tokens=True) == sample_text`) | ✅ **PASSED** |

---

## 3. Pretrained Model Offline Loading Verification

| Parameter | Observed Telemetry | Expected Architecture Specification | Status |
| :--- | :--- | :--- | :--- |
| **Model Class** | `DebertaV2ForSequenceClassification` | `DebertaV2ForSequenceClassification` | ✅ **PASSED** |
| **Total Parameters** | **141,896,450 (141.9M)** | $\approx 141.9\text{M}$ ($141.89\text{M}$ base $+ 1,538$ cls head) | ✅ **MATCH** |
| **Trainable Parameters**| **141,896,450** | 100% active | ✅ **MATCH** |
| **Hidden Dimension ($d$)**| 768 | 768 | ✅ **MATCH** |
| **Encoder Layers ($L$)** | 6 | 6 | ✅ **MATCH** |
| **Attention Heads ($A$)**| 12 | 12 | ✅ **MATCH** |
| **Model Load Latency** | `312.3 ms` | Fast local disk loading | ✅ **PASSED** |

---

## 4. Single-Example Inference Forward Pass

To confirm that model weights, embeddings, relative attention calculations, and classification projections operate stably on CPU without crashing or generating NaN values, a single inference forward pass was executed:

- **Input Prompt:**
  `Question: Is AES-256 secure? Context: AES-256 uses 256-bit symmetric keys and is resistant to brute force.`  
  `Candidate Answer: AES-256 is secure.`
- **Input Token Count:** 39 tokens
- **Inference Latency:** **322.5 ms**
- **Output Logits:** `[0.151611328125, 0.245361328125]` (Valid non-NaN finite floats)
- **Softmax Probabilities:** `[0.4765625, 0.5234375]`
- **Autograd Execution:** `torch.no_grad()` strictly enforced; zero backward pass or optimizer steps were executed.

---

## 5. Memory Telemetry Before & After

| Phase | Process RSS (MB) | Available Physical RAM (MB) | Swap Free (MB) |
| :--- | :--- | :--- | :--- |
| **Pre-Test Baseline** | 14.33 MB | 3,014.91 MB | 0.41 MB |
| **Post-Model Load** | 514.92 MB | 2,634.87 MB | 0.41 MB |
| **Peak During Forward Pass** | **623.10 MB** | **2,618.70 MB** | 0.41 MB |

**Safety Assessment:** Peak resident memory (623.1 MB) consumed only ~20% of available RAM. More than 2.6 GB of unallocated physical RAM remained free. Zero bytes were paged to swap.
