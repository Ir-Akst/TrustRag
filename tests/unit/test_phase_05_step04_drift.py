"""Focused tests for Phase 05 Step 4: Distribution and Attack Drift Detection."""

from __future__ import annotations

from trustrag.adaptive import (
    DriftMonitor,
    TelemetryRecord,
    compute_categorical_jsd,
    compute_psi,
)


def _make_clean_records(n: int, *, f3: float = 0.72, prov: str = "known", g3: str = "SUPPORTED") -> list[TelemetryRecord]:
    return [
        TelemetryRecord(
            f1_perplexity=0.80,
            f2_embedding_norm=0.82,
            f3_query_match=f3 + (0.02 * (i % 3)),
            f4_instruction_risk=0.0,
            f5_consensus_dev=0.85,
            f6_provenance_state=prov,
            g2_trust_score=0.82,
            g3_verdict=g3,
            retrieval_quality=0.80,
        )
        for i in range(n)
    ]


def test_psi_and_jsd_sanity() -> None:
    a = [0.7, 0.75, 0.8, 0.82, 0.85] * 6
    b = [0.1, 0.15, 0.2, 0.22, 0.25] * 6
    assert compute_psi(a, a) == 0.0
    assert compute_psi(a, b) > 0.25
    assert compute_categorical_jsd(["SUPPORTED"] * 20, ["SUPPORTED"] * 20) == 0.0
    assert compute_categorical_jsd(["SUPPORTED"] * 20, ["CONTRADICTED"] * 20) > 0.15


def test_insufficient_sample_suppresses_alerts() -> None:
    mon = DriftMonitor(window_size=30, min_samples=15)
    mon.set_baseline(_make_clean_records(25))
    mon.record_batch(_make_clean_records(5, f3=0.1))  # small window < 15
    rep = mon.evaluate_window("small-win")
    assert rep.classification == "insufficient_sample"
    assert rep.overall_severity == "insufficient_sample"
    assert rep.recommended_action == "none"


def test_separates_benign_drift_from_suspected_attack_drift_and_preserves_privacy() -> None:
    mon = DriftMonitor(window_size=40, min_samples=15)
    mon.set_baseline(_make_clean_records(30, f3=0.85, prov="known"))

    # Benign domain shift: lower F3 lexical overlap and unknown provenance, ZERO instruction risk & safe G2 trust
    benign_shifted = _make_clean_records(30, f3=0.15, prov="unknown")
    mon.record_batch(benign_shifted)
    rep_benign = mon.evaluate_window("benign-shift")
    assert rep_benign.classification == "benign_distribution_drift"
    assert rep_benign.recommended_action == "log_only"

    # Attack drift: rising F4 instruction risk + collapsing G2 trust + F5 consensus outlier
    atk_shifted = [
        TelemetryRecord(
            f1_perplexity=0.80,
            f2_embedding_norm=0.82,
            f3_query_match=0.65,
            f4_instruction_risk=0.75 if i % 2 == 0 else 0.45,
            f5_consensus_dev=0.25,
            f6_provenance_state="unknown",
            g2_trust_score=0.28,
            g3_verdict="CONTRADICTED",
            retrieval_quality=0.55,
        )
        for i in range(30)
    ]
    mon.current_window.clear()
    mon.record_batch(atk_shifted)
    rep_atk = mon.evaluate_window("attack-shift")
    assert rep_atk.classification == "suspected_attack_drift"
    assert rep_atk.recommended_action == "tighten_thresholds"
    assert "raw_query" not in rep_atk.model_dump_json()

