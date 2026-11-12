"""Centralized Phase 10 metrics library for Security, Retrieval, Verification, and Operational telemetry.

Extends `trustrag.evaluation.metrics` without altering Phase 04-09 contracts.
Enforces strict statistical guards:
- Single-class samples return `None` for ROC-AUC and PR-AUC.
- Percentile latencies (`p50`, `p95`, `p99`) require `>= 5` observations.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np

from trustrag.evaluation.metrics import (
    compute_binary_classification_metrics,
    compute_multiclass_metrics,
)


def compute_security_metrics(
    y_true_attack: Sequence[int],
    y_pred_attack: Sequence[int],
    y_scores_attack: Sequence[float] | None = None,
    *,
    attack_succeeded: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Compute security detection metrics and Attack Success Rate (ASR)."""
    base = compute_binary_classification_metrics(y_true_attack, y_pred_attack, y_scores_attack)
    tn = int(base["tn"])
    fp = int(base["fp"])
    specificity = round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0.0
    asr: float | None = None
    if attack_succeeded is not None:
        total_attacks = sum(1 for y in y_true_attack if y == 1)
        if total_attacks > 0:
            succ = sum(
                1 for y, s in zip(y_true_attack, attack_succeeded, strict=False) if y == 1 and s == 1
            )
            asr = round(succ / total_attacks, 4)
    return {
        **base,
        "tpr": base["recall"],
        "specificity": specificity,
        "asr": asr,
    }


def _dcg_at_k(relevances: Sequence[float], k: int) -> float:
    total = 0.0
    for idx, rel in enumerate(relevances[:k]):
        if rel > 0:
            total += (2.0**rel - 1.0) / math.log2(idx + 2)
    return total


def compute_retrieval_metrics(
    ranked_doc_ids_list: Sequence[Sequence[str]],
    relevant_doc_ids_list: Sequence[set[str]],
    *,
    k_values: tuple[int, ...] = (1, 5, 10),
    supporting_facts_list: Sequence[set[str]] | None = None,
) -> dict[str, Any]:
    """Compute Recall@k, MRR, nDCG@10, and optional supporting-fact recall."""
    n = len(ranked_doc_ids_list)
    if n == 0 or n != len(relevant_doc_ids_list):
        return {
            "count": 0,
            **{f"recall_at_{k}": None for k in k_values},
            "mrr": None,
            "ndcg_at_10": None,
            "supporting_fact_recall": None,
        }

    recall_sums: dict[int, float] = {k: 0.0 for k in k_values}
    mrr_sum = 0.0
    ndcg_sum = 0.0
    valid_queries = 0

    for ranked, rel_set in zip(ranked_doc_ids_list, relevant_doc_ids_list, strict=False):
        if not rel_set:
            continue
        valid_queries += 1
        for k in k_values:
            hits = sum(1 for doc_id in ranked[:k] if doc_id in rel_set)
            recall_sums[k] += hits / len(rel_set)

        rr = 0.0
        for rank_idx, doc_id in enumerate(ranked, start=1):
            if doc_id in rel_set:
                rr = 1.0 / rank_idx
                break
        mrr_sum += rr

        rels = [1.0 if doc_id in rel_set else 0.0 for doc_id in ranked[:10]]
        ideal = [1.0] * min(len(rel_set), 10)
        idcg = _dcg_at_k(ideal, 10)
        ndcg_sum += (_dcg_at_k(rels, 10) / idcg) if idcg > 0 else 0.0

    if valid_queries == 0:
        return {
            "count": 0,
            **{f"recall_at_{k}": None for k in k_values},
            "mrr": None,
            "ndcg_at_10": None,
            "supporting_fact_recall": None,
        }

    sf_recall: float | None = None
    if supporting_facts_list is not None and len(supporting_facts_list) == n:
        sf_vals: list[float] = []
        for ranked, sf_set in zip(ranked_doc_ids_list, supporting_facts_list, strict=False):
            if sf_set:
                sf_vals.append(sum(1 for d in ranked if d in sf_set) / len(sf_set))
        if sf_vals:
            sf_recall = round(float(np.mean(sf_vals)), 4)

    out: dict[str, Any] = {"count": valid_queries}
    for k in k_values:
        out[f"recall_at_{k}"] = round(recall_sums[k] / valid_queries, 4)
    out["mrr"] = round(mrr_sum / valid_queries, 4)
    out["ndcg_at_10"] = round(ndcg_sum / valid_queries, 4)
    out["supporting_fact_recall"] = sf_recall
    return out


