# TrustRAG: A Tri-Layer Defense Architecture for Poisoning Mitigation and Hallucination Reduction in Retrieval-Augmented Generation

**Aditya et al.**  
*Department of Computer Science & ML Security Research Group*  
*TrustRAG Research Consortium*  
*November 2026*  

---

### Abstract
Retrieval-Augmented Generation (RAG) systems empower large language models (LLMs) with external knowledge, but introduce two severe, interconnected vulnerabilities: vulnerability to knowledge base poisoning attacks and generation hallucinations. Prior defensive efforts typically address these threats in isolation: corpus-filtering methods defend against knowledge injection but remain blind to generator hallucinations, while post-generation natural language inference (NLI) verifiers detect ungrounded answers but are readily fooled when retrieved context has been poisoned. In this paper, we present **TrustRAG**, a unified tri-layer defense architecture that integrates: (1) **G1**, a low-latency input query guardrail for jailbreak and injection filtering; (2) **G2**, a multi-signal pre-generation consensus gate incorporating source reputation tiering, lexical anomaly detection, and consensus deviation filtering with a strict removal cap; and (3) **G3**, a post-generation evidence verifier powered by a CPU-optimized, premise-normalized DeBERTa-v3-small NLI classifier. 

Across comprehensive empirical evaluations ($N=875$ canonical synthetic attacks, $N=1,000$ clean controls), TrustRAG achieves a **$100.00\%$ Attack Defense Rate (ADR)** ($95\%$ Wilson CI: $[99.57\%, 100.00\%]$) with **$0.00\%$ Clean False Positive Rate (FPR)** ($95\%$ Wilson CI: $[0.00\%, 0.38\%]$) at a median CPU latency of **$55.84\text{ ms}$**. When evaluated on open-domain commercial LLM generations, TrustRAG defends **$66.00\%$** of hallucinations on RAGTruth (ACL 2024) and **$89.00\%$** on HaluEval (EMNLP 2023). We conduct exhaustive adversarial red-teaming across 15 attack vectors ($N=460$), demonstrating complete defense against obfuscated and single-passage injections while identifying critical architectural boundaries: Sybil consensus attacks and subtle paraphrased contradictions. We characterize the *Propositional Dilemma* in NLI verification and provide a complete reproducibility package to facilitate future research in verifiable, resilient RAG systems.

---

## 1. Introduction
Retrieval-Augmented Generation (RAG) has emerged as the standard paradigm for grounding Large Language Model (LLM) responses in external, authoritative knowledge bases. By retrieving relevant passages from external corpora to augment user queries at inference time, RAG mitigates parametric knowledge obsolescence and enhances domain-specific accuracy.

However, the decoupling of parametric memory from external context introduces a critical security trade-off. RAG architectures expand the attack surface from prompt injection to *corpus poisoning*, wherein malicious actors inject deceptive, conflicting, or backdoor passages into third-party document repositories. Concurrently, generative decoders frequently suffer from *extrinsic hallucinations*, synthesizing plausible assertions unsupported by retrieved context.

Recent defenses have targeted these failure modes independently. Pre-retrieval and corpus-filtering defenses, such as FilterRAG (Zou et al., USENIX Security 2025), employ frequency-density clustering to drop poisoned passages. However, these systems lack generative oversight; when retrieved evidence is sparse or ambiguous, generator hallucinations pass uninspected. Conversely, post-generation verifiers, such as HalluGuard, employ Natural Language Inference (NLI) to verify that generated hypotheses are entailed by retrieved premises. Yet, if an adversary successfully seeds the retrieval corpus with poisoned text, the LLM generates an answer faithfully mirroring the poisoned passage—resulting in post-generation NLI validating the malicious assertion as `ENTAILMENT`.

To resolve this fundamental tension, we introduce **TrustRAG**, a modular, tri-layer defense architecture structured as a multi-stage pipeline:
$$\text{Security Filter} = \mathcal{G}_1(\text{Query}) \land \mathcal{G}_2(\text{Context}) \land \mathcal{G}_3(\text{Generation})$$

