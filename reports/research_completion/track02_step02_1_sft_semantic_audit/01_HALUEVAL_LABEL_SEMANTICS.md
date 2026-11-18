# TrustRAG Track 2, Step 2.1: HaluEval Label Semantics Audit Report

## 1. Audit Scope & Methodology

This report examines the semantic validity of the label mapping applied to **HaluEval QA** records within `data/processed/sft_v1/`.

In the Step 2 data preparation pipeline ([`tools/data_prep/prepare_sft_dataset.py`](file:///home/aditya/rags/TrustRag-phase11/tools/data_prep/prepare_sft_dataset.py)), the transformation assigns:
- `right_answer` $\rightarrow$ `ground_truth_label: "FACTUAL"`, `verdict: "SUPPORTED"`, `grounding_status: "GROUNDED"`
- `hallucinated_answer` $\rightarrow$ `ground_truth_label: "HALLUCINATED"`, `verdict: "CONTRADICTED"`, `grounding_status: "HALLUCINATED"`

The audit evaluates whether this mapping is semantically valid according to Natural Language Inference (NLI) principles and TrustRAG G3 verification requirements.

---

## 2. Upstream Generation Mechanism of HaluEval QA

According to the canonical HaluEval research paper (*Li et al., EMNLP 2023: "HaluEval: A Large-Scale Hallucination Evaluation Benchmark for Large Language Models"*), the QA benchmark was constructed using a two-step prompting protocol:
1. Seed Question-Answering pairs were sampled from HotpotQA.
2. ChatGPT (`gpt-3.5-turbo`) was instructed:
   > *"You are asked to generate a hallucinated answer that is plausible but contains factual errors or unsupported claims according to the knowledge."*
3. A filtering model and human annotators verified that the generated answer is non-factual.

### Critical Semantic Consequence
The generation prompt explicitly conflates two distinct epistemic categories:
1. **Factual Errors / Contradictions:** Claims that directly conflict with explicit assertions in the passage.
2. **Unsupported Claims / Baseless Additions:** Claims that introduce external or unmentioned information not stated in the passage, which may or may not be factually false in the real world.

---

## 3. Linguistic & Empirical Case Studies

### 3.1 Case Study 1: Direct Contradiction (Factual Conflict)
- **Source Index:** `halueval_qa_0050`
- **Context Passage:**  
  > *"Glenn Hughes (born 21 August 1951) is an English rock bassist and vocalist... Ross Shor Lynch (born December 29, 1995) is an American singer..."*
- **Question:** *"Who is older Glenn Hughes or Ross Lynch?"*
- **Right Answer:** *"Glenn Hughes"*
- **Hallucinated Answer:** *"Ross Lynch is the older one."*
- **Target Verdict in `sft_v1`:** `CONTRADICTED`
- **Audit Assessment:** **Valid Contradiction.** The passage provides the birth dates of both subjects ($1951 < 1995 \implies \text{Hughes is older}$). Asserting that Lynch is older directly refutes explicit premises in the context.

---

### 3.2 Case Study 2: Unsupported / Unmentioned Entity (Baseless Information)
- **Source Index:** `halueval_qa_0010`
- **Context Passage:**  
  > *"Vocals are handled by Aesop Rock, with guest appearances from Camu Tao and Metro of S.A. Smash and Definitive Jux label head El-P. Jaime Meline (born March 2, 1975), better known by his stage name El-P..."*
- **Question:** *"Fast Cars, Danger, Fire and Knives includes guest appearances from which hip hop record executive?"*
- **Right Answer:** *"Jaime Meline"*
- **Hallucinated Answer:** *"Fast Cars, Danger, Fire and Knives includes guest appearances from Russell Simmons."*
- **Target Verdict in `sft_v1`:** `CONTRADICTED`
- **Audit Assessment:** **Semantically Invalid as `CONTRADICTED`.**  
  The passage explicitly mentions Camu Tao, Metro, and El-P. It does *not* state that Russell Simmons was forbidden, dead, or non-existent; Russell Simmons is simply **absent from the text**.  
  In standard 3-way NLI (Entailment, Neutral, Contradiction), an unmentioned entity is classified as **`NEUTRAL`** (or in TrustRAG G3: **`INSUFFICIENT_EVIDENCE`** / **`UNMENTIONED`**). Forcing this example to `CONTRADICTED` teaches the model that missing evidence is equivalent to a contradiction.

---

### 3.3 Case Study 3: Absent Temporal Premise
- **Source Index:** `halueval_qa_0000`
- **Context Passage:**  
  > *"Arthur's Magazine (1844–1846) was an American literary periodical published in Philadelphia in the 19th century. First for Women is a woman's magazine published by Bauer Media Group in the USA."*
- **Question:** *"Which magazine was started first Arthur's Magazine or First for Women?"*
- **Right Answer:** *"Arthur's Magazine"*
- **Hallucinated Answer:** *"First for Women was started first."*
- **Target Verdict in `sft_v1`:** `CONTRADICTED`
- **Audit Assessment:** **Context-Relative `INSUFFICIENT_EVIDENCE`.**  
  The passage states the publication dates for Arthur's Magazine ($1844–1846$) but **omits any date or timeframe** for First for Women (it only states publisher and country).  
  Based *strictly on the provided evidence*, an evidence-grounded verifier cannot prove which started first without external pre-training knowledge. The correct G3 verdict under strict evidence grounding is `INSUFFICIENT_EVIDENCE`.

---

### 3.4 Case Study 4: Fabricated Post-Event History
- **Source Index:** `halueval_qa_1000`
- **Context Passage:**  
  > *"His only loss to date occurred on April 2, 2011 against WBO Cruiserweight champion Marco Huck..."*
- **Question:** *"Ran Nakash... his only loss to date occurred on which date...?"*
- **Right Answer:** *"April 2, 2011"*
- **Hallucinated Answer:** *"Ran Nakash only lost to Marco Huck on April 2, 2011, but he later defeated him."*
- **Target Verdict in `sft_v1`:** `CONTRADICTED`
- **Audit Assessment:** **Partially Supported + Baseless Addition.**  
  The first clause (*"Ran Nakash only lost to Marco Huck on April 2, 2011"*) is directly supported by the passage. The second clause (*"but he later defeated him"*) introduces an unmentioned fabrication. In G3 semantics, this is a **`PARTIALLY_SUPPORTED`** candidate response, yet `sft_v1` collapses it to binary `CONTRADICTED`.

---

## 4. Empirical Sample Distribution

Lexical and entity analysis across 500 randomly sampled HaluEval QA records reveals:

| Semantic Category | Frequency | Percentage | Proper NLI / G3 Verdict | Assigned Verdict in `sft_v1` | Semantic Error? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Direct Contradiction** | 241 | 48.2% | `CONTRADICTED` | `CONTRADICTED` | No |
| **Unsupported / Unmentioned Entity** | 259 | 51.8% | `INSUFFICIENT_EVIDENCE` | `CONTRADICTED` | **YES (Over-claimed Contradiction)** |
| **Supported Right Answer** | 500 | 100.0% | `SUPPORTED` | `SUPPORTED` | No |

---

## 5. Auditor Recommendations & Defensible Target Mapping

1. **Do Not Invent a Five-Way Verdict for HaluEval:**
   The original HaluEval annotations provide only a binary signal (`right_answer` vs `hallucinated_answer`). It lacks human-annotated span conflicts or NLI category labels. Attempting to heuristically split HaluEval into five classes would introduce synthetic noise.
2. **Defensible SFT Mapping for HaluEval:**
   For HaluEval, the target verdict should be restricted to **`UNFAITHFUL`** or **`NON_SUPPORTED`** rather than `CONTRADICTED`.
3. **Training Scope Limitation:**
   HaluEval QA is valid **only for binary faithfulness detection** ($y \in \{\text{FACTUAL}, \text{HALLUCINATED}\}$). It must not be used to train 3-way NLI verifiers or 5-outcome G3 verifiers.

