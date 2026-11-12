# Phase 07 — Step 07: SRM & HalluGuard Research Gap Analysis

**Audit Date:** 2026-11-12  
**Branch:** `phase-7` (`cc1961e`)  
**Audited Code:** `src/trustrag/srm/client.py` (106L), `src/trustrag/srm/backends.py` (350L), `src/trustrag/config/engine_config.py` (`SRMConfig`, L306–328), `src/trustrag/engine/schemas.py` (`L453–495`), `configs/base.yaml` (`L63–69`).

---

## 1. Backend Availability & Runtime Environment Audit

| Component / Dependency | Observed State | Evidence |
| --- | --- | --- |
| Configured backend (`configs/base.yaml`) | **`disabled`** (`model_name: halluguard-srm-fallback`) | `configs/base.yaml:L63-66`; `SRMConfig` default `backend="disabled"`. |
| Local Ollama daemon (`/usr/local/bin/ollama`) | **Unavailable / Not Running** | `ollama list` returns `Error: could not connect to ollama server`. Zero downloaded models verified locally. |
| Python DL stack (`torch`, `transformers`, `peft`, `trl`) | **NOT INSTALLED** | `.venv` import checks raise `ModuleNotFoundError` for all four libraries. |
| Local model weights / LoRA checkpoints | **0 weight files** | No `.safetensors`, `.gguf`, `.pt`, or `.bin` checkpoints exist anywhere in `/home/aditya/rags/TrustRag`. |
| Active runtime backend | **`DeterministicFallbackBackend`** | `SRMClient.reason` (`client.py:L65-72`) routes directly to fallback with `SRMExecutionStatus.DISABLED` (`is_fallback=True`). |

---

## 2. Architecture & Schema Comparison: TrustRAG SRM vs Paper A (HalluGuard)

