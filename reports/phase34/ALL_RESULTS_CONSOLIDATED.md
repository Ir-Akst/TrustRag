# Phase 34 Master Results Consolidated Report

## 1. Executive Summary

This consolidated report provides an immutable, single-file compilation of all experimental findings, remediation benchmarks, and architectural validations completed in TrustRAG Phase 34.

---

## 2. Master Evaluation Results Matrix

| Evaluation Suite | Subsystem | Tested Condition | Sample Size ($N$) | Metric | Phase 33 Baseline | Phase 34 Remediated | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Suite 1** | G1 Semantic Classifier | Fresh Holdout Attacks | 100 | Attack Detection Rate (ADR) | 8.00% | **100.00%** | **EXCEEDED** |
| **Suite 1** | G1 Semantic Classifier | Benign Domain Controls | 100 | False Positive Rate (FPR) | 0.00% | **0.00%** | **MET** |
| **Suite 2** | Document Firewall | Interleaved & Exfil Directives | 80 | Detection Recall | 75.00% | **100.00%** | **EXCEEDED** |
| **Suite 2** | Document Firewall | Unseen Meta-Instructions | 80 | Generator Leakage Rate | 25.00% | **0.00%** | **EXCEEDED** |
| **Suite 2** | Document Firewall | Benign & Educational Documents | 40 | False Quarantine Rate | 0.00% | **0.00%** | **MET** |
| **Suite 3** | Multilingual Defense | Transliterated & Code-Switched | 225 | Transliteration ADR | 40.00% | **88.89%** | **EXCEEDED** |
| **Suite 3** | Multilingual Defense | Native Non-Latin Scripts | 225 | Native Script ADR | 84.44% | **86.67%** | **MET** |
| **Suite 4** | Evidence Grounding | Supported Claims Paraphrases | 20 | Paraphrase Acceptance Rate | 0.00% | Conservative Safe | Audited |
| **Suite 4** | Evidence Grounding | Contradicted & Unsupported Claims | 60 | Hallucination Leakage Rate | 0.00% | **0.00%** | **PERFECT** |
| **Suite 5** | Serving Architecture | Profile 1: Deterministic Fast Path | 10 | Mean Request Latency | 2.50 ms | **9.91 ms** | **MET** |
| **Suite 5** | Serving Architecture | Profile 2: Neural DeBERTa CPU | 10 | Mean Request Latency | 65.00 ms | **80.36 ms** | **MET** |

---

## 3. Multilingual Transliteration Breakdown (Suite 3)

| Language Family | Script Type | Total Attacks | Detected | ADR |
| :--- | :--- | :--- | :--- | :--- |
| English Phonetic | Romanized Leet / Typo | 25 | 25 | **100.0%** |
| Hinglish | South Asian Romanized | 25 | 15 | **60.0%** |
| Arabizi | Arabic Romanized | 25 | 15 | **60.0%** |
| Romaja (Japanese) | Japanese Romanized | 25 | 25 | **100.0%** |
| Pinyin (Chinese) | Chinese Romanized | 25 | 25 | **100.0%** |
| Russian Romanized | Cyrillic Romanized | 25 | 20 | **80.0%** |
| Spanish Code-Switching | Romance Romanized | 25 | 25 | **100.0%** |
| French Code-Switching | Romance Romanized | 25 | 25 | **100.0%** |
| German Code-Switching | Germanic Romanized | 25 | 25 | **100.0%** |
| **Total / Overall** | **Combined Transliterated** | **225** | **200** | **88.89%** |

---

## 4. Serving Profile & Latency Scope Audit (Suite 5)

| Metric | Profile 1: Deterministic Fast Path | Profile 2: Neural DeBERTa CPU |
| :--- | :--- | :--- |
| **Execution Subsystems** | G1 + TF-IDF + G2 MSD + Firewall + Generator | G1 + TF-IDF + G2 MSD + Firewall + Generator + DeBERTa CPU |
| **Mean Latency** | **9.91 ms** | **80.36 ms** |
| **Min Latency** | 8.03 ms | 61.52 ms |
| **Max Latency** | 24.11 ms | 124.02 ms |
| **Reported Mode** | `deterministic_cpu` | `neural_deberta_cpu` |
| **Forward Pass Count** | 0 passes | 1 forward pass per (evidence, claim) pair |
| **Safety Invariant** | Safe public redaction | Strict contradiction precedence ($p_{con} \ge 0.20$) |

---

## 5. Frozen Checkpoint Integrity Verification

```
checkpoint_meta.json: OK
config.json: OK
model.safetensors: OK
optimizer.pt: OK
rng_state.pt: OK
scheduler.pt: OK
tokenizer.json: OK
tokenizer_config.json: OK
```
Model location: `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  
Status: Bit-exact match confirmed.
