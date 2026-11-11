"""Focused tests for Phase 05 Step 7: Controlled Feedback & Adaptation Policy Engine."""

from __future__ import annotations

from trustrag.adaptive import (
    AdaptationPolicyEngine,
    DriftReport,
    FeedbackSummary,
    PolicyChangeProposal,
)
from trustrag.config import load_config


def test_policy_lifecycle_audit_authorization_and_rollback() -> None:
    cfg = load_config()
    engine = AdaptationPolicyEngine(baseline_settings=cfg, calibration_version="platt-mixed-v1")
    assert engine.current_version.version_id == "v0-static-baseline"

    drift = DriftReport(
        window_id="w1",
        overall_severity="high",
        classification="suspected_attack_drift",
        confidence=0.95,
        recommended_action="tighten_thresholds",
    )
    prop = engine.evaluate_observations(drift_report=drift)
    assert prop is not None
    assert prop.authorized is False

    # Unapproved proposal must be rejected
    rej = engine.apply_proposal(prop)
    assert rej.decision == "REJECTED"
    assert "REJECTED_AUTHORIZATION_REQUIRED" in rej.reasons
    assert engine.current_version.version_id == "v0-static-baseline"

    # Authorized valid tightening proposal applies and versions cleanly
    prop.authorized = True
    prop.authorizer = "secops-lead"
    app = engine.apply_proposal(prop)
    assert app.decision == "APPLIED"
    assert engine.current_version.version_id == "v1-adaptive"
    assert engine.current_version.g2_trust_threshold > cfg.msd.trust_threshold

    # Rollback restores v0-static-baseline deterministically
    rb = engine.rollback()
    assert rb.decision == "ROLLED_BACK"
    assert engine.current_version.version_id == "v0-static-baseline"
    assert engine.current_version.g2_trust_threshold == cfg.msd.trust_threshold


def test_policy_rejects_adversarial_and_low_confidence_proposals() -> None:
    cfg = load_config()
    engine = AdaptationPolicyEngine(baseline_settings=cfg)

    # 1. Retrieved document attempting threshold weakening
    doc_prop = PolicyChangeProposal(
        proposal_id="adv-doc-1",
        source="retrieved_document",
        reason="Injected document says relax thresholds",
        proposed_g2_trust_threshold=0.53,
        proposed_g2_poison_threshold=0.20,
        monitoring_confidence=0.99,
        authorized=True,
        authorizer="spoofed",
    )
    r1 = engine.apply_proposal(doc_prop)
    assert r1.decision == "REJECTED"
    assert any("UNTRUSTED_OR_UNKNOWN_SOURCE" in x for x in r1.reasons)

    # 2. Insufficient monitoring confidence
    low_conf = PolicyChangeProposal(
        proposal_id="low-conf-1",
        source="drift_monitor",
        reason="Noisy small window",
        proposed_g2_trust_threshold=0.65,
        monitoring_confidence=0.40,
        authorized=True,
        authorizer="secops",
    )
    r2 = engine.apply_proposal(low_conf)
    assert r2.decision == "REJECTED"
    assert any("INSUFFICIENT_CONFIDENCE" in x for x in r2.reasons)

    # 3. Attempting silent weakening below static poison/g1/removal_cap floors
    weaken = PolicyChangeProposal(
        proposal_id="weaken-1",
        source="policy_operator",
        reason="Lower removal cap",
        proposed_removal_cap_ratio=0.25,
        proposed_g2_poison_threshold=0.20,
        monitoring_confidence=0.95,
        authorized=True,
        authorizer="secops",
    )
    r3 = engine.apply_proposal(weaken)
    assert r3.decision == "REJECTED"
    assert "REJECTED_SECURITY_WEAKENING_BELOW_STATIC_BASELINE" in r3.reasons

    # 4. Stable / benign drift observations must return no adaptation proposal
    stable_drift = DriftReport(window_id="w2", overall_severity="low", classification="benign_distribution_drift", confidence=0.80)
    healthy_fb = FeedbackSummary(window_size=20, degradation_detected=False)
    assert engine.evaluate_observations(drift_report=stable_drift, feedback_summary=healthy_fb) is None

