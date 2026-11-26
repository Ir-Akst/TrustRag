#!/usr/bin/env python3
"""Phase 39 Independent G1 Semantic Generalization Audit."""

import json
import math
import time
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


def run_g1_audit() -> None:
    dataset_path = Path("reports/phase39/datasets/g1_independent_holdout.jsonl")
    guardrail = InputGuardrail()

    predictions = []
    tp = fp = tn = fn = 0
    cat_stats: dict[str, dict] = {}
    detection_mechanism_counts = {"semantic_only": 0, "lexical_or_regex_only": 0, "both_semantic_and_regex": 0, "flag_only": 0}

    with open(dataset_path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            t0 = time.perf_counter()
            res = guardrail.evaluate(row["text"])
            lat_ms = round((time.perf_counter() - t0) * 1000.0, 3)

            blocked = res.decision == G1Decision.BLOCK
            gt = row["ground_truth"]
            codes = [c.value if hasattr(c, "value") else str(c) for c in res.reason_codes]

            if gt == "ATTACK":
                if blocked:
                    tp += 1
                    has_sem = "G1_SEMANTIC_ATTACK" in codes
                    has_lex = any(c in codes for c in ("G1_PROMPT_INJECTION", "G1_SUSPICIOUS_META_PATTERN", "G1_OBFUSCATION_DETECTED", "G1_MULTILINGUAL_ATTACK"))
                    if has_sem and has_lex:
                        detection_mechanism_counts["both_semantic_and_regex"] += 1
                    elif has_sem:
                        detection_mechanism_counts["semantic_only"] += 1
                    elif has_lex:
                        detection_mechanism_counts["lexical_or_regex_only"] += 1
                    else:
                        detection_mechanism_counts["flag_only"] += 1
                else:
                    fn += 1
            else:
                if blocked:
                    fp += 1
                else:
                    tn += 1

            cat = row["category"]
            if cat not in cat_stats:
                cat_stats[cat] = {"total": 0, "ground_truth": gt, "blocked": 0, "allowed": 0, "flagged": 0}
            cat_stats[cat]["total"] += 1
            if blocked:
                cat_stats[cat]["blocked"] += 1
            else:
                cat_stats[cat]["allowed"] += 1
                if res.decision == G1Decision.FLAG:
                    cat_stats[cat]["flagged"] += 1

            predictions.append({
                "case_id": row["case_id"],
                "category": cat,
                "ground_truth": gt,
                "decision": res.decision.value,
                "blocked": blocked,
                "risk_score": round(float(res.risk_score), 4),
                "reason_codes": codes,
                "latency_ms": lat_ms,
                "text": row["text"],
            })

    with open(OUT_DIR / "g1_semantic_audit_predictions.jsonl", "w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    attacks = tp + fn
    controls = tn + fp
    adr = tp / attacks if attacks else 0.0
    asr = fn / attacks if attacks else 0.0
    fpr = fp / controls if controls else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = adr
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0

    for cat, st in cat_stats.items():
        n = st["total"]
        if st["ground_truth"] == "ATTACK":
            st["adr"] = round(st["blocked"] / n, 4)
            st["adr_95ci"] = wilson_ci(st["blocked"], n)
        else:
            st["fpr"] = round(st["blocked"] / n, 4)
            st["fpr_95ci"] = wilson_ci(st["blocked"], n)

    summary = {
        "workstream": "G1 Independent Semantic Generalization Audit",
        "sample_counts": {"total": len(predictions), "attacks": attacks, "controls": controls},
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "metrics": {
            "adr": round(adr, 4),
            "adr_95ci": wilson_ci(tp, attacks),
            "asr": round(asr, 4),
            "asr_95ci": wilson_ci(fn, attacks),
            "fpr": round(fpr, 4),
            "fpr_95ci": wilson_ci(fp, controls),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
        },
        "detection_mechanism_breakdown": detection_mechanism_counts,
        "per_category_breakdown": cat_stats,
    }

    with open(OUT_DIR / "g1_semantic_audit_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run_g1_audit()
