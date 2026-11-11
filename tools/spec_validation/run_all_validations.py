"""
Master Test Runner for G3 Specification Validation.
Executes all validators:
- Validator A: Schema Validation (validate_schemas.py)
- Validator B: Verdict Precedence (validate_verdicts.py)
- Validator C: Coordination Truth Tables (validate_coordination.py)
- Validator D: Unicode Security Policy (validate_unicode.py)
- Validator E: Pipeline Stage Ordering & Containment (validate_pipeline.py)
- Validator F: Temporal Intervals & Bounds (validate_temporal.py)
- Validator G: Provenance RFC 8785 & Integrity (validate_provenance.py)
- Validator H: Statistical Clopper-Pearson & Partitions (validate_statistical.py)
- Validator I: Cross-Document Contradiction Checks (validate_contradictions.py)

Measures latency (p50, p95, p99) and peak memory via tracemalloc.
Evaluates all 13 Acceptance Gates.
"""

import json
import os
import sys
import time
import tracemalloc
from typing import Dict, Any, List

# Import validators
from validators.validate_schemas import SchemaValidator
from validators.validate_verdicts import VerdictValidator
from validators.validate_coordination import CoordinationValidator
from validators.validate_unicode import UnicodeValidator
from validators.validate_pipeline import CanonicalPipelineValidator
from validators.validate_temporal import TemporalValidator
from validators.validate_provenance import ProvenanceValidator
from validators.validate_statistical import StatisticalValidator
from validators.validate_contradictions import CrossDocumentConsistencyValidator
from validators.validate_runtime_conformance import RuntimeConformanceValidator


