# TrustRAG Track 2, Step 2: SFT Schema Specification

## 1. Overview

The `sft_v1` dataset defines a unified schema designed for supervised fine-tuning of TrustRAG verification models (G3 Output Guardrail).

All records strictly adhere to the `SFTExampleRecord` Pydantic model (`ConfigDict(extra="forbid")`), preventing unexpected fields or schema drift.

---

## 2. Pydantic Model Definition

```python
class SFTExampleRecord(BaseModel):
    """Canonical schema for TrustRAG evidence-grounded SFT examples."""

    model_config = ConfigDict(extra="forbid")

    example_id: str = Field(description="Unique identifier for the SFT example")
    source_dataset: str = Field(description="Source benchmark ('ragtruth' or 'halueval')")
    source_id: str = Field(description="Original document or query identifier from source benchmark")
    split: Literal["train", "validation"] = Field(description="Target SFT split ('train' or 'validation')")
    question_or_claim: str = Field(description="User query, prompt, or task specification")
    context_or_evidence: str = Field(description="Passage or document text against which claim is verified")
    candidate_response: str = Field(description="The generated claim or answer evaluated for faithfulness")
    ground_truth_label: Literal["FACTUAL", "HALLUCINATED"] = Field(
        description="Ground-truth binary faithfulness label"
    )
    target: str = Field(description="Structured target verification output derived from original annotations")
    target_provenance: str = Field(description="Explicit description of how target was derived from annotations")
```

---

## 3. Field Specifications & Integrity Constraints

| Field | Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `example_id` | `str` | Unique, non-empty, prefix `sft_` | Deterministic identifier e.g. `sft_ragtruth_train_0001`. |
| `source_dataset` | `str` | Must be `"ragtruth"` or `"halueval"` | Provenance marker indicating upstream corpus. |
| `source_id` | `str` | Non-empty | Original source document or query ID used for grouping. |
| `split` | `Literal` | `"train"` or `"validation"` | Strict split allocation. |
| `question_or_claim` | `str` | Non-empty | Query / prompt given to the generation system. |
| `context_or_evidence`| `str` | Non-empty | Supporting context document against which candidate is judged. |
| `candidate_response` | `str` | Non-empty | Model-generated response evaluated for hallucinations. |
| `ground_truth_label` | `Literal` | `"FACTUAL"` or `"HALLUCINATED"` | Ground truth classification label. |
| `target` | `str` | Valid serialized JSON | Structured verification verdict and span evidence. |
| `target_provenance` | `str` | Non-empty | Audit trail documenting derivation from upstream source. |

---

## 4. Structured Target Schemas by Benchmark

### 4.1 RAGTruth Target Schema

#### Case A: Factual (Supported) Example
```json
{
  "verdict": "SUPPORTED",
  "grounding_status": "GROUNDED",
  "hallucination_spans": []
}
```
**Provenance:** `"ragtruth_original_annotations: verified factual summary with zero hallucinated spans"`

#### Case B: Hallucinated (Contradicted) Example
```json
{
  "verdict": "CONTRADICTED",
  "grounding_status": "HALLUCINATED",
  "hallucination_spans": [
    {
      "text": "The patient was prescribed amoxicillin.",
      "conflict_type": "Conflict",
      "meta": "Evidentiary conflict with documented allergy"
    }
  ]
}
```
**Provenance:** `"ragtruth_original_annotations: verified hallucination with 1 annotated span conflicts"`

---

### 4.2 HaluEval QA Target Schema

#### Case A: Factual (Supported) Example
```json
{
  "verdict": "SUPPORTED",
  "grounding_status": "GROUNDED",
  "source_pair_type": "right_answer"
}
```
**Provenance:** `"halueval_qa_original_annotations: canonical right_answer grounded in context passage"`

#### Case B: Hallucinated (Contradicted) Example
```json
{
  "verdict": "CONTRADICTED",
  "grounding_status": "HALLUCINATED",
  "source_pair_type": "hallucinated_answer"
}
```
**Provenance:** `"halueval_qa_original_annotations: canonical hallucinated_answer conflicting with or unsupported by passage"`

---

## 5. Exported JSON Schema

The full standard JSON schema is exported at [`data/processed/sft_v1/schema.json`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v1/schema.json) for programmatic validation across external fine-tuning toolkits.

