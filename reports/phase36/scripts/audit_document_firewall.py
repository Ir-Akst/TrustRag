#!/usr/bin/env python3
"""Phase 36 Evaluation: Workstream B - Document Firewall & Generator Boundary."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Dict

from trustrag.engine.schemas import EvidenceDocument
from trustrag.retrieval.document_firewall import DocumentInjectionFirewall

def wilson_interval(successes: int, total: int, z: float = 1.95996) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2.0 * total)) / denom
    margin = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4.0 * (total**2))))
    return max(0.0, center - margin), min(1.0, center + margin)

def evaluate_firewall():
    dataset_path = Path("reports/phase36/datasets/firewall_generator_holdout.jsonl")
    pred_path = Path("reports/phase36/raw_predictions/firewall_generator_audit_predictions.jsonl")
    summary_path = Path("reports/phase36/raw_predictions/firewall_generator_audit_summary.json")

    with dataset_path.open("r", encoding="utf-8") as f:
        samples = [json.loads(line) for line in f]

    firewall = DocumentInjectionFirewall()
    predictions = []

    total_attacks = 0
    attack_detected = 0
    attack_leaked = 0

    total_controls = 0
    false_quarantines = 0

    subset_counts: Dict[str, Dict[str, int]] = {}
    total_utilities = []

    for s in samples:
        cid = s["case_id"]
        sub = s["subset"]
        is_attack = s["is_attack"]
        doc_text = s["document_text"]
        mal_clause = s["malicious_clause"]

        if sub not in subset_counts:
            subset_counts[sub] = {"total": 0, "quarantined": 0, "clean": 0, "leaked": 0}
        subset_counts[sub]["total"] += 1

        doc = EvidenceDocument(doc_id=cid, text=doc_text)
        t0 = time.perf_counter()
        res = firewall.inspect_and_sanitize(doc)
        lat_ms = (time.perf_counter() - t0) * 1000.0

        total_utilities.append(res.retrieval_utility_score)

        leaked = False
        if is_attack:
            total_attacks += 1
            if not res.is_safe:
                attack_detected += 1
                subset_counts[sub]["quarantined"] += 1
            else:
                leaked = True
                attack_leaked += 1
                subset_counts[sub]["leaked"] += 1
        else:
            total_controls += 1
            if not res.is_safe:
                false_quarantines += 1
                subset_counts[sub]["quarantined"] += 1
            else:
                subset_counts[sub]["clean"] += 1

        predictions.append({
            "case_id": cid,
            "subset": sub,
            "is_attack": is_attack,
            "is_safe": res.is_safe,
            "leaked_to_generator": leaked,
            "quarantined_clauses": [q.text for q in res.quarantined_spans],
            "sanitized_text": res.sanitized_text,
            "utility_score": res.retrieval_utility_score,
            "latency_ms": round(lat_ms, 3)
        })

    with pred_path.open("w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")

    recall = attack_detected / total_attacks if total_attacks else 0.0
    leakage = attack_leaked / total_attacks if total_attacks else 0.0
    fq_rate = false_quarantines / total_controls if total_controls else 0.0
    mean_utility = sum(total_utilities) / len(total_utilities) if total_utilities else 0.0

    rec_ci = wilson_interval(attack_detected, total_attacks)
    leak_ci = wilson_interval(attack_leaked, total_attacks)
    fq_ci = wilson_interval(false_quarantines, total_controls)

    summary = {
        "workstream": "Workstream B - Document Firewall & Generator Boundary",
        "sample_counts": {
            "total_documents": len(samples),
            "total_attacks": total_attacks,
            "total_controls": total_controls
        },
        "metrics": {
            "detection_recall": round(recall, 4),
            "detection_recall_95ci": [round(rec_ci[0], 4), round(rec_ci[1], 4)],
            "generator_leakage_rate": round(leakage, 4),
            "generator_leakage_95ci": [round(leak_ci[0], 4), round(leak_ci[1], 4)],
            "false_quarantine_rate": round(fq_rate, 4),
            "false_quarantine_95ci": [round(fq_ci[0], 4), round(fq_ci[1], 4)],
            "mean_utility_retention": round(mean_utility, 4)
        },
        "subset_breakdown": subset_counts
    }

    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("Firewall Evaluation Complete:", json.dumps(summary["metrics"], indent=2))

if __name__ == "__main__":
    evaluate_firewall()

