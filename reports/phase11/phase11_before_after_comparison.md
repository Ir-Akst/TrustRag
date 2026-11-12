# TrustRAG Phase 11 — Before / After Comparison

**Baseline Artifact:** `reports/phase10_experiments/phase10_20261112T073204Z_canonical_v2/bundle.json`  
**Remediated Artifact:** `reports/phase10_experiments/phase10_20261112T085610Z_phase11_remediated/bundle.json` (`seed=42`)

| Metric / Probe | Phase 10 Baseline | Phase 11 Remediated | Delta |
| :--- | :---: | :---: | :---: |
| **G1 Attack vs. Benign Accuracy (`n=6`)** | `0.8333` (`hier_1` missed) | **`1.0000`** | `+0.1667` |
| **G1 Benign FPR (`n=3`)** | `0.0000` | **`0.0000`** | `0.0000` |
| **G1 Paraphrase & Drift Accuracy (`n=6`)** | `0.8333` (`para_eq` rejected) | **`1.0000`** | `+0.1667` |
| **G2 2v1 Same-Source Repetition Trust** | Clean `0.8932` < Poison `0.9056` | **`0.8997 == 0.8997`** | Parity restored |
| **G2 `adversarial_robustness` Adaptive (`n=40`)** | `acc=0.8250`, `ASR=0.3500`, `FPR=0.0000` | **`acc=0.8250`, `ASR=0.3500`, `FPR=0.0000`** | Preserved |
| **G3 Linguistic Suite (`n=25`)** | `25/25` (`1.0000`), `0` false support | **`25/25` (`1.0000`), `0` false support** | Preserved |
| **G3 Unseen Numeric/Temporal Accuracy (`n=4`)** | `0.5000` (`2/4`) | **`1.0000` (`4/4`)** | `+0.5000` |
| **G3 Unseen False-Supported Rate** | `0.0000` | **`0.0000`** | `0.0000` |
| **Clean RAG Retention (`n=15`)** | `1.0000` (`0.0000` FPR) | **`1.0000` (`0.0000` FPR)** | `0.0000` |

