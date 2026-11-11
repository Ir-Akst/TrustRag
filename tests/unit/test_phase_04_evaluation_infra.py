"""Focused unit tests for Phase 04 Step 2 Evaluation Infrastructure."""

from __future__ import annotations

import json
from pathlib import Path

from trustrag.evaluation.loader import load_evaluation_partition
from trustrag.evaluation.metrics import (
    bootstrap_confidence_interval,
    compute_binary_classification_metrics,
    compute_multiclass_metrics,
    mcnemar_test,
    paired_effect_comparison,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    summarize_distribution,
    wilson_confidence_interval,
)
from trustrag.evaluation.runner import EvaluationRunner
from trustrag.evaluation.schemas import ExperimentConfig, SampleOutcome


def test_deterministic_runner_and_exports(tmp_path: Path) -> None:
    ds_dir = tmp_path / "clean_rag"
    ds_dir.mkdir()
    test_file = ds_dir / "test.jsonl"
    records = [
        {"query_id": "q1", "query": "Is sky blue?", "source_dataset": "boolq", "answer": "yes"},
        {"query_id": "q2", "query": "Is water dry?", "source_dataset": "boolq", "answer": "no"},
    ]
    test_file.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")

    cfg = ExperimentConfig(
        experiment_name="unit_eval",
        dataset_name="clean_rag",
        split="test",
        dataset_dir=str(ds_dir),
        random_seed=42,
    )
    runner = EvaluationRunner(output_dir=tmp_path / "out")

    def eval_fn(rec):
        return SampleOutcome(
            sample_id=rec.query_id,
            status="success",
            prediction=rec.answer,
            ground_truth=rec.answer,
        )

    def metrics_fn(outcomes, _recs):
        correct = sum(1 for o in outcomes if o.prediction == o.ground_truth)
        return {"accuracy": correct / len(outcomes) if outcomes else 0.0}

    res1 = runner.run(cfg, eval_fn, metrics_fn, export=True)
    res2 = runner.run(cfg, eval_fn, metrics_fn, export=False)

    assert res1.experiment_id == res2.experiment_id
    assert res1.metrics["accuracy"] == res2.metrics["accuracy"] == 1.0
    assert res1.successful_examples == 2
    assert res1.failed_examples == 0
    assert res1.invalid_examples == 0
    assert (tmp_path / "out" / f"{res1.experiment_id}.json").is_file()
    assert (tmp_path / "out" / f"{res1.experiment_id}_metrics.csv").is_file()
    assert (tmp_path / "out" / f"{res1.experiment_id}_samples.csv").is_file()


def test_invalid_and_failed_records_never_counted_as_success(tmp_path: Path) -> None:
    ds_dir = tmp_path / "hallucination"
    ds_dir.mkdir()
    f = ds_dir / "test.jsonl"
    f.write_text(
        "\n".join([
            json.dumps({
                "record_id": "h1",
                "document": "Doc one.",
                "claim": "Claim one.",
                "label": "SUPPORTED",
                "source_dataset": "wice",
            }),
            "{corrupt json line",
            json.dumps({"record_id": "bad_schema"}),
            json.dumps({
                "record_id": "h2",
                "document": "Doc two.",
                "claim": "Claim two.",
                "label": "CONTRADICTED",
                "source_dataset": "wice",
            }),
        ]) + "\n",
        encoding="utf-8",
    )

    loaded = load_evaluation_partition("hallucination", split="test", dataset_dir=ds_dir)
    assert len(loaded.records) == 2
    assert len(loaded.invalid_records) == 2

    cfg = ExperimentConfig(
        experiment_name="error_accounting",
        dataset_name="hallucination",
        split="test",
        dataset_dir=str(ds_dir),
    )
    runner = EvaluationRunner(output_dir=tmp_path / "out")

    def eval_fn(rec):
        if rec.record_id == "h2":
            raise RuntimeError("Simulated inference error")
        return SampleOutcome(sample_id=rec.record_id, status="success", prediction="SUPPORTED", ground_truth=rec.label)

    def metrics_fn(outcomes, _recs):
        return {"evaluated_success": len(outcomes)}

    res = runner.run(cfg, eval_fn, metrics_fn, partition=loaded, export=False)
    assert res.total_examples == 4
    assert res.successful_examples == 1
    assert res.failed_examples == 1
    assert res.invalid_examples == 2
    assert len(res.errors) == 3  # 2 invalid + 1 runtime failure


def test_metrics_and_statistical_utilities() -> None:
    bm = compute_binary_classification_metrics(
        y_true=[1, 1, 0, 0],
        y_pred=[1, 0, 0, 1],
        y_scores=[0.9, 0.4, 0.1, 0.7],
    )
    assert bm["tp"] == 1 and bm["fn"] == 1 and bm["tn"] == 1 and bm["fp"] == 1
    assert bm["accuracy"] == 0.5
    assert bm["roc_auc"] is not None

    # Single-class y_true must return None for ROC-AUC without crashing
    bm_single = compute_binary_classification_metrics([1, 1], [1, 0], [0.8, 0.3])
    assert bm_single["roc_auc"] is None

    mm = compute_multiclass_metrics(["A", "B", "A"], ["A", "A", "A"])
    assert mm["accuracy"] == 0.6667

    assert precision_at_k(["d1", "d2", "d3"], ["d2", "d4"], k=2) == 0.5
    assert recall_at_k(["d1", "d2", "d3"], ["d2", "d4"], k=2) == 0.5
    assert reciprocal_rank(["d1", "d2", "d3"], ["d2"]) == 0.5

    dist = summarize_distribution([1.0, 2.0, 3.0, 4.0, 5.0])
    assert dist["p50"] == 3.0

    p, lo, hi = wilson_confidence_interval(8, 10)
    assert 0.0 <= lo <= p <= hi <= 1.0

    boot = bootstrap_confidence_interval([0.8, 0.9, 0.7, 1.0], seed=42)
    assert boot["ci_low"] <= boot["mean"] <= boot["ci_high"]

    mc = mcnemar_test([True, False, False, True], [True, True, True, True])
    assert mc["c_b_only"] == 2 and mc["b_a_only"] == 0

    eff = paired_effect_comparison([0.2, 0.3, 0.4], [0.5, 0.6, 0.7], seed=42)
    assert eff["mean_diff_b_minus_a"] > 0.0

