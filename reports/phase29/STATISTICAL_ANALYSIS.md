# Phase 29 — Statistical Analysis & Metric Verification

---

## 1. Cross-Experiment Metric Summary

| Experiment | Focus Area | Sample Count ($N$) | Primary Metric | Empirical Value | Wilson 95% Confidence Interval |
| :--- | :--- | :---: | :--- | :---: | :--- |
| **Exp A** | FilterRAG Comparison | 64 attack / 75 clean | Clean Retention | **$100.00\%$** (MSD) vs. **$20.00\%$** (FilterRAG) | MSD: $[95.13\%, 100.00\%]$ |
| **Exp B** | Indirect Injection | 9 attacks / 3 clean | Leakage to Generator | **$44.44\%$** ($4/9$ leaked) | $[18.88\%, 73.34\%]$ |
| **Exp C** | Adaptive White-Box | 50 adaptive attacks | Attack Detection Rate | **$40.00\%$** ($20/50$ blocked) | $[27.61\%, 53.82\%]$ |
| **Exp D** | Multilingual Defense | 45 attacks / 45 clean | Attack Detection Rate | **$15.56\%$** ($7/45$ blocked) | $[7.75\%, 28.78\%]$ |
| **Exp E** | Natural Benign | 500 natural queries | Clean Delivery Rate | **$100.00\%$** ($500/500$) | $[99.24\%, 100.00\%]$ |

---

## 2. Statistical Protocol Compliance

- **No Invalid Hypothesis Testing:** The invalid two-proportion $z$-test criticized in Phase 28 has been completely excised. All metrics are presented with exact sample counts and Wilson score intervals.
- **Independence:** Experiment E (MS MARCO / HotpotQA) is completely independent of earlier benchmark development splits.
