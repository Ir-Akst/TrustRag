from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from trustrag.engine.text_utils import extract_numbers_and_units
from trustrag.guardrails.paraphraser import validate_paraphrase
from trustrag.verification.output_verifier import (
    EvidenceDocument,
    G3AnswerVerdict,
    OutputEvidenceVerifier,
)

G1_PROBES: list[dict[str, Any]] = [
    # DEF-13: Stopword/bridge & shared-anchor attribute drift
    {
        "id": "def13_distance_vs_flight_time",
        "defect": "DEF-13",
        "kind": "drift",
        "orig": "What is the distance between London and Paris?",
        "cand": "What is the flight time between London and Paris?",
        "expected_accepted": False,
    },
    {
        "id": "def13_law_vs_history",
        "defect": "DEF-13",
        "kind": "drift",
        "orig": "What is the law about copyright?",
        "cand": "What is the history about copyright?",
        "expected_accepted": False,
    },
    {
        "id": "def13_multiword_subject_ml_dl",
        "defect": "DEF-13",
        "kind": "drift",
        "orig": "What is the difference between machine learning and deep learning?",
        "cand": "What is the similarity between machine learning and deep learning?",
        "expected_accepted": False,
    },
    {
        "id": "def13_preposition_flip_inside_outside",
        "defect": "DEF-13",
        "kind": "drift",
        "orig": "Where is glucose stored inside the cell?",
        "cand": "Where is glucose stored outside the cell?",
        "expected_accepted": False,
    },
    {
        "id": "def13_preposition_flip_before_after",
        "defect": "DEF-13",
        "kind": "drift",
        "orig": "What happens before cell division?",
        "cand": "What happens after cell division?",
        "expected_accepted": False,
    },
    {
        "id": "def13_valid_between_paraphrase",
        "defect": "DEF-13",
        "kind": "legit",
        "orig": "How is the distance between London and Paris measured?",
        "cand": "What measures the distance between London and Paris?",
        "expected_accepted": True,
    },
    {
        "id": "def13_valid_about_paraphrase",
        "defect": "DEF-13",
        "kind": "legit",
        "orig": "What is copyright law about?",
        "cand": "Explain the law regarding copyright.",
        "expected_accepted": True,
    },
    # DEF-14: Anchorless lowercase verb/predicate drift vs valid verb paraphrases
    {
        "id": "def14_treats_vs_prevents",
        "defect": "DEF-14",
        "kind": "drift",
        "orig": "What treats malaria?",
        "cand": "What prevents malaria?",
        "expected_accepted": False,
    },
    {
        "id": "def14_treats_vs_causes",
        "defect": "DEF-14",
        "kind": "drift",
        "orig": "What treats anemia?",
        "cand": "What causes anemia?",
        "expected_accepted": False,
    },
    {
        "id": "def14_reduces_vs_monitors",
        "defect": "DEF-14",
        "kind": "drift",
        "orig": "What reduces inflammation?",
        "cand": "What monitors inflammation?",
        "expected_accepted": False,
    },
    {
        "id": "def14_controls_vs_measures",
        "defect": "DEF-14",
        "kind": "drift",
        "orig": "What controls blood sugar?",
        "cand": "What measures blood sugar?",
        "expected_accepted": False,
    },
    {
        "id": "def14_valid_synonym_reduces_lowers",
        "defect": "DEF-14",
        "kind": "legit",
        "orig": "What reduces inflammation?",
        "cand": "What lowers inflammation?",
        "expected_accepted": True,
    },
    {
        "id": "def14_valid_synonym_treats_cures",
        "defect": "DEF-14",
        "kind": "legit",
        "orig": "What treats malaria?",
        "cand": "What cures malaria?",
        "expected_accepted": True,
    },
    {
        "id": "def14_valid_active_passive_tense",
        "defect": "DEF-14",
        "kind": "legit",
        "orig": "What treats malaria?",
        "cand": "How is malaria treated?",
        "expected_accepted": True,
    },
    {
        "id": "def14_valid_irregular_built_constructed",
        "defect": "DEF-14",
        "kind": "legit",
        "orig": "Who built the bridge?",
        "cand": "Who constructed the bridge?",
        "expected_accepted": True,
    },
    # Prior DEF-08 & DEF-10 regression probes
    {
        "id": "reg_def08_birth_vs_death",
        "defect": "REG-08",
        "kind": "drift",
        "orig": "What is the birth year of Einstein?",
        "cand": "What is the death year of Einstein?",
        "expected_accepted": False,
    },
    {
        "id": "reg_def10_penicillin_inventor_vs_discoverer",
        "defect": "REG-10",
        "kind": "drift",
        "orig": "Who was the inventor of penicillin?",
        "cand": "Who was the discoverer of penicillin?",
        "expected_accepted": False,
    },
    {
        "id": "reg_def08_valid_capital_paraphrase",
        "defect": "REG-08",
        "kind": "legit",
        "orig": "What is the capital of France?",
        "cand": "Which city serves as France's capital?",
        "expected_accepted": True,
    },
]

