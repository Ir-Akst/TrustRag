# TrustRAG — Dataset Adapter Field Mapping & Schema Normalization Specification

> **Document Version:** 1.1.0  
> **Phase:** Phase 01 & Phase 02 (Dataset Engineering & Benchmark Construction)  
> **Subsystem:** `trustrag.data.loaders`, `trustrag.data.taxonomy`, `trustrag.data.benchmarks`  
> **Audit Date:** 2026-11-08  

---

## 1. Overview & Normalization Strategy

The TrustRAG dataset engineering pipeline standardizes heterogeneous schemas from 13 different public, local, and benchmark datasets into 4 strongly-typed Pydantic records:

1. **`DocumentRecord`**: Used for unstructured corpus documents, passages, and pretraining data.
2. **`QueryRecord`**: Used for question answering, retrieval queries, relevance judgements, and reference answers.
3. **`ClaimVerificationRecord`**: Used for fine-grained claim evaluation, fact-checking, and hallucination detection.
4. **`SecurityRecord`**: Used for corpus poisoning, adversarial contexts, triggers, and defense evaluation.

### Core Adapter Guarantees
- **No Information Loss:** Original raw IDs and dataset-specific fields are preserved in `source_id` and `metadata`.
- **Content Hash Generation:** A deterministic SHA-256 hash (`content_hash`) is computed over normalized primary text for deduplication and cross-split leakage tracking.
- **Explicit Label Normalization:** Categorical and numerical labels are mapped to standardized enum values. Any unrecognized or ambiguous label immediately raises a `ValidationError`.
- **Mock vs Live Distinction:** Adapter tests execute using hermetic in-memory representative samples. Live downloading is limited to verified integration tests (`pytest -m integration`) and explicit CLI executions with configured sample caps.

---

## 2. Comprehensive Field Mapping Tables (All 13 Datasets)

---

### Category A: RAG & Question-Answering Datasets

#### 1. Natural Questions (NQ)
- **Target Schema:** `QueryRecord`
- **Adapter Module:** `src/trustrag/data/loaders/natural_questions.py`
- **Official Source:** `google-research-datasets/natural_questions` (Hugging Face / GCS)
- **Verification Status:** Mocked unit tests verified; live download pending full network test.

| Source Raw Field | Target Normalized Field | Transformation / Extraction Logic | Handling of Missing / Optional |
|---|---|---|---|
| `id` / `example_id` | `source_id` | Cast to `str` | Mandatory |
| `id` / `example_id` | `query_id` | Formatted as `f"nq_{id}"` | Mandatory |
| `question.text` / `question` | `query` | Stripped and cleaned via NFKC Unicode normalization | Raises `ValidationError` if empty |
| `annotations.short_answers` | `answer` | Extracted text from first short answer span; formatted as string | Defaults to `""` if unannotated |
| `id` / `example_id` | `relevant_document_ids` | `[f"nq_doc_{id}"]` | Defaults to empty list `[]` |
| `annotations.yes_no_answer` | `metadata["yes_no_answer"]` | Preserved as integer/string flag | Defaults to `None` |
| `document.url` | `metadata["document_url"]` | Preserved as source Wikipedia URL | Optional, defaults to `None` |
| *(computed)* | `content_hash` | SHA-256 hash over normalized `query` | Computed deterministically |
| *(constant)* | `source_dataset` | `"natural_questions"` | Fixed constant |
| `split` | `source_split` | Split name passed during load (`train` or `validation`) | Defaults to `"train"` |

---

#### 2. HotpotQA
- **Target Schema:** `QueryRecord`
- **Adapter Module:** `src/trustrag/data/loaders/hotpotqa.py`
- **Official Source:** `hotpotqa/hotpot_qa` (Hugging Face)
- **Verification Status:** Mocked unit tests verified.

| Source Raw Field | Target Normalized Field | Transformation / Extraction Logic | Handling of Missing / Optional |
|---|---|---|---|
| `_id` / `id` | `source_id` | Cast to string | Mandatory |
| `_id` / `id` | `query_id` | Formatted as `f"hotpot_{id}"` | Mandatory |
| `question` | `query` | Stripped and cleaned Unicode text | Raises `ValidationError` if empty |
| `answer` | `answer` | Direct reference answer string | Defaults to `""` if missing |
| `supporting_facts.title` | `relevant_document_ids` | Deduplicated list of Wikipedia article titles cited as evidence | Empty list if omitted |
| `type` | `metadata["type"]` | Multi-hop reasoning type (`comparison` or `bridge`) | Preserved in metadata |
| `level` | `metadata["level"]` | Difficulty level (`easy`, `medium`, `hard`) | Preserved in metadata |
| `context` | `metadata["context"]` | Retained in metadata if context passages provided | Optional |
| *(computed)* | `content_hash` | SHA-256 hash over `query` | Computed deterministically |
| *(constant)* | `source_dataset` | `"hotpotqa"` | Fixed constant |

