"""Versioned configuration, artifact, monitoring, and policy schemas for Phase 05 adaptive defense."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class AdaptiveMode(StrEnum):
    """Execution mode for Phase 05 adaptive intelligence."""

    DISABLED = "disabled"
    SHADOW = "shadow"
    ENFORCED = "enforced"


class CalibrationMethod(StrEnum):
    """Supported deterministic trust-score calibration methods."""

    NONE = "none"
    PLATT = "platt"
    ISOTONIC = "isotonic"
    TEMPERATURE = "temperature"


class ReliabilityBin(BaseModel):
    """Single bin of a reliability diagram comparing confidence to empirical accuracy."""

    bin_index: int = Field(ge=0)
    lower_bound: float = Field(ge=0.0, le=1.0)
    upper_bound: float = Field(ge=0.0, le=1.0)
    count: int = Field(ge=0)
    mean_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    empirical_clean_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    calibration_gap: float | None = Field(default=None, ge=0.0, le=1.0)


class CalibrationArtifact(BaseModel):
    """Serializable, versioned calibration artifact using explicit numeric parameters."""

    version: str = Field(default="cal-v1.0.0", min_length=1)
    method: CalibrationMethod = Field(default=CalibrationMethod.PLATT)
    fitted_datasets: list[str] = Field(default_factory=list)
    fitted_splits: list[str] = Field(default_factory=list)
    fit_seed: int = Field(default=42)
    sample_count: int = Field(default=0, ge=0)
    clean_count: int = Field(default=0, ge=0)
    attack_count: int = Field(default=0, ge=0)
    class_weight: str | None = Field(default=None)
    # Platt parameters (logistic regression in logit or raw space)
    platt_coef: float | None = Field(default=None)
    platt_intercept: float | None = Field(default=None)
    use_logit_transform: bool = Field(default=True)
    # Isotonic regression piecewise linear thresholds
    isotonic_x_thresholds: list[float] = Field(default_factory=list)
    isotonic_y_thresholds: list[float] = Field(default_factory=list)
    # Temperature scaling parameter (T > 0)
    temperature: float | None = Field(default=None)
    clip_eps: float = Field(default=1e-4, gt=0.0, lt=0.1)
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    artifact_sha256: str = Field(default="")

    @model_validator(mode="after")
    def validate_split_hygiene_and_params(self) -> CalibrationArtifact:
        """Reject test-split leakage and invalid non-finite parameters."""
        import math

        for split_name in self.fitted_splits:
            if "test" in split_name.strip().lower():
                raise ValueError(
                    f"Split hygiene violation: calibration split '{split_name}' appears to be a test split."
                )

        if self.method == CalibrationMethod.PLATT:
            if self.platt_coef is None or self.platt_intercept is None:
                raise ValueError("Platt calibration requires platt_coef and platt_intercept.")
            if not (math.isfinite(self.platt_coef) and math.isfinite(self.platt_intercept)):
                raise ValueError("Platt parameters must be finite.")
            if self.platt_coef <= 0.0:
                raise ValueError("Platt slope must remain positive to preserve trust monotonicity.")
        elif self.method == CalibrationMethod.ISOTONIC:
            if (
                len(self.isotonic_x_thresholds) < 2
                or len(self.isotonic_x_thresholds) != len(self.isotonic_y_thresholds)
            ):
                raise ValueError("Isotonic calibration requires matching x/y threshold arrays (>=2 points).")
            for x, y in zip(self.isotonic_x_thresholds, self.isotonic_y_thresholds, strict=False):
                if not (math.isfinite(x) and math.isfinite(y) and 0.0 <= y <= 1.0):
                    raise ValueError("Isotonic thresholds must be finite with y in [0, 1].")
        elif (
            self.method == CalibrationMethod.TEMPERATURE
            and (self.temperature is None or not math.isfinite(self.temperature) or self.temperature <= 0.0)
        ):
            raise ValueError("Temperature scaling requires a finite positive temperature > 0.")

        if not self.artifact_sha256:
            self.artifact_sha256 = self.compute_content_hash()
        return self

    def compute_content_hash(self) -> str:
        """Compute deterministic SHA-256 hash over calibration metadata and numeric parameters."""
        payload = self.model_dump(exclude={"artifact_sha256", "created_at"})
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify stored artifact checksum matches serialized parameters."""
        if not self.artifact_sha256:
            return False
        return self.artifact_sha256 == self.compute_content_hash()


