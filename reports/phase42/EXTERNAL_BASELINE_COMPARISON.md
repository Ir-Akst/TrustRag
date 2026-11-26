# External Baseline Benchmarking Report

## 1. Public Non-Cycled Hallucination Benchmarks (`seed=42`)

### A. RAGTruth (`data/processed/ragtruth/test.jsonl`, $N=200$: 100 FACTUAL, 100 HALLUCINATED)
| System | Accuracy (95% CI) | Hallucination Leakage (95% CI) | Factual Recall | Precision | TP/FP/TN/FN |
|---|---|---|---:|---:|---|
| **Vanilla RAG (No G3)** | 50.00% [43.14%, 56.86%] | 100.00% [96.30%, 100.0%] | 100.00% | 50.00% | 100/100/0/0 |
| **Lexical Overlap (>=0.25)** | 56.50% [49.57%, 63.18%] | 16.00% [10.10%, 24.42%] | 29.00% | 64.44% | 29/16/84/71 |
| **TrustRAG G3 (Frozen DeBERTa)** | 55.50% [48.57%, 62.22%] | **3.00%** [1.03%, 8.45%] | 14.00% | **82.35%** | 14/3/97/86 |

### B. HaluEval (`data/processed/halueval/test.jsonl`, $N=200$: 100 FACTUAL, 100 HALLUCINATED)
| System | Accuracy (95% CI) | Hallucination Leakage (95% CI) | Factual Recall | Precision | TP/FP/TN/FN |
|---|---|---|---:|---:|---|
| **Vanilla RAG (No G3)** | 50.00% [43.14%, 56.86%] | 100.00% [96.30%, 100.0%] | 100.00% | 50.00% | 100/100/0/0 |
| **Lexical Overlap (>=0.25)** | 42.50% [35.85%, 49.43%] | 16.00% [10.10%, 24.42%] | 1.00% | 5.88% | 1/16/84/99 |
| **TrustRAG G3 (Frozen DeBERTa)** | 43.00% [36.33%, 49.93%] | 24.00% [16.69%, 33.23%] | 10.00% | 29.41% | 10/24/76/90 |

*Critical Finding:* HaluEval QA answers are often 1–3 words, which `extract_atomic_claims` (`len < 3 words`) filters out as non-substantive; RAGTruth summaries are multi-sentence syntheses where strict per-claim NLI abstains whenever any sub-claim lacks sentence-level entailment.

## 2. Prompt-Injection & Boundary Security Baselines (`p41_g1` $N=250$ + `p41_firewall` $N=140$)
| System | G1 ADR (95% CI) | G1 FPR | Boundary Leakage |
|---|---|---:|---:|
| **Vanilla RAG (No Security)** | 0.00% | 0.00% | 100.00% |
| **Spotlighting-Only (XML Isolation)** | 0.00% | 0.00% | 100.00% (directives unstripped) |
| **Heuristic/Regex-Only** | 30.00% [23.24%, 37.76%] | 20.00% | 100.00% |
| **TrustRAG Full** | **96.67%** [92.43%, 98.57%] | 10.00% | **0.00%** |

*Baseline Availability Disclosure:* No external pretrained HuggingFace prompt-injection checkpoint (e.g. ProtectAI DeBERTa-v3-prompt-injection) is cached locally on disk, and offline sandbox execution prohibits remote downloads; therefore no external checkpoint numbers were fabricated.
