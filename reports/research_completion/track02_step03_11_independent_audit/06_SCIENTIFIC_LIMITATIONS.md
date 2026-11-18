# TrustRAG — Track 2, Step 3.11: Scientific Limitations & Adversarial Assessment

## 1. Detailed Limitations Analysis

While the Step 3.10 remediation resolves the operational crash and class collapse, the following scientific limitations remain:

### Limitation 1: Remaining 2.03% Hypothesis Truncation
- Across the 2,662 validation records, exactly **54 samples (2.03%)** have hypotheses that exceed 317 tokens.
- In these 54 records, the tail of the hypothesis is truncated to guarantee that the premise receives at least 64 tokens of evidence.
- *Impact:* For these 54 samples, if a hallucination claim appears after token 317, the model will not observe it.
- *Remediation Path:* Future production pipelines can either increase sequence length to 512 for these long instances or implement sentence-level claim splitting.

### Limitation 2: Premise Evidence Truncation (36.88% Retention)
- Retaining an average of 216.6 premise tokens is a 4× improvement over the 55 tokens preserved at `max_seq_len = 128`.
- However, document premises have a median of 502 tokens and p90 of 1,008 tokens.
- *Impact:* For long documents (>600 tokens), evidence residing deep in the document is truncated unless sentence-level relevance extraction or chunking is used.

### Limitation 3: Multi-Chunk Aggregation is Designed, Not Yet Implemented
- The Step 3.10 design recommends splitting long premises into multiple chunks with hypothesis pairing and pooling logits (e.g. max contradiction logit).
- *Status:* This architectural enhancement is documented in research reports, but has **not yet been implemented** in `train_nli_classifier.py` (which currently takes a single pair `(premise[:K_p], hypothesis[:K_h])`).

### Limitation 4: Span-Level Retention is Inferred Rather Than Explicitly Tracked
- In RAGTruth, character start/end offsets are recorded in the raw benchmark annotations, but are not present as token indices in the SFT JSONL files.
- While case study analysis proves span retention on representative examples, dataset-wide span intersection was inferred from hypothesis token completeness rather than automated token-span index tracking.

---

## 2. Verdict Justification

Because the core operational defects (unshuffled starvation tail and severe 128-token truncation) are definitively fixed and verified, but the four scientific limitations above remain acknowledged and documented, the scientifically defensible verdict is:

**`INDEPENDENTLY_VERIFIED_WITH_LIMITATIONS`**