---

#### 3. MS MARCO
- **Target Schema:** `QueryRecord`
- **Adapter Module:** `src/trustrag/data/loaders/ms_marco.py`
- **Official Source:** `microsoft/ms_marco` (Hugging Face: `v1.1` or `v2.1`)
- **Verification Status:** Mocked unit tests verified.

| Source Raw Field | Target Normalized Field | Transformation / Extraction Logic | Handling of Missing / Optional |
|---|---|---|---|
| `query_id` | `source_id` | Cast to string | Mandatory |
| `query_id` | `query_id` | Formatted as `f"msmarco_{query_id}"` | Mandatory |
| `query` | `query` | Normalized query string | Raises `ValidationError` if empty |
| `answers` | `answer` | First non-empty string in answers list; `"No answer provided"` if empty | Safe fallback |
| `passages.is_selected` | `relevant_document_ids` | List of formatted passage indices where `is_selected == 1` | `[]` if none selected |
| `query_type` | `metadata["query_type"]` | Description / Numeric query category | Preserved in metadata |
| `passages.passage_text` | `metadata["passages"]` | Full passage candidate texts preserved in metadata | Preserved in metadata |
| *(computed)* | `content_hash` | SHA-256 hash over `query` | Computed deterministically |
| *(constant)* | `source_dataset` | `"ms_marco"` | Fixed constant |

---

#### 4. SQuAD
- **Target Schema:** `QueryRecord`
- **Adapter Module:** `src/trustrag/data/loaders/squad.py`
- **Official Source:** `rajpurkar/squad` (Hugging Face)
- **Verification Status:** Live integration test verified (`2 passed in 17.40s`).

| Source Raw Field | Target Normalized Field | Transformation / Extraction Logic | Handling of Missing / Optional |
|---|---|---|---|
| `id` | `source_id` | Unique question hex ID | Mandatory |
| `id` | `query_id` | Formatted as `f"squad_{id}"` | Mandatory |
| `question` | `query` | Question text | Raises `ValidationError` if empty |
| `answers.text` | `answer` | First answer in list; `""` if SQuAD 2.0 unanswerable | Safe fallback |
| `id` / `title` | `relevant_document_ids` | `[f"squad_doc_{id}"]` | Preserved as context link |
| `title` | `metadata["title"]` | Wikipedia article title | Preserved in metadata |
| `context` | `metadata["context"]` | Reference reading paragraph | Preserved in metadata |
| `answers.answer_start` | `metadata["answer_start"]` | Character offset of reference answer | Optional list of ints |
| *(computed)* | `content_hash` | SHA-256 hash over `query` | Computed deterministically |
| *(constant)* | `source_dataset` | `"squad"` | Fixed constant |

---

#### 5. BoolQ
- **Target Schema:** `QueryRecord`
- **Adapter Module:** `src/trustrag/data/loaders/boolq.py`
- **Official Source:** `google/boolq` (Hugging Face)
- **Verification Status:** Live integration test & smoke-test partition verified.

| Source Raw Field | Target Normalized Field | Transformation / Extraction Logic | Handling of Missing / Optional |
|---|---|---|---|
| *(row index or hash)* | `source_id` | Row index or hash of question+title | Assigned sequentially if missing |
| *(derived)* | `query_id` | `f"boolq_{source_id}"` | Generated deterministically |
| `question` | `query` | Yes/No query text | Raises `ValidationError` if empty |
| `answer` | `answer` | Normalized string: `"yes"` if `answer is True` else `"no"` | Converted from boolean |
| `title` | `relevant_document_ids` | `[f"boolq_doc_{title}"]` | Extracted from article title |
| `passage` | `metadata["passage"]` | Reference Wikipedia paragraph | Preserved in metadata |
| `title` | `metadata["title"]` | Article title | Preserved in metadata |
| `answer` | `metadata["raw_bool_answer"]`| Original boolean (`True` or `False`) | Preserved in metadata |
| *(computed)* | `content_hash` | SHA-256 hash over `query` | Computed deterministically |
| *(constant)* | `source_dataset` | `"boolq"` | Fixed constant |

---

### Category B: Hallucination & Claim-Verification Datasets

#### 6. HaluEval
- **Target Schema:** `ClaimVerificationRecord` (Generates paired factual + hallucinated records)
- **Adapter Module:** `src/trustrag/data/loaders/halueval.py`
- **Official Source:** `pminervini/HaluEval` (Hugging Face)
- **Verification Status:** Mocked unit tests verified.

