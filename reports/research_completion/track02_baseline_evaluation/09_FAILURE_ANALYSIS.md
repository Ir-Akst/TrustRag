# TrustRAG Research Completion — Track 1, Step 2: Failure Analysis

## 1. Failure Taxonomy & Quantitative Distribution

Across the 5,700 evaluated G3 verification records, errors were categorized into distinct failure types:

```
Failure Distribution:
-----------------------------------------------------------
RAGTruth (2,700 records):
  - False Contradictions (Factual flagged Contradicted): 1,100 (40.74%)
  - Insufficient Evidence on Factual:                      285 (10.56%)
  - False Supported (Hallucinated accepted):                 0 ( 0.00%)
  - Correct / Non-Failure:                               1,315 (48.70%)

HaluEval (3,000 records):
  - Insufficient Evidence on Factual:                      573 (19.10%)
  - False Supported (Hallucinated accepted):               239 ( 7.97%)
  - False Contradictions (Factual flagged Contradicted):    13 ( 0.43%)
  - Correct / Non-Failure:                               2,175 (72.50%)
-----------------------------------------------------------
```

---

## 2. Concrete Case Studies from Dataset Records

### Case 1: Paraphrase and Synonym Mismatch (False Contradiction)
- **Record ID:** `ragtruth_26`
- **Ground Truth:** `FACTUAL`
- **Verifier Verdict:** `CONTRADICTED`
- **Claim:** `"The FBI charged a Philadelphia woman named Keonna Thomas, also known as Fatayat Al Khilafah, with attempting to provide material support to ISIS."`
- **Context Preview:** Federal prosecutors unsealed criminal charges alleging the defendant sought travel to Syria...
- **Failure Cause:** The model used synonyms ("charged", "attempting to provide material support") while the reference text used slightly different legal phrasing. The lexical overlap score fell below 0.6, triggering a contradiction verdict.

### Case 2: Syntactic Inversion (False Contradiction)
- **Record ID:** `ragtruth_27`
- **Ground Truth:** `FACTUAL`
- **Verifier Verdict:** `CONTRADICTED`
- **Claim:** `"FBI charges Philadelphia woman with attempting to join ISIS after purchasing a plane ticket to Spain."`
- **Failure Cause:** Headline-style grammatical compression without a finite verb resulted in low TF-IDF token intersection with narrative source paragraphs.

### Case 3: Ultra-Short Entity Answers (Insufficient Evidence Abstention)
- **Record ID:** `halueval_7170_factual`
- **Ground Truth:** `FACTUAL`
- **Verifier Verdict:** `INSUFFICIENT_EVIDENCE`
- **Claim:** `"track"`
- **Context:** A sports competition context where the event was track and field.
- **Failure Cause:** Single-word claims lack sufficient sentence length and token entropy to satisfy the minimum length filter, causing the verifier to abstain.

### Case 4: Subtle Entity Hallucination (False Supported)
- **Record ID:** `halueval_2962_hallucinated`
- **Ground Truth:** `HALLUCINATED`
- **Verifier Verdict:** `SUPPORTED`
- **Claim:** `"The actor known for W is Lee Jong-suk!"`
- **Failure Cause:** The context contained multiple Korean television drama credits, including the actor's name and the show title "W", in close proximity. Lexical overlap was high despite the factual relationship being hallucinated in the context of the question.

---

## 3. Architectural Implications for Track 2

The failure taxonomy decisively proves that:
1. Lexical overlap is incapable of distinguishing true entailment from lexical sharing (bag-of-words fallacy).
2. Lexical overlap cannot handle synonymy, paraphrase, or syntactic inversion.
3. To resolve both False Contradictions and subtle False Supported errors, Track 2 must integrate a pretrained **Cross-Encoder / NLI model** (e.g. DeBERTa-v3 or RoBERTa-large-MNLI) fine-tuned for claim-context entailment.
