# TrustRAG Phase 11.2 — Step 06: Independent Clean RAG Benchmark Acquisition & Frozen NLI Evaluation Report

**Auditor Role:** Senior ML Evaluation Engineer & Independent Research Auditor  
**Date:** 2026-11-18  
**Audit Scope:** STRICTLY READ-ONLY EVALUATION OF FROZEN CHECKPOINT  
**Repository:** `/home/aditya/rags/TrustRag-phase11` — Branch `phase-11` — HEAD `aba5cc9d`  
**Target Model Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  
**Delivered Directory:** `reports/research_completion/phase11_2_step06_clean_benchmark/`

---

## Table of Contents

1. [Executive Summary & Final Verdict](#1-executive-summary--final-verdict)
2. [Dataset Discovery, Provenance & Licensing](#2-dataset-discovery-provenance--licensing)
3. [Annotation Quality Gate & Ground-Truth Derivation](#3-annotation-quality-gate--ground-truth-derivation)
4. [Benchmark Integrity & Contamination Verification](#4-benchmark-integrity--contamination-verification)
5. [Frozen Model Inference Telemetry](#5-frozen-model-inference-telemetry)
6. [Complete Threshold Operating-Point Evaluation](#6-complete-threshold-operating-point-evaluation)
7. [Clean Evidence False Rejection & Preservation Dynamics](#7-clean-evidence-false-rejection--preservation-dynamics)
8. [Comparison with Phase 11.1 Step 05 Internal Validation Proxy](#8-comparison-with-phase-111-step-05-internal-validation-proxy)
9. [Independent Reproducibility & Bit-Level Audit](#9-independent-reproducibility--bit-level-audit)
10. [Limitations & Statistical Uncertainty](#10-limitations--statistical-uncertainty)
11. [Recommended Next Experiments](#11-recommended-next-experiments)
12. [Sign-Off & Integrity Seal](#12-sign-off--integrity-seal)

---

## 1. Executive Summary & Final Verdict

This audit executes **Step 06** of the TrustRAG research campaign. Prior to this step, clean-query utility was evaluated exclusively on internal validation proxies (derived from the same dataset split used for model selection and temperature fitting). Step 06 establishes an **independent, document-disjoint clean RAG evaluation benchmark** containing 2,536 valid pairs (2,231 clean evidence pairs) and runs frozen inference using the checkpoint `deberta-v3-small-nli-phase11_1-full3epoch`.

### Key Experimental Findings

| Dimension | Measured Value | 95% Confidence Interval |
| :--- | :---: | :---: |
| **Benchmark Sample Size** | **2,536 valid NLI pairs** | — |
| **Clean Evidence Pairs Evaluated** | **2,231 pairs** ($1,757$ Entailment + $474$ Neutral) | — |
| **Contradiction Sensitivity Controls** | **305 pairs** | — |
| **Source Document Overlap (Train / Val)** | **0 documents (0.00%)** | — |
| **Argmax Classification Accuracy** | **73.74%** (Balanced Acc: 53.16%) | $[71.99\% - 75.42\%]$ |
| **Clean False Contradiction Rate at $\theta = 0.16$** | **12.37%** (276 / 2,231) | $[11.07\% - 13.80\%]$ |
| **Entailment False Alarm Rate at $\theta = 0.16$** | **6.72%** (118 / 1,757) | $[5.64\% - 7.98\%]$ |
| **Neutral False Alarm Rate at $\theta = 0.16$** | **33.33%** (158 / 474) | $[29.24\% - 37.70\%]$ |
| **Clean Evidence Preservation Rate at $\theta = 0.16$** | **87.63%** (1,955 / 2,231) | $[86.20\% - 88.93\%]$ |
| **Contradiction Recall at $\theta = 0.16$** | **48.85%** (149 / 305) | $[43.29\% - 54.44\%]$ |
| **Contradiction F1 at $\theta = 0.16$** | **0.4082** | — |

### Final Audit Verdict: **`PASS_WITH_LIMITATIONS`**

**Justification:**
- ✅ **Valid Independent Benchmark:** Acquired and formatted $N = 2,536$ records from the independent held-out RAGTruth test set with zero training or validation document overlap.
- ✅ **Defensible Ground Truth:** Ground truth is established by human annotators at the character span level with published inter-annotator agreement (Fleiss' Kappa $> 0.65$), completely rejecting unverified automated pseudo-labeling.
- ✅ **Deterministic Frozen Inference:** Evaluated the exact checkpoint weights in 867.12 seconds on CPU with no weight or optimizer modifications.
- ✅ **Bit-Level Reproducibility:** Standalone script [`independent_reproduction.py`](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/phase11_2_step06_clean_benchmark/independent_reproduction.py) reproduced every metric and confusion count.
- ⚠️ **Limitations:** Out-of-domain open-web search corpora (MS MARCO, Natural Questions) could not be utilized because they lack sentence-level NLI entailment ground truth (relevance $\neq$ entailment). The benchmark represents independent held-out test documents from the same underlying generation tasks (News, Bio, QA) rather than open-web search.

---

## 2. Dataset Discovery, Provenance & Licensing

An exhaustive audit of public datasets and local repository resources was conducted:

| Candidate Benchmark | Local Path | License | Usable Volume | Ground-Truth Supervision Status | Audit Decision |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **Natural Questions** | `data/raw/natural_questions` | CC BY-SA 3.0 | 0 | Unavailable locally (lock file only); external downloads prohibited. | **REJECTED (UNAVAILABLE)** |
| **MS MARCO v1.1** | `data/raw/ms_marco/` | Microsoft Non-Commercial | 10,047 | Passage relevance only (`is_selected`). Relevance cannot be equated to formal sentence-level NLI entailment without human annotation. | **REJECTED FOR NLI SUPERVISION** |
| **HotpotQA** | `data/raw/hotpotqa/` | CC BY-SA 4.0 | 7,405 | Multi-hop QA supporting fact indices. Lacks NLI directional entailment labels. | **REJECTED FOR NLI SUPERVISION** |
| **HaluEval QA** | `data/processed/halueval/` | MIT | 3,000 | Conflates contradictory statements with unmentioned entity insertions. | **EXCLUDED (SUPERVISION DEFICIT)** |
| **Clean RAG Baseline** | `data/benchmarks/clean_rag/` | CC BY-SA 3.0 | 10 | Statistically inadequate ($N=10$ total across 3 splits). | **REJECTED (INSUFFICIENT SAMPLE)** |
| **RAGTruth Held-out Test Split** | `data/processed/ragtruth/test.jsonl` | MIT | **2,700** | Human character-span annotations categorizing factual statements, conflict, and baseless unmentioned info. | **ACCEPTED AS PRIMARY BENCHMARK** |

Full discovery analysis and failure mode documentation is detailed in [`dataset_inventory.md`](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/phase11_2_step06_clean_benchmark/dataset_inventory.md).

---

## 3. Annotation Quality Gate & Ground-Truth Derivation

### 3.1 Derivation Protocol
To prevent label manufacturing or heuristic degradation:
1. **`ENTAILMENT` ($N = 1,757$):** Responses labeled as `FACTUAL` by human raters. Zero hallucination spans exist; every proposition is confirmed by the source passage.
2. **`NEUTRAL` ($N = 474$):** Responses labeled as `HALLUCINATED` where human raters marked **only** `Baseless Info` spans (no conflict). The response introduces unmentioned facts without contradicting source statements.
3. **`CONTRADICTION` ($N = 305$):** Responses labeled as `HALLUCINATED` where human raters marked **only** `Conflict` spans (no baseless info). The response directly refutes source statements.
4. **Quarantine ($N = 164$):** Responses containing both conflict and baseless spans simultaneously were excluded to preserve 3-way semantic cleanliness.

### 3.2 Quality Gate Sign-Off
- Provenance: Human annotator pool with Fleiss' Kappa inter-annotator agreement $> 0.65$.
- Formal Protocol Documentation: [`annotation_protocol.md`](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/phase11_2_step06_clean_benchmark/annotation_protocol.md).
- Quality Gate Status: **PASSED (0 manufactured or heuristic labels)**.

---

## 4. Benchmark Integrity & Contamination Verification

Integrity verification was conducted prior to model inference:
- **Total Valid Pairs:** 2,536 (Clean Evidence: 2,231 | Contradiction Controls: 305).
- **Exact Duplicate Pairs:** 0 duplicates detected.
- **Source Document Isolation:**
  - Training Set Overlap (`sft_v2/nli/train.jsonl`): **0 documents / 450 unique test documents (0.00%)**.
  - Validation Set Overlap (`sft_v2/nli/validation.jsonl`): **0 documents / 450 unique test documents (0.00%)**.
- **Dataset Manifest:** Saved and hashed at [`dataset_manifest.json`](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/phase11_2_step06_clean_benchmark/dataset_manifest.json).

---

## 5. Frozen Model Inference Telemetry

Inference was executed using the frozen FP32 model checkpoint:

| Parameter | Recorded Value |
| :--- | :--- |
| **Model Checkpoint** | `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` |
| **Model Weights SHA-256** | `0464758a2cd31260b44af96093dd52c2824a8305278d136ec438c87ee2b92313` |
| **Execution Hardware** | Intel(R) Xeon(R) CPU @ 2.20GHz (Host Linux Sandbox) |
| **PyTorch Version** | `2.14.1+cpu` |
| **Inference Mode** | Deterministic `torch.no_grad()`, `model.eval()`, zero optimizer updates |
| **Tokenization Strategy** | `evidence_preserving_tokenize` (max length: 384, min premise: 64) |
| **Total Inference Samples** | 2,536 samples |
| **Total Wall-Clock Time** | 867.12 seconds (~14.45 minutes) |
| **Throughput** | 2.92 samples/second |
| **Inference Failures / Crashes** | 0 failures (100.0% completion rate) |
| **Output Prediction Artifact** | [`predictions_clean_benchmark.jsonl`](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/phase11_2_step06_clean_benchmark/predictions_clean_benchmark.jsonl) |
| **Predictions SHA-256** | `6c2a998e9a806baf47e93a3197aef481597cf72b6cffd584f25165bc81e80dc5` |

---

## 6. Complete Threshold Operating-Point Evaluation

Both uncalibrated ($T = 1.0$) and temperature-calibrated ($T = 1.770106$) probabilities were evaluated across the mandatory candidate thresholds:

### 6.1 Uncalibrated Probability Distribution ($T = 1.0$)

| Threshold ($\theta$) | Pred+ | TP | FP (ENT / NEU) | FN | TN | Precision | Recall (95% CI) | F1 Score | FPR | Clean Evidence Rejection Rate | Clean Evidence Preservation Rate |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.16 (Max F1)** | 425 | 149 | 276 (118 / 158) | 156 | 1,955 | 35.06% | **48.85%** $[43.29-54.44\%]$ | **0.4082** | 12.37% | **12.37%** $[11.07-13.80\%]$ | **87.63%** $[86.20-88.93\%]$ |
| **0.20** | 186 | 87 | 99 (43 / 56) | 218 | 2,132 | 46.77% | **28.52%** $[23.75-33.83\%]$ | **0.3544** | 4.44% | **4.44%** $[3.66-5.37\%]$ | **95.56%** $[94.63-96.34\%]$ |
| **0.24** | 138 | 79 | 59 (23 / 36) | 226 | 2,172 | 57.25% | **25.90%** $[21.31-31.10\%]$ | **0.3567** | 2.64% | **2.64%** $[2.06-3.40\%]$ | **97.36%** $[96.60-97.94\%]$ |
| **0.25** | 136 | 78 | 58 (22 / 36) | 227 | 2,173 | 57.35% | **25.57%** $[21.00-30.75\%]$ | **0.3537** | 2.60% | **2.60%** $[2.02-3.35\%]$ | **97.40%** $[96.65-97.98\%]$ |
| **0.50 (Majority)** | 123 | 72 | 51 (19 / 32) | 233 | 2,180 | 58.54% | **23.61%** $[19.18-28.67\%]$ | **0.3364** | 2.29% | **2.29%** $[1.74-2.99\%]$ | **97.71%** $[97.01-98.26\%]$ |

---

### 6.2 Temperature-Calibrated Probability Distribution ($T^* = 1.770106$)

| Threshold ($\theta$) | Pred+ | TP | FP (ENT / NEU) | FN | TN | Precision | Recall (95% CI) | F1 Score | FPR | Clean Evidence Rejection Rate | Clean Evidence Preservation Rate |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.16** | 1,051 | 232 | 819 (497 / 322) | 73 | 1,412 | 22.07% | **76.07%** $[70.99-80.50\%]$ | 0.3422 | 36.71% | **36.71%** $[34.73-38.73\%]$ | **63.29%** $[61.27-65.27\%]$ |
| **0.20** | 678 | 200 | 478 (235 / 243) | 105 | 1,753 | 29.50% | **65.57%** $[60.08-70.68\%]$ | 0.4069 | 21.43% | **21.43%** $[19.77-23.18\%]$ | **78.57%** $[76.82-80.23\%]$ |
| **0.24 (Cal Peak)** | 399 | 150 | 249 (96 / 153) | 155 | 1,982 | 37.59% | **49.18%** $[43.61-54.77\%]$ | **0.4261** | 11.16% | **11.16%** $[9.92-12.53\%]$ | **88.84%** $[87.47-90.08\%]$ |
| **0.25** | 332 | 132 | 200 (76 / 124) | 173 | 2,031 | 39.76% | **43.28%** $[37.84-48.89\%]$ | **0.4144** | 8.96% | **8.96%** $[7.85-10.22\%]$ | **91.04%** $[89.78-92.15\%]$ |
| **0.50 (Majority)** | 117 | 70 | 47 (17 / 30) | 235 | 2,184 | 59.83% | **22.95%** $[18.59-27.99\%]$ | **0.3318** | 2.11% | **2.11%** $[1.59-2.79\%]$ | **97.89%** $[97.21-98.41\%]$ |

---

## 7. Clean Evidence False Rejection & Preservation Dynamics

### 7.1 Class-Decomposed False Alarm Rates (Uncalibrated)

| Threshold ($\theta$) | Overall Clean FCR | Entailment FAR ($N=1,757$) | 95% CI (Entailment) | Neutral FAR ($N=474$) | 95% CI (Neutral) | Neutral Proportion of FPs |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.16** | **12.37%** | **6.72%** (118) | $[5.64\% - 7.98\%]$ | **33.33%** (158) | $[29.24\% - 37.70\%]$ | **57.25%** |
| **0.20** | **4.44%** | **2.45%** (43) | $[1.82\% - 3.28\%]$ | **11.81%** (56) | $[9.21\% - 15.03\%]$ | **56.57%** |
| **0.24** | **2.64%** | **1.31%** (23) | $[0.87\% - 1.96\%]$ | **7.59%** (36) | $[5.54\% - 10.34\%]$ | **61.02%** |
| **0.25** | **2.60%** | **1.25%** (22) | $[0.83\% - 1.89\%]$ | **7.59%** (36) | $[5.54\% - 10.34\%]$ | **62.07%** |
| **0.50** | **2.29%** | **1.08%** (19) | $[0.69\% - 1.68\%]$ | **6.75%** (32) | $[4.80\% - 9.42\%]$ | **62.75%** |

### 7.2 Key Behavioral Insights
1. **Severe Neutral Sensitivity:** Exactly **$33.33\%$ (1 in 3)** of completely non-contradictory Neutral evidence is falsely flagged as contradiction at the Max-F1 threshold ($\theta = 0.16$). Even at $\theta = 0.20$, more than $1$ in $9$ neutral passages is discarded.
2. **Entailment Robustness:** Factual entailed evidence is substantially better preserved, maintaining a $93.28\%$ survival rate at $\theta = 0.16$ and $> 97.5\%$ at $\theta \ge 0.20$.
3. **Compound Rejection in RAG:** In a 5-passage RAG retrieval context with uncalibrated $\theta = 0.16$, the probability of false rejection across 5 passages is:
   $$P(\ge 1 \text{ rejection}) = 1 - (1 - 0.1237)^5 = \mathbf{48.69\%}$$
   Almost exactly half of all multi-passage queries lose valid evidence.

---

## 8. Comparison with Phase 11.1 Step 05 Internal Validation Proxy

A critical question of Step 06 was: **Do the internal Step 05 validation findings generalize to an independent test set?**

| Metric Dimension | Phase 11.1 Step 05 (Internal Val Proxy, $N=2,662$) | Phase 11.2 Step 06 (Independent Test Bench, $N=2,536$) | Absolute Delta | Generalization Status |
| :--- | :---: | :---: | :---: | :---: |
| **Clean FCR at $\theta = 0.16$** | 11.93% | **12.37%** | +0.44 pp | **CONFIRMED GENERALIZED** |
| **Entailment FAR at $\theta = 0.16$** | 6.38% | **6.72%** | +0.34 pp | **CONFIRMED GENERALIZED** |
| **Neutral FAR at $\theta = 0.16$** | 26.24% | **33.33%** | +7.09 pp | **ELEVATED ON TEST SET** |
| **Contradiction Recall at $\theta = 0.16$** | 46.63% | **48.85%** | +2.22 pp | **CONFIRMED GENERALIZED** |
| **Contradiction F1 at $\theta = 0.16$** | 0.4166 | **0.4082** | -0.0084 | **STABLE WITHIN 0.01** |
| **Clean FCR at $\theta = 0.20$** | 4.68% | **4.44%** | -0.24 pp | **CONFIRMED GENERALIZED** |
| **Clean FCR at $\theta = 0.50$** | 2.12% | **2.29%** | +0.17 pp | **CONFIRMED GENERALIZED** |
| **Contradiction Recall at $\theta = 0.50$** | 25.00% | **23.61%** | -1.39 pp | **CONFIRMED GENERALIZED** |

### Significance of the Comparison
The comparison confirms that the findings of Step 05 were **not an artifact of validation overfitting**:
1. The ~12% clean false rejection penalty at $\theta = 0.16$ reproduces almost identically on independent test documents ($11.93\% \to 12.37\%$).
2. The neutral false alarm vulnerability is even more pronounced on unseen test documents ($26.24\% \to 33.33\%$), confirming that DeBERTa-v3-small inherently struggles with the Neutral/Contradiction decision boundary.
3. The baseline majority threshold ($\theta = 0.50$) reliably preserves $\sim 97.7\%$ of clean evidence, but leaves over $76\%$ of true contradictions undetected.

---

## 9. Independent Reproducibility & Bit-Level Audit

To guarantee complete audit transparency:
- Standalone verification script: [`independent_reproduction.py`](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/phase11_2_step06_clean_benchmark/independent_reproduction.py).
- Execution verified 100% metric congruence between raw predictions and serialized JSON output.
- SHA-256 manifests generated and recorded in [`sha256_manifest.txt`](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/phase11_2_step06_clean_benchmark/sha256_manifest.txt).

---

## 10. Limitations & Statistical Uncertainty

1. **Domain Overlap:** While the test set features completely disjoint source documents, it originates from the same RAGTruth distribution (summarization, QA, bio-medical tasks). Generalization to colloquial enterprise chat or domain-specific code retrieval remains unverified.
2. **Missing Open-Domain Web Corpora:** MS MARCO and Natural Questions could not be integrated due to the absence of human NLI entailment annotations. Relevance-based heuristics were rejected to protect ground-truth integrity.
3. **Wilson Score Uncertainty:** For small classes like Neutral ($N=474$), 95% confidence intervals span $\pm 4.2\%$, indicating that production false-alarm rates could realistically range between $29\%$ and $38\%$ at $\theta = 0.16$.

---

## 11. Recommended Next Experiments

1. **Step 07 — Multi-Passage Downstream RAG Generation Audit:** Connect the frozen NLI guardrail to a live RAG pipeline (e.g. Llama-3-8B generator) and measure downstream QA exact match, ROUGE-L, and hallucination rate at $\theta = 0.50$ vs $\theta = 0.24$ vs $\theta = 0.16$.
2. **Dedicated Neutral-Boundary Remediation:** Implement a two-stage verifier where low-scoring contradiction predictions ($\theta \in [0.10, 0.30]$) pass through a specialized Neutral-vs-Contradiction re-ranker.
3. **Human Annotation Campaign on MS MARCO:** Commission a formal human annotation study on 1,000 MS MARCO query-passage pairs to evaluate out-of-domain open-web retrieval transfer.

---

## 12. Sign-Off & Integrity Seal

### Audit Verdict: **`PASS_WITH_LIMITATIONS`**

- **Benchmark Validity:** Confirmed independent, human-verified, and document-disjoint ($N=2,536$).
- **Frozen Model Inference:** Successfully executed and bit-level verified.
- **Scientific Integrity:** Maintained zero pseudo-labeling, zero heuristic fabrication, and strict read-only model access.

**Auditor:** Senior ML Evaluation Engineer & Independent Research Auditor  
**Date:** 2026-11-18  
**Directory:** `reports/research_completion/phase11_2_step06_clean_benchmark/`

