"""Measured runtime monitoring tracker & static benchmark reference loader."""

from __future__ import annotations

import json
import threading
import time
from collections import Counter, deque
from pathlib import Path
from typing import Any

from trustrag.api.schemas import MonitoringMetricsResponse


class MonitoringTracker:
    """Tracks actual observed latencies, errors, and G1/G2/G3 decisions without fabrication."""

    MIN_PERCENTILE_SAMPLES = 5

    def __init__(
        self,
        *,
        benchmark_report_path: str | Path = "reports/phase08_comprehensive_benchmark.json",
        max_latency_samples: int = 1000,
    ) -> None:
        self._lock = threading.RLock()
        self._start_time = time.monotonic()
        self._latencies_ms: deque[float] = deque(maxlen=max_latency_samples)
        self._total_requests = 0
        self._error_requests = 0
        self._timeout_requests = 0
        self._blocked_requests = 0
        self._abstained_requests = 0
        self._g1_decisions: Counter[str] = Counter()
        self._g2_decisions: Counter[str] = Counter()
        self._g3_verdicts: Counter[str] = Counter()
        self._benchmark_path = Path(benchmark_report_path)

    def record_pipeline_outcome(
        self,
        *,
        latency_ms: float,
        status: str,
        g1_decision: str | None = None,
        g3_verdict: str | None = None,
        blocked: bool = False,
        abstained: bool = False,
        is_timeout: bool = False,
    ) -> None:
        with self._lock:
            self._total_requests += 1
            self._latencies_ms.append(max(0.0, float(latency_ms)))
            if status == "ERROR":
                self._error_requests += 1
            if is_timeout:
                self._timeout_requests += 1
            if blocked:
                self._blocked_requests += 1
            if abstained:
                self._abstained_requests += 1
            if g1_decision:
                self._g1_decisions[g1_decision] += 1
            if g3_verdict:
                self._g3_verdicts[g3_verdict] += 1

    def record_g1_decision(self, decision: str, *, latency_ms: float) -> None:
        with self._lock:
            self._total_requests += 1
            self._latencies_ms.append(max(0.0, float(latency_ms)))
            self._g1_decisions[decision] += 1
            if decision == "BLOCK":
                self._blocked_requests += 1

    def record_g2_assessments(self, decisions: list[str], *, latency_ms: float) -> None:
        with self._lock:
            self._total_requests += 1
            self._latencies_ms.append(max(0.0, float(latency_ms)))
            for dec in decisions:
                self._g2_decisions[dec] += 1

    def record_g3_verdict(self, verdict: str, *, abstained: bool, latency_ms: float) -> None:
        with self._lock:
            self._total_requests += 1
            self._latencies_ms.append(max(0.0, float(latency_ms)))
            self._g3_verdicts[verdict] += 1
            if abstained:
                self._abstained_requests += 1

    @staticmethod
    def _percentile(sorted_vals: list[float], pct: float) -> float:
        if not sorted_vals:
            return 0.0
        idx = min(len(sorted_vals) - 1, max(0, round((pct / 100.0) * (len(sorted_vals) - 1))))
        return round(sorted_vals[idx], 4)

    def _load_historical_benchmark(self) -> tuple[bool, dict[str, Any]]:
        if not self._benchmark_path.is_file():
            return False, {}
        try:
            raw = json.loads(self._benchmark_path.read_text(encoding="utf-8"))
            return True, {
                "metadata": raw.get("metadata", {}),
                "security_pipeline": raw.get("security_pipeline", {}),
                "clean_utility_boolq_test_n15_in_100": raw.get(
                    "clean_utility_boolq_test_n15_in_100", {}
                ),
                "msd_document_level": raw.get("msd_document_level", {}),
                "g3_generalization_13_probes": raw.get("g3_generalization_13_probes", {}),
                "external_research_benchmarks": {
                    "status_counts": raw.get("external_research_benchmarks", {}).get(
                        "status_counts", {}
                    )
                },
                "serving_reliability": raw.get("serving_reliability", {}),
            }
        except Exception:
            return False, {}

    def snapshot(self) -> MonitoringMetricsResponse:
        with self._lock:
            uptime = max(0.001, time.monotonic() - self._start_time)
            lats = sorted(self._latencies_ms)
            sample_count = len(lats)
            pct_ready = sample_count >= self.MIN_PERCENTILE_SAMPLES
            p50 = self._percentile(lats, 50.0) if pct_ready else None
            p95 = self._percentile(lats, 95.0) if pct_ready else None
            p99 = self._percentile(lats, 99.0) if pct_ready else None
            err_rate = (
                round(self._error_requests / self._total_requests, 4)
                if self._total_requests > 0
                else 0.0
            )
            qps = round(self._total_requests / uptime, 4)
            hist_ok, hist_data = self._load_historical_benchmark()
            return MonitoringMetricsResponse(
                uptime_seconds=round(uptime, 3),
                total_requests=self._total_requests,
                error_requests=self._error_requests,
                error_rate=err_rate,
                blocked_requests=self._blocked_requests,
                abstained_requests=self._abstained_requests,
                timeout_requests=self._timeout_requests,
                throughput_qps=qps,
                latency_sample_count=sample_count,
                min_percentile_samples=self.MIN_PERCENTILE_SAMPLES,
                percentiles_available=pct_ready,
                latency_p50_ms=p50,
                latency_p95_ms=p95,
                latency_p99_ms=p99,
                g1_decisions=dict(self._g1_decisions),
                g2_decisions=dict(self._g2_decisions),
                g3_verdicts=dict(self._g3_verdicts),
                historical_benchmark_available=hist_ok,
                historical_benchmark=hist_data,
            )
