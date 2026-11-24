# Phase 30 — G2 Sybil Attack Resilience & Removal Cap Trade-off Analysis

---

## 1. Threat Model: Sybil Knowledge-Poisoning & Starvation

In Retrieval-Augmented Generation (RAG), a **Sybil knowledge poisoning attack** occurs when an adversary injects numerous colluding malicious documents into the knowledge base to manipulate retrieval results.

To protect generation quality and prevent denial-of-service, TrustRAG enforces a **retrieval removal cap**:
$$\text{removal\_cap} = \lfloor K \times \text{removal\_cap\_ratio} \rfloor \le \lfloor K / 2 \rfloor$$
With requested final $K=10$ and default $\text{removal\_cap\_ratio} = 0.50$, at most **$\lfloor 10 \times 0.5 \rfloor = 5$ passages** can be pruned.

This introduces a fundamental security vs. availability trade-off:
- **Availability Guarantee:** Enforcing the cap guarantees that an attacker cannot starve the LLM by causing $100\%$ of candidate passages to be discarded.
- **Residual Poisoning Risk:** When an attacker floods the retrieval pool with $>50\%$ poisoned documents, the excess poisoned passages cannot be pruned by G2 and survive into the candidate pool.

---

## 2. Empirical Benchmark Results ($K=10$, Ratios $10\%$ to $80\%$)

We evaluated G2 Multi-Signal Detector performance across 8 controlled poisoning ratios in a candidate pool of $K=10$:

| Injected Poison Ratio | Injected Poison Passages | Injected Clean Passages | MSD Detected Poison | Removal Cap Limit | Cap Applied? | Passages Pruned | Residual Poison in Context | Clean Passages Retained | Availability Preserved? |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$10\%$** | 1 | 9 | 1 | 5 | No | **1** | **0** | 9 | **Yes** ($100\%$) |
| **$20\%$** | 2 | 8 | 2 | 5 | No | **2** | **0** | 8 | **Yes** ($100\%$) |
| **$30\%$** | 3 | 7 | 3 | 5 | No | **3** | **0** | 7 | **Yes** ($100\%$) |
| **$40\%$** | 4 | 6 | 4 | 5 | No | **4** | **0** | 6 | **Yes** ($100\%$) |
| **$50\%$** | 5 | 5 | 5 | 5 | No | **5** | **0** | 5 | **Yes** ($100\%$) |
| **$60\%$** | 6 | 4 | 6 | 5 | **Yes** | **5** | **1** | 4 | **Yes** ($100\%$) |
| **$70\%$** | 7 | 3 | 7 | 5 | **Yes** | **5** | **2** | 3 | **Yes** ($100\%$) |
| **$80\%$** | 8 | 2 | 8 | 5 | **Yes** | **5** | **3** | 2 | **Yes** ($100\%$) |

---

## 3. Security vs Availability Trade-off Analysis

### 1. Safe Operational Envelope ($\le 50\%$ Poisoning):
- For all poisoning ratios up to $50\%$, MSD detection ($100\%$ precision/recall on injected Sybils) combined with the removal cap cleanly purges **all malicious documents**.
- **Residual Poisoning:** **$0$ passages**.
- **Clean Document Retention:** **$100\%$** of clean documents are retained.

### 2. Saturation & Spillover Regime ($> 50\%$ Poisoning):
- At poisoning ratios $\ge 60\%$, the number of malicious candidates exceeds the 5-document budget.
- The retrieval engine prioritizes the top 5 lowest-trust poisoned passages for pruning.
- Consequently, $1$ to $3$ residual poisoned passages remain in the surviving context pool.

### 3. Downstream Containment by G3:
- In the full pipeline (`src/trustrag/pipeline/trustrag_pipeline.py`), surviving passages flagged with high instruction risk or security anomalies trigger the **Pre-Generation Evidence Gate** (`_is_security_quarantined_assessment`).
- Unsafe passages are quarantined, and if contaminated evidence reaches generation, the generator output is quarantined from public release (`OUTPUT:QUARANTINED_POISONED_CONTEXT`).
- Thus, the removal cap preserves retrieval pipeline execution, while downstream verification prevents unverified attacker payloads from reaching the end user.