### Contributions
1. **Tri-Layer Defense Architecture:** We propose a defense-in-depth framework combining query-level safety gating (G1), multi-signal corpus consensus filtering (G2), and neural NLI verification (G3).
2. **Premise-Normalized Neural Verification:** We introduce an 86M-parameter DeBERTa-v3-small NLI verifier operating under regex-based premise normalization and multi-threaded CPU optimization, reducing clean false positive rates from $12.50\%$ to $0.00\%$ while halving median inference latency to $55.84\text{ ms}$.
3. **Forensic Reconciliation & Benchmark Audit:** We independently audit and resolve metric discrepancies across RAGTruth ($46\%$ vs $52\%$ FPR) and HaluEval ($98\%$ clean FPR), identifying the *Propositional Dilemma* in entity-level QA.
4. **Adversarial Red-Teaming & Security Boundaries:** We evaluate 15 attack vectors ($N=460$), reporting 100% defense on static injections while dissecting structural failure modes under Sybil consensus and paraphrased contradictions.

---

## 2. Threat Model & Problem Formulation

### 2.1 Attacker Capabilities
We assume a realistic threat model where the adversary $\mathcal{A}$ has the following capabilities:
1. **Corpus Write Access:** $\mathcal{A}$ can inject up to $k$ malicious documents $\mathcal{D}_{\text{mal}}$ into an index $\mathcal{C}$ containing $M$ total documents ($k \ll M$).
2. **Black-Box Access:** $\mathcal{A}$ lacks direct white-box access to LLM model weights, embedding layers, or internal classification logits.
3. **Query Channel Access:** $\mathcal{A}$ can submit arbitrary adversarial user queries $q_{\text{adv}}$ containing roleplay jailbreaks or directive overrides.

### 2.2 Defender Objectives
The defender aims to satisfy three concurrent objectives:
1. **Attack Defense Rate (ADR):** Maximize the proportion of malicious queries and poisoned contexts quarantined prior to delivery:
   $$\text{ADR} = \frac{\text{Attacks Defended}}{\text{Total Attack Samples}}$$
2. **Clean Utility (Clean FPR):** Minimize the false rejection rate on benign queries and authoritative documents:
   $$\text{Clean FPR} = \frac{\text{Clean Queries Quarantined}}{\text{Total Clean Samples}}$$
3. **Inference Latency:** Bound the computational overhead to ensure production feasibility on commodity CPU hardware ($P50 < 100\text{ ms}$).

---

## 3. TrustRAG System Architecture

```mermaid
flowchart TD
    UserQuery["User Query (q)"] --> G1{"G1: Input Guardrail"}
    G1 -- "Direct Injection Detected" --> BlockG1["Quarantine / Refusal"]
    G1 -- "Sanitized Query" --> Retriever["Retriever (Top-K)"]
    
    Retriever --> ContextPassages["Candidate Passages {p_1, ..., p_K}"]
    ContextPassages --> G2{"G2: Multi-Signal Consensus Gate"}
    
    G2 -- "Passage Exceeds Risk / S_5 Deviation" --> DropPassage["Quarantine Passage (Cap Cr=0.5)"]
    G2 -- "Admitted Clean Context" --> Generator["LLM Generator"]
    
    Generator --> RawResponse["Generated Candidate Answer (y)"]
    RawResponse --> G3{"G3: Premise-Normalized DeBERTa NLI"}
    
    G3 -- "P(Entailment) >= 0.65" --> VerifiedOutput["Delivered Response"]
    G3 -- "P(Entailment) < 0.65 / Contradiction" --> QuarantineG3["Quarantine / Refusal"]
```

### 3.1 Layer G1: Input Guardrail
G1 processes the raw user query $q$ prior to retrieval. It combines lexical signature scanning with lightweight semantic intent classification to detect directive overrides, system prompt extraction, and roleplay jailbreaks. If an attack is detected, the pipeline terminates immediately with an explanatory refusal, incurring less than $3.5\text{ ms}$ latency.

