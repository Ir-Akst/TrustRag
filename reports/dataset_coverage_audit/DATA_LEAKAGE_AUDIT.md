# TrustRAG — Data Leakage, Split Integrity & Calibration Audit

**Audit Date:** 2026-11-12  
**Verification Method:** Independent read-only forensic inspection of all `.jsonl` partitions, `manifest.json`, `quality_report.json`, `split_report.json`, calibration artifacts, and splitting source code across both **Current Working Tree** (`data/`) and **`1eeb831`** (`data/benchmarks_backup/`, `data/raw/`, `data/processed/`).

---

## 1. Summary of Data Leakage & Split Integrity Findings

> **Overall Leakage Verdict:** **FAIL (Multiple Severe Split, Template, & Cross-Dataset Leakage Defects Detected)**

Although `LeakageResistantSplitter` (`1eeb831:src/trustrag/data/splitting.py`) and `TrustCalibrator._assert_non_test_splits` ([calibration.py](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/adaptive/calibration.py)) enforced hash-level `record_id`/`source_id` partitioning and `"test"`-name blocking correctly in code, actual benchmark construction suffered **5 severe empirical leakage & duplication defects**:

| # | Defect Type | Affected Datasets / Artifacts | Exact Quantitative Evidence | Severity | Impact |
|---|---|---|---|---|---|
| **L1** | **Within-Split Exact Duplicate Records** | [data/benchmarks/adversarial_robustness/](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/adversarial_robustness/train.jsonl) (WT & `1eeb831`) | `10 / 30` records duplicated (**`33.33%`**): **`8/22` (`36.4%`)** in `train.jsonl` (`sec_pair_0002`, `0003`, `0006`, `0007` clean+poison x2) and **`2/4` (`50.0%`)** in `val.jsonl` (`sec_pair_0004` clean+poison x2) | **HIGH** | Inflates effective sample weights on repeated items during eval/val |
| **L2** | **100% Query-Group Leakage Across `train`/`val`/`test`** | `knowledge_poisoning` & `adversarial_robustness` (both WT `data/benchmarks/` and `1eeb831:data/benchmarks_backup/`) | Security splitting grouped by `source_id` (`pair_id`), NOT `target_query`. **`1eeb831:backup/knowledge_poisoning`:** Only `3` unique queries across all `150` rows — **`3/3` (`100%`) query overlap** `train ∩ val`, `train ∩ test`, `val ∩ test`. **`1eeb831:backup/adversarial_robustness`:** Only `5` unique queries across `250` rows — **`5/5` (`100%`) query overlap** across splits. **WT `knowledge_poisoning` & `adversarial_robustness`:** **`2/2` (`100%`)** test queries appear in `train`! | **CRITICAL** | Any detector/calibrator/ML-FilterRAG fitted on `train` evaluates on the exact same `target_query` strings in `test` |
| **L3** | **Near-Duplicate Template Leakage (`>= 0.85` Jaccard)** | `custom_security` -> `knowledge_poisoning` & `adversarial_robustness` (WT & `1eeb831`) | `security_generator.py` generated all records from `8` static `_TEMPLATES` varying only `[Topic - Item N]`. Pairwise token Jaccard >= `0.85` between `train` and `test` affects **`104/104` train rows** (`backup kp`), **`174/174` train rows** (`backup adv`), and **`4/4` test rows** (`WT kp` & `adv`)! Plus `1eeb831:raw/custom_security/raw_train.jsonl` has **`24/24` + `40/40` (`100%`) exact passage overlap** with `backup/test`. | **CRITICAL** | Zero held-out lexical generalization: `train`, `val`, and `test` contain near-identical template sentences |
| **L4** | **Cross-Dataset BoolQ / Calibrator Contamination (`70/100`)** | [boolq/validation.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/processed/boolq/validation.jsonl), `clean_rag`, `platt_calibrator_v1`, Phase 05/06 evals | `boolq/validation.jsonl` (`100` rows) is the exact disjoint union of `1eeb831:benchmarks_backup/clean_rag/{train(70), val(15), test(15)}` (`0` overlap among train/val/test themselves, **`70 + 15 + 15 = 100` exact overlap** with `boolq/validation.jsonl`). WT `clean_rag/{train(7), val(1), test(2)}` is also an exact `10/10` subset. | **HIGH** | Phase 05–06 evaluations running on `boolq/validation.jsonl (N=100)` with `platt_calibrator_v1` evaluated on **70% in-sample calibration training data**. *(Phases 07–08 fixed query split by using `clean_rag/test n=15`, though the `N=100` distractor corpus still included the `70` train passages.)* |
| **L5** | **`raw/ragtruth/test` Split Into `hallucination/train+val`** | `hallucination` & `1eeb831:data/raw/ragtruth/test.jsonl` | All `5` records of `raw/ragtruth/test.jsonl` were split `4` -> [hallucination/train.jsonl](file:///c:/Users/Dell/Desktop/trustrag/data/benchmarks/hallucination/train.jsonl) and `1` -> `val.jsonl`, leaving **`0` `ragtruth` rows in `test.jsonl`** (`test` has `1` `wice` + `2` `expertqa`). | **MEDIUM** | Subsequent Phase 06–08 runs on `raw/ragtruth/test.jsonl (n=5)` overlapped `5/5` (`100%`) with `hallucination/train+val` |

---

## 2. Automated Cross-Split Verification Table (Exact Measurements)

Computed directly via SHA-256 content hashes, normalized query/doc/claim exact intersection, and token Jaccard `>= 0.85` near-duplicate scan:

### 2.1 Current Working Tree (`data/`)

| Dataset / Partition Pair | Exact `(q,d,c)` Overlap | `target_query` / `query` Overlap | Passage / Doc Overlap | `source_id` Overlap | Near-Dup Docs (`Jaccard >= 0.85`) | Within-Split Exact Dups |
|---|---:|---:|---:|---:|---:|---:|
| `clean_rag` `train(7)` vs `val(1)` / `test(2)` | `0` / `0` | `0` / `0` | `0` / `0` | `0` / `0` | `0` / `0` | `0` |
| `clean_rag` `train+val+test(10)` vs `boolq/validation(100)` | **`10`** (`100%`) | **`10`** (`100%`) | **`10`** (`100%`) | **`10`** | `0` | `0` |
| `knowledge_poisoning` `train(14)` vs `val(2)` | `0` | `0/7` vs `0/1` | `0` | `0` | `0` | `0` |
| `knowledge_poisoning` `train(14)` vs `test(4)` | `0` | **`2/2` (`100%` of test)** | `0` | `0` | **`4/4` test docs** | `0` |
| `adversarial_robustness` `train(22)` vs `test(4)` | `0` | **`2/2` (`100%` of test)** | `0` | `0` | **`4/4` test docs** | **`8/22 train + 2/4 val`** |
| `hallucination` `train(7)` vs `val(1)` / `test(3)` | `0` / `0` | N/A | `0` / `0` | `0` / `0` | `0` / `0` | `0` |

### 2.2 Pre-Minimization Backup & Raw (`1eeb831:data/`)

| Dataset / Partition Pair | Exact `(q,d,c)` Overlap | Query Overlap | Doc Overlap | `source_id` Overlap | Near-Dup Docs (`Jaccard >= 0.85`) | Label Integrity Status |
|---|---:|---:|---:|---:|---:|---|
| `backup/clean_rag` `train(70)` / `val(15)` / `test(15)` | `0` (`0` pair overlaps) | `0` | `0` | `0` | `0` | Clean (`yes/no`), `0` dups |
| `backup/clean_rag (100)` vs `boolq/validation(100)` | **`100`** (`100%`) | **`100`** | **`100`** | **`100`** | — | Exact 1:1 partition |
| `backup/knowledge_poisoning` `train(104)` vs `test(24)` | `0` | **`3/3` (`100%`)** | `0` | `0` | **`104/104` train docs** | `50/50` clean/poison (`KNOWLEDGE_POISONING` + `TRIGGER_DOS`) |
| `backup/adversarial_robustness` `train(174)` vs `test(40)` | `0` | **`5/5` (`100%`)** | `0` | `0` | **`174/174` train docs** | **Corrupted label semantics:** `BENIGN_INSTRUCTION_LIKE` has `clean_poison_label="poisoned"` on 50% of controls |
| `backup/{kp,adv}/test` (`64`) vs `raw/custom_security/raw_train` (`2,000`) | **`64`** (`100%`) | **`8/8`** | **`64`** (`100%`) | `32` pairs | — | `raw_train` is a strict superset containing all test items |

---

## 3. Preprocessing, Calibration & Label Semantics Integrity

1. **Preprocessing Leak Check:** `cleaning.py` (`NFKC`, whitespace collapse), `text_utils.py` (Unicode scan & normalization), and `TfidfVectorizer` inside `TrustAwareRetriever`/`OutputEvidenceVerifier` do **not** fit corpus-wide parameters during `train` and leak across splits; `boolq/validation.jsonl` was preprocessed identically per-record. **PASS** for preprocessing leakage.
2. **Threshold & Calibrator Fitting Separation:** Both [platt_calibrator_v1.json](file:///c:/Users/Dell/Desktop/trustrag/configs/adaptive/platt_calibrator_v1.json) (`sample_count=428`, `fit_seed=42`) and [temperature_calibrator_v1.json](file:///c:/Users/Dell/Desktop/trustrag/configs/adaptive/temperature_calibrator_v1.json) (`sample_count=478`, `fit_seed=42`) verified `fitted_splits = ["train"]`, enforced programmatically by `_assert_non_test_splits` and `CalibrationArtifact.validate_splits`. Threshold tuning in Phase 08 FilterRAG (`eps=0.70`) ran strictly on `val` (`n=58`). **PASS** on split-label enforcement, **FAIL** on template/query leakage between `train` and `test` security splits and **INCONSISTENCY** in WT where `clean_rag/train` shrunk to `7` rows while `platt/temp` artifacts remain parametrized from deleted `backups` (`n=428`/`478`).
3. **Label Semantics Defect (`BENIGN_INSTRUCTION_LIKE`):** In `adversarial_robustness`, `security_generator.py` stamped `clean_poison_label="poisoned"` on generated counterpart rows even when `attack_family == "BENIGN_INSTRUCTION_LIKE"` (`metadata.expected_security_outcome == "permit_legitimate_procedural_content"`). Downstream [calibration.py](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/adaptive/calibration.py#L342-L345) works around this via `is_atk = 1 if (lbl == "poisoned" and fam != "BENIGN_INSTRUCTION_LIKE") else 0`, meaning any external evaluator reading raw `clean_poison_label` directly mislabels benign sourdough/procedural controls as attacks.
4. **Seeds Recorded:** Deterministic `seed=42` is consistently recorded across manifests, calibration JSONs, `configs/base.yaml`, and Phase 04–08 evaluation JSONs.

