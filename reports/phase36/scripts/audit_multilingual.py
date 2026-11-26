#!/usr/bin/env python3
"""Phase 36 Evaluation: Workstream C - Multilingual & Transliteration Defense."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Dict

from trustrag.guardrails.multilingual_engine import MultilingualSemanticDefense

def wilson_interval(successes: int, total: int, z: float = 1.95996) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2.0 * total)) / denom
    margin = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4.0 * (total**2))))
    return max(0.0, center - margin), min(1.0, center + margin)

def evaluate_multilingual():
    dataset_path = Path("reports/phase36/datasets/multilingual_holdout.jsonl")
    pred_path = Path("reports/phase36/raw_predictions/multilingual_audit_predictions.jsonl")
    summary_path = Path("reports/phase36/raw_predictions/multilingual_audit_summary.json")

    with dataset_path.open("r", encoding="utf-8") as f:
        samples = [json.loads(line) for line in f]

    engine = MultilingualSemanticDefense()
    predictions = []

    per_lang_stats: Dict[str, Dict[str, int]] = {}
    total_native = 0
    detected_native = 0
    total_translit = 0
    detected_translit = 0

    for s in samples:
        cid = s["case_id"]
        lang = s["language"]
        stype = s["script_type"]
        is_attack = s["is_attack"]
        text = s["text"]

        if lang not in per_lang_stats:
            per_lang_stats[lang] = {
                "native_total": 0, "native_detected": 0,
                "translit_total": 0, "translit_detected": 0
            }

        t0 = time.perf_counter()
        res = engine.evaluate_query(text)
        lat_ms = (time.perf_counter() - t0) * 1000.0

        if stype == "native":
            total_native += 1
            per_lang_stats[lang]["native_total"] += 1
            if res.is_attack:
                detected_native += 1
                per_lang_stats[lang]["native_detected"] += 1
        else:
            total_translit += 1
            per_lang_stats[lang]["translit_total"] += 1
            if res.is_attack:
                detected_translit += 1
                per_lang_stats[lang]["translit_detected"] += 1

        predictions.append({
            "case_id": cid,
            "language": lang,
            "script_type": stype,
            "text": text,
            "is_attack": is_attack,
            "detected_as_attack": res.is_attack,
            "risk_score": res.risk_score,
            "matched_stems": res.matched_stems,
            "category": res.attack_category,
            "latency_ms": round(lat_ms, 3)
        })

    with pred_path.open("w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")

    overall_native_adr = detected_native / total_native if total_native else 0.0
    overall_translit_adr = detected_translit / total_translit if total_translit else 0.0
    overall_combined_adr = (detected_native + detected_translit) / (total_native + total_translit)

    native_ci = wilson_interval(detected_native, total_native)
    translit_ci = wilson_interval(detected_translit, total_translit)
    comb_ci = wilson_interval(detected_native + detected_translit, total_native + total_translit)

    breakdown = {}
    for lang, counts in per_lang_stats.items():
        n_adr = counts["native_detected"] / counts["native_total"] if counts["native_total"] else 0.0
        t_adr = counts["translit_detected"] / counts["translit_total"] if counts["translit_total"] else 0.0
        c_adr = (counts["native_detected"] + counts["translit_detected"]) / (counts["native_total"] + counts["translit_total"])
        breakdown[lang] = {
            "native_adr": round(n_adr, 4),
            "translit_adr": round(t_adr, 4),
            "combined_adr": round(c_adr, 4),
            "native_detected": f"{counts['native_detected']}/{counts['native_total']}",
            "translit_detected": f"{counts['translit_detected']}/{counts['translit_total']}"
        }

    summary = {
        "workstream": "Workstream C - Multilingual & Transliteration Generalization",
        "sample_counts": {
            "total_samples": len(samples),
            "native_attacks": total_native,
            "translit_attacks": total_translit
        },
        "metrics": {
            "overall_native_adr": round(overall_native_adr, 4),
            "overall_native_adr_95ci": [round(native_ci[0], 4), round(native_ci[1], 4)],
            "overall_translit_adr": round(overall_translit_adr, 4),
            "overall_translit_adr_95ci": [round(translit_ci[0], 4), round(translit_ci[1], 4)],
            "overall_combined_adr": round(overall_combined_adr, 4),
            "overall_combined_adr_95ci": [round(comb_ci[0], 4), round(comb_ci[1], 4)]
        },
        "per_language_breakdown": breakdown
    }

    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("Multilingual Evaluation Complete:", json.dumps(summary["metrics"], indent=2))

if __name__ == "__main__":
    evaluate_multilingual()

