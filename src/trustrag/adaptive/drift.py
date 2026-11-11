"""Distribution and attack-pattern drift monitoring for Phase 05 Step 4."""

from __future__ import annotations

import logging
import math
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from scipy.spatial.distance import jensenshannon
from scipy.stats import ks_2samp

from trustrag.adaptive.schemas import DriftReport, SignalDriftResult
from trustrag.engine.schemas import EvidenceDocument, G2DocumentAssessment, G3VerificationReport

LOGGER = logging.getLogger(__name__)


@dataclass
class TelemetryRecord:
    """Privacy-preserving numeric & categorical telemetry snapshot (retains NO raw query text)."""

    f1_perplexity: float | None = None
    f2_embedding_norm: float | None = None
    f3_query_match: float | None = None
    f4_instruction_risk: float | None = None
    f5_consensus_dev: float | None = None
    f6_provenance_state: str = "unknown"
    g2_trust_score: float | None = None
    g3_verdict: str | None = None
    retrieval_quality: float | None = None
    mean_top_relevance: float | None = None

    @classmethod
    def from_pipeline_step(
        cls,
        *,
        assessments: Sequence[G2DocumentAssessment],
        retained_docs: Sequence[EvidenceDocument],
        requested_top_k: int,
        g3_report: G3VerificationReport | None = None,
    ) -> list[TelemetryRecord]:
        """Extract privacy-safe telemetry rows from G2/G3 outputs without storing raw query/doc text."""
        records: list[TelemetryRecord] = []
        retention_ratio = min(1.0, len(retained_docs) / max(1, requested_top_k))
        rels = [a.original_retrieval_score for a in assessments if a.original_retrieval_score is not None]
        mean_rel = float(sum(rels) / len(rels)) if rels else 0.0
        g3_v = (
            g3_report.verdict.value
            if g3_report is not None and g3_report.verdict is not None
            else (g3_report.overall_status.to_answer_verdict().value if g3_report is not None else None)
        )

        for a in assessments:
            prov = (a.provenance or "").strip().lower()
            prov_cat = "unknown" if not prov or prov == "unknown" else "known"

            def _get_sig(assessment: G2DocumentAssessment, name: str) -> float | None:
                s = assessment.signals.get(name)
                if s is not None and s.available and s.value is not None:
                    return float(s.value)
                return None

            records.append(
                cls(
                    f1_perplexity=_get_sig(a, "perplexity"),
                    f2_embedding_norm=_get_sig(a, "embedding_norm"),
                    f3_query_match=_get_sig(a, "query_match"),
                    f4_instruction_risk=float(a.instruction_risk_score),
                    f5_consensus_dev=_get_sig(a, "consensus_deviation"),
                    f6_provenance_state=prov_cat,
                    g2_trust_score=float(a.trust_score),
                    g3_verdict=g3_v,
                    retrieval_quality=round(0.5 * retention_ratio + 0.5 * min(1.0, mean_rel), 4),
                    mean_top_relevance=round(mean_rel, 4),
                )
            )
        if not assessments and g3_v is not None:
            records.append(cls(g3_verdict=g3_v, retrieval_quality=0.0, mean_top_relevance=0.0))
        return records


def compute_psi(
    baseline: Sequence[float],
    current: Sequence[float],
    *,
    n_bins: int = 5,
    bounded_unit: bool = True,
    eps: float = 1e-2,
) -> float:
    """Compute Population Stability Index (PSI) with Laplace bin smoothing."""
    b_arr = np.asarray(baseline, dtype=float)
    c_arr = np.asarray(current, dtype=float)
    if b_arr.size == 0 or c_arr.size == 0:
        return 0.0

    if bounded_unit:
        edges = np.linspace(0.0, 1.0, n_bins + 1)
    else:
        lo = float(min(np.min(b_arr), np.min(c_arr)))
        hi = float(max(np.max(b_arr), np.max(c_arr)))
        if math.isclose(lo, hi):
            return 0.0
        edges = np.quantile(b_arr, np.linspace(0.0, 1.0, n_bins + 1))
        edges[0] = min(lo, float(edges[0])) - 1e-9
        edges[-1] = max(hi, float(edges[-1])) + 1e-9
        # Ensure strictly increasing edges if quantiles tie
        if len(np.unique(edges)) < len(edges):
            edges = np.linspace(lo - 1e-9, hi + 1e-9, n_bins + 1)

    b_counts, _ = np.histogram(b_arr, bins=edges)
    c_counts, _ = np.histogram(c_arr, bins=edges)

    b_probs = (b_counts.astype(float) + eps) / (b_arr.size + eps * n_bins)
    c_probs = (c_counts.astype(float) + eps) / (c_arr.size + eps * n_bins)
    psi = float(np.sum((c_probs - b_probs) * np.log(c_probs / b_probs)))
    return round(max(0.0, psi), 4)