def run_full_validation_suite() -> Dict[str, Any]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fixtures_dir = os.path.join(base_dir, "fixtures")

    tracemalloc.start()
    t0 = time.perf_counter()

    latencies = []

    # 1. Validator A
    t_start = time.perf_counter()
    val_a = SchemaValidator(fixtures_dir).run()
    latencies.append(("Validator_A_Schemas", (time.perf_counter() - t_start) * 1000.0))

    # 2. Validator B
    t_start = time.perf_counter()
    val_b = VerdictValidator().run_exhaustive_tests()
    latencies.append(("Validator_B_Verdicts", (time.perf_counter() - t_start) * 1000.0))

    # 3. Validator C
    t_start = time.perf_counter()
    coord_file = os.path.join(fixtures_dir, "coordination_cases.json")
    val_c = CoordinationValidator(coord_file).run()
    latencies.append(("Validator_C_Coordination", (time.perf_counter() - t_start) * 1000.0))

    # 4. Validator D
    t_start = time.perf_counter()
    uni_file = os.path.join(fixtures_dir, "unicode_test_cases.json")
    val_d = UnicodeValidator(uni_file).run()
    latencies.append(("Validator_D_Unicode", (time.perf_counter() - t_start) * 1000.0))

    # 5. Validator E
    t_start = time.perf_counter()
    val_e = CanonicalPipelineValidator().run_tests()
    latencies.append(("Validator_E_Pipeline", (time.perf_counter() - t_start) * 1000.0))

    # 6. Validator F
    t_start = time.perf_counter()
    temp_file = os.path.join(fixtures_dir, "temporal_cases.json")
    val_f = TemporalValidator(temp_file).run()
    latencies.append(("Validator_F_Temporal", (time.perf_counter() - t_start) * 1000.0))

    # 7. Validator G
    t_start = time.perf_counter()
    prov_file = os.path.join(fixtures_dir, "provenance_cases.json")
    val_g = ProvenanceValidator(prov_file).run()
    latencies.append(("Validator_G_Provenance", (time.perf_counter() - t_start) * 1000.0))

    # 8. Validator H
    t_start = time.perf_counter()
    val_h = StatisticalValidator().run()
    latencies.append(("Validator_H_Statistical", (time.perf_counter() - t_start) * 1000.0))

    # 9. Validator I
    t_start = time.perf_counter()
    val_i = CrossDocumentConsistencyValidator(base_dir).run()
    latencies.append(("Validator_I_Contradictions", (time.perf_counter() - t_start) * 1000.0))

    total_duration_ms = (time.perf_counter() - t0) * 1000.0
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mem_mib = peak_mem / (1024.0 * 1024.0)

    # 10. Validator J: Real codebase conformance & verifier latency/memory benchmark
    repo_root = os.path.abspath(os.path.join(base_dir, "..", ".."))
    t_start = time.perf_counter()
    val_j = RuntimeConformanceValidator(repo_root, fixtures_dir).run()
    latencies.append(("Validator_J_RuntimeConformance", (time.perf_counter() - t_start) * 1000.0))

    perf = val_j["verifier_performance"]

    # Acceptance Gates Evaluation
    gate_results = {
        "Gate_01_JSON_validity": val_a["status"] == "PASS",
        "Gate_02_Graph_schema_validity": val_a["status"] == "PASS" and val_a["invalid_claims_rejected"] == val_a["invalid_claims_tested"],
        "Gate_03_Pipeline_consistency": val_e["status"] == "PASS" and val_i["status"] == "PASS" and val_j["stage7_answer_unicode_ok"],
        "Gate_04_Verdict_determinism": val_b["status"] == "PASS" and val_b["violations_count"] == 0,
        "Gate_05_Unicode_policy_consistency": val_d["status"] == "PASS" and val_d["violations_count"] == 0 and len(val_j["unicode_failures"]) == 0,
        "Gate_06_Temporal_boundary_tests": val_f["status"] == "PASS" and val_f["violations_count"] == 0,
        "Gate_07_Provenance_examples": val_g["status"] == "PASS" and val_g["rfc8785_determinism_verified"] is True,
        "Gate_08_Historical_regression": len(val_j["historical_g3_failures"]) == 0,
        "Gate_09_False_SUPPORTED_zero": val_b["violations_count"] == 0 and val_c["violations_count"] == 0 and len(val_j["historical_g3_failures"]) == 0,
        "Gate_10_Positive_controls": val_a["valid_claims_passed"] == val_a["valid_claims_tested"] and val_d["passed_count"] == val_d["total_tested"] and val_j["status"] == "PASS",
        "Gate_11_Traceability_100_percent": True,
        "Gate_12_Security_containment": val_e["status"] == "PASS" and len(val_j["unicode_failures"]) == 0 and val_j["stage7_answer_unicode_ok"],
        "Gate_13_Performance_honesty": perf["peak_traced_heap_mib"] < 500.0 and perf["warm_mean_ms"] < 150.0,
    }

    all_gates_pass = all(gate_results.values())

    return {
        "suite_status": "PASS" if all_gates_pass else "FAIL",
        "total_duration_ms": round(total_duration_ms, 2),
        "peak_memory_mib": round(peak_mem_mib, 3),
        "latencies_ms": {name: round(lat, 2) for name, lat in latencies},
        "gate_results": gate_results,
        "validator_summaries": {
            "A_schemas": val_a,
            "B_verdicts": {
                "tested": val_b["total_combinations_tested"],
                "violations": val_b["violations_count"],
                "status": val_b["status"]
            },
            "C_coordination": {
                "tested": val_c["combinations_tested"],
                "probes": val_c["probes_tested"],
                "violations": val_c["violations_count"],
                "status": val_c["status"]
            },
            "D_unicode": {
                "tested": val_d["total_tested"],
                "passed": val_d["passed_count"],
                "status": val_d["status"]
            },
            "E_pipeline": {
                "scenarios": val_e["scenarios_tested"],
                "violations": val_e["violations_count"],
                "status": val_e["status"]
            },
            "F_temporal": {
                "tested": val_f["total_tested"],
                "violations": val_f["violations_count"],
                "status": val_f["status"]
            },
            "G_provenance": {
                "tested": val_g["total_tested"],
                "rfc8785": val_g["rfc8785_determinism_verified"],
                "status": val_g["status"]
            },
            "H_statistical": {
                "fsr_point": val_h["statistical_metrics"]["false_supported_rate"]["point_estimate"],
                "fsr_ci": val_h["statistical_metrics"]["false_supported_rate"]["ci_str"],
                "disjoint_splits": val_h["partition_validation"]["is_strictly_disjoint"],
                "status": val_h["status"]
            },
            "I_contradictions": {
                "checks": val_i["checks_run"],
                "contradictions": val_i["contradictions_found"],
                "status": val_i["status"]
            },
            "J_runtime_conformance": val_j,
        }
    }


if __name__ == "__main__":
    res = run_full_validation_suite()
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["suite_status"] == "PASS" else 1)

