#!/usr/bin/env python3
"""Phase 36 Evaluation: Workstream D - Evidence Verification Utility."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any, Dict, List

from trustrag.engine.schemas import EvidenceDocument
from trustrag.verification.grounded_verifier import EvidenceGroundedVerifier

def wilson_interval(successes: int, total: int, z: float = 1.95996) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2.0 * total)) / denom
    margin = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4.0 * (total**2))))
    return max(0.0, center - margin), min(1.0, center + margin)

def evaluate_evidence_verification():
    dataset_file = Path("reports/phase36/datasets/evidence_verification_holdout.jsonl")
    pred_path = Path("reports/phase36/raw_predictions/evidence_verification_audit_predictions.jsonl")
    summary_path = Path("reports/phase36/raw_predictions/evidence_verification_audit_summary.json")

    with dataset_file.open("r", encoding="utf-8") as f:
        samples = [json.loads(line) for line in f]

    verifier = EvidenceGroundedVerifier()
    verifier.initialize()

    predictions = []
    cat_stats: Dict[str, Dict[str, int]] = {}

    total_scenarios = len(samples)
    correct_release_decisions = 0
    total_contradictions = 0
    contradiction_detections = 0
    total_unsupported = 0
    unsupported_leakages = 0

    total_supported = 0
    accepted_supported = 0
    false_abstained_supported = 0

    for item in samples:
        cid = item["case_id"]
        cat = item["category"]
        query = item["query"]
        answer = item["answer"]
        evidence_texts = item["evidence"]
        expected_release = item["expected_release"]

        if cat not in cat_stats:
            cat_stats[cat] = {"total": 0, "safe_released": 0, "abstained": 0, "contradiction_flagged": 0}
        cat_stats[cat]["total"] += 1

        docs = [EvidenceDocument(doc_id=f"doc_{idx}", text=t) for idx, t in enumerate(evidence_texts)]

        t0 = time.perf_counter()
        rep = verifier.verify_answer(query=query, answer_text=answer, retrieved_documents=docs)
        lat_ms = (time.perf_counter() - t0) * 1000.0

        if rep.safe_to_release:
            cat_stats[cat]["safe_released"] += 1
        else:
            cat_stats[cat]["abstained"] += 1

        if rep.contradiction_detected:
            cat_stats[cat]["contradiction_flagged"] += 1

        is_decision_accurate = (rep.safe_to_release == expected_release)
        if is_decision_accurate:
            correct_release_decisions += 1

        if "CONTRADICTED" in cat:
            total_contradictions += 1
            if rep.contradiction_detected or rep.overall_status == "CONTRADICTED" or not rep.safe_to_release:
                contradiction_detections += 1

        if cat == "UNSUPPORTED":
            total_unsupported += 1
            if rep.safe_to_release:
                unsupported_leakages += 1

        if cat == "SUPPORTED":
            total_supported += 1
            if rep.safe_to_release:
                accepted_supported += 1
            else:
                false_abstained_supported += 1

        predictions.append({
            "case_id": cid,
            "category": cat,
            "query": query,
            "answer": answer,
            "overall_status": rep.overall_status,
            "safe_to_release": rep.safe_to_release,
            "expected_release": expected_release,
            "accurate_gate_decision": is_decision_accurate,
            "contradiction_detected": rep.contradiction_detected,
            "total_claims": rep.total_claims,
            "supported_claims": rep.supported_claims_count,
            "contradicted_claims": rep.contradicted_claims_count,
            "unsupported_claims": rep.unsupported_claims_count,
            "claim_support_rate": rep.claim_support_rate,
            "latency_ms": round(lat_ms, 3)
        })

    with pred_path.open("w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")

    overall_accuracy = correct_release_decisions / total_scenarios if total_scenarios else 0.0
    supported_acceptance_rate = accepted_supported / total_supported if total_supported else 0.0
    false_abstention_rate = false_abstained_supported / total_supported if total_supported else 0.0
    contradiction_recall = contradiction_detections / total_contradictions if total_contradictions else 0.0
    unsupported_leakage_rate = unsupported_leakages / total_unsupported if total_unsupported else 0.0

    acc_ci = wilson_interval(correct_release_decisions, total_scenarios)
    sup_ci = wilson_interval(accepted_supported, total_supported)
    con_ci = wilson_interval(contradiction_detections, total_contradictions)
    leak_ci = wilson_interval(unsupported_leakages, total_unsupported)

    summary = {
        "workstream": "Workstream D - Evidence Verification Utility",
        "sample_counts": {
            "total_scenarios": total_scenarios,
            "supported_scenarios": total_supported,
            "contradicted_scenarios": total_contradictions,
            "unsupported_scenarios": total_unsupported
        },
        "metrics": {
            "overall_accuracy": round(overall_accuracy, 4),
            "overall_accuracy_95ci": [round(acc_ci[0], 4), round(acc_ci[1], 4)],
            "supported_acceptance_rate": round(supported_acceptance_rate, 4),
            "supported_acceptance_95ci": [round(sup_ci[0], 4), round(sup_ci[1], 4)],
            "false_abstention_rate": round(false_abstention_rate, 4),
            "contradiction_recall": round(contradiction_recall, 4),
            "contradiction_recall_95ci": [round(con_ci[0], 4), round(con_ci[1], 4)],
            "unsupported_leakage_rate": round(unsupported_leakage_rate, 4),
            "unsupported_leakage_95ci": [round(leak_ci[0], 4), round(leak_ci[1], 4)]
        },
        "category_breakdown": cat_stats
    }

    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("Evidence Verification Evaluation Complete:", json.dumps(summary["metrics"], indent=2))

if __name__ == "__main__":
    evaluate_evidence_verification()

