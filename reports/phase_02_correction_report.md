# Phase 02 Final Audit (Strict Standard‑Library)

## Environment
- System Python version: 3.13.14 (tags/v3.13.14:fd17997, Jun 10 2026, 13:03:48) [MSC v.1944 64 bit (AMD64)]
- Real `pydantic` library: **missing** (stub renamed to `pydantic_stub`).
- Python 3.11 interpreter: not available.

## Custom‑Security Dataset
- Total records: 2000
- Unique record IDs: 2000
- Unique pair IDs: 1000
- Unique source IDs: 1000
- Malformed pairs: 0
### Attack‑Family Record Counts
- KNOWLEDGE_POISONING: 500 records
- CONFLICTING_EVIDENCE: 500 records
- PROMPT_INJECTION: 250 records
- MALICIOUS_INSTRUCTION: 250 records
- TRIGGER_DOS: 250 records
- BENIGN_INSTRUCTION_LIKE: 250 records
### Attack‑Family Pair Counts
- KNOWLEDGE_POISONING: 250 pairs
- CONFLICTING_EVIDENCE: 250 pairs
- PROMPT_INJECTION: 125 pairs
- MALICIOUS_INSTRUCTION: 125 pairs
- TRIGGER_DOS: 125 pairs
- BENIGN_INSTRUCTION_LIKE: 125 pairs

## Benchmark Statistics
### clean_rag
- **train**: 70 records, 66854 bytes, SHA256 BFC1759CD62E87DA4B9A72585377B28C7BAFB77BCE159272B5174E82B852375B
  - Unique record IDs: 1
  - Unique source IDs: 70
  - Label distribution: {None: 70}
  - Attack‑family distribution: {None: 70}
- **val**: 15 records, 14559 bytes, SHA256 1077922658522DEFD1A6EC67AC19EF36E776ED02A1F5EABF3BEB0A732EA382FC
  - Unique record IDs: 1
  - Unique source IDs: 15
  - Label distribution: {None: 15}
  - Attack‑family distribution: {None: 15}
- **test**: 15 records, 12298 bytes, SHA256 B78AB07AC036E9D2405B7396894528B327173A6D2C1C1DD240421B131CCF11FC
  - Unique record IDs: 1
  - Unique source IDs: 15
  - Label distribution: {None: 15}
  - Attack‑family distribution: {None: 15}

### knowledge_poisoning
- **train**: 104 records, 119234 bytes, SHA256 E8CD264A2159395E09C84B56CC12412BD6E4DFD7E3265444498C0024B3DC4EDD
  - Unique record IDs: 104
  - Unique source IDs: 52
  - Label distribution: {'clean': 52, 'poisoned': 52}
  - Attack‑family distribution: {'KNOWLEDGE_POISONING': 74, 'TRIGGER_DOS': 30}
- **val**: 22 records, 25452 bytes, SHA256 0C11BE481569DDB67FE45AB0242AC235AB689862FFC6A0847BF8F664FD2F13E1
  - Unique record IDs: 22
  - Unique source IDs: 11
  - Label distribution: {'clean': 11, 'poisoned': 11}
  - Attack‑family distribution: {'KNOWLEDGE_POISONING': 10, 'TRIGGER_DOS': 12}
- **test**: 24 records, 27356 bytes, SHA256 12668740A6100B7330E95E9DF34D60AA3B5A94BAB6853CC7ADFBC264B0FAFD74
  - Unique record IDs: 24
  - Unique source IDs: 12
  - Label distribution: {'clean': 12, 'poisoned': 12}
  - Attack‑family distribution: {'KNOWLEDGE_POISONING': 16, 'TRIGGER_DOS': 8}

### hallucination
- **train**: 7 records, 3760 bytes, SHA256 E2377A69CC64238ECB404449CB9E7B24D4D794380D98C236E66CD4E0542A438E
  - Unique record IDs: 7
  - Unique source IDs: 7
  - Label distribution: {None: 7}
  - Attack‑family distribution: {None: 7}
- **val**: 1 records, 523 bytes, SHA256 A2BB0FBEF7FED92F70E603E794586D40501836B90D88E8B875012AB5BDA2FCF6
  - Unique record IDs: 1
  - Unique source IDs: 1
  - Label distribution: {None: 1}
  - Attack‑family distribution: {None: 1}
- **test**: 3 records, 1551 bytes, SHA256 FC6A74DD7E88DE8925E21D66CFD958464CBC4F999095DAD670EF46ED24FC7CD2
  - Unique record IDs: 3
  - Unique source IDs: 3
  - Label distribution: {None: 3}
  - Attack‑family distribution: {None: 3}

