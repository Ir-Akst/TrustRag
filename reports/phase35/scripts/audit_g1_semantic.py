#!/usr/bin/env python3
"""Phase 35 Audit Script: Workstream A - G1 Semantic Generalization.

Evaluates the Phase 34 G1 Input Guardrail and SemanticAttackClassifier against
the sealed independent holdout (N=240):
- Novel action verbs (unfetter, dethrone, repudiate, abnegate, unfasten, vacate, shun, etc.)
- Contextual hierarchy & indirect injections
- Spaced-letter & obfuscated variants
- Adaptive white-box attacks
- Benign cybersecurity education controls
- Benign general domain controls

Calculates:
- Per-subset confusion matrix
- Overall ADR, ASR, FPR, Precision, Recall, F1
- Wilson 95% Confidence Intervals
- Distinct False Positive Rates on educational security vs general queries
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any, Dict, List

from trustrag.engine.schemas import G1Decision
from trustrag.guardrails.input_guardrail import InputGuardrail
from trustrag.guardrails.semantic_classifier import SemanticAttackClassifier

def wilson_interval(successes: int, total: int, z: float = 1.95996) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2.0 * total)) / denom
    margin = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4.0 * (total**2))))
    return max(0.0, center - margin), min(1.0, center + margin)

def run_workstream_a_audit():
    dataset_file = Path("reports/phase35/datasets/g1_semantic_holdout.jsonl")
    with dataset_file.open("r", encoding="utf-8") as f:
        samples = [json.loads(line) for line in f]

    g1 = InputGuardrail()
    clf = SemanticAttackClassifier()

    predictions = []
    subset_stats: Dict[str, Dict[str, int]] = {}

    tp, fn, tn, fp = 0, 0, 0, 0
    edu_fp, edu_total = 0, 0
    gen_fp, gen_total = 0, 0

    print(f"Executing G1 Semantic Audit on {len(samples)} sealed holdout samples...")

    for item in samples:
        cid = item["case_id"]
        subset = item["subset"]
        text = item["text"]
        is_attack = item["is_attack"]

        if subset not in subset_stats:
            subset_stats[subset] = {"total": 0, "blocked": 0, "allowed": 0}
        subset_stats[subset]["total"] += 1

        t0 = time.perf_counter()
        res = g1.evaluate(text)
        lat_ms = (time.perf_counter() - t0) * 1000.0

        is_blocked = (res.decision in (G1Decision.BLOCK, G1Decision.FLAG))

        if is_attack:
            if is_blocked:
                tp += 1
                subset_stats[subset]["blocked"] += 1
            else:
                fn += 1
                subset_stats[subset]["allowed"] += 1
        else:
            if is_blocked:
                fp += 1
                subset_stats[subset]["blocked"] += 1
                if subset == "benign_security_education":
                    edu_fp += 1
                else:
                    gen_fp += 1
            else:
                tn += 1
                subset_stats[subset]["allowed"] += 1

            if subset == "benign_security_education":
                edu_total += 1
            else:
                gen_total += 1

        predictions.append({
            "case_id": cid,
            "subset": subset,
            "is_attack": is_attack,
            "detected_attack": is_blocked,
            "decision": res.decision.value,
            "risk_score": round(res.risk_score, 4),
            "reason_codes": [r.value for r in res.reason_codes],
            "latency_ms": round(lat_ms, 3)
        })

    total_attacks = tp + fn
    total_clean = tn + fp

    adr = tp / total_attacks if total_attacks else 0.0
    asr = fn / total_attacks if total_attacks else 0.0
    fpr = fp / total_clean if total_clean else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = adr
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0

    adr_ci = wilson_interval(tp, total_attacks)
    fpr_ci = wilson_interval(fp, total_clean)

    edu_fpr = edu_fp / edu_total if edu_total else 0.0
    gen_fpr = gen_fp / gen_total if gen_total else 0.0

    summary = {
        "workstream": "Workstream A - G1 Semantic Generalization",
        "sample_counts": {
            "total_samples": len(samples),
            "total_attacks": total_attacks,
            "total_clean_controls": total_clean,
            "security_education_controls": edu_total,
            "general_domain_controls": gen_total
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
            "security_education_fpr": round(edu_fpr, 4),
            "general_domain_fpr": round(gen_fpr, 4)
        },
        "subset_breakdown": subset_stats
    }

    out_file = Path("reports/phase35/raw_predictions/g1_semantic_audit_predictions.jsonl")
    with out_file.open("w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")

    summary_file = Path("reports/phase35/raw_predictions/g1_semantic_audit_summary.json")
    with summary_file.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=== Workstream A: G1 Semantic Audit Complete ===")
    print(f"Overall ADR: {adr*100:.2f}% (CI: [{adr_ci[0]*100:.2f}%, {adr_ci[1]*100:.2f}%]) | TP={tp}, FN={fn}")
    print(f"Overall FPR: {fpr*100:.2f}% (CI: [{fpr_ci[0]*100:.2f}%, {fpr_ci[1]*100:.2f}%]) | TN={tn}, FP={fp}")
    print(f"Precision:   {precision*100:.2f}% | Recall: {recall*100:.2f}% | F1: {f1:.4f}")
    print(f"Security Education FPR: {edu_fpr*100:.2f}% ({edu_fp}/{edu_total})")
    print(f"General Domain FPR:     {gen_fpr*100:.2f}% ({gen_fp}/{gen_total})")
    print("\nPer-Subset Breakdown:")
    for sub, stats in subset_stats.items():
        sub_rate = stats["blocked"] / stats["total"] * 100
        print(f"  - {sub:30s}: Total={stats['total']:2d} | Blocked={stats['blocked']:2d} | Rate={sub_rate:.1f}%")

if __name__ == "__main__":
    run_workstream_a_audit()
