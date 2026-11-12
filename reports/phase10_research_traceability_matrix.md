# TrustRAG Phase 10 — Research Paper Traceability Matrix

**Verification Note:** A recursive filesystem search (`find /home/aditya -maxdepth 3 -iname "*.pdf"`) confirmed that the three reference PDFs (`HalluGuard_ Evidence-Grounded Small Reasoning Models to Mitigate Hallucinations in Retrieval-Augmented Generation.pdf`, `TrustRAG_RAG_Security_Paper.pdf`, and `2508.02835v2.pdf`) are **not present** in the repository or local workspace. In accordance with Phase 10 research integrity rules, no paper section numbers, tables, page numbers, or reported benchmark metrics are invented from memory; unverified PDF details are explicitly marked `Unverified (PDF absent locally)`.

---

## Paper A: HalluGuard — Evidence-Grounded Small Reasoning Models

| Paper contribution | Paper evidence | TrustRAG implementation | Test / evaluation | Status |
| :--- | :--- | :--- | :--- | :--- |
| 5-class evidence-grounded claim judgment (`GROUNDED`, `INTRINSIC_HALLUCINATION`, `EXTRINSIC_HALLUCINATION`, `INSUFFICIENT_EVIDENCE`, `CONTRADICTED`) | Unverified (PDF absent locally; schema documented in `src/trustrag/srm/schemas.py`) | `src/trustrag/srm/schemas.py`, `src/trustrag/srm/client.py`, `src/trustrag/verification/output_verifier.py` | `tests/unit/test_phase_08_srm_backend.py`, `tests/evaluation/test_phase_10_*.py` | **Implemented (Deterministic Fallback)** |
| `<think>...</think>` reasoning trace parsing and structured JSON judgment extraction | Unverified (PDF absent locally) | `src/trustrag/srm/parser.py`, `src/trustrag/srm/client.py` | `tests/unit/test_phase_08_srm_backend.py` | **Implemented** |
| Small Reasoning Model (4B) neural inference (`hf_local` / `transformers` / `peft`) | Unverified (PDF absent locally) | `src/trustrag/srm/hf_local.py` (raises `SRMUnavailableError` when `torch`/`transformers` absent) | `reports/phase10_srm_evaluation_report.md` | **Blocked** (`torch`/`transformers`/weights unavailable) |
| ORPO / LoRA fine-tuning pipeline on RAGTruth / training corpora | Unverified (PDF absent locally) | Not implemented in Phase 08/09/10 (`Offline CPU-only`) | `reports/phase10_srm_evaluation_report.md` | **Blocked** (`peft`/`trl`/GPU/weights unavailable) |
| Full RAGTruth (`~18k`) & LLM-AggreFact evaluation parity | Unverified (PDF absent locally; prior Phase 08 report notes `84.0%`/`75.7%` unverified against PDF) | `src/trustrag/data/loaders/{ragtruth,llm_aggrefact}.py`, `src/trustrag/evaluation/external_benchmarks.py` | `reports/phase10_comparative_evaluation_report.md` | **Blocked** (only 6-record RAGTruth smoke fixture locally; LLM-AggreFact absent) |

---

## Paper B: TrustRAG — RAG Security Architecture & Six-Signal Detection

| Paper contribution | Paper evidence | TrustRAG implementation | Test / evaluation | Status |
| :--- | :--- | :--- | :--- | :--- |
| G1 Input Query Guardrail (prompt injection, structural/semantic checks, paraphrase defense) | Unverified (PDF absent locally) | `src/trustrag/guardrails/input_guardrail.py` | `reports/phase10_g1_evaluation_report.md` | **Implemented** |
| G2 Six-Signal Multi-Signal Detector (`F1` perplexity, `F2` embedding norm, `F3` query match, `F4` instruction content, `F5` consensus deviation, `F6` provenance prior) | Unverified (PDF absent locally) | `src/trustrag/detection/msd.py`, `src/trustrag/detection/signals.py` | `reports/phase10_g2_ablation_report.md` | **Partial** (`F1` causal LM perplexity & `F2` dense neural embedding unavailable offline without `torch`/`transformers`; `F2` uses TF-IDF/hashed fallback) |
| Trust calibration & trust-aware retrieval with removal cap (`<= 0.5`) | Unverified (PDF absent locally) | `src/trustrag/adaptive/calibration.py`, `src/trustrag/retrieval/retriever.py`, `src/trustrag/adaptive/controller.py` | `reports/phase10_g2_ablation_report.md` | **Implemented** |
| G3 Evidence-grounded claim verification, provenance, and query consistency | Unverified (PDF absent locally) | `src/trustrag/verification/output_verifier.py` | `reports/phase10_g3_verification_report.md` | **Implemented (Heuristic/TF-IDF)** |
| External security & QA benchmarks (`RSB`, `NQ`, `HotpotQA`, `MS MARCO`, `HaluEval`) | `arXiv:2505.18543` cited in `src/trustrag/data/loaders/rsb.py` (PDF absent locally) | `src/trustrag/data/loaders/`, `src/trustrag/evaluation/datasets/inventory.py` | `reports/phase10_dataset_inventory.md` | **Blocked** (external corpora absent offline) |

---

## Paper C: FilterRAG / ML-FilterRAG (`2508.02835v2`)

| Paper contribution | Paper evidence | TrustRAG implementation | Test / evaluation | Status |
| :--- | :--- | :--- | :--- | :--- |
| Extractive Frequency Density (FD) proxy over retrieved passages | Unverified (PDF `2508.02835v2.pdf` absent locally) | `src/trustrag/evaluation/filterrag_experiment.py` (kept isolated from production `MSDConfig.enable_freq_density = False`) | `reports/phase10_filterrag_evaluation_report.md` | **Implemented (Proxy Only)** |
| SLM-based intermediate answer generation + Frequency Density filtering | Unverified (PDF `2508.02835v2.pdf` absent locally) | `src/trustrag/evaluation/filterrag_experiment.py` (raises/marks SLM stage `BLOCKED` offline) | `reports/phase10_filterrag_evaluation_report.md` | **Blocked** (live SLM unavailable offline) |
