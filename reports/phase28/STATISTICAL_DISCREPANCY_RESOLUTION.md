# Phase 28 — Statistical Discrepancy Resolution

This document provides exact, reproducible resolutions to the five statistical discrepancies identified during the hostile audit of Phase 26 and Phase 27.

---

## 1. Discrepancy 1: The Phase 25 vs. Phase 26 $z$-Test

### The Claim in Phase 27:
- Phase 27 claimed a two-proportion $z$-test yielding $z = 7.62$ ($p < 0.0001$) between Phase 25 ($n_1 = 164, x_1 = 164, p_1 = 1.00$) and Phase 26 ($n_2 = 500, x_2 = 359, p_2 = 0.7180$).

### Recomputation:
- Pooled proportion:
  $$\hat{p} = \frac{164 + 359}{164 + 500} = \frac{523}{664} \approx 0.787651$$
- Pooled standard error:
  $$SE_{pool} = \sqrt{0.787651 \times (1 - 0.787651) \times \left(\frac{1}{164} + \frac{1}{500}\right)} = \sqrt{0.167252 \times 0.008098} \approx 0.036802$$
- $z$-statistic:
  $$z = \frac{1.0000 - 0.7180}{0.036802} = \frac{0.2820}{0.036802} = \mathbf{7.6627}$$

### Resolution & Methodological Assessment:
- The exact $z$-value is **7.66** (rounded to 7.62 in Phase 27 due to intermediate rounding of $SE$ to $0.037$).
- **Methodological Invalidity**: While arithmetically sound, **the application of a two-proportion $z$-test across Phase 25 and Phase 26 is statistically invalid**. A two-sample $z$-test tests whether two samples drawn from the *same underlying population* differ due to random sampling variance. Here, Phase 25 evaluated curated in-distribution unit regression tests, while Phase 26 evaluated out-of-distribution red-team attacks. The performance drop of 28.20% is caused by **benchmark distribution shift**, not sampling noise. The manuscript must report this as an empirical distributional drop, not a $p$-value from a null hypothesis of identical distributions.

---

## 2. Discrepancy 2: F1 Score Confidence Interval

### The Claim in Phase 27:
- Phase 27 reported F1 = 83.59% with a 95% Confidence Interval of $[80.74\%, 86.08\%]$.

### Recomputation & Methodology:
- F1 is the harmonic mean of precision ($1.0000$) and recall ($0.7180$):
  $$F1 = \frac{2 \times 1.0 \times 0.7180}{1.0 + 0.7180} = \frac{1.436}{1.718} \approx \mathbf{83.5856\%}$$
- Because F1 is a non-linear combination of random variables, normal/binomial interval formulas cannot be applied.
- Applying non-parametric bootstrapping ($B = 10,000$ iterations with seed 42) directly to the paired ground truth and prediction vectors ($N=1000$):
  - 2.5th percentile: **$80.77\%$**
  - 97.5th percentile: **$86.19\%$**
- Bootstrap 95% CI: **$[80.77\%, 86.19\%]$**.

### Resolution:
- The Phase 27 interval ($[80.74\%, 86.08\%]$) was derived from a coarser bootstrap ($B=1,000$). The definitive, reproducible non-parametric bootstrap interval is **$[80.77\%, 86.19\%]$** ($B=10,000$).

---

## 3. Discrepancy 3: G1 Latency Figures ($0.11$ ms vs. $0.23$ ms vs. $0.199$ ms)

### The Claim in Phase 27:
- Phase 27 reported G1 CPU latency as $0.11$ ms median and $0.23$ ms $p99$.
- Phase 26 text reported latency of $\approx 0.19$ ms.

### Empirical Measurement on `phase26_raw_predictions.jsonl` ($N=1000$):
- **Mean**: $0.1965$ ms
- **Median (P50)**: **$0.1995$ ms**
- **P90**: $0.2401$ ms
- **P95**: $0.2510$ ms
- **P99**: **$0.2660$ ms**
- **Benign-only P99**: **$0.2340$ ms**

### Resolution:
- The $0.11$ ms figure reported in Phase 27 originated from an isolated micro-benchmark on short queries without structured JSON audit logging.
- The $0.23$ ms figure was specifically the **$p99$ latency on the benign control subset** ($0.2340$ ms).
- Across the complete 1,000 evaluation requests with logging enabled, the true empirical median is **$0.20$ ms** and the overall $p99$ is **$0.27$ ms**. The manuscript must report both micro-benchmark and end-to-end evaluation figures transparently.

---

## 4. Discrepancy 4: Multilingual Aggregate (6/40) vs. Language Breakdown

### The Claim in Phase 27:
- Table 2 reported "Multilingual Injection: 6/40 (15.0% ADR)".

### Breakdown from Raw Records (`UNSEEN_ML_001` to `UNSEEN_ML_040`):
| Language / Script | Total Cases | Blocked (TP) | Allowed (FN) | ADR (%) | Wilson 95% CI |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Spanish** (Latin) | 4 | 2 | 2 | **50.0%** | $[15.0\%, 85.0\%]$ |
| **French** (Latin) | 4 | 2 | 2 | **50.0%** | $[15.0\%, 85.0\%]$ |
| **German** (Latin) | 4 | 2 | 2 | **50.0%** | $[15.0\%, 85.0\%]$ |
| **Russian** (Cyrillic) | 4 | 0 | 4 | **0.0%** | $[0.0\%, 49.0\%]$ |
| **Chinese** (Han) | 4 | 0 | 4 | **0.0%** | $[0.0\%, 49.0\%]$ |
| **Hindi** (Devanagari)| 4 | 0 | 4 | **0.0%** | $[0.0\%, 49.0\%]$ |
| **Arabic** (Arabic) | 4 | 0 | 4 | **0.0%** | $[0.0\%, 49.0\%]$ |
| **Japanese** (Kana/Kanji)| 4 | 0 | 4 | **0.0%** | $[0.0\%, 49.0\%]$ |
| **Suffixed Non-Latin** | 8 | 0 | 8 | **0.0%** | $[0.0\%, 32.4\%]$ |
| **Total Multilingual** | **40** | **6** | **34** | **15.0%** | **$[7.1\%, 29.1\%]$** |

### Resolution:
- Aggregating all languages into a single 15.0% figure conceals a critical scientific truth: **G1 has zero coverage (0.0% ADR) against non-Latin writing systems.** In Latin-script languages, it detected 50% of attacks because common attack keywords ("Ignora", "Ignorez", "Ignoriere") matched Latin root stems. Against Cyrillic, Chinese, Devanagari, and Arabic, G1 was completely blind. The manuscript must explicitly report Latin vs. Non-Latin breakdown.

---

## 5. Discrepancy 5: Dataset Uniqueness & Synthetic Suffix Bias

### Investigation:
- 1,000 / 1,000 query strings are unique.
- However, 200 / 500 benign queries (40.0%) were constructed by appending synthetic suffixes (e.g. `(Context aspect #1)`) to 320 unique questions.

### Resolution:
- While formally unique strings, 40% of the benign evaluation suite shares base semantic prompts with slight synthetic suffixes. This must be acknowledged as a benchmark limitation regarding linguistic diversity.
