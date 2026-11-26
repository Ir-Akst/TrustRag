import json, time, math
from trustrag.engine.schemas import EvidenceDocument
from trustrag.retrieval.document_firewall import DocumentInjectionFirewall

def wilson_score_interval(k, n, confidence=0.95):
    if n == 0:
        return 0.0, 0.0
    z = 1.959963984540054
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return round(max(0.0, centre - spread), 4), round(min(1.0, centre + spread), 4)

def run_firewall_audit():
    dataset_path = "reports/phase38/datasets/firewall_generator_holdout.jsonl"
    pred_path = "reports/phase38/raw_predictions/firewall_generator_audit_predictions.jsonl"
    summary_path = "reports/phase38/raw_predictions/firewall_generator_audit_summary.json"

    firewall = DocumentInjectionFirewall()

    with open(dataset_path) as f:
        records = [json.loads(line) for line in f]

    predictions = []
    tp = fp = tn = fn = leaked = 0
    cat_breakdown = {}
    attack_retentions = []
    all_retentions = []

    for item in records:
        cid = item["case_id"]
        cat = item["category"]
        text = item["full_text"]
        payload = item["adversarial_payload"]
        is_attack = (item["ground_truth"] == "ATTACK")

        doc = EvidenceDocument(doc_id=cid, text=text)
        t0 = time.perf_counter()
        result = firewall.inspect_and_sanitize(doc)
        lat = (time.perf_counter() - t0) * 1000.0

        sanitized_text = result.sanitized_text
        quarantined = (not result.is_safe or len(result.quarantined_spans) > 0)
        utility = result.retrieval_utility_score

        # Check generator leakage
        generator_leakage = False
        if is_attack and payload:
            core_phrase = payload.split(":", 1)[-1].strip() if ":" in payload else payload
            check_sub = core_phrase.replace("[", "").replace("]", "").replace("<!--", "").replace("-->", "").strip()[:30]
            if check_sub.lower() in sanitized_text.lower():
                generator_leakage = True

        cat_breakdown.setdefault(cat, {"total": 0, "quarantined": 0, "leaked": 0, "clean": 0})
        cat_breakdown[cat]["total"] += 1
        all_retentions.append(utility)

        if is_attack:
            attack_retentions.append(utility)
            if quarantined:
                tp += 1
                cat_breakdown[cat]["quarantined"] += 1
            else:
                fn += 1
                cat_breakdown[cat]["clean"] += 1

            if generator_leakage:
                leaked += 1
                cat_breakdown[cat]["leaked"] += 1
        else:
            if quarantined:
                fp += 1
                cat_breakdown[cat]["quarantined"] += 1
            else:
                tn += 1
                cat_breakdown[cat]["clean"] += 1

        quarantined_clauses = [s.text for s in result.quarantined_spans]

        predictions.append({
            "case_id": cid,
            "category": cat,
            "ground_truth": item["ground_truth"],
            "quarantined": quarantined,
            "is_safe": result.is_safe,
            "generator_leakage": generator_leakage,
            "quarantined_clauses": quarantined_clauses,
            "sanitized_text": sanitized_text,
            "utility_score": round(utility, 4),
            "latency_ms": round(lat, 3)
        })

    with open(pred_path, "w") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")

    n_attacks = tp + fn
    n_controls = fp + tn
    rec = tp / n_attacks if n_attacks > 0 else 0.0
    leak_rate = leaked / n_attacks if n_attacks > 0 else 0.0
    false_quar = fp / n_controls if n_controls > 0 else 0.0
    mean_att_ret = sum(attack_retentions) / len(attack_retentions) if attack_retentions else 0.0
    mean_all_ret = sum(all_retentions) / len(all_retentions) if all_retentions else 0.0

    summary = {
        "workstream": "Workstream B - Document Firewall & Generator Boundary Audit",
        "sample_counts": {
            "total_documents": len(records),
            "total_attacks": n_attacks,
            "total_controls": n_controls
        },
        "metrics": {
            "detection_recall": round(rec, 4),
            "detection_recall_95ci": wilson_score_interval(tp, n_attacks),
            "generator_leakage_rate": round(leak_rate, 4),
            "generator_leakage_95ci": wilson_score_interval(leaked, n_attacks),
            "false_quarantine_rate": round(false_quar, 4),
            "false_quarantine_95ci": wilson_score_interval(fp, n_controls),
            "mean_utility_retention_attacks": round(mean_att_ret, 4),
            "mean_utility_retention_all_docs": round(mean_all_ret, 4)
        },
        "subset_breakdown": cat_breakdown
    }

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("=== DOCUMENT FIREWALL AUDIT RESULTS ===")
    print(f"Total Docs: {len(records)} (Attacks: {n_attacks}, Controls: {n_controls})")
    print(f"Detection Recall: {rec:.4f} (95% CI: {summary['metrics']['detection_recall_95ci']})")
    print(f"Generator Leakage Rate: {leak_rate:.4f} ({leaked}/{n_attacks})")
    print(f"False Quarantine Rate: {false_quar:.4f} ({fp}/{n_controls})")
    print(f"Mean Utility Retention (Attacks): {mean_att_ret:.4f}")
    print(f"Mean Utility Retention (All Docs): {mean_all_ret:.4f}")
    for k, v in cat_breakdown.items():
        print(f"  {k}: {v['quarantined']}/{v['total']} quarantined, {v['leaked']} leaked")

if __name__ == "__main__":
    run_firewall_audit()
