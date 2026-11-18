# TrustRAG Research Completion — Track 1, Step 2: G1 and G2 Evaluation Scope

## 1. Component Scope Designation

In the Track 1, Step 2 benchmark baseline evaluation, the security guardrail components are assigned the following scientific designations:

| Guardrail Component | Evaluation Status | Ground Truth Source | Rationale |
| :--- | :--- | :--- | :--- |
| **G1: Input Guardrail** (Prompt Injection, Delimiters, Base64 Evasion) | **NOT_EVALUABLE** | None in Canonical Benchmarks | Canonical benchmarks (RAGTruth, HaluEval, HotpotQA, MS MARCO) are standard natural language QA and hallucination datasets containing zero adversarial prompt-injection payloads or injection labels. |
| **G2: Source Guardrail** (Knowledge Poisoning, Untrusted Corpus Injection) | **NOT_EVALUABLE** | None in Canonical Benchmarks | Canonical benchmarks contain clean reference passages with no poisoned corpus metadata or attack annotations. |
| **G3: Output Verifier** (Faithfulness, Contradiction Detection) | **COMPLETED** | RAGTruth, HaluEval | Evaluated on 5,700 ground-truth annotated factual and hallucinated claims. |
| **Retriever** (TrustAwareRetriever Candidate Re-ranking) | **COMPLETED** | HotpotQA, MS MARCO | Evaluated on 17,111 candidate retrieval pools. |

---

## 2. Scientific Integrity & Refusal to Fabricate Labels

A foundational principle of TrustRAG research is strict adherence to empirical honesty:

1. **No Pseudo-Labeling:** We strictly refuse to invent or fabricate artificial prompt-injection labels on standard datasets like MS MARCO or HotpotQA. Classifying benign search queries as "safe" without true adversarial negatives yields a meaningless 100% specificity metric.
2. **Dedicated Security Test Suites:** G1 and G2 security protections are independently and comprehensively validated by TrustRAG's dedicated adversarial test suites:
   - `tests/unit/test_phase_13_step05_adv_evasion01.py` (43 adversarial tests)
   - `tests/unit/test_phase_13_step07_urlsafe_b64.py` (52 adversarial tests)
   - `tests/unit/test_phase_13_step09_resource_bounds.py` (Deterministic resource exhaustion tests)
   - Total test suite: 680 automated unit tests passing across all security boundaries.
3. **Future Benchmark Integration:** Dedicated security benchmark datasets (such as RSB, arXiv:2505.18543) will be integrated in subsequent tracks once their official distribution becomes publicly accessible.
