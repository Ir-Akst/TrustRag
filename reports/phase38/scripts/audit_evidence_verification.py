import json, time, math
from trustrag.engine.schemas import EvidenceDocument
from trustrag.verification.grounded_verifier import EvidenceGroundedVerifier

def wilson_score_interval(k, n, confidence=0.95):
    if n == 0:
        return 0.0, 0.0
    z = 1.959963984540054
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return round(max(0.0, centre - spread), 4), round(min(1.0, centre + spread), 4)

def run_evidence_audit():
    dataset_path = "reports/phase38/datasets/evidence_verification_holdout.jsonl"
    pred_path = "reports/phase38/raw_predictions/evidence_verification_audit_predictions.jsonl"
    summary_path = "reports/phase38/raw_predictions/evidence_verification_audit_summary.json"

    verifier = EvidenceGroundedVerifier()
    verifier.initialize()

    with open(dataset_path) as f:
        records = [json.loads(line) for line in f]

    predictions = []
    cat_breakdown = {}

    for item in records:
        cid = item["case_id"]
        cat = item["category"]
        query = item["query"]
        answer = item["answer"]
        evidence_texts = item["evidence"]
        expected_release = item["expected_release"]

        docs = [EvidenceDocument(doc_id=f"doc_{idx}", text=t) for idx, t in enumerate(evidence_texts)]

        t0 = time.perf_counter()
        rep = verifier.verify_answer(query=query, answer_text=answer, retrieved_documents=docs)
        lat = (time.perf_counter() - t0) * 1000.0

        safe_to_release = rep.safe_to_release
        accurate_decision = (safe_to_release == expected_release)
        contradiction_detected = rep.contradiction_detected

        cat_breakdown.setdefault(cat, {
            "total": 0, "safe_to_release": 0, "accurate_decision": 0, "contradiction_detected": 0
        })
        cat_breakdown[cat]["total"] += 1
        if safe_to_release:
            cat_breakdown[cat]["safe_to_release"] += 1
        if accurate_decision:
            cat_breakdown[cat]["accurate_decision"] += 1
        if contradiction_detected:
            cat_breakdown[cat]["contradiction_detected"] += 1

        predictions.append({
            "case_id": cid,
            "category": cat,
            "query": query,
            "answer": answer,
            "overall_status": rep.overall_status,
            "safe_to_release": safe_to_release,
            "expected_release": expected_release,
            "accurate_decision": accurate_decision,
            "contradiction_detected": contradiction_detected,
            "total_claims": rep.total_claims,
            "supported_claims": rep.supported_claims_count,
            "contradicted_claims": rep.contradicted_claims_count,
            "unsupported_claims": rep.unsupported_claims_count,
            "claim_support_rate": rep.claim_support_rate,
            "latency_ms": round(lat, 3)
        })

    with open(pred_path, "w") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")

    sup_d = cat_breakdown.get("SUPPORTED", {"total": 1, "safe_to_release": 0, "accurate_decision": 0})
    sup_acc_rate = sup_d["safe_to_release"] / sup_d["total"]
    false_abstention = 1.0 - sup_acc_rate

    # Contradiction recall
    con_sem_d = cat_breakdown.get("CONTRADICTED_SEMANTIC", {"total": 0, "contradiction_detected": 0})
    con_num_d = cat_breakdown.get("CONTRADICTED_NUMERICAL", {"total": 0, "contradiction_detected": 0})
    tot_contra = con_sem_d["total"] + con_num_d["total"]
    det_contra = con_sem_d["contradiction_detected"] + con_num_d["contradiction_detected"]
    contra_rec = det_contra / tot_contra if tot_contra > 0 else 0.0

    # Unsupported leakage
    unsup_d = cat_breakdown.get("UNSUPPORTED", {"total": 1, "safe_to_release": 0})
    unsup_leak_rate = unsup_d["safe_to_release"] / unsup_d["total"]

    # Partially supported leakage
    part_d = cat_breakdown.get("PARTIALLY_SUPPORTED", {"total": 1, "safe_to_release": 0})
    part_leak_rate = part_d["safe_to_release"] / part_d["total"]

    total_correct = sum(d["accurate_decision"] for d in cat_breakdown.values())
    overall_acc = total_correct / len(records)

    summary = {
        "workstream": "Workstream D - Evidence Verification Reliability Audit",
        "sample_counts": {
            "total_scenarios": len(records),
            "supported_scenarios": sup_d["total"],
            "contradicted_scenarios": tot_contra,
            "unsupported_scenarios": unsup_d["total"],
            "partially_supported_scenarios": part_d["total"]
        },
        "metrics": {
            "overall_accuracy": round(overall_acc, 4),
            "overall_accuracy_95ci": wilson_score_interval(total_correct, len(records)),
            "supported_acceptance_rate": round(sup_acc_rate, 4),
            "supported_acceptance_95ci": wilson_score_interval(sup_d["safe_to_release"], sup_d["total"]),
            "false_abstention_rate": round(false_abstention, 4),
            "contradiction_recall": round(contra_rec, 4),
            "contradiction_recall_95ci": wilson_score_interval(det_contra, tot_contra),
            "unsupported_leakage_rate": round(unsup_leak_rate, 4),
            "unsupported_leakage_95ci": wilson_score_interval(unsup_d["safe_to_release"], unsup_d["total"]),
            "partially_supported_leakage_rate": round(part_leak_rate, 4)
        },
        "subset_breakdown": cat_breakdown
    }

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("=== EVIDENCE VERIFICATION AUDIT RESULTS ===")
    print(f"Total Scenarios: {len(records)}")
    print(f"Overall Gate Accuracy: {overall_acc:.4f} ({total_correct}/{len(records)}) (95% CI: {summary['metrics']['overall_accuracy_95ci']})")
    print(f"Supported Acceptance Rate: {sup_acc_rate:.4f} (95% CI: {summary['metrics']['supported_acceptance_95ci']})")
    print(f"False Abstention Rate: {false_abstention:.4f}")
    print(f"Contradiction Recall: {contra_rec:.4f} ({det_contra}/{tot_contra}) (95% CI: {summary['metrics']['contradiction_recall_95ci']})")
    print(f"Unsupported Leakage Rate: {unsup_leak_rate:.4f} ({unsup_d['safe_to_release']}/{unsup_d['total']})")
    print(f"Partially Supported Leakage Rate: {part_leak_rate:.4f} ({part_d['safe_to_release']}/{part_d['total']})")
    for k, v in cat_breakdown.items():
        print(f"  {k}: {v['accurate_decision']}/{v['total']} accurate, {v['safe_to_release']} safe_to_release, {v['contradiction_detected']} contra_detected")

if __name__ == "__main__":
    run_evidence_audit()
