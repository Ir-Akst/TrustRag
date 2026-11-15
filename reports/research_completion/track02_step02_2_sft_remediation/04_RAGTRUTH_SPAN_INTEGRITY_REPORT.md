# TrustRAG Track 2, Step 2.2: RAGTruth Span Integrity Report

## 1. Objective & Specification

The **Span-Level Hallucination Detection Dataset** is located at:
[`data/processed/sft_v2/spans/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/spans/)

### 1.1 Objective Scope
This dataset is designed for training token-level sequence labelers, pointer networks, and span extraction models that localize exact hallucinated text within a candidate response:
$$f(x_{\text{context}}, x_{\text{candidate}}) \rightarrow \{(s_i, e_i, \text{label\_type})\}$$

---

## 2. Schema Specification

The dataset strictly implements `SpanExampleRecord` and `HallucinationSpan` Pydantic models (`ConfigDict(extra="forbid")`):

```python
class HallucinationSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: int = Field(description="Character start offset in candidate response")
    end: int = Field(description="Character end offset in candidate response")
    text: str = Field(description="Exact substring text of the hallucination")
    label_type: str = Field(description="Upstream taxonomy label (e.g. Evident Conflict)")
    meta: str = Field(description="Annotator notes and explanation")

class SpanExampleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    example_id: str = Field(description="Unique identifier for span example")
    source_dataset: Literal["ragtruth"] = Field(description="Upstream source corpus (RAGTruth only)")
    source_id: str = Field(description="Original document ID")
    split: Literal["train", "validation"] = Field(description="Partition split")
    question_or_claim: str = Field(description="Input prompt or task instruction")
    context_or_evidence: str = Field(description="Passage or document text")
    candidate_response: str = Field(description="Candidate response with annotated spans")
    ground_truth_label: Literal["FACTUAL", "HALLUCINATED"] = Field(description="Binary classification label")
    hallucination_spans: list[HallucinationSpan] = Field(description="List of verified character spans")
    source_provenance: str = Field(description="Audit trail of span origin")
```

The exported standard JSON Schema is available at [`data/processed/sft_v2/spans/schema.json`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/spans/schema.json).

---

## 3. Offset Exactness & Character Verification

Every single span in `data/processed/sft_v2/spans/` was verified by slicing the exact candidate response text:
$$\text{candidate\_response}[\text{span.start} : \text{span.end}] == \text{span.text}$$

### Verification Results
- **Total Spans Verified:** **12,756 spans** (10,248 in train, 2,508 in validation).
- **Exact Slicing Matches:** **12,756 spans (100.00%)**.
- **Character Offset Mismatches:** **0 (0.00%)**.
- **Empty or Null Spans:** **0 (0.00%)**.

---

## 4. Multi-Span Distribution & Span Taxonomy

Across the 6,721 hallucinated responses in `sft_v2/spans`:

| Spans per Response | Response Count | Percentage |
| :---: | :---: | :---: |
| **0 Spans (Factual)** | 8,369 | 55.46% |
| **1 Span** | 3,365 | 22.30% |
| **2 Spans** | 1,811 | 12.00% |
| **3 Spans** | 868 | 5.75% |
| **4 Spans** | 398 | 2.64% |
| **5+ Spans** | 279 | 1.85% |

### Span Taxonomy Breakdown
- `Evident Baseless Info`: 5,572 spans (43.68%)
- `Evident Conflict`: 4,763 spans (37.34%)
- `Subtle Baseless Info`: 2,242 spans (17.58%)
- `Subtle Conflict`: 179 spans (1.40%)
- **Total Spans:** **12,756 spans (100.00%)**.

---

## 5. File Manifest & Checksums

| File | Records / Lines | Size | Cryptographic SHA-256 Digest |
| :--- | :---: | :---: | :--- |
| `train.jsonl` | 12,072 | ~34.8 MB | `ea158525eef050dbd2fa8c13e414c5b3c45fe155a069df8b49e6f2162fb16556` |
| `validation.jsonl` | 3,018 | ~8.7 MB | `6cebe4684a0d9382f6e9195b0fe21bc566a7b7ea2ae1e5f86b4df9d1bdf6b5c3` |
| `schema.json` | 68 lines | ~2.1 KB | `532c256e6d194883f3baeeefaa8a6669fec6f184711f58b5fa21e646271c72f1` |
| `dataset_manifest.json` | 37 lines | ~1.3 KB | `9c4a5c53177995123d573663a8a0058b8d9633e6fa16b048740c266858276f5f` |
| `exclusion_manifest.json` | 11 lines | ~560 B | `44955c4d682490d1f705e4c6981881e188229b1399f666f21226a0fe3dc3ccaa` |

