# TrustRAG — Track 1, Step 2.3: Independent Corrected Baseline Acceptance Audit
# 05 — Baseline Fairness, Independence & Leakage Audit

**Audit Objective:** Confirm that the established baselines are scientifically fair, uncompromised by data leakage, free of test-set tuning, and representative of genuine zero-shot heuristic capability before neural fine-tuning.

---

## 1. Fairness Checklist

| Fairness Dimension | Audit Requirement | Verification Evidence & Findings | Compliance Status |
| :--- | :--- | :--- | :---: |
| **Identical Evaluation Populations** | All baselines (`no_verification`, `default_g3`, `strict_g3`) must be evaluated on the exact same test splits. | Verified: RAGTruth evaluated on identical 2,700 records; HaluEval evaluated on identical 3,000 records across all three modes. Record IDs match 100%. | **COMPLIANT** |
| **Zero Test-Split Data Leakage** | Test splits must never be used during heuristic construction or vocabulary building. | Verified: TF-IDF vectorizers are fit on-the-fly per record between the claim and the retrieved passage/evidence context only. No global corpus vocabulary or IDF weights are trained on test data. | **COMPLIANT** |
| **No Benchmark-Specific Tuning** | Parameters must not be tuned or overfitted to maximize test-set metrics. | Verified: `min_support_coverage = 0.65` is the standard Phase 10 production default established long before benchmark evaluation. `min_support_coverage = 0.80` is a round, generic strict threshold. No parameter grid searches were conducted on the test sets. | **COMPLIANT** |
| **No Test-Set Modifications** | Dataset ground truth labels, claims, and context must remain untouched. | Verified: SHA-256 checksums of raw and processed test files match Track 1, Step 1 manifests exactly. Zero edits or cherry-picking. | **COMPLIANT** |
| **Clear Heuristic Demarcation** | Evaluation must reflect pure heuristic algorithms without neural or LLM assistance. | Verified: G3 verification relies entirely on `OutputEvidenceVerifier` (spacy/regex tokenization, TF-IDF cosine similarity, entity extraction, and numerical consistency). No API calls, neural embeddings, or LLM verifiers were employed. | **COMPLIANT** |
| **Accurate Retrieval Scope Disclosure** | Retrieval evaluation constraints must be explicitly disclosed. | Verified: MS MARCO candidate snippet re-ranking (6–10 snippets) is explicitly disclosed and distinguished from full 8.84M web corpus retrieval, which is formally marked as `BLOCKED`. HotpotQA candidate distractor paragraphs (10 paragraphs) are clearly documented. | **COMPLIANT** |

---

## 2. Scientific Evaluation of Heuristic Behaviors

### 2.1 The RAGTruth Contradiction Paradox (High FCR)
On RAGTruth, the heuristic G3 verifier exhibits a False Contradiction Rate of **62.61%** (default) and **64.03%** (strict). 
- **Cause:** RAGTruth factual claims often paraphrase source passages using synonyms, syntactic inversions, and high-level summaries. Heuristic bag-of-words overlap fails to capture semantic entailment between synonymous phrases (e.g. "relinquished control" vs "stepped down from his position"), triggering the coverage fallback to `CONTRADICTED` or `INSUFFICIENT_EVIDENCE`.
- **Fairness Assessment:** This high error rate is not suppressed, concealed, or artificially smoothed. Reporting it transparently establishes the critical scientific justification for **Track 2 Neural Verification (Cross-Encoder / DeBERTa NLI)**.

### 2.2 The HaluEval Safety Performance
On HaluEval, the heuristic verifier performs significantly better:
- Default Policy 1 Accuracy: **72.50%**, Strict Policy 1 Accuracy: **75.93%**.
- Strict Decisive Accuracy: **88.40%**.
- FCR is remarkably low: **0.87%** (only 13 out of 1,500 factual claims contradicted).
- **Cause:** HaluEval QA hallucinated answers frequently introduce distinct, hallucinated named entities or conflicting factual statements that easily violate TF-IDF and entity overlap checks.
- **Fairness Assessment:** The contrast between RAGTruth and HaluEval highlights the structural differences between hallucination benchmarks and underscores the necessity of multi-dataset evaluation.

---

## 3. Fairness Audit Conclusion

The Track 1 baseline evaluations are scientifically sound, strictly independent, free of data contamination, and completely objective. They provide a rock-solid, unimpeachable baseline against which all future neural architectures in Track 2 will be measured.

