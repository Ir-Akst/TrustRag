# TrustRAG Track 2, Step 2.1: RAGTruth Annotation Audit Report

## 1. Audit Scope & Methodology

This report audits the extraction and preservation of **RAGTruth** human annotations in [`tools/data_prep/prepare_sft_dataset.py`](file:///home/aditya/rags/TrustRag-phase11/tools/data_prep/prepare_sft_dataset.py) and their serialization in `data/processed/sft_v1/`.

The audit inspects the raw source file [`data/raw/ragtruth/response.jsonl`](file:///home/aditya/rags/TrustRag-phase11/data/raw/ragtruth/response.jsonl) (17,790 records) against the processed training (12,072) and validation (3,018) splits.

---

## 2. Upstream RAGTruth Human Annotation Schema

RAGTruth (*Niu et al., ACL 2024: "RAGTruth: A Hallucination Benchmark for Retrieval-Augmented Generation"*) provides fine-grained, span-level human annotations on model responses across News Summarization, QA, and Data-to-Text tasks.

Each hallucination instance contains:
- `text`: Exact character substring containing the hallucination.
- `start`, `end`: Character offsets within the response.
- `label_type`: Human taxonomy category.
- `meta`: Verbatim annotator notes contrasting source text against generated text.

Across the entire canonical corpus, annotators identified **14,289 hallucinated spans** distributed across four categories:

| Upstream `label_type` | Span Count | Percentage | Semantic Meaning |
| :--- | :---: | :---: | :--- |
| **`Evident Baseless Info`** | 6,237 | 43.65% | Information introduced that is completely absent from source text. |
| **`Evident Conflict`** | 5,324 | 37.26% | Information that directly contradicts source document facts. |
| **`Subtle Baseless Info`** | 2,527 | 17.68% | Minor or nuanced unsupported assertions. |
| **`Subtle Conflict`** | 201 | 1.41% | Nuanced or borderline factual contradictions. |
| **Total Spans** | **14,289** | **100.00%** | |

---

## 3. Preservation of Spans and Metadata in `sft_v1`

### 3.1 Verification of Factual Records
- **Audit Check:** Do all records labeled `FACTUAL` in `sft_v1` have zero hallucinated spans in the original annotations?
- **Result:** **PASSED (100% clean).**
  All 6,660 RAGTruth train records and 1,709 validation records labeled `FACTUAL` correspond to original responses with empty `labels: []`. Not a single factual record has undetected or dropped spans.

### 3.2 Verification of Hallucinated Records
- **Audit Check:** Do all records labeled `HALLUCINATED` in `sft_v1` contain valid span annotations?
- **Result:** **PASSED.**
  Every hallucinated RAGTruth record in `sft_v1` preserves its original character spans, conflict types, and annotator metadata notes in `target["hallucination_spans"]`.

---

## 4. Critical Semantic Audit: Systematic Mislabeling of Baseless Info as Contradiction

While span preservation is technically intact, the transformation logic in [`tools/data_prep/prepare_sft_dataset.py`](file:///home/aditya/rags/TrustRag-phase11/tools/data_prep/prepare_sft_dataset.py) executes a flawed categorical mapping:

```python
# Lines 70-74 of tools/data_prep/prepare_sft_dataset.py
target_dict = {
    "verdict": "CONTRADICTED",
    "grounding_status": "HALLUCINATED",
    "hallucination_spans": formatted_spans,
}
```

This unconditionally assigns `"verdict": "CONTRADICTED"` to **all** hallucinated records, completely ignoring `label_type`.

### 4.1 Empirical Census of Conflict vs. Baseless Info Records

Independent analysis of the span composition of every RAGTruth record in `sft_v1` reveals:

| Category Breakdown | Train Count (12,072) | Train % | Val Count (3,018) | Val % | Total Records | Assigned in `sft_v1` | True Epistemic Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Factual (Zero Spans)** | 6,660 | 55.17% | 1,709 | 56.63% | 8,369 | `SUPPORTED` | `SUPPORTED` |
| **Pure Conflict** | 1,415 | 11.72% | 361 | 11.96% | 1,776 | `CONTRADICTED` | `CONTRADICTED` |
| **Mixed Conflict & Baseless** | 1,319 | 10.93% | 294 | 9.74% | 1,613 | `CONTRADICTED` | `CONTRADICTED` |
| **Pure Baseless Info** | **2,678** | **22.18%** | **654** | **21.67%** | **3,332** | `CONTRADICTED` | **`INSUFFICIENT_EVIDENCE`** |

### 4.2 Impact of the Pure Baseless Info Category
- **3,332 records (22.08% of all RAGTruth records in `sft_v1`)** contain **ONLY** `Evident Baseless Info` or `Subtle Baseless Info`.
- They contain **zero factual conflicts or contradictions** with the source text.
- *Representative Example:*
  - *Source Document:* An article about Anne Frank's diary and family history.
  - *Generated Text:* Claims that *"the Anne Frank House issued a corrected statement regarding the date of her passing."*
  - *Human Annotator Note:* *"HIGH INTRODUCTION OF NEW INFORMATION. It was not mentioned in the source content that the Anne Frank House issued a corrected statement."*
  - *Assigned Target in `sft_v1`:* `verdict: "CONTRADICTED"`.
  - *Auditor Finding:* The source document does not assert that the Anne Frank House *refused* to issue a statement. The claim is unmentioned and cannot be verified from the text. In TrustRAG G3, this must be `INSUFFICIENT_EVIDENCE`, not `CONTRADICTED`.

---

## 5. Auditor Conclusion & Recommendation

1. **RAGTruth Contains High-Quality Span Annotations:**
   The original span texts and annotator notes are well-formed and suitable for span-level hallucination detection.
2. **Defensible Re-Mapping:**
   Because RAGTruth explicitly annotates `Evident Baseless Info` vs `Evident Conflict`, RAGTruth **can** support a defensible 3-way or 4-way G3 classification:
   - Zero spans $\rightarrow$ `SUPPORTED`
   - Only `Conflict` spans $\rightarrow$ `CONTRADICTED`
   - Only `Baseless Info` spans $\rightarrow$ `INSUFFICIENT_EVIDENCE` (or `UNMENTIONED`)
   - Both spans $\rightarrow$ `CONTRADICTED` (or `PARTIALLY_SUPPORTED` with conflict)
3. **Current Dataset Limitation:**
   As currently packaged in `sft_v1`, the 3,332 pure baseless info examples inject label noise into `CONTRADICTED`.

