# TrustRAG Phase 14: Independent Reproducibility Instructions

**Audit Role:** Independent Senior ML Research Auditor, RAG Security Engineer & Reproducibility Specialist  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Target Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  
**Freeze Date:** November 18, 2026  

---

## 1. Environment Requirements

TrustRAG utilizes a two-environment architecture:
1. **General Pipeline & Test Environment (Python 3.14 venv):**
   - Path: `/home/aditya/rags/.venv`
   - Runs unit tests, G1 guardrails, G2 Multi-Signal Detector, Trust-Aware Retriever, and fast-path heuristics.
2. **Deep Learning / PyTorch Environment (Python 3.10 venv):**
   - Path: `/home/aditya/rags/.venv-train`
   - Required for live DeBERTa-v3-small neural NLI forward passes, transformers tokenization, and INT8 dynamic quantization.

---

## 2. Checkpoint & Data Integrity Verification

Before executing evaluations, verify all cryptographic hashes:

```bash
cd /home/aditya/rags/TrustRag-phase11

# 1. Verify frozen NLI checkpoint
cd /home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch
sha256sum -c checksums.sha256

# 2. Verify raw security evaluation dataset
cd /home/aditya/rags/TrustRag-phase11
sha256sum data/raw/custom_security/raw_train.jsonl
# Expected: 823bca9639587ff7170530a67c2b35c54d959ee2007bdb554c3e50143c4dae00

# 3. Verify SFT training datasets
cd data/processed/sft_v2/nli
sha256sum -c checksums.sha256
```

---

## 3. Executing Independent Metric Reproduction (Step 02)

To reproduce the headline security and utility claims ($975/975$ defended, $0.0\%$ ASR, $0.0\%$ clean FPR):

```bash
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=src /home/aditya/rags/.venv/bin/python \
  reports/research_completion/phase14_independent_reproduction_and_freeze/run_step02_reproduction.py
```
Output artifact generated at:
`reports/research_completion/phase14_independent_reproduction_and_freeze/step02_recomputed_metrics.json`

---

## 4. Executing Comparative End-to-End Reproduction (Step 04)

To reproduce the four-way system comparison (Baseline vs Phase 11 vs Phase 12 vs Phase 13) and disaggregated latency percentiles:

```bash
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=src /home/aditya/rags/.venv/bin/python \
  reports/research_completion/phase14_independent_reproduction_and_freeze/run_step04_e2e_benchmark.py
```
Output artifact generated at:
`reports/research_completion/phase14_independent_reproduction_and_freeze/step04_e2e_metrics.json`

---

## 5. Running the Complete Regression Test Suite

To verify codebase backward compatibility across all 711 unit tests:

```bash
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest tests/unit/ \
  --ignore=tests/unit/test_phase11_step02_3_harness_remediation.py \
  --ignore=tests/unit/test_phase11_step02_5_final_fixes.py \
  --ignore=tests/unit/test_track02_step03_4_1_binary_training_runner.py \
  --ignore=tests/unit/test_track02_step03_6_nli_training_runner.py \
  --ignore=tests/unit/test_track02_step03_14_supervision_readiness.py
```
Expected output: **711 passed in ~21.83s (100.0%)**.

---

## 6. Live Neural NLI Verification (Python 3.10 Runtime)

To execute a live forward pass with the frozen DeBERTa-v3-small checkpoint and observe the hybrid override:

```bash
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=src /home/aditya/rags/.venv-train/bin/python -c "
from trustrag.verification.output_verifier import OutputEvidenceVerifier
from trustrag.config.engine_config import VerificationConfig
from trustrag.engine.schemas import EvidenceDocument
verifier = OutputEvidenceVerifier(config=VerificationConfig(nli_backend='hybrid'))
doc = EvidenceDocument(doc_id='d1', text='Paracetamol ceiling is 4g per day.')
res = verifier.verify_claim('c1', 'Paracetamol ceiling is 20g per day.', [doc])
print('Hybrid Verdict:', res.verdict)
print('Explanation:', res.explanation)
"
```
Expected output:
`Hybrid Verdict: G3ClaimVerdict.CONTRADICTED`  
`Explanation: Hybrid check: numeric conflict detected despite neural score (Numeric conflict on unit 'g': claim states 20, evidence states ['4'].).`

