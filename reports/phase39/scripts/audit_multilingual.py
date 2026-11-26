#!/usr/bin/env python3
"""Phase 39 Independent Multilingual Generalization Audit."""

import json
import math
from pathlib import Path
from trustrag.guardrails.input_guardrail import InputGuardrail, G1Decision

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


def run_multilingual_audit() -> None:
    dataset_path = Path("reports/phase39/datasets/multilingual_holdout.jsonl")
    guardrail = InputGuardrail()

    predictions = []
    per_lang: dict[str, dict] = {}
    tot_atk = tot_blk = tot_ben = tot_fp = 0
    cat_totals: dict[str, dict] = {}

    with open(dataset_path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            res = guardrail.evaluate(row["text"])
            blocked = res.decision == G1Decision.BLOCK
            lang = row["language"]
            cat = row["category"]
            gt = row["ground_truth"]

            if lang not in per_lang:
                per_lang[lang] = {
                    "attacks": 0, "blocked": 0, "benign": 0, "fp": 0,
                    "native_attack": [0, 0], "transliterated_unseen": [0, 0], "mixed_script_paraphrase": [0, 0]
                }
            if cat not in cat_totals:
                cat_totals[cat] = {"total": 0, "blocked": 0, "ground_truth": gt}
            cat_totals[cat]["total"] += 1
            if blocked:
                cat_totals[cat]["blocked"] += 1

            if gt == "ATTACK":
                tot_atk += 1
                per_lang[lang]["attacks"] += 1
                per_lang[lang][cat][1] += 1
                if blocked:
                    tot_blk += 1
                    per_lang[lang]["blocked"] += 1
                    per_lang[lang][cat][0] += 1
            else:
                tot_ben += 1
                per_lang[lang]["benign"] += 1
                if blocked:
                    tot_fp += 1
                    per_lang[lang]["fp"] += 1

            predictions.append({
                "case_id": row["case_id"],
                "language": lang,
                "category": cat,
                "ground_truth": gt,
                "decision": res.decision.value,
                "blocked": blocked,
                "reason_codes": [c.value if hasattr(c, "value") else str(c) for c in res.reason_codes],
                "text": row["text"],
            })

    with open(OUT_DIR / "multilingual_audit_predictions.jsonl", "w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    lang_summary = {}
    for lang, st in per_lang.items():
        atk_n = st["attacks"]
        ben_n = st["benign"]
        blk = st["blocked"]
        fp = st["fp"]
        lang_summary[lang] = {
            "attack_denominator": atk_n,
            "benign_denominator": ben_n,
            "adr": round(blk / atk_n, 4),
            "asr": round((atk_n - blk) / atk_n, 4),
            "adr_95ci": wilson_ci(blk, atk_n),
            "fpr": round(fp / ben_n, 4),
            "fpr_95ci": wilson_ci(fp, ben_n),
            "native_detected": f"{st['native_attack'][0]}/{st['native_attack'][1]}",
            "translit_unseen_detected": f"{st['transliterated_unseen'][0]}/{st['transliterated_unseen'][1]}",
            "mixed_paraphrase_detected": f"{st['mixed_script_paraphrase'][0]}/{st['mixed_script_paraphrase'][1]}",
        }

    summary = {
        "workstream": "Multilingual Independent Generalization Audit",
        "sample_counts": {"total": len(predictions), "attacks": tot_atk, "benign": tot_ben},
        "overall_metrics": {
            "overall_adr": round(tot_blk / tot_atk, 4),
            "overall_adr_95ci": wilson_ci(tot_blk, tot_atk),
            "overall_asr": round((tot_atk - tot_blk) / tot_atk, 4),
            "overall_fpr": round(tot_fp / tot_ben, 4),
            "overall_fpr_95ci": wilson_ci(tot_fp, tot_ben),
        },
        "per_category_totals": {
            k: {
                "total": v["total"],
                "blocked": v["blocked"],
                "rate": round(v["blocked"] / v["total"], 4),
                "ci_95": wilson_ci(v["blocked"], v["total"]),
            }
            for k, v in cat_totals.items()
        },
        "per_language_breakdown": lang_summary,
    }

    with open(OUT_DIR / "multilingual_audit_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run_multilingual_audit()
