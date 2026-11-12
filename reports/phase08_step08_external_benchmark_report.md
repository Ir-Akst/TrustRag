# TrustRAG Phase 08 Step 08 Report — External Research Benchmark Infrastructure

## 1. Objective
Establish reproducible external research benchmark runners, license/provenance verification, schema/label validation, duplicate and cross-split leakage checks, and honest offline availability accounting across all 7 required external research benchmarks without downloading datasets automatically or fabricating missing metrics.

---

## 2. Implementation Summary
- **Module:** [external_benchmarks.py](file:///home/aditya/rags/TrustRag/src/trustrag/evaluation/external_benchmarks.py)
  - [`audit_external_benchmark`](file:///home/aditya/rags/TrustRag/src/trustrag/evaluation/external_benchmarks.py#L229-L333): Inspects registry [`DatasetMetadata`](file:///home/aditya/rags/TrustRag/src/trustrag/data/registry.py), local cache paths (`data/raw/<name>`, `data/processed/<name>`, explicit `local_path`), record-schema conformance via the official `BaseAdapter`, content-hash duplicates, label distribution, and `train` vs `eval` hash overlap leakage strictly in `offline=True` mode.
  - [`run_external_benchmark`](file:///home/aditya/rags/TrustRag/src/trustrag/evaluation/external_benchmarks.py#L336-L483): Deterministically executes:
    - Claim-verification hallucination benchmarks (`ClaimVerificationRecord`: `ragtruth`, `llm_aggrefact`, `halueval`) via `OutputEvidenceVerifier` (plus optional `SRMClient`), recording `accuracy`, `balanced_accuracy`, `precision`, `recall`, `f1`, `fpr`, and `false_supported_rate`.
    - Security poisoning benchmarks (`SecurityRecord`: `rsb`) via `MultiSignalDetector`.
    - RAG/QA benchmarks (`QueryRecord`: `natural_questions`, `hotpotqa`, `ms_marco`) with reference-answer and relevant-doc-ID completeness checks.
  - **Honesty Classification (`ExternalBenchmarkResult.status`):** Uses `"COMPLETED"`, `"PARTIALLY_READY"`, `"READY"`, and `"BLOCKED"`. Sub-research sample fixtures (`< min_research_records=100`) are marked `"PARTIALLY_READY"` with `parity_claimed=False`. Unavailable corpora stay strictly `"BLOCKED"` with empty metrics (`n=0`).

---

## 3. Offline Audit & Benchmark Results (`seed=42`, `offline=True`)

| Benchmark | Source URI | License / Access | Evaluation / Train Rules | Status | `n` Evaluated | Observed Metrics (`parity_claimed=False`) | Integrity Checks |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **RAGTruth** | `ParticleMedia/RAGTruth` | `MIT` / `open` | Eval + Train allowed | **PARTIALLY_READY** | 5 (smoke fixture `data/raw/ragtruth/test.jsonl`, vs target 18,000) | `acc=0.6000`, `bal_acc=0.6667`, `prec=0.5000`, `rec=1.0000`, `f1=0.6667`, `false_supported_rate=0.0000` | `dup=0`, `leak=0`, `schema_errors=0` |
| **LLM-AggreFact** | `lytang/LLM-AggreFact` | `CC-BY-ND-4.0` / `gated` | Eval only (`permitted_for_training=False`) | **BLOCKED** | 0 | `—` (no cached files offline) | Adapter & usage restriction verified |
| **RSB** | `arXiv:2505.18543` | Academic / `pending_verification` | Eval only (`permitted_for_training=False`) | **BLOCKED** | 0 | `—` (no cached files offline; no public URL) | Adapter & usage restriction verified |
| **HaluEval** | `pminervini/HaluEval` | `MIT` / `open` | Eval + Train allowed | **BLOCKED** | 0 | `—` (no cached files offline) | Adapter & schema verified via fixture test |
| **Natural Questions** | `google-research-datasets/natural_questions` | `CC-BY-SA-3.0` / `open` | Eval + Train allowed | **BLOCKED** | 0 | `—` (no cached files offline) | Adapter & schema verified |
| **HotpotQA** | `hotpotqa/hotpot_qa` | `CC-BY-SA-4.0` / `open` | Eval + Train allowed | **BLOCKED** | 0 | `—` (no cached files offline) | Adapter & schema verified via fixture test |
| **MS-MARCO** | `microsoft/ms_marco` | `Microsoft Research License` / `open` | Eval + Train allowed | **BLOCKED** | 0 | `—` (no cached files offline) | Adapter & schema verified |

**Status Breakdown:** `{'PARTIALLY_READY': 1, 'BLOCKED': 6}`. Research parity against Paper A (`84.0%` RAGTruth / `75.7%` LLM-AggreFact), Paper B, or Paper C is **NOT CLAIMED**.

---

## 4. Verification
- **Unit Tests:** [test_phase_08_step08_external_benchmarks.py](file:///home/aditya/rags/TrustRag/tests/unit/test_phase_08_step08_external_benchmarks.py): **2 passed in 0.81s** (`pytest -W error -q`) covering all 7 offline benchmark status assertions plus synthetic `local_path` runner tests across `ClaimVerificationRecord` (`halueval`), `SecurityRecord` (`rsb`), and `QueryRecord` (`hotpotqa`) including duplicate & split-leakage checks.
- **Type Check (`mypy`):** **2/2 source files passed**.
- **Lint (`ruff check`):** **All checks passed**.
