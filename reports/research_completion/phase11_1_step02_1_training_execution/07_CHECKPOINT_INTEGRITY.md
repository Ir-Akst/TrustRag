# TrustRAG — Phase 11.1, Step 2.1: Checkpoint Integrity & Immutability Audit

## 1. Target Checkpoint Verification

| Checkpoint Path | Expected Status | Actual Status | Forensic Notes |
| :--- | :--- | :--- | :--- |
| `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` | Trained 3-epoch NLI model | **DOES NOT EXIST** | Run aborted at Step 325 prior to epoch completion. Atomic serialization was never invoked. |

Because the runner enforces atomic serialization (writing to a temporary directory before renaming upon successful validation), zero partial, malformed, or corrupt model weights were committed to disk.

---

## 2. Protected Baseline Asset Immutability Audit

Every pre-existing reference model and historical checkpoint was independently verified via cryptographic SHA-256 checksumming before and after execution:

| Asset Description | Absolute Path | Target File | SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Base Pretrained DeBERTa-v3** | `/home/aditya/rags/models/pretrained/deberta-v3-small` | `pytorch_model.bin` | `d4b0ebcc7799a2c2dde1a39199cb0ed709f2c6b63a48b8c05133b77955f271a9` | **VERIFIED INTACT** |
| **Binary Classifier (Pilot 1000)** | `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000` | `model.safetensors` | `472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b` | **VERIFIED INTACT** |
| **NLI Classifier (Pilot 1000)** | `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000` | `model.safetensors` | `500832fa1b9b7c67c2c08d9e1f4d4c76d235d15fa9960d76e1e6e81c220a2f8a` | **VERIFIED INTACT** |
| **Remediated NLI Pilot (Step 3.10)**| `/home/aditya/rags/models/trained/deberta-v3-small-nli-remediated` | `model.safetensors` | `bb4c26bab4a147c2ad6bdae7ec8a1ecc56841ea56fc89922fd377fb5d70fe113` | **VERIFIED INTACT** |

---

## 3. Path Security Guard Enforcement

The runner's `PROTECTED_PATHS` registry strictly forbids writes to protected locations:
```python
PROTECTED_PATHS = {
    Path("/home/aditya/rags/models/pretrained/deberta-v3-small").resolve(),
    Path("/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000").resolve(),
    Path("/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000").resolve(),
    Path("/home/aditya/rags/models/trained/deberta-v3-small-nli-remediated").resolve(),
    Path("/home/aditya/rags/TrustRag").resolve(),
}
```
Any execution targeting these locations raises `SecurityViolationError` before any file handle is opened.

