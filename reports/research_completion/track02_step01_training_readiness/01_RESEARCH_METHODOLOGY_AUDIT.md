# TrustRAG — Track 2, Step 1: Independent Neural Training Readiness Audit
# 01 — Research Paper Methodology Audit

**Audit Scope:** Deep inspection of the three primary reference papers guiding TrustRAG neural development:
1. **Paper A:** *HalluGuard: Evidence-Grounded Small Reasoning Models to Mitigate Hallucinations in Retrieval-Augmented Generation*
2. **Paper B:** *TrustRAG: A Dual-Stage Guardrail and Multi-Signal Detection Framework for Defending Retrieval-Augmented Generation Against Knowledge-Base Poisoning* (Aditya et al., PDF at `step_1239_media_0.pdf`)
3. **Paper C:** *FilterRAG: Defending Retrieval-Augmented Generation Against Knowledge Poisoning Attacks via Frequency Density Filtering* (arXiv:2408.02835 / 2508.02835)

---

## 1. Paper A: HalluGuard Methodology Audit

### 1.1 Model Architecture & Parameter Scale
- **Proposed Architecture:** Decoder-only causal Small Reasoning Model (SRM) with explicit chain-of-thought `<think>` capabilities.
- **Model Size:** **4 Billion parameters (4B)**.
- **Backbone Class:** Compact open-weights autoregressive language models (e.g., Llama-3-4B / Qwen-2.5-4B family).
- **Core Role:** Evaluates query-document-claim triplets in a closed-book, document-grounded verification setup.

### 1.2 Verification Output Format
Unlike binary classifiers that output only a scalar score or classification token, HalluGuard outputs a structured reasoning payload:
```
<think>
[Detailed natural language step-by-step reasoning cross-checking the claim against the source document]
</think>
{
  "judgment": "SUPPORTED" | "CONTRADICTED" | "INSUFFICIENT_EVIDENCE",
  "hallucination_type": "GROUNDED" | "EVIDENT_CONFLICT" | "BASELESS_INFO" | "UNRESOLVED_DISCREPANCY",
  "cited_spans": ["exact text verbatim from document"],
  "confidence": float
}
```

### 1.3 Training Methodology & Objectives
HalluGuard prescribes a two-stage training paradigm:
1. **Stage 1 — Supervised Fine-Tuning (SFT):**
   - **Objective:** Teach the 4B backbone the reasoning format, evidence extraction, citation syntax, and JSON schema conformity.
   - **Data:** Synthetic/curated evidence-claim reasoning pairs (HalluClaim dataset, constructed from FineWeb and distilled via Llama-3.3-70B).
2. **Stage 2 — Odds Ratio Preference Optimization (ORPO):**
   - **Objective:** Jointly optimizes the causal language modeling loss and a preference odds-ratio penalty without needing a separate reference model or reward model.
   - **Loss Function:**
     $$\mathcal{L}_{\text{ORPO}} = \mathcal{L}_{\text{SFT}} + \lambda \mathcal{L}_{\text{OR}}$$
   - **Preference Pair Format:**
     - Prompt: Context passage + Question + Candidate Claim.
     - Chosen: Verifiable reasoning trace with accurate span citation and correct judgment.
     - Rejected: Plausible but ungrounded reasoning trace, hallucinated citation span, or incorrect classification.

### 1.4 Hardware Requirements
- **Reported Environment:** Multiple high-memory GPUs (e.g., 4x to 8x NVIDIA A100 80GB SXM) for synthetic data generation and full/LoRA ORPO fine-tuning.
- **Inference Requirements:** Low-latency deployment on a single 16GB–24GB GPU (e.g., RTX 4090 or A10G) under 8-bit or 4-bit quantization.

---

## 2. Paper B: TrustRAG Paper Methodology Audit

