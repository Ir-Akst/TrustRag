import json, time, math
from trustrag.guardrails.multilingual_engine import MultilingualSemanticDefense

def wilson_score_interval(k, n, confidence=0.95):
    if n == 0:
        return 0.0, 0.0
    z = 1.959963984540054
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return round(max(0.0, centre - spread), 4), round(min(1.0, centre + spread), 4)

def run_multilingual_audit():
    dataset_path = "reports/phase38/datasets/multilingual_holdout.jsonl"
    pred_path = "reports/phase38/raw_predictions/multilingual_audit_predictions.jsonl"
    summary_path = "reports/phase38/raw_predictions/multilingual_audit_summary.json"

    engine = MultilingualSemanticDefense()

    with open(dataset_path) as f:
        records = [json.loads(line) for line in f]

    predictions = []
    lang_stats = {}
    total_native_tp = total_native_n = 0
    total_translit_tp = total_translit_n = 0

    for item in records:
        cid = item["case_id"]
        lang = item["language"]
        script_type = item["script_type"]
        text = item["text"]
        is_attack = (item["ground_truth"] == "ATTACK")

        t0 = time.perf_counter()
        assessment = engine.evaluate_query(text)
        lat = (time.perf_counter() - t0) * 1000.0

        detected = assessment.is_attack

        lang_stats.setdefault(lang, {
            "native_total": 0, "native_tp": 0,
            "translit_total": 0, "translit_tp": 0
        })

        if script_type == "native":
            total_native_n += 1
            lang_stats[lang]["native_total"] += 1
            if detected:
                total_native_tp += 1
                lang_stats[lang]["native_tp"] += 1
        else:
            total_translit_n += 1
            lang_stats[lang]["translit_total"] += 1
            if detected:
                total_translit_tp += 1
                lang_stats[lang]["translit_tp"] += 1

        predictions.append({
            "case_id": cid,
            "language": lang,
            "script_type": script_type,
            "text": text,
            "is_attack": is_attack,
            "detected_as_attack": detected,
            "risk_score": round(assessment.risk_score, 4),
            "matched_stems": assessment.matched_stems,
            "category": assessment.attack_category,
            "latency_ms": round(lat, 3)
        })

    with open(pred_path, "w") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")

    native_adr = total_native_tp / total_native_n if total_native_n > 0 else 0.0
    translit_adr = total_translit_tp / total_translit_n if total_translit_n > 0 else 0.0
    comb_adr = (total_native_tp + total_translit_tp) / (total_native_n + total_translit_n)

    per_lang_summary = {}
    for l, d in lang_stats.items():
        n_adr = d["native_tp"] / d["native_total"] if d["native_total"] > 0 else 0.0
        t_adr = d["translit_tp"] / d["translit_total"] if d["translit_total"] > 0 else 0.0
        c_adr = (d["native_tp"] + d["translit_tp"]) / (d["native_total"] + d["translit_total"])
        per_lang_summary[l] = {
            "native_adr": round(n_adr, 4),
            "translit_adr": round(t_adr, 4),
            "combined_adr": round(c_adr, 4),
            "native_detected": f"{d['native_tp']}/{d['native_total']}",
            "translit_detected": f"{d['translit_tp']}/{d['translit_total']}"
        }

    summary = {
        "workstream": "Workstream C - Multilingual Generalization Audit",
        "sample_counts": {
            "total_samples": len(records),
            "native_attacks": total_native_n,
            "translit_attacks": total_translit_n
        },
        "metrics": {
            "overall_native_adr": round(native_adr, 4),
            "overall_native_adr_95ci": wilson_score_interval(total_native_tp, total_native_n),
            "overall_translit_adr": round(translit_adr, 4),
            "overall_translit_adr_95ci": wilson_score_interval(total_translit_tp, total_translit_n),
            "overall_combined_adr": round(comb_adr, 4),
            "overall_combined_adr_95ci": wilson_score_interval(total_native_tp + total_translit_tp, len(records))
        },
        "per_language_breakdown": per_lang_summary
    }

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("=== MULTILINGUAL AUDIT RESULTS ===")
    print(f"Total: {len(records)} across {len(lang_stats)} languages")
    print(f"Native ADR: {native_adr:.4f} (95% CI: {summary['metrics']['overall_native_adr_95ci']})")
    print(f"Translit ADR: {translit_adr:.4f} (95% CI: {summary['metrics']['overall_translit_adr_95ci']})")
    print(f"Combined ADR: {comb_adr:.4f} (95% CI: {summary['metrics']['overall_combined_adr_95ci']})")
    for l, d in per_lang_summary.items():
        print(f"  {l}: Native={d['native_detected']}, Translit={d['translit_detected']}")

if __name__ == "__main__":
    run_multilingual_audit()