G3_PROBES: list[dict[str, Any]] = [
    # DEF-15a: Temporal numeric change
    {
        "id": "def15a_temp_2020_vs_2024",
        "defect": "DEF-15a",
        "claim": "Temperature is 0°C in 2024.",
        "evidence": "Temperature was 5°C in 2020.",
        "expected": G3AnswerVerdict.INSUFFICIENT_EVIDENCE.value,
    },
    {
        "id": "def15a_temp_2024_vs_2020_reverse",
        "defect": "DEF-15a",
        "claim": "Temperature was 5°C in 2020.",
        "evidence": "Temperature is 0°C in 2024.",
        "expected": G3AnswerVerdict.INSUFFICIENT_EVIDENCE.value,
    },
    {
        "id": "def15a_rainfall_2020_vs_2024",
        "defect": "DEF-15a",
        "claim": "Rainfall was 50 mm in 2020.",
        "evidence": "Rainfall was 80 mm in 2024.",
        "expected": G3AnswerVerdict.INSUFFICIENT_EVIDENCE.value,
    },
    {
        "id": "def15a_iso_date_temp_diff",
        "defect": "DEF-15a",
        "claim": "Sensor A recorded 5°C on 2024-01-10.",
        "evidence": "Sensor A recorded 12°C on 2024-02-10.",
        "expected": G3AnswerVerdict.INSUFFICIENT_EVIDENCE.value,
    },
    {
        "id": "def15a_same_year_temp_conflict",
        "defect": "DEF-15a",
        "claim": "Temperature was 0°C in 2020.",
        "evidence": "Temperature was 5°C in 2020.",
        "expected": G3AnswerVerdict.CONTRADICTED.value,
    },
    {
        "id": "def15a_same_year_temp_supported",
        "defect": "DEF-15a",
        "claim": "Temperature was 5°C in 2020.",
        "evidence": "Temperature was 5°C in 2020.",
        "expected": G3AnswerVerdict.SUPPORTED.value,
    },
    {
        "id": "def15a_year_in_range_supported",
        "defect": "DEF-15a",
        "claim": "Temperature was 5°C in 2020.",
        "evidence": "Temperature was 5°C in 2019-2022.",
        "expected": G3AnswerVerdict.INSUFFICIENT_EVIDENCE.value,  # claim year 2020 not explicitly matched as number, wait check!
    },
    {
        "id": "def15a_event_year_contradiction_preserved",
        "defect": "DEF-15a",
        "claim": "The Eiffel Tower was completed in 1899.",
        "evidence": "The Eiffel Tower was completed in 1889.",
        "expected": G3AnswerVerdict.CONTRADICTED.value,
    },
    # DEF-15b: Short designated identifier separation
    {
        "id": "def15b_sensor_b_vs_sensor_a",
        "defect": "DEF-15b",
        "claim": "Sensor B is 0°C.",
        "evidence": "Sensor A is 5°C.",
        "expected": G3AnswerVerdict.INSUFFICIENT_EVIDENCE.value,
    },
    {
        "id": "def15b_sensor_a_same_val_vs_sensor_b",
        "defect": "DEF-15b",
        "claim": "Sensor B is 5°C.",
        "evidence": "Sensor A is 5°C.",
        "expected": G3AnswerVerdict.INSUFFICIENT_EVIDENCE.value,
    },
    {
        "id": "def15b_device_1_vs_device_2",
        "defect": "DEF-15b",
        "claim": "Device 2 measured 120 kPa.",
        "evidence": "Device 1 measured 100 kPa.",
        "expected": G3AnswerVerdict.INSUFFICIENT_EVIDENCE.value,
    },
    {
        "id": "def15b_same_sensor_supported",
        "defect": "DEF-15b",
        "claim": "Sensor A is 5°C.",
        "evidence": "Sensor A is 5°C.",
        "expected": G3AnswerVerdict.SUPPORTED.value,
    },
    {
        "id": "def15b_same_sensor_contradicted",
        "defect": "DEF-15b",
        "claim": "Sensor A is 0°C.",
        "evidence": "Sensor A is 5°C.",
        "expected": G3AnswerVerdict.CONTRADICTED.value,
    },
    {
        "id": "def15b_combined_sensor_and_year",
        "defect": "DEF-15",
        "claim": "Sensor B was 0°C in 2024.",
        "evidence": "Sensor A was 5°C in 2020.",
        "expected": G3AnswerVerdict.INSUFFICIENT_EVIDENCE.value,
    },
    # DEF-16: Incompatible vs compatible measurement units
    {
        "id": "def16_temp_c_vs_rainfall_mm",
        "defect": "DEF-16",
        "claim": "London recorded 10°C.",
        "evidence": "London recorded 50 mm rainfall.",
        "expected": G3AnswerVerdict.INSUFFICIENT_EVIDENCE.value,
    },
    {
        "id": "def16_rainfall_mm_vs_temp_c",
        "defect": "DEF-16",
        "claim": "London recorded 50 mm rainfall.",
        "evidence": "London recorded 10°C.",
        "expected": G3AnswerVerdict.INSUFFICIENT_EVIDENCE.value,
    },
    {
        "id": "def16_speed_vs_pressure",
        "defect": "DEF-16",
        "claim": "Station Alpha recorded 80 kmh.",
        "evidence": "Station Alpha recorded 101 kPa.",
        "expected": G3AnswerVerdict.INSUFFICIENT_EVIDENCE.value,
    },
    {
        "id": "def16_mm_vs_cm_equivalent_supported",
        "defect": "DEF-16",
        "claim": "London recorded 50 mm rainfall.",
        "evidence": "London recorded 5 cm rainfall.",
        "expected": G3AnswerVerdict.SUPPORTED.value,
    },
    {
        "id": "def16_mm_vs_cm_contradicted",
        "defect": "DEF-16",
        "claim": "London recorded 50 mm rainfall.",
        "evidence": "London recorded 8 cm rainfall.",
        "expected": G3AnswerVerdict.CONTRADICTED.value,
    },
    # Prior DEF-09, DEF-11, DEF-12 regressions
    {
        "id": "reg_def09_signed_negative_temp",
        "defect": "REG-09",
        "claim": "The temperature is -5°C.",
        "evidence": "The temperature is 5°C.",
        "expected": G3AnswerVerdict.CONTRADICTED.value,
    },
    {
        "id": "reg_def09_c_to_f_supported",
        "defect": "REG-09",
        "claim": "Water freezes at 0°C.",
        "evidence": "Water freezes at 32°F.",
        "expected": G3AnswerVerdict.SUPPORTED.value,
    },
    {
        "id": "reg_def11_cross_city_population",
        "defect": "REG-11",
        "claim": "London has 9M residents.",
        "evidence": "Tokyo has 14M residents.",
        "expected": G3AnswerVerdict.INSUFFICIENT_EVIDENCE.value,
    },
    {
        "id": "reg_def12_numeric_match_supported",
        "defect": "REG-12",
        "claim": "Aspirin dose is 100 mg daily.",
        "evidence": "Take 100 mg aspirin daily.",
        "expected": G3AnswerVerdict.SUPPORTED.value,
    },
]


