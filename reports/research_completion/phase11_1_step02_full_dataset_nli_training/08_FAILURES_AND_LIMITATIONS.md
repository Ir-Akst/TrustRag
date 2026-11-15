# TrustRAG — Phase 11.1, Step 2: Full-Dataset NLI Training Audit
## 08 — Failures, Limitations & Remediation Plan (Step 2.1)

- **Audit Date:** 2026-11-14T18:25:00Z
- **Auditor:** Senior ML Training Engineer & Independent Experimental Auditor

---

### 1. Root Cause Breakdown of Preflight Blockage

The authorized 3-epoch full-dataset training run could not safely proceed due to three intersecting constraints:

1. **Sampler Quota Incompatibility:**  
   The training harness enforces equal 1:1:1 stratified class-balanced sampling (`targets = max_samples // 3`), requiring 3,605 Contradiction examples for a 10,815 run. However, the raw training split contains only 1,420 Contradiction examples, triggering an unhandled exception before step 1.
2. **Double-Compensation Methodological Risk:**  
   Applying class weights `[1.0, 3.5, 1.5]` on top of a 1:1:1 balanced sampler inflates the effective gradient weight of Contradiction by $8.89\times$ over its natural frequency, severely biasing the model against Entailment.
3. **Runtime & Watchdog Mismatch:**  
   Processing 32,445 forward-backward passes on the 10-core CPU requires ~25.1 hours (90,400 seconds). The runner's watchdog defaults to 3,600s, and the Step 3.15.2 maximum is 36,000s. The runner would have been automatically terminated mid-run by the watchdog monitor.
4. **Harness Capability Deficits:**  
   The script lacked gradient accumulation, multi-epoch looping, best-model selection, and per-sample JSONL serialization.

---

### 2. Remediation Plan: Phase 11.1, Step 2.1 (Harness & Sampler Update)

To unblock the authorized full-dataset run, a narrowly scoped engineering remediation (Step 2.1) is required before training can execute:

1. **Implement Sampling Strategy Selection via CLI:**
   - Add `--sampler-strategy {stratified_class_balanced, frequency_weighted_sequential}` to `train_nli_classifier.py`.
   - When training on the full 10,815 dataset, use `frequency_weighted_sequential` (natural distribution) paired with class-weighted cross-entropy loss `[1.0, 3.5, 1.5]`.
   - This eliminates the quota crash and applies the desired $3.5\times$ penalty to Contradiction without double-compensation.
2. **Implement Gradient Accumulation & Multi-Epoch Support:**
   - Add `--epochs 3` and `--gradient-accumulation-steps 4` to achieve the authorized effective batch size of 4 over ~8,111 optimizer steps.
3. **Implement Per-Sample Prediction Serialization:**
   - Update `evaluate()` to dump `predictions_val.jsonl` containing sample IDs, true labels, predicted logits, and probability triples.
4. **Extend Watchdog Limit or Enable GPU:**
   - For CPU execution: Formally authorize `--max-duration-seconds 100000` (~27.8 hours).
   - *Alternative (Strongly Recommended):* Provide access to a GPU environment to reduce total execution time from 25.1 hours to ~45–75 minutes.

Once Step 2.1 is implemented and audited, the authorized Step 2 full-dataset training run can execute cleanly.

