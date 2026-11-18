# TrustRAG Track 2, Step 2.2: Evidence-Grounded NLI Dataset Report

## 1. Objective & Specification

The **Evidence-Grounded 3-Way NLI Dataset** is located at:
[`data/processed/sft_v2/nli/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/)

### 1.1 Objective Scope
This dataset is designed for training evidence-grounded Natural Language Inference (NLI) models:
$$f(x_{\text{premise}}, x_{\text{hypothesis}}) \rightarrow y \in \{\text{ENTAILMENT}, \text{CONTRADICTION}, \text{NEUTRAL}\}$$
It remediates the core defect of `sft_v1`, which collapsed all non-entailment into `CONTRADICTED`.

---

## 2. Definitive RAGTruth NLI Mapping Rules

The labels in `sft_v2/nli` are derived directly from RAGTruth human span annotations:

| Original RAGTruth Annotation Pattern | Assigned NLI Label | Epistemic Justification |
| :--- | :---: | :--- |
| **`label == 'FACTUAL'` (0 spans)** | **`ENTAILMENT`** | Human annotators verified that the response is completely supported by the document. |
| **Pure Conflict Spans Only** (`Evident Conflict`, `Subtle Conflict` with NO baseless info) | **`CONTRADICTION`** | Every annotated span directly refutes explicit premises in the document. |
| **Pure Baseless Info Spans Only** (`Evident Baseless Info`, `Subtle Baseless Info` with NO conflict) | **`NEUTRAL`** | Information introduced is absent from the document, representing unmentioned assertions rather than refutations. |
| **Mixed Conflict & Baseless Info** (Spans of both types in one response) | **EXCLUDED** | The response simultaneously refutes and introduces unmentioned info; cannot be collapsed into a single 3-way label without atomic proposition decomposition. Logged in `exclusion_manifest.json`. |
| **HaluEval QA Benchmark** | **EXCLUDED** | Lacks human conflict/baseless distinction. Logged in `exclusion_manifest.json`. |

---

## 3. Schema Specification

The dataset strictly implements `NLIExampleRecord` Pydantic model (`ConfigDict(extra="forbid")`):

```python
class NLIExampleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    example_id: str = Field(description="Unique identifier for NLI example")
    source_dataset: Literal["ragtruth"] = Field(description="Upstream source corpus (RAGTruth only)")
    source_id: str = Field(description="Original document ID")
    split: Literal["train", "validation"] = Field(description="Partition split")
    premise: str = Field(description="Grounding context / source document")
    hypothesis: str = Field(description="Candidate response to evaluate")
    nli_label: Literal["ENTAILMENT", "CONTRADICTION", "NEUTRAL"] = Field(
        description="3-way NLI label grounded in human annotations"
    )
    conflict_types: list[str] = Field(description="List of human annotated conflict types")
    span_count: int = Field(description="Total number of annotated spans")
    source_provenance: str = Field(description="Audit trail documenting derivation from human annotations")
```

The exported standard JSON Schema is available at [`data/processed/sft_v2/nli/schema.json`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/schema.json).

---

## 4. Definitive Census & Label Distribution

| Split | Total Records | ENTAILMENT | CONTRADICTION | NEUTRAL | Unique Document Hashes | Document Leakage Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Train Split** | 10,815 | 6,660 (61.58%) | 1,415 (13.08%) | 2,740 (25.34%) | 2,011 | **0.00%** |
| **Validation Split** | 2,662 | 1,709 (64.20%) | 361 (13.56%) | 592 (22.24%) | 503 | **0.00%** |
| **Total Combined** | **13,477** | **8,369 (62.10%)** | **1,776 (13.18%)** | **3,332 (24.72%)** | **2,514** | **0.00%** |

### Split Balance Stability
The proportions of `ENTAILMENT`, `CONTRADICTION`, and `NEUTRAL` match between training and validation within 3.1%, maintaining clean distributional characteristics.

---

## 5. Exclusions & Quarantine Log

Every excluded record is documented in [`data/processed/sft_v2/nli/exclusion_manifest.json`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/exclusion_manifest.json):
1. **RAGTruth Mixed Conflict & Baseless Info (1,613 records):**
   - 1,257 train records and 356 validation records contain both conflict and baseless spans.
   - Quarantined to preserve pure, uncompromised 3-way NLI supervision.
2. **HaluEval Benchmark (17,000 records):**
   - Completely quarantined from NLI training due to conflation of contradiction and unmentioned entities.

---

## 6. File Manifest & Checksums

| File | Records / Lines | Size | Cryptographic SHA-256 Digest |
| :--- | :---: | :---: | :--- |
| `train.jsonl` | 10,815 | ~29.1 MB | `16867e3a992ca79979ccf415309d29837a77df3c467a2eec9313cb1277a08b98` |
| `validation.jsonl` | 2,662 | ~7.2 MB | `775f0a78601db7a195325b6a7a00ff01908990c8e312f1dfb1b36ae270a4a833` |
| `schema.json` | 51 lines | ~1.6 KB | `c0fc4419aa3370e28f32aa78cebf1b145d58ff3229b4db0cbf17c4627197063f` |
| `dataset_manifest.json` | 33 lines | ~1.1 KB | `0d0c3beafcc67118cae7d4be15e10cfb12204c382b6be0702d0865cbb6892b15` |
| `exclusion_manifest.json` | 14,529 lines | ~845 KB | `a906231920ee9575916a4cba8db9c8d5069255a6d9eb4f39c1e7a5eb43f8ca68` |

