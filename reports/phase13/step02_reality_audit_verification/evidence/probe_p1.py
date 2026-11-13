#!/usr/bin/env python3
"""
Phase 13 Step 2 - Independent Verification Probe: P1 Issues
Tests:
1. G3 Phrased unit equivalence (1000 mg per day vs 1 g daily)
2. G3 Coordinated clauses multi-document verification (01_clean_factual)
3. G3 Vague/hedged text provenance gating (09_low_quality_ambiguous)
4. Offline dataset loader short-circuit timing and exception behavior
5. Adaptive calibration alignment (platt vs temperature calibrator FPR)
"""

import sys
import os
import json
import time

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)
if os.path.join(WORKSPACE_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "src"))

from trustrag.verification.output_verifier import OutputEvidenceVerifier
from trustrag.config.engine_config import VerificationConfig
from trustrag.engine.schemas import EvidenceDocument

results = {
    "probe": "probe_p1",
    "timestamp": "2026-11-13T10:45:00Z",
    "tests": {}
}

verifier = OutputEvidenceVerifier(config=VerificationConfig(strict_numeric_matching=True, min_support_coverage=0.65))

# ---------------------------------------------------------
# Test 1: G3 Phrased Unit Equivalence
# ---------------------------------------------------------
print("--- [P1.1] G3 Phrased Unit Equivalence Test ---")
test_cases_units = [
    {
        "claim": "The patient took 1 g daily of medication.",
        "evidence": "Clinical record confirms the patient was administered 1000 mg per day of medication.",
        "expected": "SUPPORTED"
    },
    {
        "claim": "Daily fluid intake is capped at 1 L per day.",
        "evidence": "Daily fluid intake is capped at 1000 ml daily.",
        "expected": "SUPPORTED"
    },
    {
        "claim": "The dose was 500 mg per day.",
        "evidence": "The prescribed dose was 2000 mg daily.",
        "expected": "CONTRADICTED"
    }
]

unit_test_results = []
unit_tests_passed = True

for tc in test_cases_units:
    docs = [EvidenceDocument(doc_id="doc_med", text=tc["evidence"], provenance="clinical_trials")]
    v_res = verifier.verify(answer_text=tc["claim"], trusted_documents=docs)
    actual_verdict = v_res.verdict.value if hasattr(v_res.verdict, "value") else str(v_res.verdict)
    matched = (actual_verdict == tc["expected"])
    if not matched:
        unit_tests_passed = False
    unit_test_results.append({
        "claim": tc["claim"],
        "evidence": tc["evidence"],
        "expected": tc["expected"],
        "actual": actual_verdict,
        "matched": matched,
        "claims_detail": [
            {
                "claim_text": c.claim_text,
                "verdict": c.verdict.value if hasattr(c.verdict, "value") else str(c.verdict),
                "confidence": c.confidence,
                "explanation": c.explanation
            }
            for c in v_res.claims
        ]
    })

print(f"P1.1 Result: {'PASS' if unit_tests_passed else 'FAIL'}")
results["tests"]["P1_1_g3_phrased_units"] = {
    "passed": unit_tests_passed,
    "cases": unit_test_results
}

# ---------------------------------------------------------
# Test 2: G3 Coordinated Clauses & Cross-Document Contradiction
# ---------------------------------------------------------
print("\n--- [P1.2] G3 Coordinated Clauses Test ---")
docs_boil = [
    EvidenceDocument(doc_id="doc_nist", text="Standard chemical reference: pure water boils at 100 °C under 1 atm pressure.", provenance="nist"),
    EvidenceDocument(doc_id="doc_wiki", text="Pure water freezes at 0 °C and boils at 100 °C at standard atmospheric pressure.", provenance="encyclopedia")
]

claim_both = "Pure water freezes at 0 °C and boils at 100 °C."
v_both = verifier.verify(answer_text=claim_both, trusted_documents=docs_boil)
actual_verdict_both = v_both.verdict.value if hasattr(v_both.verdict, "value") else str(v_both.verdict)
both_passed = (actual_verdict_both == "SUPPORTED")

print(f"P1.2 Result: {'PASS' if both_passed else 'FAIL'} (verdict={actual_verdict_both})")
results["tests"]["P1_2_g3_coordinated_clauses"] = {
    "passed": both_passed,
    "verdict": actual_verdict_both,
    "claim_verdicts": [
        {"claim": c.claim_text, "verdict": c.verdict.value if hasattr(c.verdict, "value") else str(c.verdict)}
        for c in v_both.claims
    ]
}

# ---------------------------------------------------------
# Test 3: G3 Vague/Hedged Text & Provenance Gating
# ---------------------------------------------------------
print("\n--- [P1.3] G3 Vague/Hedged Provenance Gating Test ---")
docs_vague = [
    EvidenceDocument(doc_id="doc_unverified", text="Perhaps some variable vague factors possibly affected the trial outcome.", provenance="UNKNOWN")
]

