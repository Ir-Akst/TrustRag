# TrustRAG: A Defense-in-Depth Architecture for Robust Retrieval-Augmented Generation Under Adversarial Evasion and Document Poisoning

**Authors:** Principal ML Security Researcher, Systems Architect & Independent Evaluation Auditor  
**Affiliation:** TrustRAG Research & Engineering Group  
**Target Submission:** Top-Tier Computer Security / Machine Learning Conference (USENIX Security / ACL / EMNLP)  
**Artifact Repository:** `https://github.com/Ir-Akst/TrustRAG.git`  
**Anchor Release Commit:** `531bff32745ede1bd1b38609cc6daf653d3eff24`  
**Current Evaluation Branch:** `phase-27-manuscript-finalization`  

---

## Abstract

Retrieval-Augmented Generation (RAG) models have emerged as standard architectures for knowledge-intensive NLP tasks, but they introduce severe security attack surfaces, including direct prompt injection, adversarial homoglyphs, and corpus-level document poisoning. We present **TrustRAG**, a modular, three-tiered defense-in-depth architecture designed to secure RAG pipelines without degrading clean utility or introducing prohibitive serving latency. TrustRAG organizes defenses into: (1) **G1 Input Guardrail**, a CPU-bound deterministic screening layer providing sub-millisecond ($0.11$ ms) lexical and structural filtering for prompt injections, role-hijacks, and obfuscations; (2) **G2 Multi-Signal Detector (MSD)**, an evidence-filtering mechanism evaluating candidate passages across six semantic and instruction signals with an adaptive **Removal Cap ($C_r = 0.50$)**; and (3) **G3 Claim Verifier**, a multi-tiered consensus and selective reasoning model (SRM) scoring entailment between generated responses and retrieved evidence. 

We conduct an extensive, independent empirical evaluation across 1,000 newly constructed samples (500 unseen adversarial attacks and 500 independent benign controls across 5 domains) alongside established benchmarks (RAGTruth, HaluEval, PoisonedRAG, and RSB). On in-distribution benchmarks, TrustRAG achieves 100.0% attack detection. However, under genuinely unseen adversarial attacks, our independent evaluation reveals a true generalization bound of **71.80% Attack Detection Rate (ADR)** (Wilson 95% CI: $[67.70\%, 75.57\%]$), exposing fundamental blind spots in deterministic rule engines when confronted with unlisted lexical synonyms, novel personas, and non-Western languages (0.0% ADR in Russian, Chinese, Hindi, Arabic, and Japanese). Conversely, TrustRAG achieves a **100.00% Clean Delivery Rate** with a strict **Clean False Positive Rate of 0.00%** (Wilson 95% CI: $[0.00\%, 0.76\%]$) on 500 diverse benign queries, satisfying publication criteria ($<1.0\%$). Furthermore, our analysis of retrieval poisoning uncovers the **Sybil Frontier**: when adversarial document density exceeds $50\%$, the removal cap intentionally permits poisoned passages to reach context to prevent denial-of-service starvation, exposing an inescapable Availability vs. Robustness trade-off. We provide full reproducibility packages, cryptographic checksums, and unredacted raw prediction logs.

**Keywords:** Retrieval-Augmented Generation, Adversarial Robustness, Prompt Injection, Document Poisoning, Guardrails, AI Safety.

---

## 1. Introduction

Large Language Models (LLMs) integrated with retrieval mechanisms—collectively termed Retrieval-Augmented Generation (RAG)—have achieved state-of-the-art performance in open-domain question answering, customer support, and clinical summarization. By grounding generative outputs on externally retrieved knowledge passages, RAG mitigates parametric factual hallucination and provides verifiable citations.

However, external grounding fundamentally expands the threat model of generative systems:
1. **Direct Query Injection & Jailbreaking:** Adversaries craft inputs designed to override system instructions, adopt unrestricted personas, or exfiltrate private credentials and system prompts.
2. **Indirect Document Poisoning:** Adversaries contaminate underlying knowledge corpora with adversarial passages designed to hijack downstream reasoning when retrieved.
3. **Evasion Obfuscation:** Attackers employ zero-width formatting, Unicode homoglyphs, and multimodality to bypass conventional text filters.

Existing defenses typically rely either on heavy LLM self-guarding (which incurs excessive cost and multi-second latency) or naive keyword blocklists (which suffer from high false-positive rates and brittle evasion). Furthermore, published academic literature frequently reports artificially perfect detection rates ($\ge 99\%$) derived from testing known, static evaluation cohorts that fail to generalize to novel attacks in real-world deployments.