class CalibrationEvaluationReport(BaseModel):
    """Calibration and classification quality evaluation snapshot."""

    method: CalibrationMethod
    dataset_name: str
    split: str
    sample_count: int = Field(ge=0)
    clean_count: int = Field(ge=0)
    attack_count: int = Field(ge=0)
    brier_score: float = Field(ge=0.0)
    ece: float = Field(ge=0.0)
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    f1: float = Field(ge=0.0, le=1.0)
    fpr: float = Field(ge=0.0, le=1.0)
    fnr: float = Field(ge=0.0, le=1.0)
    roc_auc: float | None = Field(default=None)
    pr_auc: float | None = Field(default=None)
    reliability_bins: list[ReliabilityBin] = Field(default_factory=list)


class ThresholdBounds(BaseModel):
    """Hard safety bounds preventing silent security weakening of G1/G2 thresholds."""

    g2_trust_min: float = Field(default=0.52, ge=0.40, le=0.90)
    g2_trust_max: float = Field(default=0.75, ge=0.50, le=0.95)
    g2_poison_min: float = Field(default=0.35, ge=0.20, le=0.60)
    g2_poison_max: float = Field(default=0.50, ge=0.30, le=0.70)
    g1_flag_min: float = Field(default=0.25, ge=0.10, le=0.50)
    g1_flag_max: float = Field(default=0.40, ge=0.20, le=0.60)
    g1_block_min: float = Field(default=0.55, ge=0.30, le=0.80)
    g1_block_max: float = Field(default=0.75, ge=0.50, le=0.90)
    removal_cap_ratio_min: float = Field(default=0.50, ge=0.20, le=0.80)
    removal_cap_ratio_max: float = Field(default=0.75, ge=0.30, le=0.90)
    trust_weight_min: float = Field(default=0.20, ge=0.10, le=0.45)
    trust_weight_max: float = Field(default=0.55, ge=0.45, le=0.80)


class ContextFeatures(BaseModel):
    """Query/retrieval-derived context features (never steered by document instructions)."""

    query_intent: Literal["factual", "analytical", "instructional_ambiguous", "suspicious"] = "factual"
    query_word_count: int = Field(default=0, ge=0)
    g1_risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    g1_flagged: bool = False
    candidate_count: int = Field(default=0, ge=0)
    evidence_diversity: float = Field(default=0.0, ge=0.0, le=1.0)
    provenance_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    mean_available_signals: float = Field(default=0.0, ge=0.0, le=6.0)
    conflict_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    security_uncertainty_ratio: float = Field(default=0.0, ge=0.0, le=1.0)


class ThresholdRecommendation(BaseModel):
    """Auditable threshold recommendation bounded by fixed security invariants."""

    g1_flag_threshold: float
    g1_block_threshold: float
    g2_trust_threshold: float
    g2_poison_threshold: float
    removal_cap_ratio: float
    trust_weight: float = 0.45
    used_static_fallback: bool = False
    reason_codes: list[str] = Field(default_factory=list)
    context_snapshot: dict[str, Any] = Field(default_factory=dict)


class SignalDriftResult(BaseModel):
    """Drift assessment for an individual numeric or categorical monitoring stream."""

    stream_name: str
    stream_type: Literal["continuous", "categorical"]
    baseline_n: int = Field(ge=0)
    current_n: int = Field(ge=0)
    psi: float | None = None
    ks_statistic: float | None = None
    ks_p_value: float | None = None
    js_divergence: float | None = None
    insufficient_sample: bool = False
    drifted: bool = False