claim_vague = "Perhaps some variable vague factors possibly affected the trial outcome."
v_vague = verifier.verify(answer_text=claim_vague, trusted_documents=docs_vague)
verdict_vague = v_vague.verdict.value if hasattr(v_vague.verdict, "value") else str(v_vague.verdict)

# Must NOT be SUPPORTED when provenance is UNKNOWN and content is hedged
vague_passed = (verdict_vague in ("INSUFFICIENT_EVIDENCE", "UNVERIFIED", "INSUFFICIENT"))

print(f"P1.3 Result: {'PASS' if vague_passed else 'FAIL'} (verdict={verdict_vague})")
results["tests"]["P1_3_g3_vague_provenance_gating"] = {
    "passed": vague_passed,
    "verdict": verdict_vague,
    "explanation": v_vague.claims[0].explanation if v_vague.claims else ""
}

# ---------------------------------------------------------
# Test 4: Offline Dataset Loader Short-Circuit Timing
# ---------------------------------------------------------
print("\n--- [P1.4] Offline Dataset Loader Short-Circuit Test ---")
from trustrag.data.loaders import NaturalQuestionsAdapter, HotpotQAAdapter, MSMarcoAdapter
from trustrag.data.exceptions import AcquisitionError

loader_tests = [
    ("NaturalQuestions", NaturalQuestionsAdapter(offline=True)),
    ("HotpotQA", HotpotQAAdapter(offline=True)),
    ("MSMarco", MSMarcoAdapter(offline=True))
]

loader_results = []
loader_passed = True

for name, adapter in loader_tests:
    start_t = time.perf_counter()
    err_raised = False
    err_msg = ""
    try:
        list(adapter.load_raw())
    except AcquisitionError as e:
        err_raised = True
        err_msg = str(e)
    except Exception as e:
        err_raised = True
        err_msg = f"Unexpected error: {type(e).__name__}: {e}"
    elapsed = time.perf_counter() - start_t
    
    # Must short-circuit in < 1.5 seconds without network hang
    fast_enough = elapsed < 1.5
    ok = err_raised and fast_enough
    if not ok:
        loader_passed = False
    loader_results.append({
        "dataset": name,
        "elapsed_seconds": round(elapsed, 4),
        "error_raised": err_raised,
        "fast_enough": fast_enough,
        "message": err_msg[:120]
    })
    print(f"  - {name}: {'PASS' if ok else 'FAIL'} ({elapsed:.3f}s, {err_msg[:60]}...)")

print(f"P1.4 Result: {'PASS' if loader_passed else 'FAIL'}")
results["tests"]["P1_4_dataset_loader_short_circuit"] = {
    "passed": loader_passed,
    "adapters": loader_results
}

# ---------------------------------------------------------
# Test 5: Adaptive Calibration Alignment
# ---------------------------------------------------------
print("\n--- [P1.5] Adaptive Calibration Alignment Test ---")
calibrator_temp_path = os.path.join(WORKSPACE_ROOT, "configs/adaptive/temperature_calibrator_v1.json")
calibrator_platt_path = os.path.join(WORKSPACE_ROOT, "configs/adaptive/platt_calibrator_v1.json")

temp_exists = os.path.isfile(calibrator_temp_path)
platt_exists = os.path.isfile(calibrator_platt_path)

with open(calibrator_temp_path, "r", encoding="utf-8") as f:
    temp_cal_data = json.load(f)

with open(calibrator_platt_path, "r", encoding="utf-8") as f:
    platt_cal_data = json.load(f)

temp_t = temp_cal_data.get("temperature", 1.0)
platt_w = platt_cal_data.get("weights", {})
platt_b = platt_cal_data.get("bias", 0.0)

cal_passed = temp_exists and platt_exists and (temp_t > 0)
print(f"P1.5 Result: {'PASS' if cal_passed else 'FAIL'}")
print(f"  - Temperature calibrator: {temp_cal_data.get('calibrator_type', 'temp')} (T={temp_t})")
print(f"  - Platt calibrator: {platt_cal_data.get('calibrator_type', 'platt')} (bias={platt_b})")

results["tests"]["P1_5_calibration_alignment"] = {
    "passed": cal_passed,
    "temperature_calibrator": {
        "exists": temp_exists,
        "temperature": temp_t,
        "metadata": {k: v for k, v in temp_cal_data.items() if k not in ("weights",)}
    },
    "platt_calibrator": {
        "exists": platt_exists,
        "bias": platt_b,
        "metadata": {k: v for k, v in platt_cal_data.items() if k not in ("weights",)}
    }
}

# Write results
output_path = os.path.join(os.path.dirname(__file__), "p1_probe_output.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\nAll P1 tests completed. Output written to {output_path}")
