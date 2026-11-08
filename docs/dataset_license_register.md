# TrustRAG — Dataset License Evidence Register

> **Document Version:** 1.1.0  
> **Phase:** Phase 01 & Phase 02 (Dataset Engineering & Benchmark Construction)  
> **Audit Date:** 2026-11-08  
> **Auditor:** TrustRAG Data Integrity Review  

---

## 1. Executive Summary & Licensing Governance

This register documents the verified legal status, repository origins, underlying content licenses, commercial-use constraints, and training/evaluation permissions for all **13 supported datasets** in TrustRAG.

### Mandatory Compliance Rules
1. **Evaluation-Only Isolation:** Datasets whose terms prohibit model training or fine-tuning (e.g. `LLM-AggreFact`, `RSB`) are strictly barred from entering training pipelines.
2. **Corpus vs Benchmark Isolation:** Pre-training corpora (`FineWeb`) are strictly barred from being evaluated as benchmark tasks.
3. **Third-Party Data Distinctions:** For every dataset, repository licenses are distinguished from underlying content licenses (e.g. Wikipedia CC-BY-SA, Common Crawl web crawl terms).
4. **Unverified Sources:** Sources without public direct download URLs (`RSB`) are explicitly designated as **NOT VERIFIED** and operate via local-import interfaces only.

---

## 2. Dataset License Register (All 13 Datasets)

| # | Dataset Name | Category | Official Source / Repository | Repository License | Underlying Content License | Access Restrictions | Attribution Required | Commercial Use Permitted | Permitted for Training | Permitted for Evaluation | Verification Status |
|:---:|---|---|---|---|---|---|:---:|:---:|:---:|:---:|:---:|
| 1 | **Natural Questions** | RAG / QA | `google-research-datasets/natural_questions` | CC-BY-SA-3.0 | CC-BY-SA-3.0 (Wikipedia) | Open | Yes (Kwiatkowski 2019) | Yes (ShareAlike) | **YES** | **YES** | **VERIFIED** |
| 2 | **HotpotQA** | RAG / QA | `hotpotqa/hotpot_qa` | CC-BY-SA-4.0 | CC-BY-SA-4.0 (Wikipedia) | Open | Yes (Yang 2018) | Yes (ShareAlike) | **YES** | **YES** | **VERIFIED** |
| 3 | **MS MARCO** | RAG / QA | `microsoft/ms_marco` | MSR-LA | Third-party web search | Research Only | Yes (Nguyen 2016) | **NO** (Research Only) | **YES** (Research) | **YES** | **VERIFIED** |
| 4 | **SQuAD** | RAG / QA | `rajpurkar/squad` | CC-BY-SA-4.0 | CC-BY-SA-3.0 (Wikipedia) | Open | Yes (Rajpurkar 2016) | Yes (ShareAlike) | **YES** | **YES** | **VERIFIED** |
| 5 | **BoolQ** | RAG / QA | `google/boolq` | CC-BY-SA-3.0 | CC-BY-SA-3.0 (Wikipedia) | Open | Yes (Clark 2019) | Yes (ShareAlike) | **YES** | **YES** | **VERIFIED** |
| 6 | **HaluEval** | Hallucination | `pminervini/HaluEval` | MIT | Synthetic (OpenAI Terms) | Open | Yes (Wang 2023) | Yes (MIT) | **YES** | **YES** | **VERIFIED** |
| 7 | **RAGTruth** | Hallucination | `ParticleMedia/RAGTruth` | MIT | Mixed (MS MARCO/CNN/PubMed) | Local Import | Yes (Niu 2024) | Mixed (PubMed=Yes, MS MARCO=No) | **YES** (Research) | **YES** | **VERIFIED** |
| 8 | **LLM-AggreFact** | Hallucination | `lytang/LLM-AggreFact` | CC-BY-ND-4.0 | Aggregated Benchmark Data | Gated HF | Yes (Tang 2024) | **NO** (NoDerivs / Terms) | **NO (BLOCKED)** | **YES** | **VERIFIED** |
| 9 | **WiCE** | Hallucination | `ryokamoi/wice` | CC-BY-SA-4.0 | ODC-By-1.0 / CC-BY-SA | Local Import / HF | Yes (Kamoi 2023) | Yes (ShareAlike) | **YES** | **YES** | **VERIFIED** |
| 10 | **ExpertQA** | Hallucination | `chaitanyamalaviya/ExpertQA` | MIT | Web / Expert Citations | Local Import | Yes (Malaviya 2023) | Yes (MIT) | **YES** | **YES** | **VERIFIED** |
| 11 | **RSB** | Security | `arXiv:2505.18543` | Pending / Unverified | Unknown / Attack text | Pending / Local | Yes (Preprint) | Unknown | **NO (BLOCKED)** | **YES** | **NOT VERIFIED** |
| 12 | **Custom Security** | Security | `trustrag/internal_security` | MIT | TrustRAG Internal Synthetic | Local | Yes (TrustRAG) | Yes | **YES** | **YES** | **VERIFIED** |
| 13 | **FineWeb** | Corpus | `HuggingFaceFW/fineweb` | ODC-By-1.0 | Common Crawl (Web Terms) | Open | Yes (Penedo 2024) | Yes (Attribution) | **YES** | **NO (BLOCKED)** | **VERIFIED** |

