#!/usr/bin/env python3
"""Phase 36 Evaluation: Workstream A - G1 Semantic Generalization."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Dict

from trustrag.guardrails.input_guardrail import InputGuardrail

def wilson_interval(successes: int, total: int, z: float = 1.95996) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2.0 * total)) / denom
    margin = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4.0 * (total**2))))
    return max(0.0, center - margin), min(1.0, center + margin)

def evaluate_g1():
    dataset_path = Path("reports/phase36/datasets/g1_semantic_holdout.jsonl")
    pred_path = Path("reports/phase36/raw_predictions/g1_semantic_audit_predictions.jsonl")
    summary_path = Path("reports/phase36/raw_predictions/g1_semantic_audit_summary.json")

    with dataset_path.open("r", encoding="utf-8") as f:
        samples = [json.loads(line) for line in f]

    guardrail = InputGuardrail()
    predictions = []

    tp = fp = tn = fn = 0
    subset_counts: Dict[str, Dict[str, int]] = {}

    for s in samples:
        cid = s["case_id"]
        sub = s["subset"]
        txt = s["text"]
        is_attack = s["is_attack"]

        if sub not in subset_counts:
            subset_counts[sub] = {"total": 0, "blocked": 0, "allowed": 0}
        subset_counts[sub]["total"] += 1

        t0 = time.perf_counter()
        assessment = guardrail.evaluate(txt)
        lat_ms = (time.perf_counter() - t0) * 1000.0

        is_blocked = (assessment.decision.value == "BLOCK")

        if is_attack and is_blocked:
            tp += 1
            subset_counts[sub]["blocked"] += 1
        elif is_attack and not is_blocked:
            fn += 1
            subset_counts[sub]["allowed"] += 1
        elif not is_attack and is_blocked:
            fp += 1
            subset_counts[sub]["blocked"] += 1
        else:
            tn += 1
            subset_counts[sub]["allowed"] += 1

        predictions.append({
            "case_id": cid,
            "subset": sub,
            "text": txt,
            "is_attack": is_attack,
            "decision": assessment.decision.value,
            "risk_score": assessment.risk_score,
            "reason_codes": [r.value for r in assessment.reason_codes],
            "latency_ms": round(lat_ms, 3)
        })

    with pred_path.open("w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")

    total_attacks = tp + fn
    total_controls = tn + fp
    adr = tp / total_attacks if total_attacks else 0.0
    asr = fn / total_attacks if total_attacks else 0.0
    fpr = fp / total_controls if total_controls else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    adr_ci = wilson_interval(tp, total_attacks)
    fpr_ci = wilson_interval(fp, total_controls)

    summary = {
        "workstream": "Workstream A - G1 Semantic Generalization",
        "sample_counts": {
            "total_samples": len(samples),
            "attacks": total_attacks,
            "controls": total_controls
        },
        "confusion_matrix": {"tp": tp, "fn": fn, "tn": tn, "fp": fp},
        "metrics": {
            "adr": round(adr, 4),
            "adr_95ci": [round(adr_ci[0], 4), round(adr_ci[1], 4)],
            "asr": round(asr, 4),
            "fpr": round(fpr, 4),
            "fpr_95ci": [round(fpr_ci[0], 4), round(fpr_ci[1], 4)],
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "novel_action_verbs_adr": round(subset_counts["novel_action_verbs"]["blocked"] / subset_counts["novel_action_verbs"]["total"], 4),
            "security_education_fpr": round(subset_counts["benign_security_education"]["blocked"] / subset_counts["benign_security_education"]["total"], 4),
            "general_domain_fpr": round(subset_counts["benign_general_domain"]["blocked"] / subset_counts["benign_general_domain"]["total"], 4)
        },
        "subset_breakdown": subset_counts
    }

    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("G1 Evaluation Complete:", json.dumps(summary["metrics"], indent=2))

if __name__ == "__main__":
    evaluate_g1()

