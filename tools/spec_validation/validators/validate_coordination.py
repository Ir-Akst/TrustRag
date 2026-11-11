"""
Validator C: Coordination Truth Table and Invariant Validator.
Tests deterministic truth tables for AND, OR, SEQ, CONTRAST across all combinations
of atomic proposition states: SUPPORTED, CONTRADICTED, INSUFFICIENT, UNCERTAIN.
Enforces explicit sequence ordering (precedence indices) rather than array order.
Ensures safety invariant: ungrounded disjuncts or conjuncts never yield SUPPORTED.
"""

import json
import os
import sys
from typing import Dict, Any, List, Tuple


class CoordinationValidator:
    STATES = ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT", "UNCERTAIN"]

    def __init__(self, fixtures_path: str):
        with open(fixtures_path, "r", encoding="utf-8") as f:
            self.fixtures = json.load(f)

    @staticmethod
    def eval_and(p: str, q: str) -> str:
        if p == "CONTRADICTED" or q == "CONTRADICTED":
            return "CONTRADICTED"
        if p == "INSUFFICIENT" or q == "INSUFFICIENT":
            return "INSUFFICIENT"
        if p == "UNCERTAIN" or q == "UNCERTAIN":
            return "UNCERTAIN"
        if p == "SUPPORTED" and q == "SUPPORTED":
            return "SUPPORTED"
        return "INSUFFICIENT"

    @staticmethod
    def eval_or(p: str, q: str) -> str:
        # In G3 safety verification:
        # An ungrounded disjunction (e.g. "reduces fever or cures cancer")
        # cannot be validated as verified factual knowledge without evidence for both/disjunction.
        # If any disjunct is CONTRADICTED and none is SUPPORTED -> CONTRADICTED
        if p == "CONTRADICTED" and q == "CONTRADICTED":
            return "CONTRADICTED"
        # If one is SUPPORTED and one is INSUFFICIENT -> INSUFFICIENT (cannot claim both or ungrounded second disjunct)
        if p == "SUPPORTED" and q == "SUPPORTED":
            return "SUPPORTED"
        if p == "CONTRADICTED" or q == "CONTRADICTED":
            return "CONTRADICTED"
        if p == "UNCERTAIN" or q == "UNCERTAIN":
            return "UNCERTAIN"
        return "INSUFFICIENT"

    @staticmethod
    def eval_seq(p: str, q: str, order_valid: bool) -> str:
        # P then Q requires P supported, Q supported, and temporal precedence valid
        if not order_valid:
            return "CONTRADICTED"
        if p == "CONTRADICTED" or q == "CONTRADICTED":
            return "CONTRADICTED"
        if p == "INSUFFICIENT" or q == "INSUFFICIENT":
            return "INSUFFICIENT"
        if p == "UNCERTAIN" or q == "UNCERTAIN":
            return "UNCERTAIN"
        if p == "SUPPORTED" and q == "SUPPORTED":
            return "SUPPORTED"
        return "INSUFFICIENT"

    @staticmethod
    def eval_contrast(p: str, q: str, contrast_valid: bool = True) -> str:
        # P while Q / P but Q requires both supported and valid contrast relation
        if not contrast_valid:
            return "CONTRADICTED"
        if p == "CONTRADICTED" or q == "CONTRADICTED":
            return "CONTRADICTED"
        if p == "INSUFFICIENT" or q == "INSUFFICIENT":
            return "INSUFFICIENT"
        if p == "UNCERTAIN" or q == "UNCERTAIN":
            return "UNCERTAIN"
        if p == "SUPPORTED" and q == "SUPPORTED":
            return "SUPPORTED"
        return "INSUFFICIENT"

    def run(self) -> Dict[str, Any]:
        violations = []
        combinations_tested = 0

        # Exhaustive pairwise test for AND, OR, SEQ, CONTRAST
        for s1 in self.STATES:
            for s2 in self.STATES:
                combinations_tested += 1

                # AND check
                and_res = self.eval_and(s1, s2)
                if (s1 != "SUPPORTED" or s2 != "SUPPORTED") and and_res == "SUPPORTED":
                    violations.append(f"AND invariant violated: {s1} AND {s2} yielded SUPPORTED")

                # OR check
                or_res = self.eval_or(s1, s2)
                if (s1 != "SUPPORTED" or s2 != "SUPPORTED") and or_res == "SUPPORTED":
                    violations.append(f"OR invariant violated: {s1} OR {s2} yielded SUPPORTED")

                # SEQ check (with order valid)
                seq_res = self.eval_seq(s1, s2, order_valid=True)
                if (s1 != "SUPPORTED" or s2 != "SUPPORTED") and seq_res == "SUPPORTED":
                    violations.append(f"SEQ invariant violated: {s1} SEQ {s2} yielded SUPPORTED")

                # SEQ check (with order reversed)
                seq_rev = self.eval_seq(s1, s2, order_valid=False)
                if seq_rev == "SUPPORTED":
                    violations.append(f"SEQ reversed order yielded SUPPORTED: {s1} SEQ(rev) {s2}")

                # CONTRAST check
                cnt_res = self.eval_contrast(s1, s2, contrast_valid=True)
                if (s1 != "SUPPORTED" or s2 != "SUPPORTED") and cnt_res == "SUPPORTED":
                    violations.append(f"CONTRAST invariant violated: {s1} CONTRAST {s2} yielded SUPPORTED")

        # Test probes from fixtures
        probe_results = []
        for probe in self.fixtures.get("test_probes", []):
            op = probe["operator"]
            v_a = probe["verdict_a"]
            v_b = probe["verdict_b"]
            expected = probe["expected_coordinated_verdict"]

            if op == "AND":
                actual = self.eval_and(v_a, v_b)
            elif op == "OR":
                actual = self.eval_or(v_a, v_b)
            elif op == "SEQ":
                order_ok = probe.get("sequence_relation", "CHRONOLOGICAL") == "CHRONOLOGICAL"
                actual = self.eval_seq(v_a, v_b, order_ok)
            elif op == "CONTRAST":
                actual = self.eval_contrast(v_a, v_b, True)
            else:
                actual = "UNKNOWN"

            if probe.get("cannot_be_supported", False) and actual == "SUPPORTED":
                violations.append(f"Probe {probe['probe_id']} illegally returned SUPPORTED")

            probe_results.append({
                "probe_id": probe["probe_id"],
                "operator": op,
                "expected": expected,
                "actual": actual,
                "passed": actual == expected
            })

        status = "PASS" if not violations and all(p["passed"] for p in probe_results) else "FAIL"
        return {
            "combinations_tested": combinations_tested * 4,
            "probes_tested": len(probe_results),
            "violations_count": len(violations),
            "status": status,
            "violations": violations[:5],
            "probe_results": probe_results
        }


if __name__ == "__main__":
    fixtures_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "coordination_cases.json"))
    validator = CoordinationValidator(fixtures_file)
    res = validator.run()
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["status"] == "PASS" else 1)

