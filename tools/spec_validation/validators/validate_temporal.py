"""
Validator F: Temporal Interval, Boundary, and Reference-Time Validator.
Enforces the safety invariant: Finite evidence must never fully support
an unrestricted open-ended claim.
Tests:
- Closed intervals matching exactly
- Historical evidence vs open-ended current/future claims
- Non-overlapping intervals
- Partial overlap intervals
- Subset intervals (claim subset of evidence)
- Missing reference times for relative expressions ("currently", "yesterday")
- Conflicting timestamps across evidence sources
"""

import datetime
import json
import os
import sys
from typing import Dict, Any, List, Optional, Tuple


class TemporalValidator:
    def __init__(self, fixtures_path: str):
        with open(fixtures_path, "r", encoding="utf-8") as f:
            self.test_cases = json.load(f)

    @staticmethod
    def parse_iso_date(dt_str: Optional[str]) -> Optional[datetime.date]:
        if not dt_str:
            return None
        # Accept YYYY-MM-DD or full ISO
        clean_str = dt_str[:10]
        return datetime.date.fromisoformat(clean_str)

    @classmethod
    def evaluate_temporal_alignment(cls, test_case: Dict[str, Any]) -> str:
        # Check conflicting timestamps
        if test_case.get("conflicting_sources", False):
            return "UNCERTAIN"

        claim_int = test_case.get("claim_interval", {})
        ev_int = test_case.get("evidence_interval", {})

        # Check missing reference time for relative terms
        if claim_int.get("relative_term") and not claim_int.get("reference_time"):
            return "UNCERTAIN"

        ev_start = cls.parse_iso_date(ev_int.get("start"))
        ev_end = cls.parse_iso_date(ev_int.get("end"))
        ev_open = ev_int.get("is_open_ended", False)

        cl_start = cls.parse_iso_date(claim_int.get("start"))
        cl_end = cls.parse_iso_date(claim_int.get("end"))
        cl_open = claim_int.get("is_open_ended", False)

        # Invariant: Finite evidence (ev_open is False and ev_end is set)
        # CANNOT support open-ended claim (cl_open is True or cl_end is None)
        if not ev_open and ev_end is not None and cl_open:
            return "INSUFFICIENT_EVIDENCE"

        if ev_start is None or cl_start is None:
            return "UNCERTAIN"

        # Disjoint intervals
        if ev_end and cl_start > ev_end:
            return "INSUFFICIENT_EVIDENCE"
        if cl_end and cl_end < ev_start:
            return "INSUFFICIENT_EVIDENCE"

        # Claim must be fully contained within evidence interval
        # ev_start <= cl_start and (ev_end >= cl_end or ev_open)
        if cl_start >= ev_start:
            if cl_end and ev_end and cl_end <= ev_end:
                return "SUPPORTED"
            elif ev_open and cl_end:
                return "SUPPORTED"
            else:
                return "INSUFFICIENT_EVIDENCE"
        else:
            return "INSUFFICIENT_EVIDENCE"

    def run(self) -> Dict[str, Any]:
        violations = []
        results = []

        for tc in self.test_cases:
            tid = tc["test_id"]
            expected = tc["expected_verdict"]
            actual = self.evaluate_temporal_alignment(tc)

            passed = (actual == expected)
            if not passed:
                violations.append({
                    "test_id": tid,
                    "expected": expected,
                    "actual": actual,
                    "description": tc.get("description")
                })

            results.append({
                "test_id": tid,
                "expected": expected,
                "actual": actual,
                "passed": passed
            })

        status = "PASS" if not violations else "FAIL"
        return {
            "total_tested": len(self.test_cases),
            "passed_count": sum(1 for r in results if r["passed"]),
            "violations_count": len(violations),
            "status": status,
            "violations": violations,
            "results": results
        }


if __name__ == "__main__":
    fixtures_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "temporal_cases.json"))
    validator = TemporalValidator(fixtures_file)
    res = validator.run()
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["status"] == "PASS" else 1)

