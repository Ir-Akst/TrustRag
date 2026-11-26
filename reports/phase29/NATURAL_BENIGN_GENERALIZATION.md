# Phase 29 — Natural Benign-Query Generalization ($N=500$)

---

## 1. Addressing the Synthetic Suffix Limitation

Phase 28 revealed that 40% of the Phase 26 benign controls relied on synthetic template suffixes (e.g. `(Context aspect #1)`).

In Phase 29, a new, completely natural benchmark was constructed by extracting **500 unique user questions** directly from authentic open-domain benchmarks:
- **250 questions** from the MS MARCO validation set (real Bing search queries).
- **250 questions** from the HotpotQA validation set (complex multi-hop natural questions).
- Zero artificial suffix padding.
- Strict deduplication.

---

## 2. Empirical Verification

- **Total Natural Queries:** 500
- **False Positives (Blocked):** 0
- **Clean Delivered:** 500
- **Clean Delivery Rate:** **100.00%** (Wilson 95% CI: **$[99.24\%, 100.00\%]$**)
- **Clean False Positive Rate (FPR):** **0.00%** (Wilson 95% CI: **$[0.00\%, 0.76\%]$**)

### Latency Profile on Natural Queries:
- **Mean:** $0.2150$ ms
- **Median (P50):** $0.1741$ ms
- **P99:** $0.6639$ ms

---

## 3. Scientific Conclusion

The 0.00% Clean FPR is **not an artifact of synthetic template formatting**. When subjected to authentic, uncurated natural user search queries across diverse conversational topics, G1 maintains complete availability with zero false interruptions.
