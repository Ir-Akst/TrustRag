# TrustRAG Phase 11 — G2 MSD Consensus & Key Remediation (`DEF-02`, `DEF-07`)

## 1. DEF-02: F5 Same-Source & Duplicate Consensus Manipulation
- **Original Behavior:** Repeating poisoned `"Golden City"` twice from `source_id="s2"` against clean `"Birnin Zana"` (`s1`) gave poisoned passages higher trust (`0.9056` vs `0.8932`).
- **Root Cause:** (1) `evaluate_consensus_deviation_signals()` in `src/trustrag/detection/signals.py` counted raw peer documents without deduplicating by `(source_key, content_sig)`. (2) `MultiSignalDetector._compute_standalone_similarities()` in `src/trustrag/detection/msd.py` computed TF-IDF IDF over duplicate passages, lowering IDF for repeated poisoned terms and inflating their `query_match` (`0.7722` vs `0.6824`).
- **Fix:** Deduplicated agreeing peers by `(_effective_source_key, _norm_content_sig)` and conflicting peers by `_effective_source_key` (with ordering invariance), and deduplicated normalized texts before TF-IDF fitting in `_compute_standalone_similarities()`.
- **Before / After:** `2v1` repetition scores: `[0.8932, 0.9056, 0.9056]` -> **`[0.8997, 0.8997, 0.8997]`** (exact parity, order-invariant). `adversarial_robustness` adaptive `acc=0.8250`, `ASR=0.3500`, `FPR=0.0000` preserved.

## 2. DEF-07: F6 Canonical Signal Key Alignment
- **Original Behavior:** `phase10_runner.py` queried `"provenance_prior"` while `msd.py` emits `"provenance"`.
- **Fix:** Updated `phase10_runner.py` to use canonical `"provenance"` and added schema assertion in `test_phase_11_remediation.py`.