class DriftReport(BaseModel):
    """Aggregated drift report distinguishing benign distribution drift from attack drift."""

    window_id: str
    overall_severity: Literal["none", "insufficient_sample", "low", "moderate", "high"] = "none"
    classification: Literal[
        "stable",
        "insufficient_sample",
        "benign_distribution_drift",
        "suspected_attack_drift",
        "quality_degradation",
    ] = "stable"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    signal_results: dict[str, SignalDriftResult] = Field(default_factory=dict)
    summary_metrics: dict[str, float] = Field(default_factory=dict)
    recommended_action: Literal["none", "log_only", "propose_review", "tighten_thresholds"] = "none"


class FeedbackSummary(BaseModel):
    """Non-circular G3 verification quality feedback metrics."""

    window_size: int = Field(default=0, ge=0)
    verdict_counts: dict[str, int] = Field(default_factory=dict)
    unsupported_claim_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    contradiction_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    abstention_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    mean_support_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    low_evidence_doc_ids: list[str] = Field(default_factory=list)
    degradation_detected: bool = False
    alerts: list[str] = Field(default_factory=list)


class PolicyChangeProposal(BaseModel):
    """Candidate adaptation proposal checked against invariant safety gates before applying."""

    proposal_id: str
    source: str
    reason: str
    proposed_g1_flag_threshold: float | None = None
    proposed_g1_block_threshold: float | None = None
    proposed_g2_trust_threshold: float | None = None
    proposed_g2_poison_threshold: float | None = None
    proposed_removal_cap_ratio: float | None = None
    monitoring_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    authorized: bool = False
    authorizer: str | None = None


class PolicyVersionRecord(BaseModel):
    """Versioned configuration snapshot supporting deterministic rollback."""

    version_id: str
    timestamp: str
    g1_flag_threshold: float
    g1_block_threshold: float
    g2_trust_threshold: float
    g2_poison_threshold: float
    removal_cap_ratio: float
    calibration_version: str | None = None
    is_static_baseline: bool = False


class PolicyAuditEntry(BaseModel):
    """Immutable audit log record for every adaptation evaluation or rollback."""

    timestamp: str
    proposal_id: str
    decision: Literal["APPLIED", "REJECTED", "ROLLED_BACK", "FAIL_SAFE_STATIC"]
    from_version: str
    to_version: str | None = None
    reasons: list[str] = Field(default_factory=list)
    snapshot: dict[str, Any] = Field(default_factory=dict)


class AdaptiveConfig(BaseModel):
    """Master configuration for Phase 05 adaptive defense (defaults keep static Phase 04 intact)."""

    mode: AdaptiveMode = Field(default=AdaptiveMode.DISABLED)
    enable_calibration: bool = Field(default=False)
    calibration_artifact_path: str | None = Field(default=None)
    enable_context_thresholding: bool = Field(default=False)
    threshold_bounds: ThresholdBounds = Field(default_factory=ThresholdBounds)
    enable_drift_monitoring: bool = Field(default=False)
    drift_window_size: int = Field(default=30, ge=5)
    drift_min_samples: int = Field(default=15, ge=5)
    enable_feedback_monitoring: bool = Field(default=False)
    enable_policy_engine: bool = Field(default=False)
    min_monitoring_confidence: float = Field(default=0.70, ge=0.0, le=1.0)
    adaptation_timeout_seconds: float = Field(default=2.0, gt=0.0)


__all__ = [
    "AdaptiveConfig",
    "AdaptiveMode",
    "CalibrationArtifact",
    "CalibrationEvaluationReport",
    "CalibrationMethod",
    "ContextFeatures",
    "DriftReport",
    "FeedbackSummary",
    "PolicyAuditEntry",
    "PolicyChangeProposal",
    "PolicyVersionRecord",
    "ReliabilityBin",
    "SignalDriftResult",
    "ThresholdBounds",
    "ThresholdRecommendation",
]

