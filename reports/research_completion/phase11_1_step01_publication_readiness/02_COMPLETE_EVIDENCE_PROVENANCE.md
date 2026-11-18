# TrustRAG — Phase 11.1, Step 1: Publication Readiness Plan
## 02 — Complete Evidence Provenance & Artifact Traceability

- **Audit Date:** 2026-11-14T18:15:00Z
- **Auditor:** Principal Research Scientist, Reproducibility Engineer & ML Experimental Auditor

---

### 1. Publication-Grade Provenance Table

Every empirical claim, benchmark score, and metric reported across Track 1, Track 2, and Phase 10 was traced to its raw source file on disk. If the underlying per-sample predictions or files are missing, it is explicitly classified as `NOT_VERIFIABLE` or `UNVERIFIED`.

| Claim / Metric | Exact Source Artifact | Dataset & Split | Evaluation Scope & Method | Reproducible? | Permitted Scientific Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Binary Generalization Accuracy: 76.60%** | `reports/research_completion/track02_step03_5_binary_generalization/evaluation_results.json`<br>`metrics.combined.accuracy` | 1,000 samples from `data/processed/sft_v2/binary/validation.jsonl` (500 HaluEval, 500 RAGTruth) | Offline CPU inference; batch size 1; seq len 128; per-example predictions logged in `predictions/` | **YES** (Per-sample JSONL persisted) | Fine-tuning DeBERTa-v3-small yields 76.6% accuracy on a 1,000-sample out-of-domain binary test split. |
| **Binary Hallucination Precision: 91.30%** | `reports/research_completion/track02_step03_5_binary_generalization/evaluation_results.json`<br>`metrics.combined.per_class.HALLUCINATED.precision` | Same 1,000 validation samples | TP=294, FP=28; threshold=0.5 | **YES** | The binary verifier has a very low false positive rate (5.6%) when flagging hallucinations. |
| **Binary Hallucination Recall: 58.80%** | `reports/research_completion/track02_step03_5_binary_generalization/evaluation_results.json`<br>`metrics.combined.per_class.HALLUCINATED.recall` | Same 1,000 validation samples | TP=294, FN=206; threshold=0.5 | **YES** | The binary verifier misses 41.2% of hallucinations in out-of-domain contexts. |
| **Binary Brier Score: 0.1772** | `reports/research_completion/track02_step03_5_binary_generalization/evaluation_results.json`<br>`metrics.combined.calibration.brier_score` | Same 1,000 validation samples | Multi-class Brier reduction across sample probabilities | **YES** (Calculable from prediction logs) | Probability outputs reflect moderate binary calibration. |
| **Step 3.16 NLI Accuracy: 38.05%** | `reports/training_runs/step03_16/training_results.json`<br>`final_metrics.accuracy` | 2,662 samples from `data/processed/sft_v2/nli/validation.jsonl` | Offline CPU evaluation over full validation split; seq len 384 | **YES** (From confusion matrix) | 1,000-step remediated pilot correctly classifies 1,013 of 2,662 samples. |
| **Step 3.16 Contradiction Recall: 4.49%** | `reports/training_runs/step03_16/training_results.json`<br>`final_metrics.per_class.CONTRADICTION.recall` | 356 true CONTRADICTION samples in validation split | TP=16, FN=340 (`[[85, 16, 255]]` predicted as ENT/CON/NEU) | **YES** (From confusion matrix) | The model is effectively blind to contradictions (misses 95.51% of contradictory premises). |
| **Step 3.16 NLI ECE-10: 0.1304** | `reports/training_runs/step03_16/training_results.json`<br>`final_metrics.ece_10bins` | 2,662 validation samples | 10-bin Expected Calibration Error | **NOT_VERIFIABLE** (Raw probabilities discarded) | Cannot be independently verified without re-running full inference pass. |
| **Step 3.16 NLI Brier Score: 0.6614**| `reports/training_runs/step03_16/training_results.json`<br>`final_metrics.brier_score` | 2,662 validation samples | 3-way Brier score calculation | **NOT_VERIFIABLE** (Raw probabilities discarded) | Cannot be independently verified without re-running full inference pass. |
| **Step 3.8 Post-Training Acc: 24.12%** | `reports/research_completion/track02_step03_8_nli_training/training_results.json`<br>`final_metrics.accuracy` | 2,662 validation samples | Evaluated over unweighted 1,000-step pilot | **YES** (From confusion matrix) | Collapsed run suffered tail starvation; 0 Entailment predictions made. |
| **Step 0 Initial Baseline Acc: 24.19%**| `reports/training_runs/step03_16/training_results.json`<br>`initial_metrics.accuracy` | 2,662 validation samples | Initial evaluation before step 1 | **YES** (From confusion matrix) | All 2,662 samples predicted as NEUTRAL (`644 / 2662 = 24.19%`). |
| **Draft Baseline Figure (43.88%)** | **NONE** (Does not exist in any raw JSON artifact on disk) | Hypothesized on 2,662 validation split | Unverified calculation ($1168 / 2662$) from draft narrative table | **UNVERIFIED / PROHIBITED** | Prohibited from being cited as an empirical baseline in research manuscripts. |
| **HotpotQA Candidate MRR@10: 0.8965** | `reports/research_completion/track02_step02_4_retrieval_discrepancy_resolution/recomputed_retrieval_metrics.json` | 7,405 validation queries | TrustAwareRetriever (TF-IDF + lexical) on 10 candidate distractors | **YES** | Lexical re-ranking achieves 0.8965 MRR on 10 candidate passages. Full-corpus retrieval unverified. |
| **MS MARCO Candidate MRR@10: 0.4626** | `reports/research_completion/track02_step02_4_retrieval_discrepancy_resolution/recomputed_retrieval_metrics.json` | 9,706 validation queries | TrustAwareRetriever on 6-10 search candidate snippets | **YES** | Candidate snippet re-ranking achieves 0.4626 MRR. Full-corpus retrieval unverified. |