---

## 3. Comprehensive Dataset Profiles

### 1. Natural Questions (NQ)
- **Official Name:** Google Natural Questions
- **Official Source:** Google Research
- **Repository URL:** `https://huggingface.co/datasets/google-research-datasets/natural_questions`
- **License Identifier:** CC-BY-SA-3.0
- **License Evidence Location:** Hugging Face dataset card & Google Research repository documentation.
- **Access Restrictions:** Openly accessible via Hugging Face and Google Cloud buckets.
- **Attribution Requirements:** Must cite Kwiatkowski et al. (2019): *"Natural Questions: a Benchmark for Question Answering Research"*, TACL.
- **Commercial-Use Restrictions:** Permitted under CC-BY-SA-3.0 with reciprocal ShareAlike licensing for derivative works.
- **Training Permissions:** Permitted for model pretraining, fine-tuning, and retrieval indexing.
- **Evaluation Permissions:** Permitted for standard QA evaluation.
- **Verification Status:** **VERIFIED**.
- **Outstanding Uncertainties:** Passages derive from full Wikipedia HTML articles; individual article content retains Wikimedia CC-BY-SA terms.

---

### 2. HotpotQA
- **Official Name:** HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering
- **Official Source:** Yang et al., Carnegie Mellon University, Stanford University, Université de Montréal
- **Repository URL:** `https://huggingface.co/datasets/hotpotqa/hotpot_qa` (Homepage: `https://hotpotqa.github.io/`)
- **License Identifier:** CC-BY-SA-4.0
- **License Evidence Location:** HotpotQA official repository and website header.
- **Access Restrictions:** Open access.
- **Attribution Requirements:** Must cite Yang et al. (2018), EMNLP.
- **Commercial-Use Restrictions:** Permitted under Creative Commons Attribution-ShareAlike 4.0 International.
- **Training Permissions:** Permitted.
- **Evaluation Permissions:** Permitted.
- **Verification Status:** **VERIFIED**.
- **Outstanding Uncertainties:** None.

---

