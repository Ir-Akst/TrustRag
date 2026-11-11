"""Auditable adaptation policy engine with safety gates and versioned rollback (Phase 05 Step 7)."""

from __future__ import annotations

import logging
import math
from datetime import UTC, datetime

from trustrag.adaptive.schemas import (
    DriftReport,
    FeedbackSummary,
    PolicyAuditEntry,
    PolicyChangeProposal,
    PolicyVersionRecord,
    ThresholdBounds,
)
from trustrag.config import Settings, load_config

LOGGER = logging.getLogger(__name__)

FORBIDDEN_PROPOSAL_SOURCES: frozenset[str] = frozenset(
    {
        "retrieved_document",
        "document_instruction",
        "untrusted_document",
        "feedback_repetition",
        "unknown",
        "",
    }
)
ALLOWED_PROPOSAL_SOURCES: frozenset[str] = frozenset(
    {
        "drift_monitor",
        "feedback_monitor",
        "policy_operator",
        "validation_calibrator",
    }
)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class AdaptationPolicyEngine:
    """Controlled, auditable policy manager governing Phase 05 threshold & calibration state."""

    def __init__(
        self,
        *,
        baseline_settings: Settings | None = None,
        bounds: ThresholdBounds | None = None,
        min_monitoring_confidence: float = 0.70,
        require_authorization: bool = True,
        calibration_version: str | None = None,
    ) -> None:
        self.baseline_settings = (baseline_settings or load_config()).model_copy(deep=True)
        self.bounds = bounds or ThresholdBounds()
        self.min_monitoring_confidence = min_monitoring_confidence
        self.require_authorization = require_authorization

        self._static_record = PolicyVersionRecord(
            version_id="v0-static-baseline",
            timestamp=_now_iso(),
            g1_flag_threshold=self.baseline_settings.guardrails.flag_threshold,
            g1_block_threshold=self.baseline_settings.guardrails.block_threshold,
            g2_trust_threshold=self.baseline_settings.msd.trust_threshold,
            g2_poison_threshold=self.baseline_settings.msd.poison_threshold,
            removal_cap_ratio=self.baseline_settings.retrieval.removal_cap_ratio,
            calibration_version=calibration_version,
            is_static_baseline=True,
        )
        self.version_history: list[PolicyVersionRecord] = [self._static_record.model_copy(deep=True)]
        self.audit_log: list[PolicyAuditEntry] = []
        self._version_counter: int = 0

    @property
    def current_version(self) -> PolicyVersionRecord:
        """Return currently active policy version snapshot."""
        return self.version_history[-1]

    @property
    def static_baseline(self) -> PolicyVersionRecord:
        """Return immutable static Phase 04 baseline snapshot."""
        return self._static_record.model_copy(deep=True)

    def evaluate_observations(
        self,
        *,
        drift_report: DriftReport | None = None,
        feedback_summary: FeedbackSummary | None = None,
        proposal_id: str | None = None,
    ) -> PolicyChangeProposal | None:
        """Generate an auditable adaptation proposal ONLY when verified monitoring confidence warrants action."""
        cur = self.current_version
        pid = proposal_id or f"prop-{self._version_counter + 1}"

        if drift_report is not None and drift_report.classification == "suspected_attack_drift":
            if drift_report.confidence < self.min_monitoring_confidence:
                return None
            step = 0.06 if drift_report.overall_severity == "high" else 0.04
            b = self.bounds
            return PolicyChangeProposal(
                proposal_id=pid,
                source="drift_monitor",
                reason=f"Confirmed {drift_report.overall_severity} suspected_attack_drift in window {drift_report.window_id}",
                proposed_g1_flag_threshold=round(max(b.g1_flag_min, cur.g1_flag_threshold - 0.04), 4),
                proposed_g1_block_threshold=round(max(b.g1_block_min, cur.g1_block_threshold - 0.06), 4),
                proposed_g2_trust_threshold=round(min(b.g2_trust_max, cur.g2_trust_threshold + step), 4),
                proposed_g2_poison_threshold=round(min(b.g2_poison_max, cur.g2_poison_threshold + 0.03), 4),
                proposed_removal_cap_ratio=round(min(b.removal_cap_ratio_max, cur.removal_cap_ratio + 0.10), 4),
                monitoring_confidence=drift_report.confidence,
                authorized=False,
            )

        if feedback_summary is not None and feedback_summary.degradation_detected and feedback_summary.window_size >= 5:
            b = self.bounds
            conf = round(min(0.95, 0.65 + 0.02 * feedback_summary.window_size), 4)
            if conf < self.min_monitoring_confidence:
                return None
            return PolicyChangeProposal(
                proposal_id=pid,
                source="feedback_monitor",
                reason=f"G3 quality degradation alerts: {feedback_summary.alerts}",
                proposed_g2_trust_threshold=round(min(b.g2_trust_max, cur.g2_trust_threshold + 0.03), 4),
                proposed_removal_cap_ratio=round(min(b.removal_cap_ratio_max, cur.removal_cap_ratio + 0.05), 4),
                monitoring_confidence=conf,
                authorized=False,
            )

        return None

    def _validate_proposal(
        self,
        proposal: PolicyChangeProposal,
    ) -> tuple[bool, list[str], dict[str, float]]:
        """Verify candidate proposal against immutable security & source invariants."""
        reasons: list[str] = []
        src_norm = proposal.source.strip().lower()
        if src_norm in FORBIDDEN_PROPOSAL_SOURCES or src_norm not in ALLOWED_PROPOSAL_SOURCES:
            reasons.append(f"REJECTED_UNTRUSTED_OR_UNKNOWN_SOURCE:{proposal.source}")

        if self.require_authorization and (not proposal.authorized or not (proposal.authorizer or "").strip()):
            reasons.append("REJECTED_AUTHORIZATION_REQUIRED")

        if not math.isfinite(proposal.monitoring_confidence) or proposal.monitoring_confidence < self.min_monitoring_confidence:
            reasons.append(
                f"REJECTED_INSUFFICIENT_CONFIDENCE:{proposal.monitoring_confidence}<{self.min_monitoring_confidence}"
            )

        cur = self.current_version
        cand = {
            "g1_flag_threshold": proposal.proposed_g1_flag_threshold if proposal.proposed_g1_flag_threshold is not None else cur.g1_flag_threshold,
            "g1_block_threshold": proposal.proposed_g1_block_threshold if proposal.proposed_g1_block_threshold is not None else cur.g1_block_threshold,
            "g2_trust_threshold": proposal.proposed_g2_trust_threshold if proposal.proposed_g2_trust_threshold is not None else cur.g2_trust_threshold,
            "g2_poison_threshold": proposal.proposed_g2_poison_threshold if proposal.proposed_g2_poison_threshold is not None else cur.g2_poison_threshold,
            "removal_cap_ratio": proposal.proposed_removal_cap_ratio if proposal.proposed_removal_cap_ratio is not None else cur.removal_cap_ratio,
        }

        if not all(math.isfinite(v) for v in cand.values()):
            reasons.append("REJECTED_NON_FINITE_PARAMETERS")
            return False, reasons, cand

        b = self.bounds
        base = self._static_record
        if not (b.g1_flag_min <= cand["g1_flag_threshold"] <= b.g1_flag_max):
            reasons.append("REJECTED_G1_FLAG_OUT_OF_BOUNDS")
        if not (b.g1_block_min <= cand["g1_block_threshold"] <= b.g1_block_max):
            reasons.append("REJECTED_G1_BLOCK_OUT_OF_BOUNDS")
        if not (b.g2_trust_min <= cand["g2_trust_threshold"] <= b.g2_trust_max):
            reasons.append("REJECTED_G2_TRUST_OUT_OF_BOUNDS")
        if not (b.g2_poison_min <= cand["g2_poison_threshold"] <= b.g2_poison_max):
            reasons.append("REJECTED_G2_POISON_OUT_OF_BOUNDS")
        if not (b.removal_cap_ratio_min <= cand["removal_cap_ratio"] <= b.removal_cap_ratio_max):
            reasons.append("REJECTED_REMOVAL_CAP_OUT_OF_BOUNDS")

        # Strict ordering invariants
        if cand["g1_flag_threshold"] >= cand["g1_block_threshold"]:
            reasons.append("REJECTED_G1_THRESHOLD_ORDERING")
        if cand["g2_poison_threshold"] >= cand["g2_trust_threshold"]:
            reasons.append("REJECTED_G2_THRESHOLD_ORDERING")

        # Strict anti-weakening floors vs frozen static baseline
        if (
            cand["g1_flag_threshold"] > base.g1_flag_threshold
            or cand["g1_block_threshold"] > base.g1_block_threshold
            or cand["g2_poison_threshold"] < base.g2_poison_threshold
            or cand["removal_cap_ratio"] < base.removal_cap_ratio
        ):
            reasons.append("REJECTED_SECURITY_WEAKENING_BELOW_STATIC_BASELINE")

        return len(reasons) == 0, reasons, cand

    def apply_proposal(self, proposal: PolicyChangeProposal) -> PolicyAuditEntry:
        """Validate, authorize, apply (or reject), and log every policy proposal."""
        cur = self.current_version
        valid, reasons, cand = self._validate_proposal(proposal)
        if not valid:
            entry = PolicyAuditEntry(
                timestamp=_now_iso(),
                proposal_id=proposal.proposal_id,
                decision="REJECTED",
                from_version=cur.version_id,
                to_version=None,
                reasons=reasons,
                snapshot={"proposal": proposal.model_dump(), "current_version": cur.model_dump()},
            )
            self.audit_log.append(entry)
            LOGGER.warning("Policy proposal rejected", extra={"proposal_id": proposal.proposal_id, "reasons": reasons})
            return entry

        self._version_counter += 1
        new_vid = f"v{self._version_counter}-adaptive"
        new_rec = PolicyVersionRecord(
            version_id=new_vid,
            timestamp=_now_iso(),
            g1_flag_threshold=round(cand["g1_flag_threshold"], 4),
            g1_block_threshold=round(cand["g1_block_threshold"], 4),
            g2_trust_threshold=round(cand["g2_trust_threshold"], 4),
            g2_poison_threshold=round(cand["g2_poison_threshold"], 4),
            removal_cap_ratio=round(cand["removal_cap_ratio"], 4),
            calibration_version=cur.calibration_version,
            is_static_baseline=False,
        )
        self.version_history.append(new_rec)
        entry = PolicyAuditEntry(
            timestamp=_now_iso(),
            proposal_id=proposal.proposal_id,
            decision="APPLIED",
            from_version=cur.version_id,
            to_version=new_vid,
            reasons=[proposal.reason, f"authorized_by:{proposal.authorizer}"],
            snapshot={"before": cur.model_dump(), "after": new_rec.model_dump()},
        )
        self.audit_log.append(entry)
        LOGGER.info("Policy proposal applied", extra={"proposal_id": proposal.proposal_id, "to_version": new_vid})
        return entry

    def rollback(
        self,
        *,
        target_version_id: str | None = None,
        reason: str = "operator_rollback",
    ) -> PolicyAuditEntry:
        """Deterministically restore a prior known-good version or static baseline."""
        cur = self.current_version
        target: PolicyVersionRecord | None = None

        if target_version_id is not None:
            for rec in self.version_history:
                if rec.version_id == target_version_id:
                    target = rec.model_copy(deep=True)
                    break
            if target is None:
                return self.rollback_to_static_baseline(reason=f"missing_target:{target_version_id}_fail_safe_static")
        elif len(self.version_history) >= 2:
            target = self.version_history[-2].model_copy(deep=True)
        else:
            return self.rollback_to_static_baseline(reason=reason)

        # Validate restored record integrity before switching; on any corruption, force static baseline
        if not self._is_version_record_valid(target):
            return self.rollback_to_static_baseline(reason="corrupted_rollback_target_fail_safe_static")

        self.version_history.append(target)
        entry = PolicyAuditEntry(
            timestamp=_now_iso(),
            proposal_id=f"rollback-{len(self.audit_log) + 1}",
            decision="ROLLED_BACK",
            from_version=cur.version_id,
            to_version=target.version_id,
            reasons=[reason],
            snapshot={"restored": target.model_dump()},
        )
        self.audit_log.append(entry)
        return entry

    def rollback_to_static_baseline(self, *, reason: str = "fail_safe_static_restore") -> PolicyAuditEntry:
        """Force immediate deterministic restore to frozen Phase 04 static configuration."""
        cur = self.current_version
        restored = self._static_record.model_copy(deep=True)
        self.version_history.append(restored)
        entry = PolicyAuditEntry(
            timestamp=_now_iso(),
            proposal_id=f"static-restore-{len(self.audit_log) + 1}",
            decision="FAIL_SAFE_STATIC",
            from_version=cur.version_id,
            to_version=restored.version_id,
            reasons=[reason],
            snapshot={"restored": restored.model_dump()},
        )
        self.audit_log.append(entry)
        return entry

    def _is_version_record_valid(self, rec: PolicyVersionRecord) -> bool:
        b = self.bounds
        vals = (
            rec.g1_flag_threshold,
            rec.g1_block_threshold,
            rec.g2_trust_threshold,
            rec.g2_poison_threshold,
            rec.removal_cap_ratio,
        )
        if not all(math.isfinite(v) for v in vals):
            return False
        if rec.g1_flag_threshold >= rec.g1_block_threshold or rec.g2_poison_threshold >= rec.g2_trust_threshold:
            return False
        return (
            b.g1_flag_min <= rec.g1_flag_threshold <= b.g1_flag_max
            and b.g1_block_min <= rec.g1_block_threshold <= b.g1_block_max
            and b.g2_trust_min <= rec.g2_trust_threshold <= b.g2_trust_max
            and b.g2_poison_min <= rec.g2_poison_threshold <= b.g2_poison_max
            and b.removal_cap_ratio_min <= rec.removal_cap_ratio <= b.removal_cap_ratio_max
        )

    def apply_active_policy_to_settings(self, settings: Settings | None = None) -> Settings:
        """Return a fresh Settings copy reflecting current active policy version."""
        out = (settings or self.baseline_settings).model_copy(deep=True)
        cur = self.current_version
        out.guardrails.flag_threshold = cur.g1_flag_threshold
        out.guardrails.block_threshold = cur.g1_block_threshold
        out.msd.trust_threshold = cur.g2_trust_threshold
        out.msd.poison_threshold = cur.g2_poison_threshold
        out.retrieval.removal_cap_ratio = cur.removal_cap_ratio
        return out


__all__ = [
    "ALLOWED_PROPOSAL_SOURCES",
    "FORBIDDEN_PROPOSAL_SOURCES",
    "AdaptationPolicyEngine",
]