def compute_verification_metrics(
    y_true_verdicts: Sequence[str],
    y_pred_verdicts: Sequence[str],
    *,
    evidence_aligned: Sequence[bool] | None = None,
    citation_correct: Sequence[bool] | None = None,
) -> dict[str, Any]:
    """Compute claim-level verification metrics and hallucination safety rates."""
    if len(y_true_verdicts) != len(y_pred_verdicts) or not y_true_verdicts:
        return {
            "count": 0,
            "claim_accuracy": None,
            "macro_f1": None,
            "supported_precision": None,
            "contradicted_precision": None,
            "false_supported_rate": None,
            "false_contradicted_rate": None,
            "unsupported_claim_recall": None,
            "evidence_alignment": None,
            "citation_correctness": None,
        }

    mc = compute_multiclass_metrics(y_true_verdicts, y_pred_verdicts)
    per_cls = mc["per_class"]
    n = len(y_true_verdicts)

    non_supported_indices = [i for i, t in enumerate(y_true_verdicts) if t != "SUPPORTED"]
    false_supported = sum(1 for i in non_supported_indices if y_pred_verdicts[i] == "SUPPORTED")
    fsr = (
        round(false_supported / len(non_supported_indices), 4)
        if non_supported_indices
        else None
    )

    non_contra_indices = [i for i, t in enumerate(y_true_verdicts) if t != "CONTRADICTED"]
    false_contra = sum(1 for i in non_contra_indices if y_pred_verdicts[i] == "CONTRADICTED")
    fcr = (
        round(false_contra / len(non_contra_indices), 4)
        if non_contra_indices
        else None
    )

    unsupported_recall = (
        round(
            sum(
                1
                for t, p in zip(y_true_verdicts, y_pred_verdicts, strict=False)
                if t != "SUPPORTED" and p != "SUPPORTED"
            )
            / len(non_supported_indices),
            4,
        )
        if non_supported_indices
        else None
    )

    ev_align = (
        round(sum(1 for x in evidence_aligned if x) / len(evidence_aligned), 4)
        if evidence_aligned and len(evidence_aligned) == n
        else None
    )
    cit_corr = (
        round(sum(1 for x in citation_correct if x) / len(citation_correct), 4)
        if citation_correct and len(citation_correct) == n
        else None
    )

    return {
        "count": n,
        "claim_accuracy": mc["accuracy"],
        "macro_f1": mc["macro_f1"],
        "supported_precision": per_cls.get("SUPPORTED", {}).get("precision"),
        "contradicted_precision": per_cls.get("CONTRADICTED", {}).get("precision"),
        "false_supported_rate": fsr,
        "false_contradicted_rate": fcr,
        "unsupported_claim_recall": unsupported_recall,
        "evidence_alignment": ev_align,
        "citation_correctness": cit_corr,
        "per_class": per_cls,
    }


def compute_operational_metrics(
    latencies_ms: Sequence[float],
    *,
    error_count: int = 0,
    timeout_count: int = 0,
    total_wall_s: float | None = None,
    min_percentile_samples: int = 5,
) -> dict[str, Any]:
    """Compute operational latency percentiles (gated on >= 5 samples), throughput, and error rates."""
    n = len(latencies_ms)
    if n == 0:
        return {
            "count": 0,
            "mean_ms": None,
            "p50_ms": None,
            "p95_ms": None,
            "p99_ms": None,
            "throughput_rps": None,
            "error_rate": 0.0,
            "timeout_rate": 0.0,
        }

    arr = np.asarray(latencies_ms, dtype=float)
    p50 = round(float(np.percentile(arr, 50)), 4) if n >= min_percentile_samples else None
    p95 = round(float(np.percentile(arr, 95)), 4) if n >= min_percentile_samples else None
    p99 = round(float(np.percentile(arr, 99)), 4) if n >= min_percentile_samples else None
    wall = total_wall_s if (total_wall_s is not None and total_wall_s > 0) else (float(np.sum(arr)) / 1000.0)
    rps = round(n / wall, 2) if wall > 0 else None

    return {
        "count": n,
        "mean_ms": round(float(np.mean(arr)), 4),
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "throughput_rps": rps,
        "error_rate": round(error_count / n, 4),
        "timeout_rate": round(timeout_count / n, 4),
    }


__all__ = [
    "compute_binary_classification_metrics",
    "compute_multiclass_metrics",
    "compute_operational_metrics",
    "compute_retrieval_metrics",
    "compute_security_metrics",
    "compute_verification_metrics",
]
