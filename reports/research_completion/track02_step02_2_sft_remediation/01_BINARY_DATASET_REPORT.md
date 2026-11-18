# TrustRAG Track 2, Step 2.2: Binary Hallucination Classification Dataset Report

## 1. Objective & Specification

The **Binary Hallucination Classification Dataset** is located at:
[`data/processed/sft_v2/binary/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/)

### 1.1 Objective Scope
This dataset is designed specifically for fine-tuning binary hallucination detection models and guardrails:
$$f(x_{\text{prompt}}, x_{\text{context}}, x_{\text{candidate}}) \rightarrow y \in \{\text{FACTUAL}, \text{HALLUCINATED}\}$$
Binary labels are preserved directly from authoritative upstream annotations and are **not derived from or collapsed to G3 verdicts**.

---

## 2. Schema Specification

The dataset strictly implements the `BinaryExampleRecord` Pydantic model (`ConfigDict(extra="forbid")`):

```python
class BinaryExampleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    example_id: str = Field(description="Unique identifier for binary SFT example")
    source_dataset: Literal["ragtruth", "halueval"] = Field(description="Upstream source corpus")
    source_id: str = Field(description="Original document or query ID")
    split: Literal["train", "validation"] = Field(description="Partition split")
    question_or_claim: str = Field(description="Input prompt, task, or user query")
    context_or_evidence: str = Field(description="Passage or document text")
    candidate_response: str = Field(description="Candidate claim or response")
    binary_label: Literal["FACTUAL", "HALLUCINATED"] = Field(description="Ground truth binary label")
    source_provenance: str = Field(description="Audit trail of label origin")
```

The exported standard JSON Schema is available at [`data/processed/sft_v2/binary/schema.json`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/schema.json).

---

## 3. Definitive Census & Label Distribution

| Component | Split | Total Records | FACTUAL | HALLUCINATED | Unique Document Hashes | Document Leakage Rate |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **RAGTruth** | train | 12,072 | 6,660 | 5,412 | 2,011 | **0.00%** |
| **RAGTruth** | validation | 3,018 | 1,709 | 1,309 | 503 | **0.00%** |
| **HaluEval** | train | 13,982 | 6,991 | 6,991 | 6,973 | **0.00%** |
| **HaluEval** | validation | 2,966 | 1,483 | 1,483 | 1,475 | **0.00%** |
| **Combined** | **train** | **26,054** | **13,651** | **12,403** | **8,984** | **0.00%** |
| **Combined** | **validation** | **5,984** | **3,192** | **2,792** | **1,978** | **0.00%** |
| **Total** | **combined** | **32,038** | **16,843** | **15,195** | **10,962** | **0.00%** |

---

## 4. Leakage Remediation & Exclusions

In Step 2.1, adversarial audits revealed passage overlap in upstream HaluEval and a duplicated article in RAGTruth. Both have been remediated in `sft_v2/binary`:

1. **RAGTruth Article Duplication Resolved:**
   - Source IDs `12084` and `12085` contain the exact same CNN weather text.
   - By hashing normalized document text, both records were grouped into the training split.
   - Document overlap between train and validation: **0 (0.00%)**.
2. **HaluEval Test Set Quarantine:**
   - Exactly **18 train records (9 pairs)** and **8 validation records (4 pairs)** shared context passages with the canonical HaluEval test set.
   - All 26 records were quarantined and excluded from training and validation.
3. **HaluEval Cross-Split Overlap Remediation:**
   - Exactly **26 validation records (13 pairs)** shared context passages with the training set.
   - All 26 records were quarantined and excluded from validation.
4. **Exclusion Logging:**
   - All 52 excluded records are logged with verbatim passage snippets in [`data/processed/sft_v2/binary/exclusion_manifest.json`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/exclusion_manifest.json).

---

## 5. File Manifest & Checksums

| File | Records / Lines | Size | Cryptographic SHA-256 Digest |
| :--- | :---: | :---: | :--- |
| `train.jsonl` | 26,054 | ~67.5 MB | `c68fb5020129eb5110eb2df8f15b497676eeb182e0717208ff95f92ffccb997c` |
| `validation.jsonl` | 5,984 | ~15.8 MB | `2d5e2193b2cc2a15f3e5898d24b6113b28b61c92a9bf8c105077d2427a942fa5` |
| `schema.json` | 50 lines | ~1.6 KB | `6d6cbb159cf0ddcc250d48feae1316b11cb3ca622c710c0e76466986fa3a4794` |
| `dataset_manifest.json` | 42 lines | ~1.5 KB | `a19e2bb4a2e21b794da8722aebca1e2336338cf8c69be8633aa96ea43a8aa9c6` |
| `exclusion_manifest.json` | 427 lines | ~15.2 KB | `f931d86d52579b4a4cbbfb9ce46cb6b5c90b05b6e6d1c81dcba83207dd4ce3ee` |