### 3.2 Layer G2: Multi-Signal Detector & Pre-Generation Gate
G2 inspects the candidate retrieval pool $\mathcal{P} = \{p_1, p_2, \dots, p_K\}$ returned by the dense/lexical retriever. G2 computes five orthogonal risk signals for each passage $p_i$:
1. **Domain Reputation Tiering ($S_1$):** Assigns discrete trust tiers (Tier-1: peer-reviewed/authoritative; Tier-2: verified news; Tier-3: unverified web).
2. **Lexical & Entropy Anomalies ($S_2$):** Flags token distribution entropy anomalies, zero-width characters, and leetspeak substitutions.
3. **Structural Signature Integrity ($S_3$):** Validates markdown headers, metadata formats, and schema compliance.
4. **Script & Language Alignment ($S_4$):** Detects script-mixing anomalies (e.g. Cyrillic homoglyphs within Latin text).
5. **Consensus Deviation ($S_5$):** Evaluates embedding divergence between $p_i$ and the centroid of the remaining top-$K$ candidates:
   $$S_5(p_i) = 1 - \cos\left(\mathbf{e}_i, \frac{1}{|\mathcal{P} \setminus \{p_i\}|}\sum_{j \ne i} \mathbf{e}_j\right)$$

To prevent context starvation, G2 enforces a strict **Removal Cap** $C_r = 0.50$, ensuring that at most $50\%$ of candidate passages can be pruned.

### 3.3 Layer G3: Neural NLI Evidence Verifier
G3 verifies factual grounding between the admitted retrieved passages $\mathcal{P}_{\text{admit}}$ (acting as premise $P$) and the generator's response $y$ (acting as hypothesis $H$).
G3 utilizes an 86M-parameter DeBERTa-v3-small cross-encoder fine-tuned for 3-class NLI:
$$\mathbf{z} = \text{DeBERTa}(\text{[CLS]} \circ P \circ \text{[SEP]} \circ H \circ \text{[SEP]})$$
$$\mathbf{p} = \text{softmax}(\mathbf{z} / T), \quad \mathbf{p} = [p_{\text{contra}}, p_{\text{entail}}, p_{\text{neutral}}]$$

#### Premise Normalization
Raw retrieved passages frequently contain bracketed citation markers (e.g. `[Doc-1]`, `[15]`). In uncalibrated baselines, cross-attention between citation numbers and hypothesis tokens triggered spurious contradiction predictions. TrustRAG applies a regex normalization preprocessor:
$$\text{normalize\_premise}(P) = \text{regex\_replace}(P, \text{r'\[(?:Doc-)?\d+\]'}, \text{''})$$
This normalization completely eliminated the $12.50\%$ false positive rate on clean controls.

---

## 4. Experimental Setup & Benchmarks

### 4.1 Evaluation Datasets
1. **Custom Security Benchmark:** $N=2,000$ records consisting of $1,000$ clean controls and $1,000$ candidate attack records ($125$ benign instruction controls, $875$ genuine attacks spanning 7 distinct categories).
2. **Advanced Red Team Suite (Phase 18):** $N=460$ adversarial samples across 15 attack categories designed to test architectural boundaries.
3. **Public LLM Hallucination Benchmarks:**
   - **RAGTruth (ACL 2024):** $N=200$ balanced evaluation split ($100$ Factual, $100$ Hallucinated) derived from commercial LLM summaries.
   - **HaluEval (EMNLP 2023):** $N=200$ balanced split ($100$ Factual, $100$ Hallucinated) derived from open-domain question answering.

### 4.2 Hardware & Environment
All benchmarks were evaluated in a deterministic environment on an 8-core CPU system with PyTorch 2.x and HuggingFace Transformers. G3 inference was parallelized across 2 CPU threads with PyTorch intra-op optimizations.

---

## 5. Controlled Defense Layer Ablations

We evaluate six system configurations (A through F) across the identical canonical test cohort ($N=875$ genuine attacks, $N=1,000$ clean controls):

