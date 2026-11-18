# Track 2, Step 3.1: Model Availability & Offline Staging Assessment

**Audit Date:** November 14, 2026  
**Auditor:** Independent ML Infrastructure Engineer  
**Target Model:** `microsoft/deberta-v3-small`  

---

## 1. Local Filesystem Model Census

A recursive inspection across all local storage locations was executed to determine whether pretrained model weights, configurations, and tokenizer files for `microsoft/deberta-v3-small` exist on the host:

| Evaluated Location | Path Checked | Status | Files Found |
| :--- | :--- | :--- | :--- |
| **Workspace Pretrained Directory** | `/home/aditya/rags/models/pretrained/deberta-v3-small` | ❌ **NON-EXISTENT** | None (`models/pretrained/` contains only `.gitkeep`) |
| **Workspace Checkpoints Directory** | `/home/aditya/rags/models/checkpoints/deberta-v3-small` | ❌ **NON-EXISTENT** | None (`models/checkpoints/` contains only `.gitkeep`) |
| **Phase 11 Target Directory** | `/home/aditya/rags/TrustRag-phase11/models/` | ❌ **NON-EXISTENT** | Directory not created |
| **Hugging Face Hub Cache** | `/home/aditya/.cache/huggingface/hub/models--microsoft--deberta-v3-small`| ❌ **NON-EXISTENT** | Only dataset shards exist (`hotpotqa`, `ms_marco`, `nq`) |
| **Generic Models Directory** | `/home/aditya/models` | ❌ **NON-EXISTENT** | None |

**Census Finding:** There are **zero** pretrained weights, vocabulary files, or configuration files for `microsoft/deberta-v3-small` (or any other pretrained model) present anywhere on the local host.

---

## 2. Project Offline Policy Compliance

TrustRAG enforces strict offline execution constraints defined in `src/trustrag/config/engine_config.py` and `src/trustrag/srm/hf_local.py`:

```python
# Engine Configuration Safeguards
local_files_only: bool = Field(
    default=True,
    description="Disallow automatic remote weight downloads; require locally staged checkpoints"
)
trust_remote_code: bool = Field(
    default=False,
    description="Explicit opt-in required before executing custom tokenizer/model code"
)
```

### Policy Enforcement Rules:
1. **No Silent Downloads:** Neither `transformers.AutoModel.from_pretrained()` nor `transformers.AutoTokenizer.from_pretrained()` may initiate unsanctioned dynamic HTTP calls to the Hugging Face Hub during training or verification.
2. **Deterministic Failure:** If weights are missing, the runtime must fail deterministically with `ProviderError` rather than attempting a runtime fallback to remote fetching.
3. **Explicit Staging Requirement:** Checkpoints must be explicitly and verifiably staged in `/home/aditya/rags/models/pretrained/` with valid SHA-256 manifests.

---

## 3. Explicit Staging Procedure & Prerequisites

For `microsoft/deberta-v3-small`, the required staging files comprise:

| File Name | Description | Approximate Size | Mandatory |
| :--- | :--- | :--- | :--- |
| `config.json` | Architecture hyperparameter configuration | ~1.1 KB | Yes |
| `pytorch_model.bin` or `model.safetensors` | Model weights (FP32 or FP16) | ~286 MB (safetensors) | Yes |
| `spm.model` | SentencePiece unigram tokenizer model | ~2.4 MB | Yes |
| `tokenizer_config.json` | Tokenizer special tokens and mapping rules | ~52 B | Yes |
| `tokenizer.json` | Fast tokenizer serialized structure | ~8.6 MB | Optional (Fast) |

### Authorized Staging Path:
To authorize and stage these files without violating the project's offline isolation boundaries:
1. Obtain explicit user authorization for out-of-band weight acquisition.
2. Download the minimal snapshot files for `microsoft/deberta-v3-small` into a staging buffer.
3. Compute and commit SHA-256 digests in `/home/aditya/rags/models/pretrained/deberta-v3-small/checksums.sha256`.
4. Restrict file permissions to read-only for training workers.

**Current Operational Status:** Staging has **NOT** been performed in this step. The missing model status is formally documented, and no unapproved weight downloads were executed.
