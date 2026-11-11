"""Metric utilities and statistical validation functions for TrustRAG Phase 04."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np
from scipy import stats
from sklearn.metrics import average_precision_score, roc_auc_score


def compute_binary_classification_metrics(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    y_scores: Sequence[float] | None = None,
) -> dict[str, Any]:
    """Compute binary classification metrics from actual predictions.

    Returns exact counts (TP, FP, TN, FN), accuracy, precision, recall, F1,
    FPR, FNR, and ROC-AUC / PR-AUC when both classes are present in y_true.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true={len(y_true)}, y_pred={len(y_pred)}")

    n = len(y_true)
    if n == 0:
        return {
            "count": 0,
            "tp": 0,
            "fp": 0,
            "tn": 0,
            "fn": 0,
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "fpr": 0.0,
            "fnr": 0.0,
            "roc_auc": None,
            "pr_auc": None,
        }

    tp = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == 0 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == 0 and p == 0)
    fn = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == 1 and p == 0)

    accuracy = (tp + tn) / n
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    roc_auc: float | None = None
    pr_auc: float | None = None
    if y_scores is not None and len(set(y_true)) == 2 and len(y_scores) == n:
        roc_auc = round(float(roc_auc_score(y_true, y_scores)), 4)
        pr_auc = round(float(average_precision_score(y_true, y_scores)), 4)

    return {
        "count": n,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "fpr": round(fpr, 4),
        "fnr": round(fnr, 4),
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
    }


def compute_multiclass_metrics(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    labels: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Compute overall accuracy, macro-F1, and per-class precision/recall/F1."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have equal length")
    n = len(y_true)
    if n == 0:
        return {"count": 0, "accuracy": 0.0, "macro_f1": 0.0, "per_class": {}}

    class_labels = list(labels) if labels else sorted(set(y_true) | set(y_pred))
    correct = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == p)
    per_class: dict[str, dict[str, Any]] = {}
    f1s: list[float] = []

    for cls in class_labels:
        tp = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == cls and p == cls)
        fp = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t != cls and p == cls)
        fn = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == cls and p != cls)
        support = sum(1 for t in y_true if t == cls)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        if support > 0:
            f1s.append(f1)
        per_class[cls] = {
            "support": support,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
        }

    return {
        "count": n,
        "accuracy": round(correct / n, 4),
        "macro_f1": round(float(np.mean(f1s)) if f1s else 0.0, 4),
        "per_class": per_class,
    }


def precision_at_k(retrieved_ids: Sequence[str], relevant_ids: Sequence[str], k: int) -> float:
    """Compute Precision@K for a single query."""
    if k <= 0 or not retrieved_ids:
        return 0.0
    top = list(retrieved_ids[:k])
    rel = set(relevant_ids)
    hits = sum(1 for doc_id in top if doc_id in rel)
    return hits / len(top)


def recall_at_k(retrieved_ids: Sequence[str], relevant_ids: Sequence[str], k: int) -> float:
    """Compute Recall@K for a single query."""
    rel = set(relevant_ids)
    if not rel or k <= 0:
        return 0.0
    top = set(retrieved_ids[:k])
    return len(top & rel) / len(rel)


def reciprocal_rank(retrieved_ids: Sequence[str], relevant_ids: Sequence[str]) -> float:
    """Compute Reciprocal Rank for a single query."""
    rel = set(relevant_ids)
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in rel:
            return 1.0 / rank
    return 0.0


def summarize_distribution(values: Sequence[float]) -> dict[str, Any]:
    """Summarize numeric distributions (latencies, token counts, trust scores)."""
    if not values:
        return {
            "count": 0,
            "mean": 0.0,
            "std": 0.0,
            "min": 0.0,
            "p50": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "max": 0.0,
        }
    arr = np.asarray(values, dtype=float)
    return {
        "count": int(arr.size),
        "mean": round(float(np.mean(arr)), 4),
        "std": round(float(np.std(arr)), 4),
        "min": round(float(np.min(arr)), 4),
        "p50": round(float(np.percentile(arr, 50)), 4),
        "p95": round(float(np.percentile(arr, 95)), 4),
        "p99": round(float(np.percentile(arr, 99)), 4),
        "max": round(float(np.max(arr)), 4),
    }


def wilson_confidence_interval(
    successes: int,
    total: int,
    confidence: float = 0.95,
) -> tuple[float, float, float]:
    """Compute point estimate and Wilson score confidence interval [low, high]."""
    if total <= 0:
        return 0.0, 0.0, 0.0
    p = successes / total
    z = float(stats.norm.ppf(1.0 - (1.0 - confidence) / 2.0))
    denom = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denom
    half = (z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)) / denom
    return round(p, 4), round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)