| Source Raw Field | Target Normalized Field | Transformation / Extraction Logic | Handling of Missing / Optional |
|---|---|---|---|
| `knowledge` / `passage` | `document` | Contextual evidence passage | Raises `ValidationError` if empty |
| `right_answer` | `claim` (Record A) | Factual response paired with document | Clean factual claim |
| `hallucinated_answer`| `claim` (Record B) | Synthetic hallucinated response | Hallucinated claim |
| *(derived)* | `label` | `FACTUAL` for Record A; `HALLUCINATED` for Record B | Explicitly mapped enums |
| `query` / `question` | `metadata["query"]` | User prompt prompting the answers | Preserved in metadata |
| *(derived)* | `record_id` | `f"halueval_{idx}_factual"` and `f"halueval_{idx}_hallu"` | Grouped by index |
| *(derived)* | `source_id` | Shared `f"halueval_{idx}"` | Preserves paired grouping for split isolation |
| *(computed)* | `content_hash` | SHA-256 hash over `document + " || " + claim` | Computed deterministically |
| *(constant)* | `source_dataset` | `"halueval"` | Fixed constant |

---

#### 7. RAGTruth
- **Target Schema:** `ClaimVerificationRecord`
- **Adapter Module:** `src/trustrag/data/loaders/ragtruth.py`
- **Official Source:** `https://github.com/ParticleMedia/RAGTruth` (Local import adapter)
- **Verification Status:** Mocked unit tests verified.

| Source Raw Field | Target Normalized Field | Transformation / Extraction Logic | Handling of Missing / Optional |
|---|---|---|---|
| `id` / `record_id` | `record_id` | `f"ragtruth_{id}"` | Cast to string |
| `id` / `source_id` | `source_id` | Original source prompt / article identifier | Preserved for split grouping |
| `source_text` / `document` | `document` | Provided retrieval context | Raises `ValidationError` if empty |
| `response` / `model_output`| `claim` | Generated response evaluated for hallucinations | Raises `ValidationError` if empty |
| `label` / `hallucination` | `label` | `0` or `"factual"` -> `FACTUAL`; `1` or `"hallucinated"` -> `HALLUCINATED` | Rejects unknown labels |
| `labels` / `span_labels` | `metadata["span_labels"]` | Character or word span hallucination annotations | Optional list of dicts |
| `task` | `metadata["task"]` | Task type (`qa`, `summary`, `data2text`) | Preserved in metadata |
| `model` | `metadata["model"]` | Generator LLM identifier | Preserved in metadata |
| *(computed)* | `content_hash` | SHA-256 over `document + " || " + claim` | Computed deterministically |
| *(constant)* | `source_dataset` | `"ragtruth"` | Fixed constant |

---

#### 8. LLM-AggreFact
- **Target Schema:** `ClaimVerificationRecord`
- **Adapter Module:** `src/trustrag/data/loaders/llm_aggrefact.py`
- **Official Source:** `lytang/LLM-AggreFact` (Gated Hugging Face / Local Import)
- **Verification Status:** Mocked unit tests verified; gated access handled via offline fallback.

| Source Raw Field | Target Normalized Field | Transformation / Extraction Logic | Handling of Missing / Optional |
|---|---|---|---|
| `doc_id` / `id` | `source_id` | Original document identifier | Preserved for split grouping |
| `id` / `sent_id` | `record_id` | `f"aggrefact_{id}"` | Formatted string |
| `document` / `source` | `document` | Source context / document text | Raises `ValidationError` if empty |
| `claim` / `sentence` | `claim` | Evaluated summary sentence / claim | Raises `ValidationError` if empty |
| `label` / `binary_label` | `label` | `1` or `"consistent"` -> `FACTUAL`; `0` or `"inconsistent"` -> `HALLUCINATED` | Rejects unknown labels |
| `benchmark_source` | `metadata["benchmark_source"]` | Origin benchmark (e.g. `XSum`, `Frank`, `QAGS`) | Preserved in metadata |
| `error_type` | `metadata["error_type"]` | Specific error taxonomy (e.g. `intrinsic`, `extrinsic`) | Optional string |
| *(computed)* | `content_hash` | SHA-256 over `document + " || " + claim` | Computed deterministically |
| *(constant)* | `source_dataset` | `"llm_aggrefact"` | Fixed constant |
| *(permission)* | `permitted_for_training` | **`False`** (Enforced: Evaluation Only) | Cannot be overridden |

---

