# TrustRAG Track 2, Step 2.2.1: NLI Semantic Independent Audit Report

## 1. Audit Scope & Verification Mandate

This report independently verifies the semantic validity, label correctness, and exclusion accounting of the **Evidence-Grounded 3-Way NLI Dataset** in:
[`data/processed/sft_v2/nli/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/)

The audit examined:
1. Exact census across splits and label categories.
2. Semantic alignment of `ENTAILMENT`, `CONTRADICTION`, and `NEUTRAL` against source text and human annotator notes.
3. Verification of all 18,613 excluded entries against source records.

---

## 2. Independent Census & Distribution Verification

All records were decoded and verified directly from the JSONL files:

| Split | Total Records | ENTAILMENT | CONTRADICTION | NEUTRAL | Source Dataset | Document Hashes | Document Overlap |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Train Split** | **10,815** | 6,707 (62.02%) | 1,420 (13.13%) | 2,688 (24.85%) | RAGTruth only | 2,011 | **0.00%** |
| **Validation Split** | **2,662** | 1,662 (62.43%) | 356 (13.37%) | 644 (24.20%) | RAGTruth only | 503 | **0.00%** |
| **Total Combined** | **13,477** | **8,369 (62.10%)** | **1,776 (13.18%)** | **3,332 (24.72%)** | **RAGTruth only** | **2,514** | **0.00%** |

---

## 3. Semantic Category Audit & Case Studies

### 3.1 `CONTRADICTION` Audit (1,776 records)
- **Selection Criteria:** Every record must contain strictly `Evident Conflict` or `Subtle Conflict` spans, and **zero** baseless info spans.
- **Verification Result:** **100.00% Compliant.**
- *Audited Sample:*
  - *Premise:* Structured entity record with `rating: 3.5` and `review_count: 42`.
  - *Hypothesis:* *"Ultimate Bagels has a 4-star rating and over 100 reviews."*
  - *Annotator Annotation:* `Evident Conflict` on "4-star rating" and "over 100 reviews".
  - *Auditor Assessment:* **Valid Contradiction.** The premise explicitly specifies numeric values that refute the hypothesis.

### 3.2 `NEUTRAL` Audit (3,332 records)
- **Selection Criteria:** Every record must contain strictly `Evident Baseless Info` or `Subtle Baseless Info` spans, and **zero** conflict spans.
- **Verification Result:** **100.00% Compliant.**
- *Audited Sample:*
  - *Premise:* An article detailing a company's financial earnings.
  - *Hypothesis:* *"The CEO announced plans to open a new office in Chicago next year."*
  - *Annotator Annotation:* `Evident Baseless Info` on "plans to open a new office in Chicago". Note: *"High introduction of new information. It was not mentioned in the source."*
  - *Auditor Assessment:* **Valid Neutral.** The premise does not deny or contradict an office opening; the information is simply absent. Mappable to `NEUTRAL` (or `INSUFFICIENT_EVIDENCE`).

### 3.3 `ENTAILMENT` Audit (8,369 records)
- **Selection Criteria:** Every record must originate from a verified `FACTUAL` response with zero marked hallucination spans.
- **Critical Propositional Analysis:**  
  In abstractive summarization, human annotators considered conversational scaffolding (e.g. *"Here is a summary of the article:"*) to be faithful. In strict propositional logic, such preambles are non-truth-bearing framing devices. However, within document-grounded verification, the factual claims themselves are completely entailed by the document context.
- **Auditor Assessment:** **Valid Entailment for RAG Verification.**

---

## 4. Exclusion Manifest Accounting Verification

The audit verified all 18,613 excluded entries in [`exclusion_manifest.json`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/exclusion_manifest.json):
1. **HaluEval Benchmark (17,000 records):**  
   100% excluded due to conflation of contradiction and unmentioned entities.
2. **RAGTruth Mixed Conflict & Baseless Info (1,613 records):**  
   - 1,257 train records and 356 validation records contain both conflict and baseless spans.
   - *Example:* A summary where sentence 1 contradicts a date, while sentence 2 introduces an unmentioned entity.
   - *Auditor Finding:* Excluding these 1,613 records is scientifically sound because assigning either `CONTRADICTION` or `NEUTRAL` to a mixed multi-claim response would corrupt the classification signal.

---

## 5. Auditor Acceptance Verdict

**Evidence-Grounded 3-Way NLI:** **`READY`**  
The dataset is clean, semantically consistent, and authorized for model training under the RAGTruth 3-way NLI objective.

