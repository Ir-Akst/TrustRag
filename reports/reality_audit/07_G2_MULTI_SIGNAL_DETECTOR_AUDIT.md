# 07 — G2 Multi-Signal Detector (MSD) Audit

**Module:** [msd.py](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/detection/msd.py)
**Verdict:** `YELLOW` (**Readiness: `52%`**)

---

## 1. Signal Architecture Reality (4/6 Active Offline)

G2 defines six detection signals (`F1`–`F6`) combined via coverage-attenuated weighted fusion:

| Signal | Intended Role | Offline Status | Observed Effective Weight (`4` signals active) | Dependency / Gap |
| :--- | :--- | :---: | :---: | :--- |
| **`F1` Perplexity Anomaly** | Neural LM surprisal/perplexity (`Qwen` / causal LM) | **`UNAVAILABLE`** | `0.0000` | Requires external `perplexity_fn` callable & clean reference mean/std |
| **`F2` Embedding Norm** | Dense latent outlier L2 norm / Mahalanobis | **`UNAVAILABLE`** | `0.0000` | Requires external `embedding_fn` callable & centroid stats |
| **`F3` Query Match** | Lexical / TF-IDF query-document match | `AVAILABLE` | `0.9091` (`0.7636` w/o `F6`) | Rewards keyword stuffing (poisoners optimize `F3` upward) |
| **`F4` Instruction Content** | Imperative / override regex scanner | `AVAILABLE` | `1.5152` (`1.2727` w/o `F6`) | Primary signal carrying offline detection |
| **`F5` Consensus Deviation** | Cross-passage agreement / outlier check | `AVAILABLE` | `0.7576` (`0.6364` w/o `F6`) | Defeated by 3v1 coordinated duplicates (`spam_1..3`) |
| **`F6` Provenance Prior** | Metadata `source` / `trust_tier` / `verified` prior | `AVAILABLE` (`UNKNOWN` if omitted) | `0.6061` (`0.0` if missing) | Unverified/blog priors alone cannot flag stealth falsehoods |

Phase 10 ablation telemetry (`phase10_remediated`) directly confirms **`F1`/`F2`/`F3` have zero standalone discriminative delta offline**: `full_g2_uncalibrated`, `without_F1_perplexity`, `without_F2_embedding_norm`, and `without_F3_query_match` all produce identical metrics (`F1 = 0.6512`, `FPR = 0.0`, `accuracy = 0.7656`), whereas removing `F4` collapses F1 to `0.5507` (`FPR = 0.60`, `ROC AUC = 0.5315`) and removing `F6` raises FPR to `0.2571` (`accuracy = 0.6250`).

---

## 2. Live Probe Evidence (`part2_subsystems.json`)

### A. Offline Document Probes (`latency = 5.546 ms`)
| Document | Content Profile | Avail Signals | Trust Score | Decision | Vulnerability Exposed |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `c1` | Clean NIST-like factual doc (`verified`) | `4` (`F3..F6`) | `0.9640` | `CLEAN` | — |
| `c2` | Clean secondary factual doc | `4` | `0.9559` | `CLEAN` | — |
| `p_instr` | Explicit instruction override trigger, no meta | `3` | `0.4841` | `POISONED` | Caught solely by `F4=0.10` |
| `p_out` | **Stealth factual poison (`"500 C"`, `blog`, no trigger)** | **`4`** | **`0.9283`** | **`CLEAN`** | **`F4=1.0`, `F5=0.95` blind to factual contradiction; `F6=0.3` insufficient** |
| `no_meta` | Clean passage without provenance metadata | `3` (`F6=UNKNOWN`) | `0.9133` | `CLEAN` | Coverage attenuation avoids false positive |

### B. 3v1 Repetition Attack Probe (`clean_ind` vs `spam_1`, `spam_2`, `spam_3`)
- `clean_ind`: `trust = 0.7846` (`CLEAN`)
- `spam_1`, `spam_2`, `spam_3` (identical poisoned claim repeated 3 times): **all 3 scored `0.7834` (`CLEAN`)**—barely `0.0012` below `clean_ind`, failing to quarantine duplicate poison rings.
- *Positive check:* All-poison corpus (`K=4`) with explicit triggers enforced `removal_cap_limit = 2` (`2` removed, `2` capped-retained).
- *With external perplexity callable + `platt_calibrator_v1.json`:* `c1 -> 1.0000`, `c2 -> 0.9999`, `p_instr -> 0.0275` (`POISONED`), proving the mathematical fusion/calibration interface functions when signals are actually fed.