#### 9. WiCE
- **Target Schema:** `ClaimVerificationRecord`
- **Adapter Module:** `src/trustrag/data/loaders/wice.py`
- **Official Source:** `https://github.com/ryokamoi/wice` / Hugging Face `ryokamoi/wice`
- **Verification Status:** Mocked unit tests verified.

| Source Raw Field | Target Normalized Field | Transformation / Extraction Logic | Handling of Missing / Optional |
|---|---|---|---|
| `claim_id` / `id` | `record_id` | `f"wice_{claim_id}"` | Cast to string |
| `doc_id` / `claim_id` | `source_id` | Parent document or claim group identifier | Preserved for grouping |
| `evidence` / `document` | `document` | Cited Wikipedia reference text | Raises `ValidationError` if empty |
| `claim` / `subclaim` | `claim` | Entailment unit / subclaim sentence | Raises `ValidationError` if empty |
| `label` | `label` | `"supported"` -> `SUPPORTED`; `"refuted"` -> `REFUTED`; `"partially_supported"` -> `NOT_ENOUGH_INFO` | Rejects unknown labels |
| `justification` | `justification` | Optional natural language explanation of judgment | Defaults to `None` |
| `subclaim_index` | `metadata["subclaim_index"]`| Index of subclaim within parent sentence | Optional integer |
| *(computed)* | `content_hash` | SHA-256 over `document + " || " + claim` | Computed deterministically |
| *(constant)* | `source_dataset` | `"wice"` | Fixed constant |

---

#### 10. ExpertQA
- **Target Schema:** `ClaimVerificationRecord`
- **Adapter Module:** `src/trustrag/data/loaders/expertqa.py`
- **Official Source:** `https://github.com/chaitanyamalaviya/ExpertQA`
- **Verification Status:** Mocked unit tests verified.

| Source Raw Field | Target Normalized Field | Transformation / Extraction Logic | Handling of Missing / Optional |
|---|---|---|---|
| `id` / `claim_id` | `record_id` | `f"expertqa_{id}"` | Cast to string |
| `question_id` | `source_id` | Parent expert question identifier | Preserved for split grouping |
| `evidence` / `context` | `document` | Context passage or citation URL quote | Raises `ValidationError` if empty |
| `claim` / `sentence` | `claim` | Evaluated response sentence | Raises `ValidationError` if empty |
| `label` / `rating` | `label` | `5` or `4` or `"supported"` -> `SUPPORTED`; `1` or `2` or `"unsupported"` -> `REFUTED`; `3` -> `NOT_ENOUGH_INFO` | Rejects unknown labels |
| `expert_field` | `metadata["expert_field"]` | Domain expertise (e.g. `Medicine`, `History`, `Physics`)| Preserved in metadata |
| `question` | `metadata["question"]` | Original user question | Preserved in metadata |
| *(computed)* | `content_hash` | SHA-256 over `document + " || " + claim` | Computed deterministically |
| *(constant)* | `source_dataset` | `"expertqa"` | Fixed constant |

---

### Category C: Security & Poisoning Datasets

#### 11. RSB (RAG Security Bench)
- **Target Schema:** `SecurityRecord`
- **Adapter Module:** `src/trustrag/data/loaders/rsb.py`
- **Official Source:** `arXiv:2505.18543` (Local-import interface; download unverified)
- **Verification Status:** Documented schema & mocked unit tests verified. **NOT VERIFIED FOR REMOTE DOWNLOAD.**

| Source Raw Field | Target Normalized Field | Transformation / Extraction Logic | Handling of Missing / Optional |
|---|---|---|---|
| `sample_id` / `id` | `record_id` | `f"rsb_{id}"` | Cast to string |
| `doc_id` / `cluster_id`| `source_id` | Source document / parent passage cluster | Preserved for clean/poison pair grouping |
| `passage` / `document` | `document` | Poisoned or clean evaluation passage | Raises `ValidationError` if empty |
| `clean_poison_label` | `clean_poison_label` | `"clean"` or `0` -> `"clean"`; `"poison"` or `1` -> `"poison"` | Rejects invalid strings |
| `attack_family` | `attack_family` | Standardized family (e.g. `corpus_poisoning`, `context_injection`) | Optional |
| `attack_subtype` | `attack_subtype` | Fine-grained attack (e.g. `backdoor`, `hallucination_induction`)| Optional |
| `trigger` | `trigger_metadata` | Trigger tokens, positions, and injection rules | Dict of metadata |
| `target_query` | `target_query` | Query designed to retrieve the poisoned passage | Optional string |
| `target_response` | `target_behavior` | Malicious or biased output intended to be elicited | Optional string |
| *(computed)* | `content_hash` | SHA-256 over `document` | Computed deterministically |
| *(constant)* | `source_dataset` | `"rsb"` | Fixed constant |
| *(permission)* | `permitted_for_training` | **`False`** (Enforced: Evaluation Only) | Cannot be overridden |