### 2.1 Scope & Primary Contributions
Based on inspection of the primary paper (`step_1239_media_0.pdf`):
- **Core Framework:** Defense-in-depth architecture wrapping standard RAG with three cooperating guardrails:
  - **G1 (Input Guardrail):** Query canonicalization, character-level sanitization, Base64 decoding/extraction, prompt injection screening.
  - **G2 (Multi-Signal Detector / MSD):** Fusion of 6 heuristic/statistical signals over retrieved passages:
    1. Text perplexity (KenLM / small causal LM)
    2. Embedding-norm anomaly
    3. Query-passage lexical/semantic match
    4. Instruction-content detection
    5. Cross-consensus agreement
    6. Source provenance score
  - **G3 (Output Guardrail):** Evidence-grounded claim-level consistency verification before releasing answers to users.

### 2.2 Neural Training Mandates in TrustRAG Paper
- **Explicit Finding:** The TrustRAG paper **does not propose, require, or mandate neural model training**.
- The paper's core contributions are structural: signal fusion algorithms, soft down-weighting policies (capping passage removal at $k_{\text{cap}}$), and three-stage guardrail orchestration.
- The G3 verifier in the core paper is evaluated using heuristic and external zero-shot verification backends.
- Therefore, neural training of an SRM in TrustRAG is an **architectural extension** (incorporating HalluGuard into G3) rather than a mandate of the core TrustRAG security paper.

---

## 3. Paper C: FilterRAG & ML-FilterRAG (`2508.02835v2`)

### 3.1 Frequency Density (`Freq-Density`) Methodology
- **Concept:** Adversarial poisoned passages injected into knowledge bases exhibit an unnaturally dense concentration of target query and answer tokens.
- **FilterRAG:** Computes extractive frequency density score $FD(d_j)$ and filters passages above threshold $\epsilon$.
- **ML-FilterRAG:** Uses an intermediate Small Language Model (SLM) to generate intermediate answer $a_j = \text{SLM}(q_i, d_j)$, then computes statistical features (perplexity, joint log-prob, token density) and trains a lightweight classifier.
- **TrustRAG Implementation Status:**
  - Implemented strictly as an offline research baseline in `src/trustrag/evaluation/filterrag_experiment.py`.
  - Explicitly disabled in production runtime (`MSDConfig.enable_freq_density = False`).
  - Marked as `BLOCKED_NO_LIVE_SLM` for intermediate SLM generation due to absent local model weights.

---

## 4. Methodological Synthesis: Mandated vs Optional vs Missing

| Research Dimension | Explicitly Mandated by Paper | Reasonable Implementation Interpretation | Missing / Unspecified in Paper |
| :--- | :--- | :--- | :--- |
| **Model Size** | HalluGuard mandates **4B parameters**. | Smaller 1.5B/3B models (e.g. Qwen2.5-1.5B/3B) could be evaluated as low-compute proxies. | Exact tokenizer truncation strategy for multi-page documents. |
| **Training Stages** | HalluGuard mandates **SFT followed by ORPO**. | SFT can be evaluated independently before attempting ORPO. | Exact learning rate warmup schedule, weight decay, and random seeds. |
| **Reasoning Chains** | Explicit `<think> ... </think>` natural language justifications required. | Synthetic generation via larger teacher models (Llama-3.3-70B / GPT-4o) prior to SFT. | Full open-source release of the raw HalluClaim prompt templates. |
| **Preference Data** | Pairwise chosen/rejected reasoning traces. | Deriving answer preference pairs from HaluEval QA as an initial intermediate objective. | Quantitative ratio of SFT examples to ORPO preference pairs. |
| **Hardware** | High-end GPU clusters for 70B distillation and 4B training. | Parameter-Efficient Fine-Tuning (QLoRA 4-bit) on a single 16GB–24GB GPU. | Training time wall-clock benchmarks on commodity consumer hardware. |

---

## 5. Audit Conclusion on Methodology

The research methodology required for HalluGuard SRM training is clear and well-specified in literature. However, TrustRAG's current repository has not yet implemented the SFT formatting pipelines, ORPO data builders, or training scripts necessary to realize this methodology.