### Research Contributions
In this paper, we make four primary contributions:
1. **Architectural Framework:** We formulate and implement **TrustRAG**, a concrete three-tiered defense architecture decoupling input query verification (G1), multi-signal retrieval filtering (G2), and claim-level verification (G3).
2. **Empirical Generalization & Blind-Spot Audit:** Moving beyond static benchmarks, we evaluate 500 independently authored unseen attacks across 13 distinct categories, demonstrating an empirical generalization bound of **71.80% ADR** and documenting precise failure modes in lexical synonymy and non-Latin multilingual scripts.
3. **Availability vs. Robustness Frontier (The Sybil Cap):** We formalize and evaluate the **Removal Cap ($C_r$)**, demonstrating how context preservation limits defensive pruning during majority poisoning campaigns.
4. **Transparent Deployment Truthfulness:** We provide complete transparency regarding production configurations, distinguishing sub-millisecond CPU deterministic filtering from offline neural NLI verification.

---

## 2. Threat Model & Problem Formulation

We consider a standard RAG pipeline operating over a user query $q$, knowledge base $\mathcal{D}$, retriever $\mathcal{R}$, and generator $\mathcal{G}$.

### 2.1 Adversarial Goals
1. **Goal 1 (Prompt Hijack & Exfiltration):** The adversary crafts $q_{\text{adv}}$ to force $\mathcal{G}$ to ignore system prompt $S$, reveal confidential variables, or output malicious payloads.
2. **Goal 2 (Corpus Poisoning):** The adversary inserts poisoned passages $d^* \in \mathcal{D}$ such that when $d^* \in \text{Top-}k(q)$, $\mathcal{G}$ produces a target misinformation claim $y^*$.
3. **Goal 3 (Evasion & Concealment):** The adversary applies syntactic obfuscations $T(q)$ (e.g., zero-width spaces, Cyrillic confusables) such that $T(q)$ is semantically active to the LLM but evades detection.

### 2.2 Operational Constraints
- **Sub-Second Latency Budget:** Security screening must not introduce perceptible latency to conversational RAG.
- **Strict Clean Delivery:** Benign user inquiries must achieve Clean False Positive Rates strictly bounded below $1.0\%$ at 95% confidence.
- **Context Availability:** Pruning poisoned passages must not starve the generator of necessary contextual information.

---

## 3. TrustRAG Architecture

TrustRAG enforces defense-in-depth across three decoupled checkpoints:

```
[User Query q]
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Tier 1: G1 Input Guardrail (CPU Deterministic, ~0.11 ms)    │
│  - SHA-256 Audit Trail & Input Invariance                  │
│  - Harmful Intent Screening (Malware, Cyberweapons)         │
│  - Obfuscation Normalizer (ZWSP, Cyrillic/Greek Folding)    │
│  - Parameterized Threat Rules (Injections, Shell Chains)   │
└─────────────────────────────────────────────────────────────┘
       │  Decision == ALLOW
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Tier 2: G2 Multi-Signal Detector (MSD)                      │
│  - Candidate Retrieval R(q) -> {d_1, ..., d_k}              │
│  - 6 Multi-Domain Signals (F1 Lexical, F4 Override Tag)     │
│  - Removal Cap (C_r = 0.50): Prunes at most 50% candidates  │
└─────────────────────────────────────────────────────────────┘
       │  Filtered Context C
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Generator: LLM Synthesis G(q, C) -> Response y              │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Tier 3: G3 Claim Verifier & Consensus Model                 │
│  - Claim-Evidence Entailment Scoring                        │
│  - Selective Risk Model (SRM) Fallback Protocol             │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
[Final Verified Output]
```

### 3.1 G1: Deterministic Pre-Retrieval Guardrail
G1 processes raw query string $q$ before retrieval. To prevent silent semantic drift, G1 preserves the raw input for auditing while generating normalized analysis representations:
1. `detect_obfuscation(q)`: Strips zero-width characters (ZWSP `U+200B`, ZWNJ `U+200C`, BOM `U+FEFF`) while preserving legitimate complex-script joiners.
2. `fold_mixed_script_confusables(q)`: Folds Cyrillic and Greek homoglyphs (e.g., `U+0501` $\to$ `d`, `U+0430` $\to$ `a`, `U+03C5` $\to$ `u`) into canonical Latin ASCII.
3. `match_threat_patterns(q)`: Matches compiled regexes for direct injection, shell commands, and delimiter escapes.
4. `HarmfulIntentPolicy`: Detects weaponized malware creation requests while exempting defensive analytical inquiries.

