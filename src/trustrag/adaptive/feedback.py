"""Non-circular G3 evidence quality feedback monitoring for Phase 05 Step 6."""

from __future__ import annotations

import logging
from collections import Counter, deque
from collections.abc import Sequence
from dataclasses import dataclass, field

from trustrag.adaptive.schemas import FeedbackSummary
from trustrag.engine.schemas import (
    EvidenceDocument,
    G3AnswerVerdict,
    G3VerificationReport,
)

LOGGER = logging.getLogger(__name__)

ALL_G3_VERDICTS: tuple[str, ...] = tuple(v.value for v in G3AnswerVerdict)


@dataclass
class EvidenceFeedbackEvent:
    """Traceable G3 verification outcome linked to evidence IDs and content hashes."""

    verdict: str
    total_claims: int
    supported_claims: int
    contradicted_claims: int
    insufficient_claims: int
    uncertain_claims: int
    abstained: bool
    cited_doc_ids: list[str]
    participating_doc_hashes: dict[str, str]
    mean_confidence: float
    attributed_claim_count: int


@dataclass
class EvidenceQualityMonitor:
    """Monitors G3 claim/answer verification metrics to surface retrieval quality degradation.

    Strict Non-Circular Trust Invariant:
    - G3 feedback NEVER promotes unverified or untrusted documents to trusted/CLEAN status.
    - Repeated SUPPORTED outcomes NEVER inflate document trust scores or weaken G1/G2 thresholds.
    - Only failure diagnostics (contradictions, unsupported rates, attribution gaps) are emitted.
    """

    window_size: int = 50
    min_samples: int = 5
    unsupported_alert_threshold: float = 0.45
    contradiction_alert_threshold: float = 0.15
    min_attribution_coverage: float = 0.50
    events: deque[EvidenceFeedbackEvent] = field(default_factory=deque)

    def __post_init__(self) -> None:
        self.events = deque(self.events, maxlen=self.window_size)

    @staticmethod
    def is_document_promotion_allowed() -> bool:
        """Non-circular trust policy: G3 verification outcomes must NEVER promote documents."""
        return False

    def record_verification(
        self,
        report: G3VerificationReport,
        evidence_docs: Sequence[EvidenceDocument],
        *,
        abstained: bool = False,
    ) -> EvidenceFeedbackEvent:
        """Record one G3 verification report with full evidence traceability."""
        verdict = (
            report.verdict.value
            if report.verdict is not None
            else report.overall_status.to_answer_verdict().value
        )
        cited_ids: list[str] = []
        confidences: list[float] = []
        attributed = 0
        for claim in report.claims:
            confidences.append(float(claim.confidence))
            if claim.evidence_refs:
                attributed += 1
            for ref in claim.evidence_refs:
                if ref.doc_id not in cited_ids:
                    cited_ids.append(ref.doc_id)

        insufficient_cnt = (
            report.insufficient_count
            if report.insufficient_count is not None
            else report.not_enough_evidence_count
        )
        event = EvidenceFeedbackEvent(
            verdict=verdict,
            total_claims=report.total_claims,
            supported_claims=report.supported_count,
            contradicted_claims=report.contradicted_count,
            insufficient_claims=insufficient_cnt,
            uncertain_claims=report.uncertain_count,
            abstained=abstained,
            cited_doc_ids=cited_ids or [d.doc_id for d in evidence_docs],
            participating_doc_hashes={d.doc_id: d.content_hash for d in evidence_docs},
            mean_confidence=(
                round(sum(confidences) / len(confidences), 4) if confidences else 0.0
            ),
            attributed_claim_count=attributed,
        )
        self.events.append(event)
        return event

    def summarize(self) -> FeedbackSummary:
        """Compute windowed G3 quality summary and degradation alerts."""
        counts: dict[str, int] = {v: 0 for v in ALL_G3_VERDICTS}
        win = list(self.events)
        n = len(win)
        if n == 0:
            return FeedbackSummary(window_size=0, verdict_counts=counts)

        total_claims = 0
        total_supported = 0
        total_contradicted = 0
        total_unsupported = 0
        total_attributed = 0
        abstained_cnt = 0
        failure_doc_counter: Counter[str] = Counter()

        for ev in win:
            counts[ev.verdict] = counts.get(ev.verdict, 0) + 1
            total_claims += ev.total_claims
            total_supported += ev.supported_claims
            total_contradicted += ev.contradicted_claims
            total_unsupported += ev.insufficient_claims + ev.uncertain_claims
            total_attributed += ev.attributed_claim_count
            if ev.abstained:
                abstained_cnt += 1
            if ev.verdict in {"CONTRADICTED", "INSUFFICIENT_EVIDENCE"} or ev.contradicted_claims > 0:
                for did in ev.cited_doc_ids:
                    failure_doc_counter[did] += 1

        if total_claims > 0:
            unsupported_rate = total_unsupported / total_claims
            contradiction_rate = total_contradicted / total_claims
            support_cov = total_supported / total_claims
            attribution_cov = total_attributed / total_claims
        else:
            unsupported_rate = (counts["INSUFFICIENT_EVIDENCE"] + counts["UNCERTAIN"]) / n
            contradiction_rate = counts["CONTRADICTED"] / n
            support_cov = counts["SUPPORTED"] / n
            attribution_cov = 0.0

        abstention_rate = abstained_cnt / n
        low_evidence_docs = sorted(did for did, c in failure_doc_counter.items() if c >= 2)

        alerts: list[str] = []
        if n >= self.min_samples:
            if unsupported_rate >= self.unsupported_alert_threshold:
                alerts.append("HIGH_UNSUPPORTED_CLAIM_RATE")
            if contradiction_rate >= self.contradiction_alert_threshold or counts["CONTRADICTED"] / n >= self.contradiction_alert_threshold:
                alerts.append("ELEVATED_CONTRADICTION_RATE")
            if total_claims > 0 and attribution_cov < self.min_attribution_coverage:
                alerts.append("LOW_EVIDENCE_ATTRIBUTION_COVERAGE")
            if low_evidence_docs:
                alerts.append("REPEATED_RETRIEVAL_FAILURES")

        degradation_detected = bool(alerts)
        summary = FeedbackSummary(
            window_size=n,
            verdict_counts=counts,
            unsupported_claim_rate=round(min(1.0, unsupported_rate), 4),
            contradiction_rate=round(min(1.0, contradiction_rate), 4),
            abstention_rate=round(min(1.0, abstention_rate), 4),
            mean_support_coverage=round(min(1.0, support_cov), 4),
            low_evidence_doc_ids=low_evidence_docs,
            degradation_detected=degradation_detected,
            alerts=alerts,
        )
        if degradation_detected:
            LOGGER.info("G3 evidence quality degradation detected", extra={"alerts": alerts, "window_size": n})
        return summary


__all__ = [
    "ALL_G3_VERDICTS",
    "EvidenceFeedbackEvent",
    "EvidenceQualityMonitor",
]

