# TrustRAG Phase 04 — Step 4: Knowledge Poisoning Evaluation

**Date:** 2026-11-11  
**Dataset:** `knowledge_poisoning` (**SYNTHETIC DATA** — `TrustRAG-Synthetic-Security-Benchmark-v1.0`, derived from `custom_security`)  
**Splits Evaluated:**
- Active frozen `data/benchmarks/knowledge_poisoning/test.jsonl` (4 records, 2 pairs, 2 queries, `KNOWLEDGE_POISONING` only)
- Preserved Phase 02 `data/benchmarks_backup/knowledge_poisoning/test.jsonl` (24 records, 12 pairs, 3 unique queries, `KNOWLEDGE_POISONING` [16] + `TRIGGER_DOS` [8]) and `train.jsonl` (104 records, 52 pairs)
- **Backend Note:** No live Ollama/API/HalluGuard checkpoint is present; Full TrustRAG executes with `SRMConfig(backend="disabled")` (`halluguard-srm-fallback` deterministic fallback), so `RAG + G2 + G3` and `Full TrustRAG (G1+G2+G3+SRM_fallback)` share identical G1–G3 defense behavior on clean queries while `Full TrustRAG` adds G1 query scanning and SRM deterministic trace auditing.

---

## 1. Mixed-Corpus & Multi-Scenario Evaluation (Synthetic Benchmark)

### 1.1 Full-Split Corpus Evaluation (`mode=mixed`, `top_k=5`)

| Benchmark Split | Configuration | Queries | ASR | Attack Prevention | Clean Retention | Quarantine Rate | Clean Outranks Poison | Poison Evidence Share | Cap Violations ($\le \lfloor K/2 \rfloor$) | Mean Lat (ms) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Active `test` | `original_rag` | 2 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.5000 | 0 | 3.21 |
| Active `test` | `rag_g2` | 2 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.5000 | **0** | 3.82 |
| Active `test` | `rag_g2_g3` | 2 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.5000 | **0** | 6.00 |
| Active `test` | `full_trustrag` | 2 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.5000 | **0** | 5.68 |
| Backup `test` | `original_rag` | 3 | 0.6667 | 0.3333 | 0.6667 | 0.0000 | 0.3333 | 0.5385 | 0 | 5.18 |
| Backup `test` | `rag_g2` | 3 | 0.6667 | 0.3333 | 0.6667 | 0.0000 | 0.3333 | 0.5385 | **0** | 6.62 |
| Backup `test` | `rag_g2_g3` | 3 | 0.6667 | 0.3333 | 0.6667 | 0.0000 | 0.3333 | 0.5385 | **0** | 15.77 |
| Backup `test` | `full_trustrag` | 3 | 0.6667 | 0.3333 | 0.6667 | 0.0000 | 0.3333 | 0.5385 | **0** | 9.85 |

### 1.2 Corpus Poisoning Ratio & Clean/Poison Isolation (`data/benchmarks_backup/knowledge_poisoning/test`, Synthetic)

| Corpus Mode | Configuration | ASR | Prevention | Clean Retention | Poison Evidence Share | Cap Violations |
|---|---|---:|---:|---:|---:|---:|
| `clean_only` | `original_rag` / `full_trustrag` | 0.0000 | 1.0000 | **1.0000** | 0.0000 | 0 |
| `poisoned_only` | `original_rag` / `full_trustrag` | 0.6667 | 0.3333 | 0.0000 | 1.0000 | 0 |
| `multi_poison_2x` | `original_rag` | 0.6667 | 0.3333 | 0.6667 | 0.5714 | 0 |
| `multi_poison_2x` | `full_trustrag` | 0.6667 | 0.3333 | 0.3333 | 0.6429 | **0** |

### 1.3 Paired Single-Injection Scenario (1 Poisoned Doc Injected Into Clean KB, Synthetic)

To evaluate targeted injection where a single adversarial passage competes against the clean knowledge base (`sec_pair_XXXX` isolated per query):

| Benchmark Split | Configuration | Pairs ($N$) | ASR | Prevented or Flagged | Clean Evidence Returned | Poisoned Evidence Returned | Cap Violations |
|---|---|---:|---:|---:|---:|---:|---:|
| Active `test` | `original_rag` | 2 | 1.0000 | 0.0000 | 2 | 2 | 0 |
| Active `test` | `full_trustrag` | 2 | 1.0000 | **1.0000** | 2 | 2 | **0** |
| Backup `test` | `original_rag` | 12 | 0.6667 | 0.3333 | 44 | 8 | 0 |
| Backup `test` | `rag_g2` / `rag_g2_g3` / `full_trustrag` | 12 | **0.1667** | **1.0000** | **50** | **2** | **0** |

- **Key Result:** In single-injection attacks against a clean knowledge base (`Backup test`, $N=12$ pairs), G2 reduces ASR from **0.6667 $\rightarrow$ 0.1667 (-75% relative)**, raises `PreventedOrFlagged` from **0.3333 $\rightarrow$ 1.0000**, and increases clean evidence retained from **44 $\rightarrow$ 50** while reducing poisoned evidence returned from **8 $\rightarrow$ 2**.