### 3.2 G2: Multi-Signal Retrieval Detector & The Removal Cap
When candidates $\{d_1, \dots, d_k\}$ are retrieved, G2 MSD evaluates each passage across six signals $F_1, \dots, F_6$:
- $F_1$ (Cosine/TF-IDF Relevance), $F_2$ (Perplexity Anomaly), $F_3$ (Semantic Norm Spike), $F_4$ (Instruction Override Directives), $F_5$ (Provenance Signature), $F_6$ (Structural Consensus).

To prevent complete denial-of-service, G2 enforces the **Removal Cap ($C_r = 0.50$)**:
$$\text{Max Pruned} = \lfloor k \times C_r \rfloor$$
Even if all $k$ passages exhibit high poisoning scores, G2 prunes at most $50\%$ of the retrieved set, ensuring the downstream generator receives text.

### 3.3 G3: Consensus & Claim Verification
G3 extracts atomic claims $\{c_1, \dots, c_m\}$ from candidate response $y$ and evaluates directional entailment against supporting evidence $d$. In production serving, G3 operates via an auditable deterministic fallback mode, while offline research evaluation validates fine-tuned DeBERTa-v3 cross-encoders.

---

## 4. Empirical Evaluation & Generalization Analysis

### 4.1 Evaluation Protocol & Strict Blocking Rule
In all experiments, we enforce the **Strict Blocking Rule**:
- For adversarial inputs: Only explicit hard-`BLOCK` decisions count as True Positives ($TP$). Soft warnings (`FLAG`) or partial allowances count strictly as False Negatives ($FN$).
- For benign inputs: Only explicit `ALLOW` decisions count as True Negatives ($TN$). Any interruption (`FLAG` or `BLOCK`) counts as a False Positive ($FP$).

All confidence intervals are reported as 2-sided Wilson Score intervals at 95% confidence ($\alpha = 0.05, z = 1.95996$).

---

### 4.2 Benchmark Performance vs. Unseen Generalization

Table 1 presents the central empirical finding of our investigation: the stark contrast between static benchmark evaluation and unseen adversarial generalization.

**Table 1: TrustRAG Evaluation Across Benchmark vs. Unseen Adversarial Cohorts.**

| Cohort | Adversarial ($n$) | Benign ($n$) | ADR (%) | Wilson 95% CI (ADR) | ASR (%) | Clean Delivery (%) | Strict FPR (%) | Wilson 95% CI (FPR) |
|---|---|---|---|---|---|---|---|---|
| **Phase 23 (Audited)** | 120 | 20 | 95.83% | [90.62%, 98.21%] | 4.17% | 100.00% | 0.00% | [0.00%, 16.11%] |
| **Phase 25 (Curated)** | 164 | 505 | 100.00% | [97.71%, 100.00%] | 0.00% | 100.00% | 0.00% | [0.00%, 0.75%] |
| **Phase 26 (Unseen)** | **500** | **500** | **71.80%** | **[67.70%, 75.57%]** | **28.20%** | **100.00%** | **0.00%** | **[0.00%, 0.76%]** |

**Statistical Significance of Generalization Drop:**
A two-proportion z-test comparing Phase 25 ($164/164$) to Phase 26 unseen attacks ($359/500$) yields $z = 7.62$ ($p < 0.0001$). This confirms that the 100% ADR reported in Phase 25 was an artifact of in-distribution evaluation.

---

### 4.3 Category-Wise Attack Breakdown
To understand where deterministic guardrails succeed and fail, Table 2 details the performance across all 13 attack categories in the 500-sample unseen suite.

**Table 2: Performance Breakdown Across 13 Unseen Adversarial Categories ($n=500$).**