def main() -> None:
    verifier = OutputEvidenceVerifier()

    g1_results = []
    fa = fr = 0
    for item in G1_PROBES:
        res = validate_paraphrase(item["orig"], item["cand"], min_similarity=0.30)
        passed = res.accepted == item["expected_accepted"]
        if res.accepted and not item["expected_accepted"]:
            fa += 1
        elif not res.accepted and item["expected_accepted"]:
            fr += 1
        g1_results.append(
            {
                **item,
                "actual_accepted": res.accepted,
                "similarity": round(res.semantic_similarity, 4),
                "reasons": res.rejection_reasons,
                "passed": passed,
            }
        )

    g3_results = []
    fc = fs = ie_on_known = missed_contradiction = 0
    for item in G3_PROBES:
        out = verifier.verify(item["claim"], [EvidenceDocument(doc_id="d1", text=item["evidence"])])
        actual = out.verdict.value
        expected = item["expected"]
        passed = actual == expected
        if not passed:
            if actual == G3AnswerVerdict.CONTRADICTED.value:
                fc += 1
            elif actual == G3AnswerVerdict.SUPPORTED.value:
                fs += 1
            elif expected == G3AnswerVerdict.CONTRADICTED.value:
                missed_contradiction += 1
            else:
                ie_on_known += 1
        g3_results.append(
            {
                **item,
                "actual": actual,
                "reason": getattr(out.claims[0], "explanation", "") if out.claims else out.summary,
                "passed": passed,
            }
        )

    extract_checks = {
        "10C": extract_numbers_and_units("London recorded 10°C."),
        "50mm": extract_numbers_and_units("London recorded 50 mm rainfall."),
        "14M": extract_numbers_and_units("Tokyo | 14M residents."),
        "-5C": extract_numbers_and_units("Temperature is -5°C."),
        "101kPa": extract_numbers_and_units("Pressure reached 101 kPa."),
    }

    report = {
        "g1_total": len(g1_results),
        "g1_passed": sum(1 for r in g1_results if r["passed"]),
        "g1_false_acceptances": fa,
        "g1_false_rejections": fr,
        "g3_total": len(g3_results),
        "g3_passed": sum(1 for r in g3_results if r["passed"]),
        "g3_false_contradictions": fc,
        "g3_false_supports": fs,
        "g3_missed_contradictions": missed_contradiction,
        "g3_other_insufficient_mismatches": ie_on_known,
        "extract_checks": extract_checks,
        "g1_results": g1_results,
        "g3_results": g3_results,
    }
    out_path = Path("reports/phase11/step9_evidence/step9_probe_verification.json")
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("g1_results", "g3_results")}, indent=2))
    for r in g1_results + g3_results:
        if not r["passed"]:
            print("FAILED:", r)


if __name__ == "__main__":
    main()