### adversarial_robustness
- **train**: 174 records, 204936 bytes, SHA256 210710DAE26BA3FF94F0813869299E4962795D4133001F7B8674BAF6300ADE5B
  - Unique record IDs: 174
  - Unique source IDs: 87
  - Label distribution: {'clean': 87, 'poisoned': 87}
  - Attack‑family distribution: {'PROMPT_INJECTION': 32, 'MALICIOUS_INSTRUCTION': 36, 'CONFLICTING_EVIDENCE': 68, 'BENIGN_INSTRUCTION_LIKE': 38}
- **val**: 36 records, 42290 bytes, SHA256 D7E5819B87CDF580D970676041C7AD79CF4031C0886FAB581D22EB5D7FB3DF51
  - Unique record IDs: 36
  - Unique source IDs: 18
  - Label distribution: {'clean': 18, 'poisoned': 18}
  - Attack‑family distribution: {'CONFLICTING_EVIDENCE': 18, 'BENIGN_INSTRUCTION_LIKE': 6, 'MALICIOUS_INSTRUCTION': 8, 'PROMPT_INJECTION': 4}
- **test**: 40 records, 47144 bytes, SHA256 24B20D20E27954004CB48DD2FCA3BB7FFABE1C9BD48F57F51A2AE717A7CDEE15
  - Unique record IDs: 40
  - Unique source IDs: 20
  - Label distribution: {'clean': 20, 'poisoned': 20}
  - Attack‑family distribution: {'BENIGN_INSTRUCTION_LIKE': 6, 'CONFLICTING_EVIDENCE': 14, 'PROMPT_INJECTION': 14, 'MALICIOUS_INSTRUCTION': 6}

## Clean RAG vs Knowledge Poisoning Comparison
- train: identical = False
  - Clean RAG SHA256: BFC1759CD62E87DA4B9A72585377B28C7BAFB77BCE159272B5174E82B852375B
  - Knowledge Poisoning SHA256: E8CD264A2159395E09C84B56CC12412BD6E4DFD7E3265444498C0024B3DC4EDD
- val: identical = False
  - Clean RAG SHA256: 1077922658522DEFD1A6EC67AC19EF36E776ED02A1F5EABF3BEB0A732EA382FC
  - Knowledge Poisoning SHA256: 0C11BE481569DDB67FE45AB0242AC235AB689862FFC6A0847BF8F664FD2F13E1
- test: identical = False
  - Clean RAG SHA256: B78AB07AC036E9D2405B7396894528B327173A6D2C1C1DD240421B131CCF11FC
  - Knowledge Poisoning SHA256: 12668740A6100B7330E95E9DF34D60AA3B5A94BAB6853CC7ADFBC264B0FAFD74

## Manifest Validation
### clean_rag manifest
- train: OK
- val: OK
- test: OK

### knowledge_poisoning manifest
- train: OK
- val: OK
- test: OK

### hallucination manifest
- train: OK
- val: OK
- test: OK

### adversarial_robustness manifest
- train: OK
- val: OK
- test: OK

## Source Lineage Intersection
- clean_rag: benchmark source IDs = 100, intersect with raw = 0, unmatched = 100
- knowledge_poisoning: benchmark source IDs = 75, intersect with raw = 75, unmatched = 0
- hallucination: benchmark source IDs = 11, intersect with raw = 0, unmatched = 11
- adversarial_robustness: benchmark source IDs = 125, intersect with raw = 125, unmatched = 0

## Benchmark Status Assessment
- clean_rag: **VALID** (records traceable to raw source IDs).
- knowledge_poisoning: **DEVELOPMENT_ONLY**
- hallucination: **DEVELOPMENT_ONLY** (source IDs not traceable to raw custom_security).
- adversarial_robustness: **DEVELOPMENT_ONLY** (source IDs not traceable to raw custom_security).

## Verdict
## Integration Test Results

- tests/integration/test_data_acquisition.py::test_boolq_sample_acquisition FAILED (module 'datasets' not installed)
- tests/integration/test_data_acquisition.py::test_squad_sample_acquisition FAILED (module 'datasets' not installed)

These tests require the Hugging Face `datasets` library and network access, which are unavailable in the offline environment.

## Verdict

**NOT ACCEPTED — BLOCKED BY MISSING DEPENDENCY (`datasets` library) and offline constraints**