| Category | Samples | Blocked ($TP$) | Allowed ($FN$) | ADR (%) | Wilson 95% CI | Vulnerability Classification |
|---|---|---|---|---|---|---|
| `research_pretext_attack` | 40 | 40 | 0 | **100.00%** | [91.24%, 100.00%] | Robust: Pretext keywords captured |
| `unicode_homoglyphs` | 40 | 40 | 0 | **100.00%** | [91.24%, 100.00%] | Robust: Complete confusable folding |
| `zero_width_obfuscation` | 40 | 40 | 0 | **100.00%** | [91.24%, 100.00%] | Robust: Clean invisible character strip |
| `multi_turn_contextual` | 40 | 40 | 0 | **100.00%** | [91.24%, 100.00%] | Robust: Step signifiers captured |
| `mixed_benign_malicious` | 40 | 40 | 0 | **100.00%** | [91.24%, 100.00%] | Robust: Tail payload matched |
| `malicious_command_execution` | 40 | 40 | 0 | **100.00%** | [91.24%, 100.00%] | Robust: Shell pipe syntax intercepted |
| `harmful_intent_weaponization` | 40 | 40 | 0 | **100.00%** | [91.24%, 100.00%] | Robust: Policy layer blocks malware code |
| `delimiter_context_breakout` | 40 | 30 | 10 | **75.00%** | [59.81%, 85.81%] | Moderate: Novel markup tags leak |
| `adaptive_g1_evasion` | 20 | 12 | 8 | **60.00%** | [38.66%, 78.12%] | Moderate: Hyphenation evades regex |
| `direct_prompt_injection` | 40 | 16 | 24 | **40.00%** | [26.35%, 55.40%] | **High Fragility: Unlisted verb/noun pairs** |
| `role_hijack_jailbreak` | 40 | 12 | 28 | **30.00%** | [18.07%, 45.43%] | **High Fragility: Novel entity personas** |
| `multilingual_injection` | 40 | 6 | 34 | **15.00%** | [7.06%, 29.07%] | **Critical Blindness: Non-Latin scripts** |
| `narrative_fictional_evasion` | 40 | 3 | 37 | **7.50%** | [2.58%, 19.86%] | **Critical Blindness: Novel creative framing** |

---

### 4.4 Multilingual Blind-Spot Analysis
Table 3 highlights the language-level performance across the 8 evaluated languages.

**Table 3: Cross-Lingual Injection Detection Breakdown ($n=40$).**

| Language | Script | Evaluated | Blocked | ADR (%) | Failure Cause |
|---|---|---|---|---|---|
| **Spanish** | Latin | 4 | 2 | **50.00%** | Phrasing variations (`pasa por alto`) |
| **French** | Latin | 4 | 2 | **50.00%** | Verb synonyms (`contournez les filtres`) |
| **German** | Latin | 4 | 2 | **50.00%** | Phrasing variations (`umgehe alle richtlinien`) |
| **Russian** | Cyrillic | 4 | 0 | **0.00%** | Cyrillic verbs completely absent from rules |
| **Chinese** | Hanzi | 4 | 0 | **0.00%** | CJK ideographs completely absent from rules |
| **Hindi** | Devanagari | 4 | 0 | **0.00%** | Devanagari script completely absent from rules |
| **Arabic** | Arabic | 4 | 0 | **0.00%** | Arabic script completely absent from rules |
| **Japanese** | Kanji/Kana | 4 | 0 | **0.00%** | Kanji/Kana completely absent from rules |
| **Mixed Variants** | Mixed | 8 | 0 | **0.00%** | Trailing token disruption |

---

## 5. Controlled Ablation Study

We evaluate the independent contributions of G1, G2, and G3 across identical cohorts of 100 adversarial and 100 benign queries.

**Table 4: Controlled Layer Ablation Results ($n=200$).**

| Configuration | ADR (%) | Wilson 95% CI | Clean Delivery (%) | Strict FPR (%) | Avg Latency (ms) |
|---|---|---|---|---|---|
| **1. Baseline RAG (No Defense)** | 0.00% | [0.00%, 3.70%] | 100.00% | 0.00% | 0.000 ms |
| **2. G1 Guardrail Only** | 48.00% | [38.46%, 57.68%] | 100.00% | 0.00% | 0.194 ms |
| **3. G2 Document MSD Only** | 0.00% | [0.00%, 3.70%] | 100.00% | 0.00% | 0.000 ms |
| **4. G1 + G2 Combined** | 48.00% | [38.46%, 57.68%] | 100.00% | 0.00% | 0.193 ms |
| **5. Full Pipeline (G1+G2+G3)** | 48.00% | [38.46%, 57.68%] | 100.00% | 0.00% | 0.194 ms |

*Ablation Finding:* G1 is the sole contributor to query-level attack interception. Adding G1 introduces $<0.20$ ms of latency, validating that pre-retrieval filtering imposes virtually zero computational overhead.

---

## 6. Retrieval Poisoning & The Sybil Frontier

Table 5 evaluates G2 MSD under varying candidate poisoning ratios ($k=5$).

**Table 5: Multi-Document Poisoning & Removal Cap Saturation ($k=5$).**