---

### 2. Dataset Provenance and Licensing Audit

| Dataset | Canonical Role | Raw Record Count | Processed SFT v2 Count | License | Provenance / Upstream Source | Academic Citation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RAGTruth** | Binary & NLI Hallucination Supervision | 17,790 responses (from 2,965 sources) | 12,072 train / 3,018 val (Binary)<br>10,815 train / 2,662 val (NLI) | MIT | `https://github.com/ParticleMedia/RAGTruth` | Niu et al. (ACL 2024) |
| **HaluEval** | Binary Out-of-Domain Generalization | 35,000 (QA, Dialogue, Summarization) | 13,982 train / 2,966 val (Binary)<br>Excluded from NLI (lack of 3-way labels) | MIT | `https://github.com/RUCAIBox/HaluEval` | Li et al. (EMNLP 2023) |
| **HotpotQA** | Multi-hop Question Answering & Retrieval | 7,405 dev queries (Distractor setting) | Stored as local 10-candidate pool; full 5.23M corpus missing | CC BY-SA 4.0 | `https://hotpotqa.github.io/` | Yang et al. (EMNLP 2018) |
| **MS MARCO** | Passage Ranking Benchmark | 10,047 dev queries (Snippet setting) | Stored as local candidate pool; full 8.84M corpus missing | MS MARCO Terms | `https://microsoft.github.io/msmarco/` | Nguyen et al. (NeurIPS 2016) |

---

### 3. Checkpoint Integrity Summary

All checkpoints inspected on disk are verified against their SHA-256 manifests:
- **Binary Pilot Checkpoint:** `models/trained/deberta-v3-small-binary-pilot1000/model.safetensors`<br>`SHA-256: 472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b` (Verified immutable)
- **Failed NLI Checkpoint:** `models/trained/deberta-v3-small-nli-pilot1000/model.safetensors`<br>`SHA-256: 500832fa1b9b7c67c2c08d9e1f4d4c76d235d15fa9960d76e1e6e81c220a2f8a` (Verified immutable)
- **Remediated NLI Checkpoint:** `models/trained/deberta-v3-small-nli-remediated/model.safetensors`<br>`SHA-256: bb4c26bab4a147c2ad6bdae7ec8a1ecc56841ea56fc89922fd377fb5d70fe113` (Verified immutable)

