# 14 — Research Paper & Specification Alignment Audit

**Overall Research Compliance Score:** **`28.0%`**
**Traceability References Inspected:** `reports/phase10_research_traceability_matrix.md`, `configs/evaluation/phase10_eval.yaml`, `configs/base.yaml`

---

## 1. Subsystem-by-Subsystem Research Alignment

| Research Specification Requirement | Target Design | Implemented Reality on `main` (`713c54e`) | Status |
| :--- | :--- | :--- | :---: |
| **G1 Prompt Guardrail + Paraphrasing** | Dual syntactic + semantic injection detector with generative paraphraser | Deterministic regex + Unicode normalization; template paraphraser disabled by default | **Partial (`45%`)** |
| **Dense + Sparse Hybrid Retrieval** | Sentence-transformer bi-encoder + FAISS ANN index + persistent vector DB | Ephemeral in-memory `TfidfVectorizer` (1–2 grams) + lexical overlap | **Partial (`25%`)** |
| **G2 6-Signal Multimodal Poison Detector** | Full `F1` perplexity + `F2` embedding norm + `F3..F6` with PoisonedRAG & 3v1 defense | `F1`/`F2` `UNAVAILABLE` offline; `F4` regex + `F6` prior dominate; `p_out` scores `0.9283`; 3v1 defeats `F5`; `removal_cap` bypasses duplicates | **Partial (`35%`)** |
| **LLM Generator + FilterRAG SLM** | Dedicated generative LLM/SLM & passage-filtering SLM comparison | Extractive sentence copier (`mode: extractive`); FilterRAG variants are `PROXY_ONLY` heuristics (`ML_FilterRAG AUC = 0.299`) | **Gap / Proxy (`15%`)** |
| **G3 Claim Graph + NLI/Entailment Verifier** | Structured Claim Graph with semantic NLI verification + automated re-answering | Regex/TF-IDF lexical coverage (`>= 0.65`) + numeric/unit/year rules; `enable_reanswer: false`; `0.50` unseen accuracy in `canonical_v2` | **Partial (`40%`)** |
| **ORPO / LoRA Trained Neural SRM** | `Qwen2.5-3B-Instruct` fine-tuned via ORPO with `<think>` trace & citation checking | **Zero neural checkpoints, zero ORPO scripts**, `torch` not installed; defaults to rule-based `halluguard-srm-fallback` (`backend: disabled`) | **Missing (`5%` interface only)** |
| **Canonical External Research Datasets** | `NQ`, `HotpotQA`, `MS MARCO`, `HaluEval`, `RAGTruth (18k)`, `LLM-AggreFact`, `RSB` | `6/7` have `0` records (`BLOCKED`); `RAGTruth` has `5` records; primary benchmarks use `boolq` (`100`) and 8-template synthetic `custom_security` with split leakage | **Blocked / Insufficient (`10%`)** |
| **Statistical Evaluation Harness** | Per-example JSONL logs, Wilson 95% CIs, McNemar paired tests, Holm-Bonferroni | Implemented cleanly and mathematically verified against Phase 10 artifacts (`100%` match) | **Implemented (`85%`)** |

---

## 2. Core Research Integrity Conclusions

1. **No Measured Research Claims Can Be Made About Neural Hallucination or ORPO Reasoning Yet:** Because `torch`, `transformers`, model weights, and ORPO training scripts are absent and `srm.backend` defaults to `disabled`, Phase 10 acceptance results measure **deterministic TF-IDF + regex heuristics + extractive copy-paste + rule fallback**, not a trained neuro-symbolic TrustRAG system.
2. **External Benchmark Parity Remains Unverified (`NOT VERIFIED`):** Claims cannot generalize beyond the `79` combined `benchmarks_backup` test examples (`40` + `24` synthetic 8-template items, `15` BoolQ items) and `5` RAGTruth items.
3. **Proxy Baselines Must Not Be Cited as FilterRAG Results:** FilterRAG variants execute an extractive similarity proxy (`status="PROXY_ONLY"`), where `ML_FilterRAG` degrades below random guessing (`ROC AUC = 0.2990`, `security_clean_fpr = 1.0`).

