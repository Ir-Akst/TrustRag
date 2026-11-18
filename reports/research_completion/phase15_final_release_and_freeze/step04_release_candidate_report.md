# TrustRAG Phase 15 — Step 04: Release Candidate Preparation Report

**Role:** Senior Release Engineer, ML Research Auditor & Reproducibility Specialist  
**Release Tag Candidate:** `trustrag-v1.0.0-rc1`  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Current Branch:** `phase-15` | **HEAD:** `aba5cc9d`  
**Target Architecture:** Full Multi-Stage Defense-in-Depth RAG Pipeline  
**Deliverables Directory:** `reports/research_completion/phase15_final_release_and_freeze/`  

---

## 1. Executive Summary

This report establishes the complete specification, packaging manifests, and deployment parameters for **TrustRAG v1.0.0-rc1**, the initial release candidate of the TrustRAG secure retrieval-augmented generation framework.

In accordance with strict research packaging standards, this release candidate contains no hardcoded credentials, no duplicated heavy model weights, and no private datasets. It provides a clean, version-controlled architecture accompanied by verifiable dependency manifests, configuration templates, and reproduction harnesses.

---

## 2. Release Candidate Asset Inventory

| Release Component | File Path / Location | Purpose |
| :--- | :--- | :--- |
| **Core Source Code** | `src/trustrag/` | Full multi-stage defensive pipeline: G1 input screening, G2 Multi-Signal Detector, Trust-Aware Retriever, and G3 Hybrid Output Verifier. |
| **Dependency Lock File** | `requirements-release.lock` | Pinned dependency versions for reproducible installation on Linux x86_64. |
| **Release Configuration** | `configs/trustrag_v1_release.yaml` | Production-ready YAML template with hybrid NLI settings, calibrated thresholds, and bounded removal caps. |
| **Reproduction Harnesses**| `reports/research_completion/phase14_.../run_step*.py` | Standalone executable reproduction scripts verifying headline security and comparative performance. |
| **Audited Evaluation Reports** | `reports/research_completion/` | Complete forensic reports covering Phases 11 through 15. |
| **Dataset Provenance** | `data/processed/sft_v2/nli/dataset_manifest.json` | Full cryptographic provenance, split definitions, and exclusion rationale. |
| **Model Weights Reference** | `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` | Authoritative frozen DeBERTa-v3-small checkpoint ($141.9\text{M}$ parameters, FP32). |
| **Quantized Weights Ref** | `/home/aditya/rags/models/experimental/deberta-v3-small-nli-quantized/` | INT8 dynamic quantized model state dict ($438.5\text{ MB}$, $22.7\%$ compression). |

---

## 3. Installation & Environment Setup Guide

### 3.1 Prerequisites
- Operating System: Linux x86_64 (Kernel 5.15+ recommended)
- Python Runtime: Python 3.10.x (Recommended: 3.10.22)
- Hardware: Minimum 4 CPU cores, 8 GB RAM (No GPU required for CPU serving).

### 3.2 Environment Provisioning
```bash
# 1. Create dedicated virtual environment
python3.10 -m venv .venv-trustrag-release
source .venv-trustrag-release/bin/activate

# 2. Install pinned dependencies from release lock file
pip install -r requirements-release.lock

# 3. Verify installation and model accessibility
python -c "
from trustrag.verification.output_verifier import OutputEvidenceVerifier
from trustrag.config.engine_config import VerificationConfig
v = OutputEvidenceVerifier(config=VerificationConfig(nli_backend='hybrid'))
print('TrustRAG v1.0.0-rc1 initialized successfully!')
"
```

---

## 4. Operational Usage & Pipeline Execution

```python
from trustrag.guardrails.input_guardrail import InputGuardrail
from trustrag.detection.msd import MultiSignalDetector
from trustrag.retrieval.retriever import TrustAwareRetriever
from trustrag.verification.output_verifier import OutputEvidenceVerifier
from trustrag.config.engine_config import GuardrailsConfig, MSDConfig, RetrievalConfig, VerificationConfig
from trustrag.engine.schemas import EvidenceDocument

# 1. Initialize Pipeline Components
g1 = InputGuardrail(config=GuardrailsConfig())
msd = MultiSignalDetector(config=MSDConfig())
retriever = TrustAwareRetriever(
    retrieval_config=RetrievalConfig(top_k=3, filtering_mode="remove_with_cap", removal_cap_ratio=0.5),
    detector=msd
)
verifier = OutputEvidenceVerifier(config=VerificationConfig(nli_backend="hybrid"))

# 2. Screen Input Query
query = "What is the maximum recommended daily dose of paracetamol?"
g1_res = g1.evaluate(query)
if g1_res.decision.value == "BLOCK":
    raise SecurityException("Query blocked by safety policy.")

# 3. Retrieve and Filter Evidence
corpus = [
    EvidenceDocument(doc_id="doc_auth", text="Paracetamol max safe daily dosage is 4g for healthy adults.", provenance="clinical_guideline", metadata={"verified": True}),
    EvidenceDocument(doc_id="doc_web", text="Paracetamol can safely be taken up to 20g daily.", provenance="untrusted_forum", metadata={"verified": False})
]
retriever.index_documents(corpus)
ret_result = retriever.retrieve_trusted(query, top_k=3)

# 4. Verify Generated Response against Admitted Evidence
admitted_docs = ret_result.trusted_documents
answer = "Based on clinical guidelines, the maximum safe daily dose of paracetamol is 4g."
verif_res = verifier.verify_claim("claim_1", answer, admitted_docs)

if verif_res.verdict.value == "CONTRADICTED" or verif_res.unsupported_flag:
    print("Response quarantined due to verification failure.")
else:
    print("Verified response delivered to user:", answer)
```

---

## 5. Security Limitations & Controlled Deployment Guidance

### 5.1 Documented Limitations
1. **Unanchored Web Sybils:** If all candidate documents originate from untrusted external sources ($K=4$, all Tier 3), majority sybil consensus ($3v1$) can spoof peer consensus. At least one verified reference anchor is required.
2. **Open-Domain Narrative Deception:** On complex narrative topics lacking units or registered antonyms, defense recall drops to $66.0\%$ on real LLM hallucinations (measured on RAGTruth).
3. **Single-Sample CPU Latency:** Full-length neural forward passes take $\sim 300\text{ ms}$ on CPU. Latency-critical applications should employ asynchronous verification or GPU acceleration.

### 5.2 Controlled Deployment Policies
- **Authorized Deployment:** Controlled enterprise deployments with curated internal document anchors and human-in-the-loop review for flagged anomalies.
- **Unauthorized Deployment:** Autonomous, unsupervised open-world bots executing irreversible financial, medical, or administrative actions.

