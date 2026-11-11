"""Phase 05 adaptive trust intelligence and continuous defense package."""

from trustrag.adaptive.calibration import (
    TrustCalibrator,
    collect_g2_partition_scores,
    compute_calibration_metrics,
    compute_reliability_diagram,
    evaluate_calibrator_on_partition,
)
from trustrag.adaptive.controller import (
    AdaptiveDefenseController,
    AdaptiveRunOutcome,
)
from trustrag.adaptive.drift import (
    DriftMonitor,
    TelemetryRecord,
    compute_categorical_jsd,
    compute_psi,
)
from trustrag.adaptive.feedback import (
    ALL_G3_VERDICTS,
    EvidenceFeedbackEvent,
    EvidenceQualityMonitor,
)
from trustrag.adaptive.policy_engine import (
    ALLOWED_PROPOSAL_SOURCES,
    FORBIDDEN_PROPOSAL_SOURCES,
    AdaptationPolicyEngine,
)
from trustrag.adaptive.schemas import (
    AdaptiveConfig,
    AdaptiveMode,
    CalibrationArtifact,
    CalibrationEvaluationReport,
    CalibrationMethod,
    ContextFeatures,
    DriftReport,
    FeedbackSummary,
    PolicyAuditEntry,
    PolicyChangeProposal,
    PolicyVersionRecord,
    ReliabilityBin,
    SignalDriftResult,
    ThresholdBounds,
    ThresholdRecommendation,
)
from trustrag.adaptive.thresholding import (
    ContextAwareThresholdSelector,
    extract_context_features,
)

__all__ = [
    "ALLOWED_PROPOSAL_SOURCES",
    "ALL_G3_VERDICTS",
    "FORBIDDEN_PROPOSAL_SOURCES",
    "AdaptationPolicyEngine",
    "AdaptiveConfig",
    "AdaptiveDefenseController",
    "AdaptiveMode",
    "AdaptiveRunOutcome",
    "CalibrationArtifact",
    "CalibrationEvaluationReport",
    "CalibrationMethod",
    "ContextAwareThresholdSelector",
    "ContextFeatures",
    "DriftMonitor",
    "DriftReport",
    "EvidenceFeedbackEvent",
    "EvidenceQualityMonitor",
    "FeedbackSummary",
    "PolicyAuditEntry",
    "PolicyChangeProposal",
    "PolicyVersionRecord",
    "ReliabilityBin",
    "SignalDriftResult",
    "TelemetryRecord",
    "ThresholdBounds",
    "ThresholdRecommendation",
    "TrustCalibrator",
    "collect_g2_partition_scores",
    "compute_calibration_metrics",
    "compute_categorical_jsd",
    "compute_psi",
    "compute_reliability_diagram",
    "evaluate_calibrator_on_partition",
    "extract_context_features",
]
