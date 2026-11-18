# Track 2, Step 3.2: Model Provenance, Licensing & Lineage

**Audit Date:** November 14, 2026  
**Auditor:** Senior ML Infrastructure Engineer  
**Target Model:** `microsoft/deberta-v3-small`  

---

## 1. Upstream Source & Model Identification

The pretrained model was acquired exclusively from the official Microsoft repository on Hugging Face:

| Provenance Attribute | Value |
| :--- | :--- |
| **Repository Identifier** | `microsoft/deberta-v3-small` |
| **Hugging Face Hub URL** | https://huggingface.co/microsoft/deberta-v3-small |
| **Model Author / Publisher** | Microsoft Corporation |
| **Upstream Architecture** | `DebertaV2ForMaskedLM` / `DebertaV2Model` |
| **Acquisition Protocol** | Official `huggingface_hub.snapshot_download` (Direct HTTPS) |
| **Mirror / Third-Party Use** | **NONE** (No third-party mirrors, re-uploads, or unverified checkpoints) |

---

## 2. Architectural Lineage & Technical Specifications

DeBERTa-v3 (Decoding-enhanced BERT with Disentangled Attention, Version 3) incorporates two foundational innovations:
1. **Disentangled Attention:** Each word is represented using two vectors: content vector and relative position vector. Self-attention matrices are computed as disentangled cross-terms: content-to-content, content-to-position, and position-to-content.
2. **Enhanced Masked Language Modeling with ELECTRA-Style RTD:** Replaces traditional MLM with Replaced Token Detection (RTD) using a shared generator-discriminator token embedding structure, significantly improving sample efficiency.

### Architectural Parameters:
- **Hidden Size ($d_{\text{model}}$):** 768
- **Transformer Encoder Layers ($L$):** 6
- **Attention Heads ($A$):** 12 (64 dimensions per head)
- **Intermediate Feed-Forward Size ($d_{\text{ff}}$):** 3,072
- **Positional Embedding:** Relative disentangled position encoding ($k=512$)
- **Vocabulary Size:** 128,100 (Unigram SentencePiece vocabulary)
- **Total Parameters (Backbone + Embeddings):** 141,894,914 ($\approx 141.9\text{M}$)

---

## 3. Licensing & Terms of Use

- **License Type:** **MIT License**
- **Commercial Use:** Permitted under standard MIT terms.
- **Modification / Distribution:** Permitted provided copyright notice and license text are retained.
- **Derivative Verification Work:** Fully compliant with TrustRAG research and defense objectives.