### 3. MS MARCO
- **Official Name:** Microsoft MAchine Reading COmprehension Dataset
- **Official Source:** Microsoft AI & Research
- **Repository URL:** `https://huggingface.co/datasets/microsoft/ms_marco` (Homepage: `https://microsoft.github.io/msmarco/`)
- **License Identifier:** Microsoft Research License Agreement (MSR-LA) / Academic Non-Commercial
- **License Evidence Location:** `https://microsoft.github.io/msmarco/` Terms of Use.
- **Access Restrictions:** Open for academic and research purposes upon acceptance of Microsoft Terms of Use.
- **Attribution Requirements:** Must cite Nguyen et al. (2016): *"MS MARCO: A Human Generated MAchine Reading COmprehension Dataset"*.
- **Commercial-Use Restrictions:** **Commercial use is prohibited.** Allowed for non-commercial research and academic evaluation only.
- **Training Permissions:** Permitted for research model training and indexing.
- **Evaluation Permissions:** Permitted for research evaluation.
- **Verification Status:** **VERIFIED**.
- **Outstanding Uncertainties:** Passage contents are harvested from Bing search queries and snippets; Microsoft disclaims ownership of third-party web content.

---

### 4. SQuAD (v1.1 & v2.0)
- **Official Name:** Stanford Question Answering Dataset
- **Official Source:** Stanford NLP Group (Rajpurkar et al.)
- **Repository URL:** `https://huggingface.co/datasets/rajpurkar/squad`
- **License Identifier:** CC-BY-SA-4.0
- **License Evidence Location:** Official website (`https://rajpurkar.github.io/SQuAD-explorer/`) and dataset repository.
- **Access Restrictions:** Open access.
- **Attribution Requirements:** Must cite Rajpurkar et al. (2016) and (2018).
- **Commercial-Use Restrictions:** Permitted with attribution and ShareAlike.
- **Training Permissions:** Permitted.
- **Evaluation Permissions:** Permitted.
- **Verification Status:** **VERIFIED**.
- **Outstanding Uncertainties:** Context passages originate from English Wikipedia articles.

---

### 5. BoolQ
- **Official Name:** BoolQ: Exploring the Surprising Difficulty of Natural Yes/No Questions
- **Official Source:** Google Research / Christopher Clark et al.
- **Repository URL:** `https://huggingface.co/datasets/google/boolq`
- **License Identifier:** CC-BY-SA-3.0
- **License Evidence Location:** GitHub repository `google-research-datasets/boolean-questions` LICENSE and HF Dataset Card.
- **Access Restrictions:** Open access.
- **Attribution Requirements:** Must cite Clark et al. (2019), NAACL.
- **Commercial-Use Restrictions:** Permitted with attribution and ShareAlike.
- **Training Permissions:** Permitted.
- **Evaluation Permissions:** Permitted.
- **Verification Status:** **VERIFIED**.
- **Outstanding Uncertainties:** None.

---

### 6. HaluEval
- **Official Name:** HaluEval: A Large-Scale Hallucination Evaluation Benchmark for LLMs
- **Official Source:** Ren et al., Renmin University & Tsinghua University
- **Repository URL:** `https://huggingface.co/datasets/pminervini/HaluEval` (GitHub: `RUCAIBox/HaluEval`)
- **License Identifier:** MIT License
- **License Evidence Location:** `RUCAIBox/HaluEval/LICENSE` on GitHub.
- **Access Restrictions:** Open access.
- **Attribution Requirements:** Cite Wang et al. (2023), EMNLP.
- **Commercial-Use Restrictions:** Permitted under MIT.
- **Training Permissions:** Permitted.
- **Evaluation Permissions:** Permitted.
- **Verification Status:** **VERIFIED**.
- **Outstanding Uncertainties:** Synthetic hallucinations were generated by prompting OpenAI models (GPT-3.5-Turbo); downstream users must comply with OpenAI Terms of Use regarding synthetic output.

---

### 7. RAGTruth
- **Official Name:** RAGTruth: A Hallucination Benchmark for Retrieval-Augmented Generation
- **Official Source:** Particle Media / NewsBreak (Yuan et al.)
- **Repository URL:** `https://github.com/ParticleMedia/RAGTruth`
- **License Identifier:** MIT License (Repository codebase and word-level hallucination labels)
- **License Evidence Location:** GitHub repository `ParticleMedia/RAGTruth/LICENSE`.
- **Access Restrictions:** Open repository code and data release files (requires local file clone/import).
- **Attribution Requirements:** Cite Niu et al. (ACL 2024).
- **Commercial-Use Restrictions:** MIT license covers annotations, but constituent sub-corpora (MS MARCO, CNN/DailyMail, PubMed) carry their respective content licenses.
- **Training Permissions:** Permitted for academic research.
- **Evaluation Permissions:** Permitted.
- **Verification Status:** **VERIFIED** (Operates via documented local-import adapter).
- **Outstanding Uncertainties:** Derivative training must respect the non-commercial boundary of the MS MARCO subset.