---

## 2. Document-Level G2 Detection & Trust Score Distributions (Synthetic)

### 2.1 Candidate Assessment Metrics (`mode=mixed`, `full_trustrag`)
- **Strict `POISONED` Decision:**
  - Active `test` (`KNOWLEDGE_POISONING` only): `Precision=0.0`, `Recall=0.0`, `F1=0.0`, `FPR=0.0`, `ROC-AUC=0.0` (all symmetric conflicts labeled `UNCERTAIN`).
  - Backup `test` (`KNOWLEDGE_POISONING` + `TRIGGER_DOS`): Strict `POISONED` recall=`0.0` in mixed top-5 when `KNOWLEDGE_POISONING` dominates top-5; **per-attack inspection reveals `TRIGGER_DOS` gets `POISONED` 4/4 (100% recall, 0% FPR)**, while symmetric factual `KNOWLEDGE_POISONING` gets `UNCERTAIN` (`CONSENSUS_DEVIATION_CONFLICT`, `MINORITY_OUTLIER`, `G2_CONFLICT_DETECTED`).
  - **Combined `POISONED | UNCERTAIN` Detection (Active `test` / Backup `test`):** `F1 = 0.6667`.
  - Backup `train` (`ROC-AUC = 0.8333` for trust score separation when clean outnumbers poison in candidate pools).

### 2.2 Trust Score Distributions (`mode=mixed`)
- **Active `test`:** Clean `mean=0.7467` (`std=0.0293`, `[0.7173, 0.7760]`) vs Poisoned `mean=0.7802` (`std=0.0038`, `[0.7765, 0.7840]`).
- **Backup `test`:** Clean `mean=0.7581` (`std=0.1338`, `[0.6470, 0.9440]`) vs Poisoned `mean=0.7216` (`std=0.0011`, `[0.7194, 0.7233]`).
- **Backup `train`:** Clean `mean=0.9044` (`std=0.0856`, `[0.7129, 0.9432]`) vs Poisoned `mean=0.8883` (`std=0.0095`, `[0.8776, 0.8974]`).

---

## 3. Retrieval Rank Sensitivity & Removal Cap Verification

Evaluated on `Backup test` across initial injection ranks 1–5 (`n=5` candidates):
- **`TRIGGER_DOS`:** Classified `POISONED` (`DOC_DOS_TRIGGER`, `G2_SUSPICIOUS_INSTRUCTION`) at **all 5 ranks** (`trust=0.6296` at ranks 1–3, `0.6005` at rank 4, `0.5540` at rank 5).
- **`KNOWLEDGE_POISONING`:** Classified `UNCERTAIN` (`CONSENSUS_DEVIATION_CONFLICT`, `MINORITY_OUTLIER`, `G2_CONFLICT_DETECTED`) at **all 5 ranks** (`trust=0.8776` at ranks 1–3, `0.8638` at rank 4, `0.8397` at rank 5).
- **Removal Cap Enforcement:** **0 violations** (`removal_cap_violations = 0`) across every single query, variant, and corpus mode ($\text{removals} \le \lfloor K/2 \rfloor$ strictly upheld).

---

## 4. Documented Limitations & Critical Findings

1. **Symmetric Factual Poisoning Without External Trust Priors:** When 50% of retrieved documents assert fact $A$ and 50% assert tampered fact $A'$ with **zero instruction-injection markers** (`F4=0`), `F1 (perplexity)` and `F2 (embedding_norm)` disabled, and `F6 (provenance_priors)` empty, G2 correctly identifies a conflict (`overall_trust_decision = "FLAGGED"`), **but** `TrustRAGPipeline` does not quarantine `UNCERTAIN` conflict-only documents before generation—so `public_abstained=False` and poisoned spans can still appear in the flagged response.
2. **Removal Cap Bound Under High Poisoning Ratios:** When poisoned documents exceed $\lfloor K/2 \rfloor$, `TrustAwareRetriever` stops filtering at $\lfloor K/2 \rfloor$ by design; `TrustRAGPipeline`'s pre-generation gate blocks/quarantines surviving `POISONED` docs (e.g., `TRIGGER_DOS`), whereas pure factual `UNCERTAIN` conflicts remain `FLAGGED` rather than quarantined.

---

## 5. Step 4 Acceptance Verdict

- [x] All experiment configurations and synthetic provenance recorded.
- [x] Clean, poisoned, mixed, multi-poison, and rank-permuted contexts evaluated.
- [x] ASR, clean retention, G2 precision/recall/F1/FPR/FNR/AUC, and trust distributions computed from actual predictions (`0` failed/invalid runs).
- [x] Removal cap ($\le \lfloor K/2 \rfloor$) verified across all runs (`0` violations).

**Step 4 Status:** **PASS** — Ready to proceed to Step 5 (G1 Input Guardrail Evaluation).

