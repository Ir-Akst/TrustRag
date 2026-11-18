# TrustRAG — Track 2, Step 3.10: Training Readiness Assessment

## 1. Verification of Acceptance Criteria

| Acceptance Gate | Remediation Evidence | Compliance Status |
| :--- | :--- | :---: |
| **Exact Class Quotas** | 334 Entailment, 333 Contradiction, 333 Neutral enforced | **SATISFIED** |
| **Seeded Reproducible Shuffle** | `random.Random(seed).shuffle(selected)` implemented & tested | **SATISFIED** |
| **Starvation Prevention** | `check_class_starvation` enforces max absence $\le 25$ | **SATISFIED** |
| **Evidence Preservation** | Hypothesis prioritized; 99.5% retention at 384 tokens | **SATISFIED** |
| **Resource Feasibility** | 550 ms/sample, 1.1 GB RSS, 5.2 GB avail RAM profiled | **SATISFIED** |
| **Test Suite Green** | 28 / 28 unit tests passing across runtimes | **SATISFIED** |
| **Asset Immutability** | Phase 10, binary checkpoint, and Step 3.8 checkpoint untouched | **SATISFIED** |
| **Zero Unauthorized Training** | 0 backward passes, 0 optimizer steps executed | **SATISFIED** |
| **Training Authorization Guard** | Code strictly rejects execution without `--authorize-nli-training` | **SATISFIED** |

---

## 2. Proposed Training Configuration for Step 3.11 (Pending Authorization)

When future training is authorized by the user, the recommended configuration is:
- **Model:** DeBERTa-v3-small (141.9M params, FP32)
- **Task:** Evidence-Grounded 3-Way NLI (`ENTAILMENT=0`, `CONTRADICTION=1`, `NEUTRAL=2`)
- **Dataset:** 1,000 balanced samples (334/333/333) with seed=42 shuffling
- **Context Window:** `max_seq_len = 384` with `evidence_preserving_tokenize`
- **Optimizer:** AdamW (`lr = 2e-5`, `warmup = 100`, `weight_decay = 0.01`, `linear_decay`)
- **Batch Size:** 1 with gradient clipping (1.0)
- **Destination Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-remediated` (distinct from Step 3.8 checkpoint)
- **Watchdogs:** Active (RAM $\ge 700$ MB, swap growth $\le 1000$ MB, timeout 3600s)

---

## 3. Final Verdict

**`REMEDIATION_COMPLETE_READY_FOR_REAUDIT`**

The codebase and pipeline are remediated, tested, profiled, and fully documented.
In accordance with instructions, execution is **STOPPED**. No training has been initiated.
