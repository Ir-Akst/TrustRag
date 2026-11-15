# Track 2, Step 3.3 — Section 06: Training Readiness Assessment & Strategic Projections

## 1. Measured Throughput

- **Average Step Latency (including initialization):** 1,410.6 ms
- **Steady-State Step Latency (Steps 2 & 3):** 1,145.4 ms
- **Steady-State Throughput:** **0.873 samples/second**
- **Hourly Training Capacity (4 CPU threads):** **~3,143 samples/hour**

## 2. Training Feasibility Projections

### Objective A: Binary Classification (`sft_v2/binary`)
- **Total Training Examples:** 26,054
- **Estimated Time per Epoch (CPU, batch size 1, seq_len 128):**
  $$\text{Time} = \frac{26,054 \text{ samples}}{0.873 \text{ samples/sec}} \approx 29,844 \text{ s} \approx 8.29 \text{ hours}$$
- **Verdict:** `CONDITIONALLY_PASSED`.
  - Feasible for small-scale verification pilots, sub-epoch ablation (e.g. 1,000 samples = ~19 minutes), or linear probe tuning.
  - Multi-epoch training (e.g. 3 epochs = ~25 hours) on CPU is computationally inefficient and incurs extended thermal/resource lockup. Cloud/local GPU acceleration is strongly recommended for production training.

### Objective B: NLI 3-Way Classification (`sft_v2/nli`)
- **Total Training Examples:** 23,244
- **Context Length:** Longer premise/hypothesis sequences (typically 192–256 tokens).
- **Estimated Time per Epoch on CPU:** ~12–15 hours.
- **Verdict:** `NOT_READY`. Requires separate 3-class classification head (`num_labels=3`), format verification, and a separate bounded pilot.

### Objective C: Span Extraction (`sft_v2/spans`)
- **Total Training Examples:** 10,780
- **Architecture Requirement:** Token classification (`DebertaV2ForTokenClassification`) rather than sequence classification.
- **G3 Supervision Gap:** The G3 audit established that character-level span annotations in RAGTruth must be mapped to subword token boundaries.
- **Verdict:** `BLOCKED`. Token classification architecture and token-alignment pipeline must be implemented and audited before feasibility testing.

---

## 3. Explicit Prohibitions

1. **NO Full Training:** Full multi-epoch training is NOT authorized.
2. **NO Weight Pushes:** Model weights must remain strictly in local staging.
3. **NO Source Modifications:** Application source code and baseline repositories must remain clean.
