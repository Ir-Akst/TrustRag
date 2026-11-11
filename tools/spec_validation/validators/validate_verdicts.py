"""
Validator B: Exhaustive Verdict State and Decision Precedence Validator.
Tests all combinations of:
- Structural alignment / contradiction
- NLI entailment / contradiction / neutral
- Extraction confidence (high / low / failed)
- Source conflict (none / conflicting)
- Temporal alignment (matching / mismatch)
- Evidence availability (present / missing)
- Proposition counts (single / multiple)
Asserts the strict invariant: An empty claim, failed extraction, ambiguous claim,
or unsupported proposition must NEVER become SUPPORTED.
"""

import itertools
import json
import os
import sys
from typing import Dict, Any, List, Optional


class VerdictValidator:
    CLAIM_VERDICTS = ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT", "UNCERTAIN", "EMPTY_CLAIM"]
    ANSWER_VERDICTS = ["SUPPORTED", "PARTIALLY_SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE", "UNCERTAIN"]

    @staticmethod
    def evaluate_single_proposition(
        claim_type: str,            # "NORMAL", "EMPTY", "EXTRACTION_FAILED"
        evidence_present: bool,
        source_conflict: bool,
        extraction_conf: float,     # 0.0 to 1.0 (threshold 0.6)
        structural_status: str,     # "ALIGNED", "CONTRADICTED", "PARTIAL", "NONE"
        temporal_match: bool,
        nli_verdict: str            # "ENTAILMENT", "CONTRADICTION", "NEUTRAL"
    ) -> str:
        # Precedence Rule 1: Empty or failed extraction
        if claim_type in ("EMPTY", "EXTRACTION_FAILED"):
            return "EMPTY_CLAIM"

        # Precedence Rule 2: Missing evidence
        if not evidence_present:
            return "INSUFFICIENT"

        # Precedence Rule 3: Conflicting authoritative sources
        if source_conflict:
            return "UNCERTAIN"

        # Precedence Rule 4: Low extraction confidence
        if extraction_conf < 0.60:
            return "UNCERTAIN"

        # Precedence Rule 5: Structural contradiction
        if structural_status == "CONTRADICTED":
            return "CONTRADICTED"

        # Precedence Rule 6: Temporal mismatch
        if not temporal_match:
            return "INSUFFICIENT"

        # Precedence Rule 7: NLI Contradiction
        if nli_verdict == "CONTRADICTION":
            return "CONTRADICTED"

        # Precedence Rule 8: NLI Neutral or lack of alignment
        if structural_status != "ALIGNED" or nli_verdict != "ENTAILMENT":
            return "INSUFFICIENT"

        # Precedence Rule 9: Full alignment + NLI entailment
        return "SUPPORTED"

    @staticmethod
    def aggregate_answer_verdict(prop_verdicts: List[str]) -> str:
        if not prop_verdicts:
            return "INSUFFICIENT_EVIDENCE"

        if all(v == "EMPTY_CLAIM" for v in prop_verdicts):
            return "INSUFFICIENT_EVIDENCE"

        filtered = [v for v in prop_verdicts if v != "EMPTY_CLAIM"]
        if not filtered:
            return "INSUFFICIENT_EVIDENCE"

        # If any proposition is contradicted -> Answer is CONTRADICTED
        if any(v == "CONTRADICTED" for v in filtered):
            return "CONTRADICTED"

        # If all are supported -> Answer is SUPPORTED
        if all(v == "SUPPORTED" for v in filtered):
            return "SUPPORTED"

        # If some supported and some insufficient/uncertain -> PARTIALLY_SUPPORTED
        if any(v == "SUPPORTED" for v in filtered):
            return "PARTIALLY_SUPPORTED"

        # If any is uncertain -> UNCERTAIN
        if any(v == "UNCERTAIN" for v in filtered):
            return "UNCERTAIN"

        # Default fallback
        return "INSUFFICIENT_EVIDENCE"

    def run_exhaustive_tests(self) -> Dict[str, Any]:
        dimensions = {
            "claim_type": ["NORMAL", "EMPTY", "EXTRACTION_FAILED"],
            "evidence_present": [True, False],
            "source_conflict": [True, False],
            "extraction_conf": [0.3, 0.8],  # low, high
            "structural_status": ["ALIGNED", "CONTRADICTED", "PARTIAL", "NONE"],
            "temporal_match": [True, False],
            "nli_verdict": ["ENTAILMENT", "CONTRADICTION", "NEUTRAL"]
        }

        keys = list(dimensions.keys())
        values = list(dimensions.values())
        combinations = list(itertools.product(*values))

        total_tested = len(combinations)
        violations = []

        verdict_distribution: Dict[str, int] = {}

        for combo in combinations:
            params = dict(zip(keys, combo))
            verdict = self.evaluate_single_proposition(
                claim_type=params["claim_type"],
                evidence_present=params["evidence_present"],
                source_conflict=params["source_conflict"],
                extraction_conf=params["extraction_conf"],
                structural_status=params["structural_status"],
                temporal_match=params["temporal_match"],
                nli_verdict=params["nli_verdict"]
            )
            verdict_distribution[verdict] = verdict_distribution.get(verdict, 0) + 1

            # INVARIANT CHECKS:
            # 1. An empty claim or extraction failure must NEVER be SUPPORTED
            if params["claim_type"] in ("EMPTY", "EXTRACTION_FAILED") and verdict == "SUPPORTED":
                violations.append({"type": "EMPTY_CLAIM_SUPPORTED", "params": params})

            # 2. Missing evidence must NEVER be SUPPORTED
            if not params["evidence_present"] and verdict == "SUPPORTED":
                violations.append({"type": "MISSING_EVIDENCE_SUPPORTED", "params": params})

            # 3. Source conflict must NEVER be SUPPORTED
            if params["source_conflict"] and verdict == "SUPPORTED":
                violations.append({"type": "SOURCE_CONFLICT_SUPPORTED", "params": params})

            # 4. Low extraction confidence must NEVER be SUPPORTED
            if params["extraction_conf"] < 0.6 and verdict == "SUPPORTED":
                violations.append({"type": "LOW_CONFIDENCE_SUPPORTED", "params": params})

            # 5. Structural contradiction must NEVER be SUPPORTED
            if params["structural_status"] == "CONTRADICTED" and verdict == "SUPPORTED":
                violations.append({"type": "STRUCT_CONTRADICTED_SUPPORTED", "params": params})

            # 6. Temporal mismatch must NEVER be SUPPORTED
            if not params["temporal_match"] and verdict == "SUPPORTED":
                violations.append({"type": "TEMPORAL_MISMATCH_SUPPORTED", "params": params})

            # 7. NLI Contradiction or Neutral must NEVER be SUPPORTED
            if params["nli_verdict"] in ("CONTRADICTION", "NEUTRAL") and verdict == "SUPPORTED":
                violations.append({"type": "NON_ENTAILMENT_SUPPORTED", "params": params})

        # Answer-level multi-proposition tests
        answer_level_cases = [
            (["SUPPORTED", "SUPPORTED"], "SUPPORTED"),
            (["SUPPORTED", "INSUFFICIENT"], "PARTIALLY_SUPPORTED"),
            (["SUPPORTED", "CONTRADICTED"], "CONTRADICTED"),
            (["INSUFFICIENT", "INSUFFICIENT"], "INSUFFICIENT_EVIDENCE"),
            (["UNCERTAIN", "INSUFFICIENT"], "UNCERTAIN"),
            (["EMPTY_CLAIM", "EMPTY_CLAIM"], "INSUFFICIENT_EVIDENCE"),
            (["SUPPORTED", "EMPTY_CLAIM"], "SUPPORTED")
        ]
        answer_violations = []
        for prop_inputs, expected in answer_level_cases:
            res = self.aggregate_answer_verdict(prop_inputs)
            if res != expected:
                answer_violations.append({"inputs": prop_inputs, "expected": expected, "got": res})

        status = "PASS" if not violations and not answer_violations else "FAIL"
        return {
            "total_combinations_tested": total_tested,
            "violations_count": len(violations),
            "answer_level_cases_tested": len(answer_level_cases),
            "answer_level_violations_count": len(answer_violations),
            "verdict_distribution": verdict_distribution,
            "status": status,
            "violations": violations[:5],
            "answer_violations": answer_violations
        }


if __name__ == "__main__":
    validator = VerdictValidator()
    results = validator.run_exhaustive_tests()
    print(json.dumps(results, indent=2))
    sys.exit(0 if results["status"] == "PASS" else 1)

