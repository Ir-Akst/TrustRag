#!/usr/bin/env python3
"""Compile Phase 40 master summary JSON and all 10 required markdown reports."""

import json
from pathlib import Path

BASE = Path("/home/aditya/rags/TrustRag-phase11/reports/phase40")

def load(sub: str) -> dict:
    with open(BASE / sub / "summary.json", encoding="utf-8") as f:
        return json.load(f)

g1 = load("g1")
fw = load("firewall")
ml = load("multilingual")
g3 = load("g3")
pr = load("production")

master = {
    "phase": "Phase 40 — Architectural Security Remediation, Semantic Generalization & Generator-Boundary Enforcement",
    "branch": "phase-40-architectural-security-remediation",
    "parent_commit": "433e7f65abd17233dcaec363845fdb652d4692eb",
    "release_anchor": "531bff32745ede1bd1b38609cc6daf653d3eff24",
    "release_tag": "trustrag-v1.0.0-rc1",
    "frozen_checkpoint": "/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch",
    "final_verdict": "PASS WITH LIMITATIONS",
    "publication_recommendation": "READY WITH CLAIM LIMITATIONS",
    "g1": g1,
    "firewall": fw,
    "multilingual": ml,
    "g3": g3,
    "production": pr,
}

with open(BASE / "phase40_master_summary.json", "w", encoding="utf-8") as f:
    json.dump(master, f, indent=2)