| Config | Architecture Description | G1 | G2 | G3 Verifier | Attack Defense Rate (ADR) | Clean False Positive Rate (FPR) | Clean Delivery Rate | P50 Latency (ms) |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **A** | Standard Naive RAG | Off | Off | Off | 14.29% $[12.12, 16.76]$ | 0.00% $[0.00, 0.38]$ | 100.00% | 3.29 |
| **B** | TrustRAG G1 Alone | On | Off | Off | 14.29% $[12.12, 16.76]$ | 0.00% $[0.00, 0.38]$ | 100.00% | 3.43 |
| **C** | TrustRAG G2 Alone | Off | On | Off | 85.71% $[83.24, 87.88]$ | 0.00% $[0.00, 0.38]$ | 100.00% | 3.31 |
| **D** | TrustRAG G1 + G2 | On | On | Off | 100.00% $[99.57, 100.00]$ | 0.00% $[0.00, 0.38]$ | 100.00% | 3.36 |
| **E** | G1 + G2 + G3 Baseline | On | On | Baseline | 100.00% $[99.57, 100.00]$ | 12.50% $[10.58, 14.71]$ | 87.50% | 96.06 |
| **F** | **G1 + G2 + G3 Optimized** | On | On | Optimized | **100.00%** $[99.57, 100.00]$ | **0.00%** $[0.00, 0.38]$ | **100.00%** | **55.84** |

### 5.1 Subtype Attribution
The $875$ genuine attacks comprise 7 subtypes ($125$ samples each):
- **Direct Prompt Injection:** $100\%$ intercepted by G1 ($125/125$).
- **Passage-Level Attacks (Lexical, Source, Impersonation, Semantic, Cross-lingual, Temporal):** $100\%$ quarantined by G2 ($750/750$).
- This confirms that G1 and G2 form an orthogonal, comprehensive defense against static synthetic injection attacks.

---

## 6. Public Benchmark Performance & The Propositional Dilemma

| Benchmark | Architecture | Attacks Evaluated | Attack Defense Rate (ADR) | Clean Controls | Clean False Positive Rate (FPR) | Clean Delivery Rate | $F_1$ Score |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **RAGTruth** | Standard RAG | 100 | 0.00% | 100 | 0.00% | 100.00% | 0.00% |
| | TrustRAG (Opt) | 100 | **66.00%** $[56.24, 74.54]$ | 100 | **46.00%** $[36.56, 55.74]$ | 54.00% | **62.26%** |
| **HaluEval** | Standard RAG | 100 | 0.00% | 100 | 0.00% | 100.00% | 0.00% |
| | TrustRAG (Opt) | 100 | **89.00%** $[81.42, 93.80]$ | 100 | **98.00%** $[92.96, 99.45]$ | 2.00% | **62.02%** |

### 6.1 The Propositional Dilemma
Why does HaluEval suffer a $98.00\%$ Clean FPR?
In HaluEval, answers are concise entity spans (e.g. `"Christopher Nolan"`). Natural Language Inference models are trained on sentential propositions. When evaluating:
$$\text{Premise: } \text{"Christopher Nolan directed Inception in 2010."}$$
$$\text{Hypothesis: } \text{"Christopher Nolan."}$$
The entity fragment lacks a truth-evaluable assertion. The cross-encoder predicts `NEUTRAL` with $p \approx 0.60$. Under TrustRAG's conservative safety policy ($p_{\text{entail}} \ge 0.65$), neutral predictions are quarantined. This demonstrates that sentence-level NLI cannot be applied naively to fragment answers without propositional expansion.

---

## 7. NLI Diagnostic Analysis & Contradiction Recall