---

#### 12. Custom Security Dataset (TrustRAG Internal Security)
- **Target Schema:** `SecurityRecord`
- **Adapter Module:** `src/trustrag/data/loaders/custom_security.py`
- **Official Source:** `internal://trustrag/security`
- **Verification Status:** Unit tests & grouped split leakage audit verified.

| Source Raw Field | Target Normalized Field | Transformation / Extraction Logic | Handling of Missing / Optional |
|---|---|---|---|
| `record_id` | `record_id` | Unique record string | Mandatory |
| `source_doc_id` / `doc_id` | `source_id` | Reference parent clean document ID | Mandatory for group isolation |
| `passage` / `document` | `document` | Evaluated passage text | Raises `ValidationError` if empty |
| `clean_poison_label` | `clean_poison_label` | Allowed values: `"clean"`, `"poison"` | Strict enum validation |
| `attack_family` | `attack_family` | Categorized attack class (`corpus_poisoning`, etc.) | Optional |
| `attack_subtype` | `attack_subtype` | Subtype description | Optional |
| `trigger_metadata` | `trigger_metadata` | Trigger keys, injection rate, trigger phrase | Dictionary |
| `target_query` | `target_query` | Query targeted by injection | Optional |
| *(computed)* | `content_hash` | SHA-256 over `document` | Computed deterministically |
| *(constant)* | `source_dataset` | `"custom_security"` | Fixed constant |

---

### Category D: Training Corpus

#### 13. FineWeb
- **Target Schema:** `DocumentRecord`
- **Adapter Module:** `src/trustrag/data/loaders/fineweb.py`
- **Official Source:** `HuggingFaceFW/fineweb` (Hugging Face streaming)
- **Verification Status:** Mocked unit tests verified; live download capped to engineering sample target (20,000 documents).

| Source Raw Field | Target Normalized Field | Transformation / Extraction Logic | Handling of Missing / Optional |
|---|---|---|---|
| `id` | `source_id` | Common Crawl URL or record hash | Mandatory |
| `id` | `document_id` | `f"fineweb_{id}"` | Cast to string |
| `text` | `text` | Pretraining web page document body | Raises `ValidationError` if empty |
| `url` | `metadata["url"]` | Crawled web page origin URL | Preserved in metadata |
| `dump` | `metadata["dump"]` | Common Crawl crawl release ID (e.g. `CC-MAIN-2024-10`) | Preserved in metadata |
| `date` | `metadata["date"]` | Timestamp of scrape | Preserved in metadata |
| `token_count` | `metadata["token_count"]` | Document token length | Optional integer |
| *(constant)* | `license` | `"ODC-By-1.0"` | Mandatory license string |
| *(computed)* | `content_hash` | SHA-256 over `text` | Computed deterministically |
| *(constant)* | `source_dataset` | `"fineweb"` | Fixed constant |
| *(permission)* | `permitted_for_evaluation` | **`False`** (Training Corpus Only) | Cannot be overridden |

---

## 3. Label Validation Matrix

The following table summarizes all recognized labels and how the `RecordValidator` enforces schema compliance across dataset loaders:

| Record Type | Allowed Canonical Labels | Mapped Source Variants | Rejected / Invalid Values (Raises `ValidationError`) |
|---|---|---|---|
| `ClaimVerificationRecord` | `FACTUAL` | `1`, `true`, `"consistent"`, `"factual"`, `"correct"` | `null`, `""`, `"maybe"`, `99` |
| `ClaimVerificationRecord` | `HALLUCINATED` | `0`, `false`, `"inconsistent"`, `"hallucinated"`, `"error"` | `null`, `""`, `"unverified"` |
| `ClaimVerificationRecord` | `SUPPORTED` | `"supported"`, `"entailment"`, `5`, `4` | Unknown strings |
| `ClaimVerificationRecord` | `REFUTED` | `"refuted"`, `"contradiction"`, `1`, `2` | Unknown strings |
| `ClaimVerificationRecord` | `NOT_ENOUGH_INFO` | `"not_enough_info"`, `"partially_supported"`, `"neutral"`, `3` | Unknown strings |
| `SecurityRecord` | `clean` | `"clean"`, `"benign"`, `0` | `"neutral"`, `"unknown"`, `-1` |
| `SecurityRecord` | `poison` | `"poison"`, `"poisoned"`, `"attack"`, `1` | Any untyped attack label |

---