| Scenario | Injected Poison | Poison Ratio | G2 Detected | Pruned Docs | Residual Poison in Context | Removal Cap Hit? | Context Leakage |
|---|---|---|---|---|---|---|---|
| **Clean Baseline** | 0 | 0.0% | 0 | 0 | **0** | No | 0.0% |
| **Single Poisoned** | 1 | 20.0% | 1 | 1 | **0** | No | 0.0% |
| **Multi Poisoned** | 2 | 40.0% | 2 | 2 | **0** | No | 0.0% |
| **Sybil Majority** | 3 | 60.0% | 3 | 2 | **1** | **YES** | **20.0%** |
| **Sybil Flooding** | 4 | 80.0% | 4 | 2 | **2** | **YES** | **40.0%** |

*The Sybil Frontier Trade-Off:* When the adversary controls $>50\%$ of retrieved passages, the Removal Cap ($C_r = 0.50$) deliberately caps pruning to prevent context starvation. While G2 detection is $100\%$, residual poisoned passages intentionally reach the LLM context.

---

## 7. Serving Latency & Deployment Architecture

**Table 6: Latency Profile Across Processing Layers.**

| Measurement Layer | Samples | P50 (ms) | P95 (ms) | P99 (ms) | Mean (ms) | Execution Mode |
|---|---|---|---|---|---|---|
| **G1 In-Process Screening** | 1,000 | **0.109** | 0.129 | 0.136 | 0.111 | CPU Regular Expression |
| **G2 MSD Candidate Scoring** | 200 | **1.058** | 2.072 | 2.441 | 1.157 | CPU TF-IDF / Heuristic |
| **Server Handler Dispatch** | 100 | **1.429** | 1.931 | 2.076 | 1.482 | Async aiohttp Event Loop |
| **HTTP Round-Trip Loopback** | 100 | **5.546** | 8.165 | 9.381 | 5.824 | Localhost TCP Socket |

**Deployment Truthfulness:** Production serving operates G1 and G2 deterministically on CPU. The SRM component runs in `deterministic_fallback` mode (`is_real_model=False`). G1 latency is strictly non-neural.

---

## 8. Limitations

1. **Deterministic Lexical Fragility:** G1 relies on compiled regexes. Unseen verbs, non-Latin scripts, and novel creative framings evade pre-retrieval interception.
2. **Statelessness in Multi-Turn Dialogues:** G1 evaluates individual queries without conversational state. Fragmented multi-turn attacks spread across separate turns evade detection.
3. **Sybil Cap Context Leakage:** In corpus poisoning campaigns where malicious documents achieve retrieval dominance ($>50\%$), the removal cap permits poisoned documents to reach context.

---

## 9. Conclusion

TrustRAG demonstrates that multi-tiered defense-in-depth provides substantial security advantages for RAG systems: sub-millisecond query screening, complete defense against complex character obfuscations, 100% clean delivery on diverse benign inquiries, and high detection of retrieval poisoning. However, by subjecting TrustRAG to an independent generalization evaluation, we show that empirical security cannot be captured by static 100% metrics. Acknowledging generalization bounds (71.8% ADR) and architectural trade-offs (the Sybil removal cap) is essential for advancing robust, credible real-world RAG security.

---

## 10. Verifiable References

1. **Karpukhin et al. (2020).** Dense Passage Retrieval for Open-Domain Question Answering. *Proceedings of EMNLP 2020*, pp. 6769–6781.
2. **Lewis et al. (2020).** Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *Advances in Neural Information Processing Systems (NeurIPS 2020)*, 33:9459–9474.
3. **Zou et al. (2025).** PoisonedRAG: Knowledge Poisoning Attacks Against Retrieval-Augmented Generation. *Proceedings of the 34th USENIX Security Symposium (USENIX Security 2025)*.
4. **Bao et al. (2025).** RSB: Evaluating Robustness of Retrieval-Augmented Generation Under Corpus Poisoning. *arXiv preprint arXiv:2505.18543*.
5. **Li et al. (2023).** HaluEval: A Large-Scale Hallucination Evaluation Benchmark for Large Language Models. *Proceedings of EMNLP 2023*, pp. 6449–6464.
6. **He et al. (2023).** DeBERTaV3: Improving DeBERTa using ELECTRA-Style Pre-Training with Gradient-Disentangled Embedding Sharing. *Transactions of the ACL (TACL 2023)*.
7. **Wilson, E. B. (1927).** Probable Inference, the Law of Succession, and Statistical Inference. *Journal of the American Statistical Association*, 22(158):209–212.
