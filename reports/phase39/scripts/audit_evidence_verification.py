#!/usr/bin/env python3
"""Phase 39 Independent G3 Evidence Verification Stress Test."""

import json
import math
from pathlib import Path
from trustrag.engine.schemas import EvidenceDocument
from trustrag.verification.grounded_verifier import EvidenceGroundedVerifier

OUT_DIR = Path("reports/phase39/raw_predictions")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def wilson_ci(k: int, n: int, z: float = 1.959964) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n) / denom
    return [round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)]


def run_evidence_audit() -> None:
    dataset_path = Path("reports/phase39/datasets/evidence_verification_holdout.jsonl")
    verifier = EvidenceGroundedVerifier()
    verifier.initialize()

    predictions = []
    cat_stats: dict[str, dict] = {}

    sup_total = sup_acc = 0
    con_total = con_rec = 0
    unsup_total = unsup_leak = 0
    part_total = part_leak = 0
    accurate_decisions = 0
    # Binary release safety: positive = unsafe (CONTRADICTED / UNSUPPORTED / PARTIAL), negative = safe (SUPPORTED)
    # Also compute release precision/recall for safe_to_release
    rel_tp = rel_fp = rel_tn = rel_fn = 0

    with open(dataset_path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            docs = [EvidenceDocument(doc_id=d["doc_id"], text=d["text"], source_id=d["doc_id"], score=0.9) for d in row["evidence"]]
            report = verifier.verify_answer(row["query"], row["answer_text"], docs)

            cat = row["category"]
            exp_rel = row["expected_safe_to_release"]
            act_rel = report.safe_to_release
            accurate = (act_rel == exp_rel)
            if accurate:
                accurate_decisions += 1

            if exp_rel and act_rel:
                rel_tp += 1
            elif not exp_rel and act_rel:
                rel_fp += 1
            elif not exp_rel and not act_rel:
                rel_tn += 1
            else:
                rel_fn += 1

            if cat not in cat_stats:
                cat_stats[cat] = {
                    "total": 0, "expected_status": row["expected_status"],
                    "safe_to_release": 0, "abstained": 0, "contradiction_detected": 0,
                    "accurate_decision": 0, "verdict_counts": {}
                }
            st = cat_stats[cat]
            st["total"] += 1
            if act_rel:
                st["safe_to_release"] += 1
            else:
                st["abstained"] += 1
            if report.contradiction_detected:
                st["contradiction_detected"] += 1
            if accurate:
                st["accurate_decision"] += 1
            st["verdict_counts"][report.overall_status] = st["verdict_counts"].get(report.overall_status, 0) + 1

            if row["expected_status"] == "SUPPORTED":
                sup_total += 1
                if act_rel:
                    sup_acc += 1
            elif row["expected_status"] == "CONTRADICTED":
                con_total += 1
                if report.contradiction_detected:
                    con_rec += 1
            elif row["expected_status"] == "INSUFFICIENT_EVIDENCE":
                unsup_total += 1
                if act_rel:
                    unsup_leak += 1
            elif row["expected_status"] == "PARTIALLY_SUPPORTED":
                part_total += 1
                if act_rel:
                    part_leak += 1

            predictions.append({
                "case_id": row["case_id"],
                "category": cat,
                "expected_status": row["expected_status"],
                "expected_safe_to_release": exp_rel,
                "actual_status": report.overall_status,
                "actual_safe_to_release": act_rel,
                "contradiction_detected": report.contradiction_detected,
                "accurate_decision": accurate,
                "claim_results": [
                    {
                        "claim_text": c.claim_text,
                        "verdict": c.verdict,
                        "ent_prob": c.entailment_prob,
                        "con_prob": c.contradiction_prob,
                        "neu_prob": c.neutral_prob,
                    }
                    for c in report.claim_results
                ],
            })

    with open(OUT_DIR / "evidence_verification_audit_predictions.jsonl", "w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    n_tot = len(predictions)
    rel_prec = rel_tp / (rel_tp + rel_fp) if (rel_tp + rel_fp) else 0.0
    rel_rec = rel_tp / (rel_tp + rel_fn) if (rel_tp + rel_fn) else 0.0

    summary = {
        "workstream": "G3 Independent Evidence Verification Stress Test",
        "sample_counts": {
            "total": n_tot,
            "supported": sup_total,
            "contradicted": con_total,
            "unsupported": unsup_total,
            "partially_supported": part_total,
        },
        "metrics": {
            "overall_gate_accuracy": round(accurate_decisions / n_tot, 4),
            "overall_gate_accuracy_95ci": wilson_ci(accurate_decisions, n_tot),
            "supported_acceptance_rate": round(sup_acc / sup_total, 4),
            "supported_acceptance_95ci": wilson_ci(sup_acc, sup_total),
            "false_abstention_rate": round((sup_total - sup_acc) / sup_total, 4),
            "false_abstention_95ci": wilson_ci(sup_total - sup_acc, sup_total),
            "contradiction_recall": round(con_rec / con_total, 4),
            "contradiction_recall_95ci": wilson_ci(con_rec, con_total),
            "unsupported_leakage_rate": round(unsup_leak / unsup_total, 4),
            "unsupported_leakage_95ci": wilson_ci(unsup_leak, unsup_total),
            "partially_supported_leakage_rate": round(part_leak / part_total, 4),
            "partially_supported_leakage_95ci": wilson_ci(part_leak, part_total),
            "release_precision": round(rel_prec, 4),
            "release_recall": round(rel_rec, 4),
        },
        "release_confusion_matrix": {"tp": rel_tp, "fp": rel_fp, "tn": rel_tn, "fn": rel_fn},
        "per_category_breakdown": cat_stats,
    }

    with open(OUT_DIR / "evidence_verification_audit_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run_evidence_audit()