---

### 8. LLM-AggreFact
- **Official Name:** LLM-AggreFact: Benchmark for Aggregated Factual Error Detection
- **Official Source:** Liyan Tang et al., University of Texas at Austin
- **Repository URL:** `https://huggingface.co/datasets/lytang/LLM-AggreFact`
- **License Identifier:** Creative Commons Attribution-NoDerivatives 4.0 International (CC-BY-ND-4.0)
- **License Evidence Location:** Hugging Face dataset card `lytang/LLM-AggreFact`.
- **Access Restrictions:** Gated on Hugging Face (requires user authentication token and agreement to terms).
- **Attribution Requirements:** Must cite Tang et al. (2024).
- **Commercial-Use Restrictions:** CC-BY-ND prohibits distribution of derivative works.
- **Training Permissions:** **STRICTLY PROHIBITED.** Dataset terms explicitly state that records must not be used to train, pretrain, or fine-tune models.
- **Evaluation Permissions:** **PERMITTED (EVALUATION ONLY).** Enforced in TrustRAG via `DatasetUsageValidator`.
- **Verification Status:** **VERIFIED**.
- **Outstanding Uncertainties:** Gated download requires user Hugging Face token; hermetic testing relies on mock adapter or local import.

---

### 9. WiCE
- **Official Name:** WiCE: Real-World Entailment for Claim Verification with Wikipedia Text
- **Official Source:** Ryo Kamoi et al., University of Tokyo & Google Research
- **Repository URL:** `https://github.com/ryokamoi/wice` (HF: `ryokamoi/wice`)
- **License Identifier:** CC-BY-SA-4.0 (Annotations) / ODC-By-1.0 (Wikipedia citation data)
- **License Evidence Location:** GitHub repository README and LICENSE file.
- **Access Restrictions:** Open access.
- **Attribution Requirements:** Cite Kamoi et al. (2023), EMNLP.
- **Commercial-Use Restrictions:** Permitted with attribution and ShareAlike.
- **Training Permissions:** Permitted.
- **Evaluation Permissions:** Permitted.
- **Verification Status:** **VERIFIED** (Operates via documented local-import adapter).
- **Outstanding Uncertainties:** Citation texts cite third-party web domains linked from Wikipedia.

---

### 10. ExpertQA
- **Official Name:** ExpertQA: Evaluating Explainable and Attributed QA with Domain Experts
- **Official Source:** Chaitanya Malaviya et al., Stanford University
- **Repository URL:** `https://github.com/chaitanyamalaviya/ExpertQA`
- **License Identifier:** MIT License
- **License Evidence Location:** GitHub repository `chaitanyamalaviya/ExpertQA/LICENSE`.
- **Access Restrictions:** Open access via GitHub release JSON files.
- **Attribution Requirements:** Cite Malaviya et al. (2023), EMNLP.
- **Commercial-Use Restrictions:** Permitted under MIT.
- **Training Permissions:** Permitted.
- **Evaluation Permissions:** Permitted.
- **Verification Status:** **VERIFIED** (Operates via documented local-import adapter).
- **Outstanding Uncertainties:** Expert attributions quote external web URLs.

---