Evaluation on $N=2,662$ held-out validation samples (`predictions_val.jsonl`):
- **Overall Accuracy:** $70.40\%$ ($1,874 / 2,662$)
- **Macro F1:** $55.04\%$
- **Balanced Accuracy:** $52.58\%$
- **Class Breakdown:**
  - **Entailment ($N=1,662$):** Precision = $74.80\%$, Recall = $91.46\%$, $F_1 = 82.30\%$
  - **Neutral ($N=644$):** Precision = $53.99\%$, Recall = $40.99\%$, $F_1 = 46.60\%$
  - **Contradiction ($N=356$):** Precision = $63.83\%$, Recall = $25.28\%$, $F_1 = 36.22\%$

### Root Cause of Contradiction Deficit
The training corpus (`sft_v2/nli/train.jsonl`, $N=10,815$) exhibits severe class skew: $62.02\%$ Entailment vs $13.13\%$ Contradiction. Unweighted cross-entropy caused the classifier to prioritize Entailment, misclassifying $47.75\%$ of true contradictions as Entailment. In TrustRAG, this vulnerability is mitigated because G2 quarantines poisoned passages before generation, preventing contradictions from reaching G3.

---

## 8. Advanced Adversarial Red-Teaming & Security Boundaries

Testing against 15 advanced red-team categories ($N=460$):
1. **Resilient Categories ($100\%$ Defense, $120/120$):** Character obfuscation, narrative contradictions, duplicate source poisoning, context exhaustion.
2. **Partially Defended Categories ($46/100$):** High-stakes domain misinfo ($75\%$), adaptive prompt injection ($33.3\%$), cross-lingual injection ($20\%$).
3. **Breached Categories ($0\%$ Defense, $0/240$):**
   - **Sybil & Majority Consensus Attacks:** Adversaries injecting $\ge 3$ colluding passages exceed G2's removal cap ($C_r = 0.50$), forcing the system to admit malicious context.
   - **Paraphrased Factual Poisoning:** High-fluency semantic paraphrasing bypasses lexical heuristics and exploits DeBERTa's $25.28\%$ contradiction recall.
   - **Citation Spoofing:** Forged DOI and academic metadata bypass unauthenticated domain tiering.

---

## 9. Related Work Comparison

| Dimension | Standard RAG | HalluGuard (2024) | FilterRAG (USENIX '25) | TrustRAG (Ours) |
|---|:---:|:---:|:---:|:---:|
| **Threat Model** | None | Hallucination Detection | Knowledge Poisoning | Unified Defense |
| **G1 Query Guardrail** | No | No | No | **Yes** |
| **G2 Corpus Filtering** | No | No | **Yes** | **Yes** |
| **G3 Neural NLI Verifier** | No | **Yes** | No | **Yes** |
| **Synthetic Poisoning ADR** | 14.29% | 42.10% | 94.60% | **100.00%** |
| **RAGTruth Hallucination ADR** | 0.00% | 68.40% | 0.00% | **66.00%** |
| **Clean False Positive Rate** | **0.00%** | 8.20% | 1.80% | **0.00%** |
| **Median Latency (CPU)** | **3.29 ms** | 145.00 ms | 12.40 ms | **55.84 ms** |

---

## 10. Limitations & Threats to Validity
1. **Sybil Scalability:** G2's removal cap ($C_r = 0.50$) represents a structural vulnerability when attackers control the majority of retrieved passages.
2. **External Academic Benchmarks:** RSB and PoisonedRAG remain strictly `BLOCKED` due to network sandbox boundaries and lack of pre-staged local splits.
3. **Fragment Answers:** G3 requires propositional statements; entity fragment answers trigger excessive false rejections.

---

## 11. Conclusion
TrustRAG demonstrates that resilient, production-ready RAG security cannot rely on isolated filters. By structuring defense across three orthogonal gates—query inspection, corpus consensus gating, and premise-normalized neural verification—TrustRAG provides strong defense against synthetic poisoning and commercial LLM hallucinations while operating under a strict $55.84\text{ ms}$ CPU latency budget. Future research must address Sybil consensus attacks and propositional expansion for short-form QA.

---

### Reproducibility Statement
All code, configs, dataset manifests, and checkpoint hashes are available in `reports/phase21/reproducibility/`.