def bootstrap_confidence_interval(
    values: Sequence[float],
    n_boot: int = 2000,
    confidence: float = 0.95,
    seed: int = 42,
) -> dict[str, float]:
    """Compute percentile bootstrap confidence interval for the sample mean."""
    if not values:
        return {"mean": 0.0, "ci_low": 0.0, "ci_high": 0.0, "n": 0}
    arr = np.asarray(values, dtype=float)
    if arr.size == 1 or float(np.std(arr)) == 0.0:
        val = round(float(arr[0]), 4)
        return {"mean": val, "ci_low": val, "ci_high": val, "n": int(arr.size)}

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, arr.size, size=(n_boot, arr.size))
    boot_means = arr[idx].mean(axis=1)
    alpha = (1.0 - confidence) / 2.0
    return {
        "mean": round(float(np.mean(arr)), 4),
        "ci_low": round(float(np.quantile(boot_means, alpha)), 4),
        "ci_high": round(float(np.quantile(boot_means, 1.0 - alpha)), 4),
        "n": int(arr.size),
    }


def mcnemar_test(
    correct_a: Sequence[bool],
    correct_b: Sequence[bool],
) -> dict[str, Any]:
    """Run exact binomial McNemar's test on paired binary correctness outcomes."""
    if len(correct_a) != len(correct_b):
        raise ValueError("Paired sequences must have equal length")
    b = sum(1 for a_ok, b_ok in zip(correct_a, correct_b, strict=False) if a_ok and not b_ok)
    c = sum(1 for a_ok, b_ok in zip(correct_a, correct_b, strict=False) if not a_ok and b_ok)
    discordant = b + c
    if discordant == 0:
        return {
            "n": len(correct_a),
            "b_a_only": b,
            "c_b_only": c,
            "discordant": 0,
            "p_value": 1.0,
            "method": "exact_binomial",
            "significant_0_05": False,
        }
    res = stats.binomtest(min(b, c), n=discordant, p=0.5, alternative="two-sided")
    p_val = float(res.pvalue)
    return {
        "n": len(correct_a),
        "b_a_only": b,
        "c_b_only": c,
        "discordant": discordant,
        "p_value": round(p_val, 6),
        "method": "exact_binomial",
        "significant_0_05": p_val < 0.05,
    }


def paired_effect_comparison(
    values_a: Sequence[float],
    values_b: Sequence[float],
    n_perm: int = 5000,
    seed: int = 42,
) -> dict[str, Any]:
    """Compare two paired continuous metric vectors via paired permutation test & Cohen's d."""
    if len(values_a) != len(values_b):
        raise ValueError("Paired metric sequences must have equal length")
    n = len(values_a)
    if n == 0:
        return {"n": 0, "mean_diff": 0.0, "cohens_d": 0.0, "p_value": 1.0, "significant_0_05": False}

    a = np.asarray(values_a, dtype=float)
    b = np.asarray(values_b, dtype=float)
    diff = b - a
    mean_diff = float(np.mean(diff))
    sd = float(np.std(diff, ddof=1)) if n > 1 else 0.0
    cohens_d = (mean_diff / sd) if sd > 1e-12 else 0.0

    if n < 2 or np.allclose(diff, 0.0):
        p_val = 1.0
    else:
        rng = np.random.default_rng(seed)
        signs = rng.choice([-1.0, 1.0], size=(n_perm, n))
        perm_diffs = np.mean(signs * diff[None, :], axis=1)
        p_val = float((np.sum(np.abs(perm_diffs) >= abs(mean_diff)) + 1) / (n_perm + 1))

    return {
        "n": n,
        "mean_a": round(float(np.mean(a)), 4),
        "mean_b": round(float(np.mean(b)), 4),
        "mean_diff_b_minus_a": round(mean_diff, 4),
        "cohens_d": round(cohens_d, 4),
        "p_value": round(p_val, 6),
        "significant_0_05": p_val < 0.05,
    }


__all__ = [
    "bootstrap_confidence_interval",
    "compute_binary_classification_metrics",
    "compute_multiclass_metrics",
    "mcnemar_test",
    "paired_effect_comparison",
    "precision_at_k",
    "recall_at_k",
    "reciprocal_rank",
    "summarize_distribution",
    "wilson_confidence_interval",
]
