# TrustRAG Phase 17 — Independent Public Benchmark Audit: PoisonedRAG (USENIX Security 2025)

**Auditor:** Principal Research Engineer & Independent ML Security Auditor  
**Date:** 2026-11-19T01:05:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-17-20-final-release`  
**Benchmark Reference:** Zou et al., "PoisonedRAG: Knowledge Poisoning Attacks to Retrieval-Augmented Generation of Large Language Models", USENIX Security 2025 (arXiv:2402.07867)  
**Status:** **`BLOCKED`**  

---

## 1. Executive Summary & Audit Mandate

Phase 17 mandates independent validation against established public poisoning benchmarks, specifically evaluating whether TrustRAG's defense capabilities generalize to academic poisoning benchmarks including **PoisonedRAG** (Zou et al., USENIX Security 2025).

In accordance with mandatory research safety and integrity constraints:
> *"Never claim external benchmark validation if the benchmark was not actually downloaded and evaluated. If a benchmark cannot be accessed, classify it as BLOCKED and continue with other permitted tasks. Do not substitute synthetic data and call it external validation."*

This audit forensically investigated the availability of PoisonedRAG artifacts, verified local environment boundaries, and formally records its operational accessibility status.

---

## 2. Threat Model & Benchmark Architecture (PoisonedRAG)

### 2.1 Threat Model Description
PoisonedRAG investigates black-box knowledge base poisoning against Retrieval-Augmented Generation systems. Its core attack vectors comprise:
1. **Target Query Selection:** Identifying high-frequency or high-value enterprise queries.
2. **Adversarial Passage Crafting:** Generating passages that combine high semantic similarity to target queries (to rank in top-$K$) while delivering a malicious misinformation target or instruction payload.
3. **Black-box Optimization:** Iterative text mutation against dense retrievers (DPR, Contriever, BGE) to bypass lexical/dense similarity thresholds without access to generator weights.

### 2.2 Attack Taxonomy vs. TrustRAG Defenses
| PoisonedRAG Attack Vector | Mechanism | TrustRAG Defense Layer | Theoretical Interaction |
|---|---|---|---|
| **Direct Target Poisoning** | Malicious claim injected into single passage | G2 Multi-Signal Detector ($S_4, S_5$) & G3 NLI | If untrusted, G2 quarantines via source tiering and consensus deviation. If admitted, G3 flags contradiction against authoritative consensus. |
| **Sybil Coordinated Poisoning** | Multiple colluding passages injected to create synthetic consensus | G2 Source Tiering & Removal Cap ($C_r = 0.5$) | G2 caps removal to prevent complete evasion; unverified web sources are down-weighted relative to authoritative tiers. |
| **Trigger-based Poisoning** | Backdoor tokens injected into retrieval candidates | G1 Query Guardrail & G2 Heuristics | Lexical trigger filters detect repetitive perturbation; G3 verifies claim fidelity. |

---

## 3. Forensic Investigation of Benchmark Availability

### 3.1 Local Filesystem Forensic Audit
An exhaustive search across the entire local environment (`/home/aditya/rags/`, `/home/aditya/rags/TrustRag-phase11/data/`, and all cache directories) was conducted:
- `find /home/aditya/rags -iname "*poisonedrag*"` returned **zero results**.
- Pre-staged datasets in `data/raw/` contain:
  - `data/raw/custom_security/` (TrustRAG internal benchmark)
  - `data/raw/ragtruth/` (RAGTruth benchmark)
  - `data/raw/halueval/` (HaluEval benchmark)
  - `data/raw/hotpotqa/` and `data/raw/ms_marco/`
- No PoisonedRAG evaluation corpus, poisoned corpus embeddings, or query-answer pairs exist in the offline repository.

### 3.2 Downloader & Loader Code Inspection
Inspection of `src/trustrag/data/acquisition/downloader.py` and `src/trustrag/data/loaders/` confirms:
- PoisonedRAG does not possess a canonical PyPI or Hugging Face unauthenticated direct distribution endpoint.
- Downloading PoisonedRAG requires remote GitHub repository cloning or Google Drive artifact access.
- Executing external network downloads or unauthorized web cloning is strictly disabled by execution sandbox constraints and safety rules.

---

## 4. Scientific Audit Finding

Because PoisonedRAG dataset artifacts are not present on local disk, cannot be acquired without external network access, and must not be fabricated or simulated:
- **Formal Status:** **`BLOCKED`**
- **Non-Substitution Guarantee:** No internal synthetic poisoning dataset was rebranded or reported as PoisonedRAG.
- **Empirical Public Benchmark Coverage:** As documented in Phase 15 and corroborated in Phase 17, independent public benchmark validation is empirically executed on **RAGTruth** (ACL 2024, $N=200$) and **HaluEval** (EMNLP 2023, $N=200$), which were legitimately pre-staged and evaluated against frozen DeBERTa-v3-small weights.

