"""Reproducible statistical validation for Phase 10 comparative evaluation.

Provides:
- Wilson score confidence intervals for proportions
- Paired bootstrap confidence intervals
- Exact McNemar test for paired binary outcomes
- Paired Cohen's d effect size
- Holm-Bonferroni multiple-comparison correction
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np
from pydantic import BaseModel
from scipy import stats


class StatisticalComparison(BaseModel):
    """Structured paired comparison between a baseline and a candidate system."""

    comparison_name: str
    metric_name: str
    sample_count: int
    exploratory: bool
    baseline_mean: float
    candidate_mean: float
    abs_diff: float
    rel_diff: float | None
    ci_95_low: float
    ci_95_high: float
    statistical_test: str
    p_value: float | None
    adjusted_p_value: float | None = None
    effect_size_d: float | None = None
    interpretation: str


def wilson_confidence_interval(
    successes: int,
    total: int,
    *,
    z: float = 1.959963984540054,
) -> tuple[float, float]:
    """Compute Wilson score confidence interval for a binomial proportion."""
    if total <= 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1.0 + (z * z) / total
    center = (p + (z * z) / (2.0 * total)) / denom
    half = (z * math.sqrt((p * (1.0 - p) + (z * z) / (4.0 * total)) / total)) / denom
    return (round(max(0.0, center - half), 4), round(min(1.0, center + half), 4))


def paired_bootstrap_ci(
    baseline_scores: Sequence[float],
    candidate_scores: Sequence[float],
    *,
    n_resamples: int = 2000,
    seed: int = 42,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """Return (mean_diff, ci_low, ci_high) for candidate - baseline via paired bootstrap."""
    if len(baseline_scores) != len(candidate_scores) or not baseline_scores:
        raise ValueError("baseline_scores and candidate_scores must be non-empty and equal length")
    a = np.asarray(baseline_scores, dtype=float)
    b = np.asarray(candidate_scores, dtype=float)
    diffs = b - a
    obs_mean = float(np.mean(diffs))
    if len(diffs) == 1:
        return (round(obs_mean, 4), round(obs_mean, 4), round(obs_mean, 4))

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(diffs), size=(n_resamples, len(diffs)))
    boot_means = np.mean(diffs[idx], axis=1)
    low = float(np.percentile(boot_means, 100.0 * (alpha / 2.0)))
    high = float(np.percentile(boot_means, 100.0 * (1.0 - alpha / 2.0)))
    return (round(obs_mean, 4), round(low, 4), round(high, 4))


def mcnemar_test(
    baseline_correct: Sequence[int | bool],
    candidate_correct: Sequence[int | bool],
) -> dict[str, Any]:
    """Run exact two-sided McNemar test on paired binary outcomes."""
    if len(baseline_correct) != len(candidate_correct):
        raise ValueError("Paired sequences must have equal length")
    n01 = 0  # baseline wrong, candidate right
    n10 = 0  # baseline right, candidate wrong
    for b, c in zip(baseline_correct, candidate_correct, strict=False):
        b_int = int(bool(b))
        c_int = int(bool(c))
        if b_int == 0 and c_int == 1:
            n01 += 1
        elif b_int == 1 and c_int == 0:
            n10 += 1

    discordant = n01 + n10
    if discordant == 0:
        return {"n01": 0, "n10": 0, "discordant": 0, "p_value": 1.0, "method": "exact_binomial"}

    res = stats.binomtest(min(n01, n10), n=discordant, p=0.5, alternative="two-sided")
    return {
        "n01": n01,
        "n10": n10,
        "discordant": discordant,
        "p_value": round(float(res.pvalue), 6),
        "method": "exact_binomial",
    }


def paired_cohens_d(
    baseline_scores: Sequence[float],
    candidate_scores: Sequence[float],
) -> float | None:
    """Compute paired Cohen's d = mean(candidate - baseline) / std(diff, ddof=1)."""
    if len(baseline_scores) != len(candidate_scores) or len(baseline_scores) < 2:
        return None
    diffs = np.asarray(candidate_scores, dtype=float) - np.asarray(baseline_scores, dtype=float)
    sd = float(np.std(diffs, ddof=1))
    if sd == 0.0:
        return 0.0
    return round(float(np.mean(diffs)) / sd, 4)


def holm_bonferroni(p_values: Sequence[float]) -> list[float]:
    """Adjust p-values using Holm-Bonferroni step-down procedure."""
    m = len(p_values)
    if m == 0:
        return []
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * m
    running_max = 0.0
    for rank, (orig_idx, p) in enumerate(indexed):
        adj = min(1.0, p * (m - rank))
        running_max = max(running_max, adj)
        adjusted[orig_idx] = round(running_max, 6)
    return adjusted


def compare_paired_outcomes(
    comparison_name: str,
    metric_name: str,
    baseline_values: Sequence[float],
    candidate_values: Sequence[float],
    *,
    is_binary: bool = False,
    seed: int = 42,
    n_resamples: int = 2000,
    exploratory_threshold: int = 30,
) -> StatisticalComparison:
    """Run paired bootstrap CI + McNemar (if binary) or paired t-test, flagging small samples."""
    n = len(baseline_values)
    b_mean = round(float(np.mean(baseline_values)), 4) if n else 0.0
    c_mean = round(float(np.mean(candidate_values)), 4) if n else 0.0
    abs_diff, ci_low, ci_high = paired_bootstrap_ci(
        baseline_values, candidate_values, n_resamples=n_resamples, seed=seed
    )
    rel_diff = round(abs_diff / abs(b_mean), 4) if b_mean != 0 else None
    exploratory = n < exploratory_threshold
    d = paired_cohens_d(baseline_values, candidate_values)

    p_val: float | None = None
    test_name = "paired_bootstrap"
    if is_binary:
        mc = mcnemar_test(
            [round(v) for v in baseline_values],
            [round(v) for v in candidate_values],
        )
        p_val = float(mc["p_value"])
        test_name = f"mcnemar_exact+bootstrap(n01={mc['n01']},n10={mc['n10']})"
    elif n >= 2:
        diffs = np.asarray(candidate_values, dtype=float) - np.asarray(baseline_values, dtype=float)
        if float(np.std(diffs, ddof=1)) > 0:
            _, p_raw = stats.ttest_rel(candidate_values, baseline_values)
            p_val = round(float(p_raw), 6)
        else:
            p_val = 1.0
        test_name = "paired_t_test+bootstrap"

    if exploratory:
        interp = f"Exploratory (n={n} < {exploratory_threshold}); diff={abs_diff:+.4f}"
    elif p_val is not None and p_val < 0.05:
        interp = f"Statistically significant (p={p_val:.4f}); diff={abs_diff:+.4f}"
    else:
        interp = f"Not statistically significant (p={p_val}); diff={abs_diff:+.4f}"

    return StatisticalComparison(
        comparison_name=comparison_name,
        metric_name=metric_name,
        sample_count=n,
        exploratory=exploratory,
        baseline_mean=b_mean,
        candidate_mean=c_mean,
        abs_diff=abs_diff,
        rel_diff=rel_diff,
        ci_95_low=ci_low,
        ci_95_high=ci_high,
        statistical_test=test_name,
        p_value=p_val,
        effect_size_d=d,
        interpretation=interp,
    )
