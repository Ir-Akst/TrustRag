# TrustRAG — Track 2, Step 1: Independent Neural Training Readiness Audit
# 04 — Odds Ratio Preference Optimization (ORPO) Readiness Audit

**Audit Objective:** Evaluate whether the repository contains valid preference pairs for Odds Ratio Preference Optimization (ORPO) or Direct Preference Optimization (DPO), and determine whether preference fine-tuning is feasible.

---

## 1. Inventory of Preference Data Candidates

| Candidate Source | Underlying Records | Available Pairs | Common Prompt? | Chosen Response? | Rejected Response? | Preference Basis | ORPO Usability Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **HaluEval Train QA** | 14,000 | **7,000** | YES (`query` + `document`) | YES (`right_answer`) | YES (`hallucinated_answer`) | Ground-truth factual accuracy | **USABLE (Response Preference)** |
| **RAGTruth Train** | 15,090 | 0 (Unpaired) | Shared document | Factual claims | Hallucinated claims | Differing prompt types & models | **NOT PAIRED** |
| **HalluGuard Reasoning Traces** | 0 | **0** | N/A | High-quality reasoning | Flawed reasoning | Verification rationale quality | **BLOCKED (ABSENT)** |

---

## 2. In-Depth Analysis of HaluEval Preference Pairs

An inspection of `data/processed/halueval/train.jsonl` was conducted across all 14,000 records:
- **Grouping:** All 14,000 records group into exactly **7,000 unique `source_id` keys** (exactly 2 records per `source_id`).
- **Pair Structure:**
  - In every single pair, both records share identical `metadata.query` and `document` text.
  - Record A has `label: "FACTUAL"` with `metadata.pair_type: "right_answer"`.
  - Record B has `label: "HALLUCINATED"` with `metadata.pair_type: "hallucinated_answer"`.
- **Integrity:**
  - 0 orphan records.
  - 0 non-binary groups.
  - 0 conflicting labels.
  - Exactly **7,000 clean pairwise response preference examples** can be extracted immediately without synthetic generation.

### Format of Extracted HaluEval Preference Pair:
```json
{
  "prompt": "Context: Hollis/Brookline High School is a public school located in Hollis, New Hampshire, serving the towns of Hollis and Brookline... Question: Which wildlife sanctuary is located in the town in which the Hollis/Brookline High School services?",
  "chosen": "Talbot-Taylor Wildlife Sanctuary",
  "rejected": "The Hollis/Brookline High School is located in the Talbot-Taylor Wildlife Sanctuary."
}
```

---

## 3. The ORPO Research Gap: Generation vs Verification

While the 7,000 pairs above are valid for **Response Generation Preference Tuning** (teaching a generator LLM to answer factually rather than hallucinate), they **do not satisfy the HalluGuard SRM specification**:

1. **HalluGuard SRM Objective:**
   - The SRM is a **verifier**, not an answer generator.
   - Its prompt is: `Document + Question + Candidate Claim`.
   - Its output is: `Reasoning Chain + Verdict`.
2. **Required SRM Preference Pairs:**
   - **Chosen:** A well-reasoned verification trace that accurately identifies whether the candidate claim is supported, cites verbatim text from the passage, and reaches the correct verdict.
   - **Rejected:** An unsound reasoning trace that misses contradictory evidence, cites hallucinated spans, or reaches an incorrect verdict.
3. **Current Repository Deficit:**
   - No paired reasoning traces exist in the repository.
   - Generating these pairs requires running an offline LLM (e.g. Llama-3.3-70B) over the 7,000 HaluEval pairs to generate contrasting sound vs flawed verification chains.

---

## 4. Software & Library Dependencies for ORPO

Even if preference pairs were fully formatted:
- **Required Framework:** Hugging Face `trl` (Transformer Reinforcement Learning) library provides `ORPOTrainer` and `ORPOConfig`.
- **Status:** `trl` is **NOT INSTALLED** in the python environment.
- **Dependency Chain:** `trl` requires `transformers >= 4.40`, `torch >= 2.1`, `peft >= 0.10`, and `accelerate >= 0.28` — none of which are present.

---

## 5. ORPO Readiness Conclusion

- **HaluEval Response Preference:** **7,000 valid pairs exist** for standard response preference tuning.
- **HalluGuard Verifier ORPO:** **BLOCKED**. No reasoning trace preference pairs exist, and `trl` is uninstalled.
- **Recommendation:** Postpone ORPO until Stage 1 (SFT) is successfully trained, validated, and proven on benchmark data.

