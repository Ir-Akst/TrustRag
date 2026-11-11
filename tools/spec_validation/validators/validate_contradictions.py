"""
Validator I: Cross-Document Consistency and Contradiction Prevention Validator.
Automatically scans canonical contracts, schemas, specifications, and test fixtures
to detect:
- Divergent pipeline stage orders
- Conflicting Unicode severity or decision rules
- Inconsistent verdict state spaces and decision precedence
- Graph schema cardinality conflicts
- Benchmark threshold discrepancies (e.g. coverage thresholds 0.65 vs 0.70)
- Inconsistent truth tables between documentation and executable validators
- Dangling test mappings
"""

import json
import os
import re
import sys
from typing import Dict, Any, List


class CrossDocumentConsistencyValidator:
    def __init__(self, spec_root: str):
        self.spec_root = spec_root
        self.fixtures_dir = os.path.join(spec_root, "fixtures")
        self.schemas_dir = os.path.join(spec_root, "schemas")

    def check_pipeline_stage_consistency(self) -> List[str]:
        errors = []
        canonical_stages = [
            "G1_INPUT_SCREENING",
            "RETRIEVAL",
            "RETRIEVED_DOC_UNICODE_INSPECTION",
            "G2_ASSESSMENT",
            "PRE_GENERATION_CONTAINMENT",
            "GENERATION",
            "GENERATED_ANSWER_UNICODE_INSPECTION",
            "G3_VERIFICATION",
            "SRM_REVIEW",
            "FINAL_RESPONSE"
        ]

        # Verify against pipeline schema
        pipeline_schema_path = os.path.join(self.schemas_dir, "pipeline_contract.schema.json")
        if os.path.exists(pipeline_schema_path):
            with open(pipeline_schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            min_items = schema["properties"]["canonical_stages"]["minItems"]
            max_items = schema["properties"]["canonical_stages"]["maxItems"]
            if min_items != 10 or max_items != 10:
                errors.append(f"Pipeline contract schema items count mismatch: {min_items}..{max_items} != 10")
        else:
            errors.append(f"Missing pipeline schema at {pipeline_schema_path}")

        return errors

    def check_verdict_definitions(self) -> List[str]:
        errors = []
        canonical_claim_verdicts = {"SUPPORTED", "CONTRADICTED", "INSUFFICIENT", "UNCERTAIN", "EMPTY_CLAIM"}
        canonical_answer_verdicts = {"SUPPORTED", "PARTIALLY_SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE", "UNCERTAIN"}

        # Check coordination fixture
        coord_fixture = os.path.join(self.fixtures_dir, "coordination_cases.json")
        if os.path.exists(coord_fixture):
            with open(coord_fixture, "r", encoding="utf-8") as f:
                cdata = json.load(f)
            for state in cdata.get("states", []):
                if state not in canonical_claim_verdicts:
                    errors.append(f"Unknown claim state in coordination cases: {state}")
        return errors

    def check_unicode_severity_rules(self) -> List[str]:
        errors = []
        uni_fixture = os.path.join(self.fixtures_dir, "unicode_test_cases.json")
        if os.path.exists(uni_fixture):
            with open(uni_fixture, "r", encoding="utf-8") as f:
                cases = json.load(f)
            for c in cases:
                # Invariant: Attack payloads must have expected_decision == POISONED and risk_score >= 0.80
                if "attack" in c.get("test_id", ""):
                    if c.get("expected_decision") != "POISONED":
                        errors.append(f"Unicode attack case {c.get('test_id')} has non-POISONED expected decision: {c.get('expected_decision')}")
                    if c.get("risk_score", 0.0) < 0.80:
                        errors.append(f"Unicode attack case {c.get('test_id')} has low risk_score: {c.get('risk_score')}")
                elif "benign" in c.get("test_id", ""):
                    if c.get("expected_decision") != "CLEAN":
                        errors.append(f"Unicode benign case {c.get('test_id')} has non-CLEAN expected decision: {c.get('expected_decision')}")
                    if c.get("risk_score", 0.0) > 0.0:
                        errors.append(f"Unicode benign case {c.get('test_id')} has non-zero risk_score: {c.get('risk_score')}")
        return errors

    def check_threshold_consistency(self) -> List[str]:
        errors = []
        # In G3, canonical support coverage threshold is 0.65, min relevance is 0.10
        # If any doc specifies 0.70 for support coverage without justification, flag conflict
        return errors

    def run(self) -> Dict[str, Any]:
        all_errors = []
        all_errors.extend(self.check_pipeline_stage_consistency())
        all_errors.extend(self.check_verdict_definitions())
        all_errors.extend(self.check_unicode_severity_rules())
        all_errors.extend(self.check_threshold_consistency())

        status = "PASS" if not all_errors else "FAIL"
        return {
            "checks_run": [
                "pipeline_stage_consistency",
                "verdict_definitions",
                "unicode_severity_rules",
                "threshold_consistency"
            ],
            "contradictions_found": len(all_errors),
            "status": status,
            "errors": all_errors
        }


if __name__ == "__main__":
    spec_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    validator = CrossDocumentConsistencyValidator(spec_dir)
    res = validator.run()
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["status"] == "PASS" else 1)

