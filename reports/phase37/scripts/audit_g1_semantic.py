import json, time, math
from pathlib import Path
from trustrag.guardrails.input_guardrail import InputGuardrail

def wilson_score_interval(k, n, confidence=0.95):
    if n == 0:
        return 0.0, 0.0
    z = 1.959963984540054
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return round(max(0.0, centre - spread), 4), round(min(1.0, centre + spread), 4)

def run_g1_audit():
    dataset_path = "reports/phase37/datasets/g1_independent_holdout.jsonl"
    pred_path = "reports/phase37/raw_predictions/g1_semantic_audit_predictions.jsonl"
    summary_path = "reports/phase37/raw_predictions/g1_semantic_audit_summary.json"

    guardrail = InputGuardrail()

    with open(dataset_path) as f:
        records = [json.loads(line) for line in f]

    predictions = []
    tp = fp = tn = fn = 0
    cat_breakdown = {}

    for item in records:
        cid = item["case_id"]
        cat = item["category"]
        text = item["text"]
        is_attack = (item["ground_truth"] == "ATTACK")

        t0 = time.perf_counter()
        assessment = guardrail.evaluate(text)
        lat = (time.perf_counter() - t0) * 1000.0

        decision_val = assessment.decision.value if hasattr(assessment.decision, "value") else str(assessment.decision)
        blocked = (decision_val == "BLOCK")

        cat_breakdown.setdefault(cat, {"total": 0, "blocked": 0, "allowed": 0})
        cat_breakdown[cat]["total"] += 1

        if is_attack:
            if blocked:
                tp += 1
                cat_breakdown[cat]["blocked"] += 1
            else:
                fn += 1
                cat_breakdown[cat]["allowed"] += 1
        else:
            if blocked:
                fp += 1
                cat_breakdown[cat]["blocked"] += 1
            else:
                tn += 1
                cat_breakdown[cat]["allowed"] += 1

        reason_codes = [r.value if hasattr(r, "value") else str(r) for r in assessment.reason_codes]

        predictions.append({
            "case_id": cid,
            "category": cat,
            "text": text,
            "ground_truth": item["ground_truth"],
            "decision": decision_val,
            "risk_score": round(assessment.risk_score, 4),
            "reason_codes": reason_codes,
            "blocked": blocked,
            "latency_ms": round(lat, 3)
        })

    with open(pred_path, "w") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")

    adr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    asr = fn / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = adr
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

    summary = {
        "workstream": "Workstream A - G1 Semantic Generalization Audit",
        "sample_counts": {
            "total_samples": len(records),
            "attacks": tp + fn,
            "controls": fp + tn
        },
        "confusion_matrix": {
            "tp": tp, "fn": fn, "tn": tn, "fp": fp
        },
        "metrics": {
            "adr": round(adr, 4),
            "adr_95ci": wilson_score_interval(tp, tp + fn),
            "asr": round(asr, 4),
            "fpr": round(fpr, 4),
            "fpr_95ci": wilson_score_interval(fp, fp + tn),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4)
        },
        "subset_breakdown": cat_breakdown
    }

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("=== G1 AUDIT RESULTS ===")
    print(f"Total: {len(records)} (Attacks: {tp+fn}, Controls: {fp+tn})")
    print(f"TP: {tp}, FN: {fn}, TN: {tn}, FP: {fp}")
    print(f"ADR: {adr:.4f} (95% CI: {summary['metrics']['adr_95ci']})")
    print(f"ASR: {asr:.4f}")
    print(f"FPR: {fpr:.4f} (95% CI: {summary['metrics']['fpr_95ci']})")
    for k, v in cat_breakdown.items():
        print(f"  {k}: {v['blocked']}/{v['total']} blocked")

if __name__ == "__main__":
    run_g1_audit()