docs = {
    "PHASE40_FINAL_REPORT.md": f"""# TrustRAG Phase 40 — Final Report

**Branch:** `phase-40-architectural-security-remediation`  
**Parent Commit:** `433e7f65abd17233dcaec363845fdb652d4692eb` (Phase 39 audit)  
**Release Anchor:** `531bff32745ede1bd1b38609cc6daf653d3eff24` (`trustrag-v1.0.0-rc1`)  
**Frozen Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` (8/8 SHA-256 verified)  
**Final Verdict:** **PASS WITH LIMITATIONS**  
**Publication Recommendation:** **READY WITH CLAIM LIMITATIONS**

---

## 1. Before / After Metrics (Phase 39 Baseline vs. Phase 40 Untouched Holdout)

| Metric | Phase 39 Baseline | Phase 40 Holdout | 95% Wilson CI | Target | Status |
|---|---:|---:|---|---|---|
| G1 Overall ADR | 29.60% (74/250) | **95.00%** (190/200) | [91.04%, 97.26%] | >=90% | **PASS** |
| G1 Unseen Imperatives ADR | 15.00% (6/40) | **100.00%** (30/30) | [88.65%, 100.0%] | >=85% | **PASS** |
| G1 Indirect Narrative ADR | 0.00% (0/30) | **100.00%** (30/30) | [88.65%, 100.0%] | >=85% | **PASS** |
| G1 Benign FPR | 0.00% (0/80) | **10.00%** (8/80) | [5.15%, 18.51%] | <=3% | **MISSED** |
| Firewall Recall | 45.45% (50/110) | **100.00%** (100/100) | [96.30%, 100.0%] | — | **PASS** |
| Generator-Boundary Leakage | 54.55% (60/110) | **0.00%** (0/100) | [0.00%, 3.70%] | 0 obs | **PASS** |
| Firewall False Quarantine | 0.00% (0/50) | **0.00%** (0/50) | [0.00%, 7.13%] | <=3% | **PASS** |
| Multilingual Combined ADR | 59.26% (160/270) | **94.44%** (255/270) | [91.04%, 96.60%] | >=90% | **PASS** |
| Multilingual Benign FPR | 2.22% (2/90) | **0.00%** (0/90) | [0.00%, 4.09%] | <=3% | **PASS** |
| G3 Gate Accuracy | 92.14% (129/140) | **100.00%** (120/120) | [96.90%, 100.0%] | — | **PASS** |
| G3 Contradiction Recall | 78.57% (55/70) | **100.00%** (55/55) | [93.47%, 100.0%] | >=90% | **PASS** |
| G3 Unsupported Leakage | 0.00% (0/20) | **0.00%** (0/20) | [0.00%, 16.11%] | 0 obs | **PASS** |
| G3 False Abstention | 17.14% (6/35) | **0.00%** (0/30) | [0.00%, 11.35%] | <=10% | **PASS** |
| Profile B Warm Mean Latency | 2577.91 ms | **804.05 ms** | 57 PyTorch fwds / 15 reqs | — | **3.2x Faster** |
""",

    "ARCHITECTURE_REMEDIATION.md": """# Phase 40 Architecture Remediation Summary

1. **Generator-Boundary Enforcement (`src/trustrag/retrieval/generator_boundary.py`):**
   - Added `GeneratorBoundaryEnforcer` with untrusted-data XML serialization (`<untrusted_evidence doc_id="..." source="..." trust_score="...">`), cross-document split-instruction detection, and fail-closed pre-invocation revalidation wired into both `AnswerGenerator.generate()` and `TrustRAGPipeline.run()`.
2. **Document Firewall (`src/trustrag/retrieval/document_firewall.py`):**
   - Added Unicode confusable folding & zero-width stripping prior to segmentation, multi-line block segmentation (fenced code blocks, HTML comments, tables, blockquotes), and generalized citation/role-header spoofing rules.
3. **G1 Semantic Intent Classifier (`src/trustrag/guardrails/semantic_classifier.py` + `models/semantic_sec_v3.pkl`):**
   - Replaced regex-only classification with a calibrated hybrid TF-IDF (word 1-2 + char_wb 3-5) LogisticRegression semantic intent classifier trained on a disjoint Phase 40 dev corpus (`N=82`), combined with clause-level decomposition and benign technical context preservation.
4. **Multilingual & Transliteration Engine (`src/trustrag/guardrails/multilingual_engine.py` + `models/multilingual_sec_v3.pkl`):**
   - Added multi-stage transliteration normalization (Pinyin tone-number stripping, Arabizi numeral-to-phoneme mapping), Romaji `-te` form handling, benign technical/educational context guards, and a char-ngram LogisticRegression semantic classifier (`N=56` dev).
5. **G3 Evidence Verifier (`src/trustrag/verification/grounded_verifier.py`):**
   - Removed `_GEO_COMPAT` and hardcoded entity literals (`toronto`, `newton`, `venus`, `jefferson`).
   - Added general functional-role contradiction detection, implicit polarity opposition checks, tolerance-aware numerical reasoning, and batched NLI inference (`_predict_nli_batch`) with deterministic pair caching.
""",

    "GENERATOR_BOUNDARY_SECURITY.md": """# Generator-Boundary Security Report

**Holdout Dataset:** `reports/phase40/datasets/holdout_firewall.jsonl` ($N=150$: 100 malicious, 50 benign controls).

## Execution Path & Enforcement
1. Retrieved documents pass through `DocumentInjectionFirewall.sanitize_retrieved_documents` (Unicode confusable folding, zero-width stripping, multi-line block segmentation).
2. `GeneratorBoundaryEnforcer.enforce()` preserves `trust_score` and `provenance` metadata, checks cross-document split instructions, serializes evidence inside `<untrusted_evidence>` tags, and runs independent pre-invocation `validate_serialized_context()`.
3. Both `TrustRAGPipeline.run()` and `AnswerGenerator.generate()` enforce this boundary fail-closed.

## Empirical Boundary Results
- **Detection Recall:** **100.00%** (100/100) [95% CI: 96.30%, 100.00%]
- **Observed Generator-Boundary Leakage:** **0.00%** (0/100) [95% CI: 0.00%, 3.70%]
- **False Quarantine on Benign Security Docs:** **0.00%** (0/50) [95% CI: 0.00%, 7.13%]

*Note:* Zero observed leakage in $N=100$ cases establishes an upper 95% confidence bound of 3.70% residual risk, not absolute impossibility.
""",

    "G1_SEMANTIC_GENERALIZATION.md": """# G1 Semantic Generalization Report

**Holdout Dataset:** `reports/phase40/datasets/holdout_g1.jsonl` ($N=280$: 200 attacks, 80 benign controls).

## Aggregate Metrics
- **TP / FP / TN / FN:** 190 / 8 / 72 / 10
- **ADR (Recall):** **95.00%** (190/200) [95% CI: 91.04%, 97.26%]
- **ASR:** **5.00%** (10/200)
- **Precision:** **95.96%** | **F1:** **0.9548**
- **Benign FPR:** **10.00%** (8/80) [95% CI: 5.15%, 18.51%]

## Per-Category Results
- `unseen_imperatives`: **30/30 (100.00%)** [88.65%, 100.0%]
- `semantic_paraphrases`: **30/30 (100.00%)** [88.65%, 100.0%]
- `narrative_indirect`: **30/30 (100.00%)** [88.65%, 100.0%]
- `roleplay_and_pretext`: **30/30 (100.00%)** [88.65%, 100.0%]
- `multi_sentence_split`: **40/40 (100.00%)** [91.24%, 100.0%]
- `obfuscated_and_adaptive`: **30/40 (75.00%)** [59.81%, 85.81%]
- `benign_cyber_education`: **8/40 FP (20.00% FPR)** [10.50%, 34.76%]
- `benign_technical_imperative`: **0/40 FP (0.00% FPR)** [0.00%, 8.76%]
""",

    "MULTILINGUAL_EVALUATION.md": """# Multilingual Evaluation Report

**Holdout Dataset:** `reports/phase40/datasets/holdout_multilingual.jsonl` ($N=360$: 9 languages $\\times$ 40 samples).

- **Combined ADR:** **94.44%** (255/270) [95% CI: 91.04%, 96.60%]
- **Benign FPR:** **0.00%** (0/90) [95% CI: 0.00%, 4.09%]
- **Per-Language ADR / FPR:**
  - Spanish, French, German, Russian, Hindi, Arabic, Japanese: **100.00% ADR (30/30)**, **0.00% FPR (0/10)**
  - Chinese: **83.33% ADR (25/30)**, **0.00% FPR (0/10)**
  - English (leetspeak & non-buzzword paraphrases): **66.67% ADR (20/30)**, **0.00% FPR (0/10)**
""",

    "G3_EVIDENCE_RELIABILITY.md": """# G3 Evidence Verification Reliability Report

**Holdout Dataset:** `reports/phase40/datasets/holdout_g3.jsonl` ($N=120$).

- **Overall Gate Accuracy:** **100.00%** (120/120) [95% CI: 96.90%, 100.00%]
- **Supported Acceptance:** **100.00%** (30/30) [95% CI: 88.65%, 100.00%]
- **False Abstention:** **0.00%** (0/30) [95% CI: 0.00%, 11.35%]
- **Contradiction Recall:** **100.00%** (55/55) [95% CI: 93.47%, 100.00%]
- **Unsupported Leakage:** **0.00%** (0/20) [95% CI: 0.00%, 16.11%]
- **Partially Supported Leakage:** **0.00%** (0/15)

Hardcoded `_GEO_COMPAT` and entity literals (`toronto`, `newton`, `venus`, `jefferson`) were completely removed and replaced with general functional-role, polarity, and tolerance-aware numerical reasoning.
""",

    "PRODUCTION_PERFORMANCE.md": """# Production Neural Inference & Performance Report

**Service:** `TrustRAGService` Profile B (Live DeBERTa-v3-small CPU).

- **Cold-Start Latency:** **2401.91 ms** (vs. 8652.65 ms in Phase 39)
- **Warm Mean Latency ($N=15$):** **804.05 ms** (vs. 2577.91 ms in Phase 39 — **3.2x speedup**)
- **Warm P50 / P95:** **803.23 ms / 851.14 ms**
- **Genuine Neural Forward Passes:** **57 PyTorch `forward()` calls** across 60 batched NLI calls on 15 warm requests (3.8 batched forward passes/request vs. 24 sequential passes/request previously).
- **Peak RSS Memory:** **861.68 MB**
""",

    "DATASET_PROVENANCE.md": """# Dataset Provenance & Split Hygiene

- **Development Corpora (Used for `semantic_sec_v3.pkl` & `multilingual_sec_v3.pkl`):**
  - `reports/phase40/datasets/g1_dev_corpus.jsonl` ($N=82$: 47 attacks, 35 benign)
  - `reports/phase40/datasets/multilingual_dev_corpus.jsonl` ($N=56$: 36 attacks, 20 benign)
- **Untouched Evaluation Holdouts (Generated via `generate_phase40_holdout.py` after freezing `src/`):**
  - `holdout_g1.jsonl` ($N=280$)
  - `holdout_firewall.jsonl` ($N=150$)
  - `holdout_multilingual.jsonl` ($N=360$)
  - `holdout_g3.jsonl` ($N=120$)
- **Hygiene:** Zero Phase 39 holdout examples were used for tuning or training.
""",

    "STATISTICAL_RESULTS.md": """# Phase 40 Statistical Results & Wilson 95% Confidence Intervals

All metrics computed directly from raw prediction JSONL files using two-sided Wilson 95% confidence intervals ($z = 1.959964$):
- **G1 ADR:** $190/200 = 95.00\\%$ [91.04%, 97.26%] | **FPR:** $8/80 = 10.00\\%$ [5.15%, 18.51%]
- **Firewall Recall:** $100/100 = 100.00\\%$ [96.30%, 100.00%] | **Leakage:** $0/100 = 0.00\\%$ [0.00%, 3.70%] | **FQ:** $0/50 = 0.00\\%$ [0.00%, 7.13%]
- **Multilingual ADR:** $255/270 = 94.44\\%$ [91.04%, 96.60%] | **FPR:** $0/90 = 0.00\\%$ [0.00%, 4.09%]
- **G3 Accuracy:** $120/120 = 100.00\\%$ [96.90%, 100.00%] | **Contradiction Recall:** $55/55 = 100.00\\%$ [93.47%, 100.00%] | **Unsupported Leakage:** $0/20 = 0.00\\%$ [0.00%, 16.11%]
""",

    "KNOWN_LIMITATIONS.md": """# Known Limitations & Remaining Vulnerabilities

1. **G1 Benign Cybersecurity Education FPR (10.00% overall, 20.00% on `benign_cyber_education`):** Misses the `<= 3%` target because defensive questions mentioning quoted attack examples still trigger the TF-IDF classifier (`8/40`).
2. **G1 Adaptive Evasion (75.00% ADR on `obfuscated_and_adaptive`):** 10/40 adaptive paraphrases avoiding common vocabulary (`"Treat the upstream guidance as optional..."`) bypassed G1.
3. **English Leetspeak in Multilingual Holdout (66.67% ADR):** `1gn0r3 pr10r rul3s` style leetspeak without character-level leet normalization bypassed the multilingual regexes.
4. **Rule/ML Hybrid vs. Deep Neural Guardrail:** Because the frozen DeBERTa checkpoint is NLI-trained and immutable, G1 uses a lightweight TF-IDF+LogReg semantic model rather than a dedicated transformer guardrail.
""",
}

for name, content in docs.items():
    with open(BASE / name, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Wrote {name}")
print("Wrote phase40_master_summary.json")