def compute_categorical_jsd(
    baseline_labels: Sequence[str],
    current_labels: Sequence[str],
    *,
    eps: float = 1e-4,
) -> float:
    """Compute bounded Jensen-Shannon divergence in [0, 1] (base-2) between categorical windows."""
    if not baseline_labels or not current_labels:
        return 0.0
    categories = sorted(set(baseline_labels) | set(current_labels))
    k = len(categories)
    if k <= 1:
        return 0.0
    b_map = {c: 0 for c in categories}
    c_map = {c: 0 for c in categories}
    for x in baseline_labels:
        b_map[x] += 1
    for x in current_labels:
        c_map[x] += 1
    b_vec = np.asarray([(b_map[c] + eps) / (len(baseline_labels) + eps * k) for c in categories], dtype=float)
    c_vec = np.asarray([(c_map[c] + eps) / (len(current_labels) + eps * k) for c in categories], dtype=float)
    js_dist = float(jensenshannon(b_vec, c_vec, base=2.0))
    if not math.isfinite(js_dist):
        return 0.0
    return round(min(1.0, max(0.0, js_dist * js_dist)), 4)


@dataclass
class DriftMonitor:
    """Observational sliding-window drift monitor across F1-F6, G2 trust, G3 verdicts, and retrieval quality.

    This monitor never alters security thresholds or decisions silently; it emits DriftReports
    with explicit severity, confidence, and attack-vs-benign separation.
    """

    window_size: int = 50
    min_samples: int = 15
    psi_threshold: float = 0.25
    ks_alpha: float = 0.05
    ks_min_stat: float = 0.28
    jsd_threshold: float = 0.15
    baseline_records: list[TelemetryRecord] = field(default_factory=list)
    current_window: deque[TelemetryRecord] = field(default_factory=deque)
    reports: list[DriftReport] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.current_window = deque(self.current_window, maxlen=self.window_size)

    def set_baseline(self, records: Sequence[TelemetryRecord]) -> None:
        """Freeze reference baseline telemetry distribution from validated non-test records."""
        self.baseline_records = list(records)

    def record_batch(self, records: Sequence[TelemetryRecord]) -> None:
        """Append new runtime telemetry rows into bounded sliding window."""
        for rec in records:
            self.current_window.append(rec)

    def _eval_continuous(
        self,
        stream_name: str,
        base_vals: Sequence[float],
        curr_vals: Sequence[float],
        *,
        bounded_unit: bool = True,
    ) -> SignalDriftResult:
        nb, nc = len(base_vals), len(curr_vals)
        if nb < self.min_samples or nc < self.min_samples:
            return SignalDriftResult(
                stream_name=stream_name,
                stream_type="continuous",
                baseline_n=nb,
                current_n=nc,
                insufficient_sample=True,
                drifted=False,
            )
        psi = compute_psi(base_vals, curr_vals, n_bins=5, bounded_unit=bounded_unit)
        ks_res = ks_2samp(base_vals, curr_vals)
        ks_stat = round(float(ks_res.statistic), 4)
        ks_p = round(float(ks_res.pvalue), 6)
        drifted = (psi >= self.psi_threshold) or (ks_stat >= self.ks_min_stat and ks_p < self.ks_alpha)
        return SignalDriftResult(
            stream_name=stream_name,
            stream_type="continuous",
            baseline_n=nb,
            current_n=nc,
            psi=psi,
            ks_statistic=ks_stat,
            ks_p_value=ks_p,
            insufficient_sample=False,
            drifted=bool(drifted),
        )

    def _eval_categorical(
        self,
        stream_name: str,
        base_vals: Sequence[str],
        curr_vals: Sequence[str],
    ) -> SignalDriftResult:
        nb, nc = len(base_vals), len(curr_vals)
        if nb < self.min_samples or nc < self.min_samples:
            return SignalDriftResult(
                stream_name=stream_name,
                stream_type="categorical",
                baseline_n=nb,
                current_n=nc,
                insufficient_sample=True,
                drifted=False,
            )
        jsd = compute_categorical_jsd(base_vals, curr_vals)
        return SignalDriftResult(
            stream_name=stream_name,
            stream_type="categorical",
            baseline_n=nb,
            current_n=nc,
            js_divergence=jsd,
            insufficient_sample=False,
            drifted=bool(jsd >= self.jsd_threshold),
        )

    def evaluate_window(self, window_id: str = "window-0") -> DriftReport:
        """Compare current telemetry window against frozen baseline without mutating state."""
        curr = list(self.current_window)
        base = self.baseline_records

        if len(base) < self.min_samples or len(curr) < self.min_samples:
            rep = DriftReport(
                window_id=window_id,
                overall_severity="insufficient_sample",
                classification="insufficient_sample",
                confidence=round(min(len(base), len(curr)) / max(1, self.min_samples), 4),
                signal_results={},
                summary_metrics={"baseline_n": float(len(base)), "current_n": float(len(curr))},
                recommended_action="none",
            )
            self.reports.append(rep)
            return rep

        def _extract_num(rows: Sequence[TelemetryRecord], attr: str) -> list[float]:
            out = []
            for r in rows:
                v = getattr(r, attr)
                if v is not None and math.isfinite(float(v)):
                    out.append(float(v))
            return out

        results: dict[str, SignalDriftResult] = {
            "F1_perplexity": self._eval_continuous("F1_perplexity", _extract_num(base, "f1_perplexity"), _extract_num(curr, "f1_perplexity")),
            "F2_embedding_norm": self._eval_continuous("F2_embedding_norm", _extract_num(base, "f2_embedding_norm"), _extract_num(curr, "f2_embedding_norm")),
            "F3_query_match": self._eval_continuous("F3_query_match", _extract_num(base, "f3_query_match"), _extract_num(curr, "f3_query_match")),
            "F4_instruction_risk": self._eval_continuous("F4_instruction_risk", _extract_num(base, "f4_instruction_risk"), _extract_num(curr, "f4_instruction_risk")),
            "F5_consensus_dev": self._eval_continuous("F5_consensus_dev", _extract_num(base, "f5_consensus_dev"), _extract_num(curr, "f5_consensus_dev")),
            "F6_provenance": self._eval_categorical("F6_provenance", [r.f6_provenance_state for r in base], [r.f6_provenance_state for r in curr]),
            "G2_trust_score": self._eval_continuous("G2_trust_score", _extract_num(base, "g2_trust_score"), _extract_num(curr, "g2_trust_score")),
            "G3_verdict": self._eval_categorical("G3_verdict", [r.g3_verdict for r in base if r.g3_verdict], [r.g3_verdict for r in curr if r.g3_verdict]),
            "retrieval_quality": self._eval_continuous("retrieval_quality", _extract_num(base, "retrieval_quality"), _extract_num(curr, "retrieval_quality")),
        }

        # Directional attack vs benign indicators (prevents flagging benign domain shifts as attacks)
        b_inst = _extract_num(base, "f4_instruction_risk")
        c_inst = _extract_num(curr, "f4_instruction_risk")
        inst_high_base = sum(1 for v in b_inst if v >= 0.30) / max(1, len(b_inst))
        inst_high_curr = sum(1 for v in c_inst if v >= 0.30) / max(1, len(c_inst))
        delta_inst_rate = inst_high_curr - inst_high_base

        b_trust = _extract_num(base, "g2_trust_score")
        c_trust = _extract_num(curr, "g2_trust_score")
        delta_trust_mean = (sum(c_trust) / max(1, len(c_trust))) - (sum(b_trust) / max(1, len(b_trust)))

        b_f5 = _extract_num(base, "f5_consensus_dev")
        c_f5 = _extract_num(curr, "f5_consensus_dev")
        delta_f5_mean = (sum(c_f5) / max(1, len(c_f5))) - (sum(b_f5) / max(1, len(b_f5)))

        b_rq = _extract_num(base, "retrieval_quality")
        c_rq = _extract_num(curr, "retrieval_quality")
        delta_rq = (sum(c_rq) / max(1, len(c_rq))) - (sum(b_rq) / max(1, len(b_rq)))

        g3_curr = [r.g3_verdict for r in curr if r.g3_verdict]
        g3_bad_rate_curr = (
            sum(1 for v in g3_curr if v in {"CONTRADICTED", "INSUFFICIENT_EVIDENCE"}) / max(1, len(g3_curr))
            if g3_curr
            else 0.0
        )

        drifted_streams = [k for k, v in results.items() if v.drifted]
        n_active = sum(1 for v in results.values() if not v.insufficient_sample)
        n_drifted = len(drifted_streams)

        # Attack drift requires security risk indicators rising:
        # (a) F4 instruction risk surge, OR (b) G2 trust drop + F5 collapse, OR (c) severe F5 consensus collapse
        attack_signal_f4 = delta_inst_rate >= 0.10 or (results["F4_instruction_risk"].drifted and delta_inst_rate > 0.03)
        attack_signal_trust_consensus = (
            results["G2_trust_score"].drifted and delta_trust_mean <= -0.08 and delta_f5_mean <= -0.10
        )
        attack_signal_f5_collapse = (
            results["F5_consensus_dev"].drifted
            and (results["F5_consensus_dev"].ks_p_value or 1.0) < self.ks_alpha
            and delta_f5_mean <= -0.18
        )
        quality_signal = (
            (results["G3_verdict"].drifted and g3_bad_rate_curr >= 0.40)
            or (results["retrieval_quality"].drifted and delta_rq <= -0.10)
        )

        if attack_signal_f4 or attack_signal_trust_consensus or attack_signal_f5_collapse:
            classification = "suspected_attack_drift"
            severity = "high" if (attack_signal_f4 and (results["G2_trust_score"].drifted or attack_signal_f5_collapse)) else "moderate"
            action = "tighten_thresholds" if severity == "high" else "propose_review"
            conf = min(0.99, round(0.65 + 0.10 * min(3, n_drifted), 4))
        elif quality_signal:
            classification = "quality_degradation"
            severity = "moderate"
            action = "propose_review"
            conf = min(0.95, round(0.60 + 0.08 * min(3, n_drifted), 4))
        elif n_drifted > 0:
            classification = "benign_distribution_drift"
            severity = "low" if n_drifted <= 2 else "moderate"
            action = "log_only"
            conf = min(0.90, round(0.55 + 0.08 * min(3, n_drifted), 4))
        else:
            classification = "stable"
            severity = "none"
            action = "none"
            conf = min(0.95, round(len(curr) / max(len(curr), self.window_size), 4))

        rep = DriftReport(
            window_id=window_id,
            overall_severity=severity,  # type: ignore[arg-type]
            classification=classification,  # type: ignore[arg-type]
            confidence=conf,
            signal_results=results,
            summary_metrics={
                "baseline_n": float(len(base)),
                "current_n": float(len(curr)),
                "active_streams": float(n_active),
                "drifted_streams": float(n_drifted),
                "delta_inst_high_rate": round(delta_inst_rate, 4),
                "delta_trust_mean": round(delta_trust_mean, 4),
                "delta_f5_mean": round(delta_f5_mean, 4),
                "delta_retrieval_quality": round(delta_rq, 4),
            },
            recommended_action=action,  # type: ignore[arg-type]
        )
        self.reports.append(rep)
        LOGGER.info(
            "Drift window evaluated",
            extra={
                "window_id": window_id,
                "classification": classification,
                "severity": severity,
                "drifted_streams": drifted_streams,
            },
        )
        return rep


__all__ = [
    "DriftMonitor",
    "TelemetryRecord",
    "compute_categorical_jsd",
    "compute_psi",
]
