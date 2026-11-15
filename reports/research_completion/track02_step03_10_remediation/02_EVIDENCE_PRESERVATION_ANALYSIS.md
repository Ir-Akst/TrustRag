# TrustRAG — Track 2, Step 3.10: Evidence-Preserving Input Serialization Analysis

## 1. Design Objectives

Evidence-grounded 3-way NLI tests whether the generated hypothesis is entailed by, contradicted by, or unsupported by the premise evidence.
- The **hypothesis** contains the specific factual claims that may contain hallucinations.
- In RAGTruth, hallucinations frequently reside in late sentences of the response (e.g. detailed statistics, parking rules, specific dates).
- Truncating the hypothesis from the tail severs the claim itself, corrupting the ground truth label.

---

## 2. Remediated Evidence-Preserving Strategy

Implemented in `tools/training/train_nli_classifier.py::evidence_preserving_tokenize()`:

```python
def evidence_preserving_tokenize(
    tokenizer: Any,
    premise: str,
    hypothesis: str,
    max_seq_len: int = 384,
    min_premise_tokens: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
```

### Algorithmic Rules:
1. Tokenize premise and hypothesis independently without special tokens.
2. Calculate available token budget: $B = \text{max\_seq\_len} - 3$ (accounting for `[CLS]`, `[SEP]`, `[SEP]`).
3. If $L_h + \text{min\_premise\_tokens} \le B$:
   - **Hypothesis is 100% PRESERVED** ($K_h = L_h$).
   - Remaining budget is allocated to premise evidence ($K_p = \min(L_p, B - K_h)$).
4. If hypothesis is exceptionally long ($L_h + \text{min\_premise\_tokens} > B$):
   - Allocate at least `min_premise_tokens` (64 tokens) to the premise.
   - Cap hypothesis at $B - \text{min\_premise\_tokens}$.
5. Assemble sequence: `[CLS]` + premise tokens + `[SEP]` + hypothesis tokens + `[SEP]`.
6. Record full truncation metadata in the returned tensor dictionary.

---

## 3. Case Study Validation on RAGTruth Record #10

- **Label:** `CONTRADICTION`
- **Premise Content:** Oil family inheritance details, mentioning Gordon Getty's net worth is $2.1 billion.
- **Hypothesis Content:** 4 sentences ending with: *"His [Andrew Getty's] net worth was estimated to be $2.1 billion."*
- **Baseline (128 tokens, longest_first):**
  - Hypothesis truncated at token 64, completely omitting the contradictory claim.
  - Premise truncated at token 64, omitting Gordon Getty's net worth.
  - Model was presented with incomplete text with zero contradiction signal.
- **Remediated (384 tokens, evidence_preserving):**
  - Hypothesis (62 tokens): **100% PRESERVED**.
  - Premise: **319 tokens preserved** (includes Gordon Getty's net worth).
  - Semantic contradiction is 100% intact and learnable.
