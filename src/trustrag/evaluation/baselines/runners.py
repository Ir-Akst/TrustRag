"""Fair comparison framework across Original RAG, Static/Adaptive TrustRAG, and component ablations.

All profiles evaluate the exact same records, corpus, retriever, seed, and top_k.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from trustrag.adaptive.calibration import TrustCalibrator, collect_g2_partition_scores
from trustrag.config import Settings, load_config
from trustrag.config.engine_config import MSDConfig
from trustrag.detection.msd import MultiSignalDetector
from trustrag.engine.schemas import EvidenceDocument, G1Decision
from trustrag.evaluation.loader import load_evaluation_partition
from trustrag.evaluation.metrics_extended import (
    compute_operational_metrics,
    compute_security_metrics,
)
from trustrag.evaluation.statistics.validation import (
    StatisticalComparison,
    compare_paired_outcomes,
    holm_bonferroni,
)
from trustrag.pipeline.trustrag_pipeline import TrustRAGPipeline

SystemProfile = Literal[
    "original_rag",
    "static_trustrag",
    "adaptive_trustrag",
    "trustrag_no_g1",
    "trustrag_no_g2",
    "trustrag_no_g3",
    "trustrag_no_srm",
]

SYSTEM_PROFILES: tuple[SystemProfile, ...] = (
    "original_rag",
    "static_trustrag",
    "adaptive_trustrag",
    "trustrag_no_g1",
    "trustrag_no_g2",
    "trustrag_no_g3",
    "trustrag_no_srm",
)


class BaselineRunSummary(BaseModel):
    """Aggregated and per-example results for one system profile on one dataset."""

    profile: SystemProfile
    dataset_name: str
    split: str
    sample_count: int
    security_metrics: dict[str, Any] = Field(default_factory=dict)
    clean_utility_rate: float | None = None
    operational_metrics: dict[str, Any] = Field(default_factory=dict)
    per_example_correct: list[int] = Field(default_factory=list)
    per_example_attack_success: list[int] = Field(default_factory=list)
    per_example_latency_ms: list[float] = Field(default_factory=list)


def build_profile_settings(profile: SystemProfile, *, top_k: int = 5, seed: int = 42) -> Settings:
    """Create Settings for a fair comparison profile without mutating global config."""
    cfg = load_config()
    cfg.app.random_seed = seed
    cfg.retrieval.top_k = top_k

    if profile == "original_rag":
        cfg.guardrails.enabled = False
        cfg.msd.enabled = False
        cfg.verification.enabled = False
        cfg.srm.enabled = False
    elif profile in {"static_trustrag", "adaptive_trustrag"}:
        cfg.guardrails.enabled = True
        cfg.msd.enabled = True
        cfg.verification.enabled = True
        cfg.srm.enabled = True
    elif profile == "trustrag_no_g1":
        cfg.guardrails.enabled = False
        cfg.msd.enabled = True
        cfg.verification.enabled = True
        cfg.srm.enabled = True
    elif profile == "trustrag_no_g2":
        cfg.guardrails.enabled = True
        cfg.msd.enabled = False
        cfg.verification.enabled = True
        cfg.srm.enabled = True
    elif profile == "trustrag_no_g3":
        cfg.guardrails.enabled = True
        cfg.msd.enabled = True
        cfg.verification.enabled = False
        cfg.srm.enabled = True
    elif profile == "trustrag_no_srm":
        cfg.guardrails.enabled = True
        cfg.msd.enabled = True
        cfg.verification.enabled = True
        cfg.srm.enabled = False

    return cfg


def _record_to_docs(rec: Any, idx: int) -> tuple[str, list[EvidenceDocument], int, str]:
    """Extract (query, docs, is_attack, ground_truth_label) uniformly from benchmark records."""
    meta = getattr(rec, "metadata", {}) or {}
    query = (
        getattr(rec, "target_query", None)
        or getattr(rec, "query", None)
        or getattr(rec, "claim", None)
        or f"query_{idx}"
    )
    label_val = (
        getattr(rec, "clean_poison_label", None)
        or getattr(rec, "label", None)
        or "clean"
    )
    label_str = str(getattr(label_val, "value", label_val)).lower()
    is_attack = 1 if label_str in {"poisoned", "adversarial", "attack", "injected", "unsafe"} else 0

    prov = str(getattr(rec, "provenance", None) or meta.get("provenance", "unknown"))
    src_id = str(getattr(rec, "source_id", None) or meta.get("source_id", "local"))

    docs: list[EvidenceDocument] = []
    doc_body = (
        getattr(rec, "document", None)
        or getattr(rec, "passage", None)
        or getattr(rec, "document_text", None)
    )
    if doc_body:
        docs.append(
            EvidenceDocument(
                doc_id=str(getattr(rec, "record_id", f"doc_{idx}")),
                text=str(doc_body),
                provenance=prov,
                source_id=src_id,
            )
        )
    elif hasattr(rec, "evidence") and getattr(rec, "evidence", None):
        for j, ev in enumerate(rec.evidence):
            docs.append(
                EvidenceDocument(
                    doc_id=f"ev_{idx}_{j}",
                    text=str(ev),
                    provenance="local_corpus",
                    source_id="local",
                )
            )
    else:
        ctx = meta.get("context") or meta.get("passage") or query
        docs.append(
            EvidenceDocument(
                doc_id=f"ctx_{idx}",
                text=str(ctx),
                provenance=prov,
                source_id=src_id,
            )
        )

    return str(query), docs, is_attack, label_str


def _evaluate_profile_on_records(
    profile: SystemProfile,
    dataset_name: str,
    split: str,
    records: list[Any],
    *,
    calibrator: TrustCalibrator | None = None,
    seed: int = 42,
) -> BaselineRunSummary:
    cfg = build_profile_settings(profile, seed=seed)
    detector = MultiSignalDetector(
        config=cfg.msd,
        calibrator=calibrator if profile == "adaptive_trustrag" else None,
    )

    y_true: list[int] = []
    y_pred: list[int] = []
    y_scores: list[float] = []
    atk_succ: list[int] = []
    per_correct: list[int] = []
    latencies: list[float] = []

    for idx, rec in enumerate(records):
        query, docs, is_attack, _ = _record_to_docs(rec, idx)
        pipe = TrustRAGPipeline(settings=cfg, documents=docs)
        pipe.retriever.detector = detector

        t0 = time.perf_counter()
        resp = pipe.run(query, top_k=min(5, len(docs)))
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 4)
        latencies.append(elapsed_ms)

        g1_blocked = resp.trust_report.g1_assessment.decision == G1Decision.BLOCK
        g2_assessments = resp.trust_report.g2_assessments
        g2_flagged = any(
            str(getattr(a.decision, "value", a.decision)).lower() in {"poisoned", "uncertain"}
            or a.removed_by_cap
            for a in g2_assessments
        )
        predicted_attack = 1 if (g1_blocked or g2_flagged) else 0
        min_trust = min((a.trust_score for a in g2_assessments), default=1.0)
        attack_score = round(1.0 - min_trust, 4) if cfg.msd.enabled else (1.0 if g1_blocked else 0.0)

        succeeded = 1 if (is_attack == 1 and predicted_attack == 0) else 0
        correct = 1 if predicted_attack == is_attack else 0

        y_true.append(is_attack)
        y_pred.append(predicted_attack)
        y_scores.append(attack_score)
        atk_succ.append(succeeded)
        per_correct.append(correct)

    sec_metrics = compute_security_metrics(
        y_true, y_pred, y_scores, attack_succeeded=atk_succ
    )
    clean_indices = [i for i, y in enumerate(y_true) if y == 0]
    clean_util = (
        round(sum(per_correct[i] for i in clean_indices) / len(clean_indices), 4)
        if clean_indices
        else None
    )
    op_metrics = compute_operational_metrics(latencies)

    return BaselineRunSummary(
        profile=profile,
        dataset_name=dataset_name,
        split=split,
        sample_count=len(records),
        security_metrics=sec_metrics,
        clean_utility_rate=clean_util,
        operational_metrics=op_metrics,
        per_example_correct=per_correct,
        per_example_attack_success=atk_succ,
        per_example_latency_ms=latencies,
    )


def fit_train_calibrator(dataset_name: str, ds_path: Path) -> TrustCalibrator | None:
    """Fit TrustCalibrator strictly on the train split (never val/test)."""
    train_file = ds_path / "train.jsonl"
    if not train_file.exists():
        return None
    y_clean, raw_scores, _ = collect_g2_partition_scores(
        dataset_name, "train", dataset_dir=ds_path, msd_config=MSDConfig(), max_clean_queries=50
    )
    if len(set(y_clean)) < 2:
        return None
    return TrustCalibrator.fit(raw_scores, y_clean, fitted_splits=("train",))


def run_fair_comparison(
    dataset_name: str,
    *,
    dataset_dir: str | Path,
    split: str = "test",
    profiles: tuple[SystemProfile, ...] = SYSTEM_PROFILES,
    seed: int = 42,
    limit: int | None = None,
) -> tuple[dict[SystemProfile, BaselineRunSummary], list[StatisticalComparison]]:
    """Run all requested profiles on identical records and compute paired statistical comparisons."""
    ds_path = Path(dataset_dir)
    loaded = load_evaluation_partition(dataset_name, split=split, dataset_dir=ds_path, limit=limit)
    records = list(loaded.records)

    calibrator: TrustCalibrator | None = None
    if "adaptive_trustrag" in profiles:
        calibrator = fit_train_calibrator(dataset_name, ds_path)

    summaries: dict[SystemProfile, BaselineRunSummary] = {}
    for profile in profiles:
        summaries[profile] = _evaluate_profile_on_records(
            profile,
            dataset_name,
            split,
            records,
            calibrator=calibrator,
            seed=seed,
        )

    comparisons: list[StatisticalComparison] = []
    if "original_rag" in summaries and records:
        orig = summaries["original_rag"]
        for cand_name in profiles:
            if cand_name == "original_rag":
                continue
            cand = summaries[cand_name]
            comparisons.append(
                compare_paired_outcomes(
                    f"{cand_name}_vs_original_rag",
                    "per_example_accuracy",
                    [float(x) for x in orig.per_example_correct],
                    [float(x) for x in cand.per_example_correct],
                    is_binary=True,
                    seed=seed,
                )
            )
    if "static_trustrag" in summaries and "adaptive_trustrag" in summaries and records:
        st = summaries["static_trustrag"]
        ad = summaries["adaptive_trustrag"]
        comparisons.append(
            compare_paired_outcomes(
                "adaptive_trustrag_vs_static_trustrag",
                "per_example_accuracy",
                [float(x) for x in st.per_example_correct],
                [float(x) for x in ad.per_example_correct],
                is_binary=True,
                seed=seed,
            )
        )

    raw_p = [c.p_value for c in comparisons if c.p_value is not None]
    if raw_p:
        adj_p = holm_bonferroni(raw_p)
        idx = 0
        for c in comparisons:
            if c.p_value is not None:
                c.adjusted_p_value = adj_p[idx]
                idx += 1

    return summaries, comparisons
