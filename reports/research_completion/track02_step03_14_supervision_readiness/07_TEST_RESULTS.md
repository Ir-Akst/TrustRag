# TrustRAG — Track 2, Step 3.14: Test Suite & Verification Results

### 1. Test Harness Execution

1. **Step 3.14 Readiness Suite ([test_track02_step03_14_supervision_readiness.py](file:///home/aditya/rags/TrustRag-phase11/tests/unit/test_track02_step03_14_supervision_readiness.py)):**
   - Total Tests: 11
   - Passed: 11 (100.0%)
   - Failed: 0
   - Execution Time: 0.03s

2. **Full NLI Runner Test Suite ([test_track02_step03_6_nli_training_runner.py](file:///home/aditya/rags/TrustRag-phase11/tests/unit/test_track02_step03_6_nli_training_runner.py)):**
   - Total Tests: 36
   - Passed: 35
   - Skipped: 1 (guarded model loading)
   - Failed: 0
   - Execution Time: 0.05s

---

### 2. Verified Invariants

- Contradiction label copying to unannotated chunks raises violations / is prevented.
- Unannotated chunks are not assigned naive NEUTRAL labels.
- Oversized hypotheses (>317 tokens) are capped deterministically while preserving min 64 premise tokens.
- Zero document or ID leakage between train and validation.
- Unauthorized training attempts raise `TrainingNotAuthorizedError`.
- Protected checkpoint paths refuse write operations.
