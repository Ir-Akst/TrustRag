"""Independent tests for Phase 10 metrics, statistics, dataset inventory, and experiment harness."""

from __future__ import annotations

from pathlib import Path

from trustrag.evaluation.baselines.runners import run_fair_comparison
from trustrag.evaluation.datasets.inventory import build_dataset_inventory
from trustrag.evaluation.experiments.phase10_runner import (
    run_filterrag_phase10_experiment,
    run_g1_phase10_experiment,
    run_g3_phase10_experiment,
    run_srm_phase10_experiment,
)
from trustrag.evaluation.metrics_extended import (
    compute_operational_metrics,
    compute_retrieval_metrics,
    compute_security_metrics,
    compute_verification_metrics,
)
from trustrag.evaluation.statistics.validation import (
    compare_paired_outcomes,
    holm_bonferroni,
    mcnemar_test,
    paired_bootstrap_ci,
    wilson_confidence_interval,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_metrics_single_class_and_percentile_guards() -> None:
    # Single-class AUC must return None
    sec = compute_security_metrics([0, 0, 0], [0, 1, 0], [0.1, 0.8, 0.2])
    assert sec["roc_auc"] is None
    assert sec["pr_auc"] is None
    assert sec["fpr"] == 0.3333

    # Percentile latencies must be None when < 5 samples
    op_small = compute_operational_metrics([1.0, 2.0, 3.0])
    assert op_small["p50_ms"] is None
    assert op_small["p95_ms"] is None

    op_ok = compute_operational_metrics([1.0, 2.0, 3.0, 4.0, 5.0])
    assert op_ok["p50_ms"] == 3.0
    assert op_ok["p95_ms"] is not None


def test_retrieval_and_verification_metrics() -> None:
    ret = compute_retrieval_metrics(
        [["d2", "d1", "d3"], ["d1", "d4", "d5"]],
        [{"d1"}, {"d1", "d2"}],
        k_values=(1, 5),
        supporting_facts_list=[{"d1"}, {"d1"}],
    )
    assert ret["count"] == 2
    assert ret["recall_at_1"] == 0.25
    assert ret["mrr"] == 0.75
    assert ret["supporting_fact_recall"] == 1.0

    ver = compute_verification_metrics(
        ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"],
        ["SUPPORTED", "SUPPORTED", "INSUFFICIENT_EVIDENCE"],
        evidence_aligned=[True, False, True],
        citation_correct=[True, True, True],
    )
    assert ver["count"] == 3
    assert ver["false_supported_rate"] == 0.5
    assert ver["unsupported_claim_recall"] == 0.5


def test_statistical_validation_suite() -> None:
    lo, hi = wilson_confidence_interval(8, 10)
    assert 0.0 <= lo < 0.8 < hi <= 1.0

    mean_d, ci_l, ci_h = paired_bootstrap_ci([0.0] * 10, [1.0] * 10, n_resamples=200, seed=42)
    assert mean_d == 1.0
    assert ci_l == 1.0 and ci_h == 1.0

    mc = mcnemar_test([0, 0, 0, 0, 1, 1], [1, 1, 1, 1, 1, 1])
    assert mc["n01"] == 4 and mc["n10"] == 0

    adj = holm_bonferroni([0.01, 0.04, 0.20])
    assert adj == [0.03, 0.08, 0.20]

    comp = compare_paired_outcomes("a_vs_b", "acc", [0.0] * 10, [1.0] * 10, is_binary=True)
    assert comp.exploratory is True


def test_dataset_inventory_offline_honesty() -> None:
    inv = build_dataset_inventory(REPO_ROOT)
    ext = {item.dataset_name: item for item in inv.items if item.scope == "external_target"}
    assert ext["ragtruth"].status == "PARTIALLY_READY"
    assert ext["ragtruth"].total_local_records == 10
    assert ext["llm_aggrefact"].status == "BLOCKED"
    assert ext["rsb"].status == "BLOCKED"
    assert ext["ms_marco"].status == "BLOCKED"


def test_fair_comparison_and_component_suites() -> None:
    summaries, comparisons = run_fair_comparison(
        "clean_rag",
        dataset_dir=REPO_ROOT / "data" / "benchmarks_backup" / "clean_rag",
        split="test",
        profiles=("original_rag", "static_trustrag", "adaptive_trustrag"),
        limit=5,
        seed=42,
    )
    assert len(summaries) == 3
    assert all(s.sample_count == 5 for s in summaries.values())
    assert len(comparisons) == 3

    g1 = run_g1_phase10_experiment()
    assert g1["attack_vs_benign"]["count"] == 6

    g3 = run_g3_phase10_experiment()
    assert g3["unseen_probes_metrics"]["count"] == 4

    srm = run_srm_phase10_experiment()
    assert srm["hf_local_neural"]["status"] == "BLOCKED"
    assert srm["deterministic_fallback"]["is_fallback"] is True

    fr = run_filterrag_phase10_experiment(REPO_ROOT)
    assert "BLOCKED" in fr["status"]