### 11. RSB (RAG Security Bench)
- **Official Name:** RAG Security Bench (Poisoning and Retrieval Manipulation Benchmark)
- **Official Source:** Academic security research paper referenced in TrustRAG design (arXiv:2505.18543)
- **Repository URL:** `arXiv:2505.18543` (Preprint reference only; no public Hugging Face or GitHub URL exists)
- **License Identifier:** **NOT VERIFIED** / Pending Public Release
- **License Evidence Location:** Academic paper citation only.
- **Access Restrictions:** **Pending.** No public download URL is available. TrustRAG provides a documented local-import schema adapter.
- **Attribution Requirements:** Cite corresponding academic preprint upon release.
- **Commercial-Use Restrictions:** **UNKNOWN / PENDING.**
- **Training Permissions:** **STRICTLY PROHIBITED.** Barred from training workflows to preserve benchmark security evaluation integrity.
- **Evaluation Permissions:** Permitted as an attack and defense evaluation benchmark (`SECURITY_BENCHMARK`).
- **Verification Status:** **NOT VERIFIED (PENDING PUBLIC ACCESS).**
- **Outstanding Uncertainties:** Public availability, repository host, and formal license text are unconfirmed.

---

### 12. Custom Security Dataset
- **Official Name:** TrustRAG Internal Security & Poisoning Benchmark
- **Official Source:** TrustRAG Research Team
- **Repository URL:** `internal://trustrag/security`
- **License Identifier:** MIT License (Project Root)
- **License Evidence Location:** `LICENSE` at repository root.
- **Access Restrictions:** Internal to TrustRAG development.
- **Attribution Requirements:** TrustRAG project attribution.
- **Commercial-Use Restrictions:** Permitted under project MIT license.
- **Training Permissions:** Permitted for defense training and poisoned-context detection.
- **Evaluation Permissions:** Permitted for security benchmark evaluation.
- **Verification Status:** **VERIFIED**.
- **Outstanding Uncertainties:** None.

---

### 13. FineWeb
- **Official Name:** FineWeb: High-Quality Open Web Dataset for Pretraining
- **Official Source:** Hugging Face (HuggingFaceFW)
- **Repository URL:** `https://huggingface.co/datasets/HuggingFaceFW/fineweb`
- **License Identifier:** Open Data Commons Attribution License (ODC-By v1.0)
- **License Evidence Location:** Hugging Face dataset card `HuggingFaceFW/fineweb`.
- **Access Restrictions:** Open access (streamable Parquet partitions).
- **Attribution Requirements:** Must cite Penedo et al. (2024): *"The FineWeb Datasets: Decanting the Web for the Finest Text Data"*.
- **Commercial-Use Restrictions:** ODC-By-1.0 permits commercial use with proper attribution.
- **Training Permissions:** **PERMITTED (TRAINING CORPUS ONLY).**
- **Evaluation Permissions:** **STRICTLY PROHIBITED.** Must not be evaluated as a benchmark task; isolated strictly to `TRAINING_CORPUS`.
- **Verification Status:** **VERIFIED**.
- **Outstanding Uncertainties:** Web texts originate from Common Crawl 2013-2024.

---

## 4. Summary of Enforced Isolation Controls

| Usage Category | Permitted Datasets | Blocked Datasets | Enforcing Class |
|---|---|---|---|
| `TRAINING` | `natural_questions`, `hotpotqa`, `ms_marco`, `squad`, `boolq`, `halueval`, `ragtruth`, `wice`, `expertqa`, `custom_security` | **`llm_aggrefact`** (License constraint), **`rsb`** (Eval benchmark integrity) | `DatasetUsageValidator` |
| `TRAINING_CORPUS` | `fineweb` | All QA/Hallucination/Security benchmarks | `DatasetUsageValidator` |
| `EVALUATION` | `natural_questions`, `hotpotqa`, `ms_marco`, `squad`, `boolq`, `halueval`, `ragtruth`, `llm_aggrefact`, `wice`, `expertqa`, `rsb`, `custom_security` | **`fineweb`** (Training corpus only) | `DatasetUsageValidator` |
| `SECURITY_BENCHMARK` | `rsb`, `custom_security` | **`fineweb`** and non-security datasets | `DatasetUsageValidator` |

---