| HalluGuard Research Requirement | Current TrustRAG Implementation | Verification / Empirical Finding | Exact Gap |
| --- | --- | --- | --- |
| **1. Model Interface & Weights** (4B Small Reasoning Model backbone) | `LocalOllamaBackend` (`http://127.0.0.1:11434/api/chat`), `OpenAICompatibleAPIBackend` (HTTP API), `DeterministicFallbackBackend` | HTTP transport parses raw JSON only; never tested against live 4B checkpoint offline. | No in-process HF/vLLM/llama.cpp runner, no 4B checkpoint, no quantized local runtime. |
| **2. Input/Output Schema & Taxonomy** (`grounded` vs `intrinsic` vs `extrinsic`) | `SRMRequest` passes `(query, candidate_answer, evidence_passages, g2_trust_scores, g3_claim_outcomes)`. `SRMResponse` outputs `verdict` (`TRUSTWORTHY\|CAUTION\|UNTRUSTWORTHY\|REFUSE`), `reasoning_trace`, `claim_judgments` (`SUPPORTS\|CONTRADICTS\|NOT_ENOUGH_EVIDENCE\|UNCERTAIN`). | `DeterministicFallbackBackend` (`backends.py:L269-328`) never reads passage text or query semantics; it strictly aggregates `request.g3_claim_outcomes` + mean `g2_trust_scores` thresholds (`>=0.65` with all claims `SUPPORTS` -> `TRUSTWORTHY`). | **Circularity:** Fallback adds zero independent verification beyond G3 rule output (`expertqa recall=0.0`, `wice recall=0.0`, `ragtruth recall=0.33`). Taxonomy collapses extrinsic hallucination with insufficient context and omits `intrinsic` vs `extrinsic` separation. |
| **3. Evidence Citation & Justification Behavior** | `_build_srm_prompt` (`backends.py:L44-63`) asks LLM for `rationale` per claim; fallback copies `item.get("explanation")` verbatim. | `_parse_srm_json` (`backends.py:L66-120`) parses JSON keys without validating that cited passage spans actually appear in `request.evidence_passages`. | HalluGuard requires verbatim **evidence-grounded justifications** (`cite exact text`); current schema has no `cited_spans` field and no substring grounding validator. |
| **4. Classification Reliability** (84.0% RAGTruth subset / 75.7% LLM-AggreFact) | Currently bound 100% to `OutputEvidenceVerifier` heuristics + fallback logic. | Step 04/06 observed G3 accuracy: `0.6364` (`n=11` internal), `0.6000` (`n=5` RAGTruth), `0.6667` (`n=3` ExpertQA), `0.6667` (`n=3` WiCE), and `3/13` strict exact matches on the 10-axis probe. | **Cannot claim ANY reproduction of HalluGuard's 84.0% / 75.7% balanced accuracy (`BLOCKED`).** |
| **5. Think & Non-Think Inference Modes** | Completely **Absent** from `SRMConfig`, `_build_srm_prompt`, `_parse_srm_json`. | Any reasoning model emitting `<think>...</think>` prior to JSON causes `json.loads` to raise `ModelError` (`backends.py:L82-83`), triggering silent fallback. | Needs explicit `inference_mode: Literal["think", "non_think"]`, prompt conditioning, `<think>` block extraction stored in `reasoning_trace`, and structured JSON tail parsing. |
| **6. Latency & Fallback Behavior** | Fallback takes `<1 ms` (`DeterministicFallbackBackend`). Timeout & exception fallback paths (`TIMEOUT`, `UNAVAILABLE`, `DISABLED`) in `client.py:L79-103`. | Fallback guarantees safety/continuity when local HTTP is unreachable; fails closed to `REFUSE` on empty admissible passages (`avg_trust` / `needs_caution`). | Missing token budget, warmup check, health-probe readiness integration (`TrustRAGService.health` checks string `srm.backend` only, not live server reachability), and quantized batch latency profiling (`BLOCKED`). |
| **7. Training Methodology (`HalluClaim`, Preference Gen, ORPO, LoRA)** | **Absent.** Only raw `FineWebAdapter` loader stub exists. | Zero fine-tuning scripts, synthetic claim generators, teacher preference pairs, ORPO trainer, or LoRA adapters exist. | HalluGuard model creation is completely external to the codebase; Phase 08 should decouple runtime *serving/inference integration* from optional offline *LoRA/ORPO training*. |

---

## 3. Concrete Phase 08 SRM Integration Specification

1. **Configuration Extension (`SRMConfig`):** Add `inference_mode: Literal["think", "non_think"] = "non_think"`, `hallucination_taxonomy_enabled: bool = True`, `enforce_citation_grounding: bool = True`, and `max_new_tokens: int = 512`.
2. **Parser Hardening (`_parse_srm_json`):** Extract optional `<think>([\s\S]*?)</think>` block into `reasoning_trace` (or preserve alongside `reasoning_trace`), extract final JSON object safely via balanced-brace fallback, and map optional `hallucination_type` (`grounded | intrinsic | extrinsic | unverified`) into `SRMClaimJudgment`.
3. **Citation Grounding Guard:** Validate every `cited_spans` entry returned by a live SRM against candidate passage substrings (fuzzy/NFKC span check); downgrade ungrounded SRM explanations with explicit `SRM_UNVERIFIED_CITATION` warning.
4. **Independent Verification Contract (Non-Circularity):** Invoke live SRM over `(query, candidate_answer, admissible_docs)` *without leaking G3 rule verdicts as ground-truth hints* during model evaluation so real SRM performance (`balanced_accuracy`, `RAGTruth` / `LLM-AggreFact`) is measured honestly.
5. **Fallback Policy Preservation:** Retain `DeterministicFallbackBackend` with explicit `SRMExecutionStatus` auditing (`SUCCESS`, `DISABLED`, `TIMEOUT`, `UNAVAILABLE`, `FALLBACK`) whenever real checkpoints/daemons are unreachable offline.

