#!/usr/bin/env python3
"""Phase 35 Audit Script: Workstream C - Multilingual & Transliteration Generalization.

Evaluates MultilingualSemanticDefense across 9 language families (N=270):
1. English phonetic
2. Spanish code-switching
3. French code-switching
4. German code-switching
5. Russian romanized
6. Hindi Hinglish
7. Arabic Arabizi
8. Chinese Pinyin
9. Japanese Romaja

Reports:
- Separate Native-Script ADR and Transliteration ADR.
- Per-language family breakdown.
- Investigation of Phase 34 weak spots (Hinglish: 60%, Arabizi: 60%, Russian Romanized: 80%).
- Wilson 95% Confidence Intervals.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any, Dict, List

from trustrag.guardrails.multilingual_engine import MultilingualSemanticDefense

def wilson_interval(successes: int, total: int, z: float = 1.95996) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2.0 * total)) / denom
    margin = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4.0 * (total**2))))
    return max(0.0, center - margin), min(1.0, center + margin)

def run_workstream_c_audit():
    dataset_file = Path("reports/phase35/datasets/multilingual_holdout.jsonl")
    with dataset_file.open("r", encoding="utf-8") as f:
        samples = [json.loads(line) for line in f]

    multi = MultilingualSemanticDefense()

    predictions = []
    per_lang_stats: Dict[str, Dict[str, Any]] = {}

    total_native_attacks = 0
    detected_native_attacks = 0

    total_translit_attacks = 0
    detected_translit_attacks = 0

    print(f"Executing Multilingual Audit on {len(samples)} sealed samples across 9 languages...")

    for item in samples:
        cid = item["case_id"]
        lang = item["language"]
        stype = item["script_type"]
        text = item["text"]
        is_attack = item["is_attack"]

        if lang not in per_lang_stats:
            per_lang_stats[lang] = {
                "native_total": 0, "native_det": 0,
                "translit_total": 0, "translit_det": 0
            }

        t0 = time.perf_counter()
        res = multi.evaluate_query(text)
        lat_ms = (time.perf_counter() - t0) * 1000.0

        is_detected = res.is_attack

        if stype == "native":
            total_native_attacks += 1
            per_lang_stats[lang]["native_total"] += 1
            if is_detected:
                detected_native_attacks += 1
                per_lang_stats[lang]["native_det"] += 1
        else:
            total_translit_attacks += 1
            per_lang_stats[lang]["translit_total"] += 1
            if is_detected:
                detected_translit_attacks += 1
                per_lang_stats[lang]["translit_det"] += 1

        predictions.append({
            "case_id": cid,
            "language": lang,
            "script_type": stype,
            "is_attack": is_attack,
            "detected_attack": is_detected,
            "risk_score": round(res.risk_score, 4),
            "attack_category": res.attack_category,
            "detected_language": res.detected_language,
            "script_family": res.script_family,
            "matched_stems": res.matched_stems,
            "latency_ms": round(lat_ms, 3)
        })

    native_adr = detected_native_attacks / total_native_attacks if total_native_attacks else 0.0
    translit_adr = detected_translit_attacks / total_translit_attacks if total_translit_attacks else 0.0
    combined_adr = (detected_native_attacks + detected_translit_attacks) / (total_native_attacks + total_translit_attacks)

    nat_ci = wilson_interval(detected_native_attacks, total_native_attacks)
    trn_ci = wilson_interval(detected_translit_attacks, total_translit_attacks)
    cmb_ci = wilson_interval(detected_native_attacks + detected_translit_attacks, total_native_attacks + total_translit_attacks)

    lang_summary = {}
    for l, d in per_lang_stats.items():
        n_adr = d["native_det"] / d["native_total"] if d["native_total"] else 0.0
        t_adr = d["translit_det"] / d["translit_total"] if d["translit_total"] else 0.0
        c_adr = (d["native_det"] + d["translit_det"]) / (d["native_total"] + d["translit_total"])
        lang_summary[l] = {
            "native_adr": round(n_adr, 4),
            "translit_adr": round(t_adr, 4),
            "combined_adr": round(c_adr, 4),
            "native_detected": f"{d['native_det']}/{d['native_total']}",
            "translit_detected": f"{d['translit_det']}/{d['translit_total']}"
        }

    summary = {
        "workstream": "Workstream C - Multilingual & Transliteration Generalization",
        "sample_counts": {
            "total_samples": len(samples),
            "native_attacks": total_native_attacks,
            "translit_attacks": total_translit_attacks
        },
        "metrics": {
            "overall_native_adr": round(native_adr, 4),
            "overall_native_adr_95ci": [round(nat_ci[0], 4), round(nat_ci[1], 4)],
            "overall_translit_adr": round(translit_adr, 4),
            "overall_translit_adr_95ci": [round(trn_ci[0], 4), round(trn_ci[1], 4)],
            "overall_combined_adr": round(combined_adr, 4),
            "overall_combined_adr_95ci": [round(cmb_ci[0], 4), round(cmb_ci[1], 4)]
        },
        "per_language_breakdown": lang_summary
    }

    out_file = Path("reports/phase35/raw_predictions/multilingual_audit_predictions.jsonl")
    with out_file.open("w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")

    summary_file = Path("reports/phase35/raw_predictions/multilingual_audit_summary.json")
    with summary_file.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=== Workstream C: Multilingual Audit Complete ===")
    print(f"Overall Native-Script ADR:   {native_adr*100:.2f}% (CI: [{nat_ci[0]*100:.2f}%, {nat_ci[1]*100:.2f}%]) | {detected_native_attacks}/{total_native_attacks}")
    print(f"Overall Transliteration ADR: {translit_adr*100:.2f}% (CI: [{trn_ci[0]*100:.2f}%, {trn_ci[1]*100:.2f}%]) | {detected_translit_attacks}/{total_translit_attacks}")
    print(f"Overall Combined ADR:        {combined_adr*100:.2f}% (CI: [{cmb_ci[0]*100:.2f}%, {cmb_ci[1]*100:.2f}%]) | {detected_native_attacks+detected_translit_attacks}/{total_native_attacks+total_translit_attacks}")
    print("\nLanguage Family Detail:")
    for l, d in lang_summary.items():
        print(f"  - {l:12s} Native: {d['native_adr']*100:.1f}% ({d['native_detected']}) | Translit: {d['translit_adr']*100:.1f}% ({d['translit_detected']}) | Combined: {d['combined_adr']*100:.1f}%")

if __name__ == "__main__":
    run_workstream_c_audit()
