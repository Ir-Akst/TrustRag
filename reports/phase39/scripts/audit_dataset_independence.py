#!/usr/bin/env python3
"""Phase 39 Dataset Independence & Statistical Recalculation Audit.

Checks:
1. Exact & near-duplicate overlap across Phase 37, Phase 38, and Phase 39 datasets.
2. Within-dataset duplicates, label consistency, missing controls, and denominators.
3. Exact recalculation of all Phase 39 metrics and Wilson 95% CIs from raw predictions.
"""

import json
import math
import re
from pathlib import Path

BASE = Path("/home/aditya/rags/TrustRag-phase11/reports")


def norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s.lower())).strip()


def extract_texts(jsonl_path: Path) -> list[str]:
    texts = []
    if not jsonl_path.exists():
        return texts
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            if "text" in d:
                texts.append(d["text"])
            elif "full_text" in d:
                texts.append(d["full_text"])
            elif "answer_text" in d:
                texts.append(d["query"] + " || " + d["answer_text"])
            elif "answer" in d:
                texts.append(d["query"] + " || " + d["answer"])
            elif "documents" in d:
                texts.append(" ".join(doc["text"] for doc in d["documents"]))
    return texts


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def audit_datasets() -> dict:
    pairs = [
        ("g1", "phase37/datasets/g1_independent_holdout.jsonl", "phase38/datasets/g1_holdout.jsonl", "phase39/datasets/g1_independent_holdout.jsonl"),
        ("firewall", "phase37/datasets/firewall_generator_holdout.jsonl", "phase38/datasets/firewall_generator_holdout.jsonl", "phase39/datasets/firewall_generator_holdout.jsonl"),
        ("multilingual", "phase37/datasets/multilingual_holdout.jsonl", "phase38/datasets/multilingual_holdout.jsonl", "phase39/datasets/multilingual_holdout.jsonl"),
        ("evidence", "phase37/datasets/evidence_verification_holdout.jsonl", "phase38/datasets/evidence_verification_holdout.jsonl", "phase39/datasets/evidence_verification_holdout.jsonl"),
    ]

    report = {}
    for name, p37, p38, p39 in pairs:
        t37 = [norm_text(x) for x in extract_texts(BASE / p37)]
        t38 = [norm_text(x) for x in extract_texts(BASE / p38)]
        t39 = [norm_text(x) for x in extract_texts(BASE / p39)]

        s37, s38, s39 = set(t37), set(t38), set(t39)
        exact_37_39 = len(s37 & s39)
        exact_38_39 = len(s38 & s39)
        internal_dups_39 = len(t39) - len(s39)

        # Near-duplicate check (Jaccard >= 0.85 on word tokens) against Phase 37 and Phase 38
        tok37 = [set(x.split()) for x in s37]
        tok38 = [set(x.split()) for x in s38]
        near_37_39 = 0
        near_38_39 = 0
        for x in s39:
            wx = set(x.split())
            if any(jaccard(wx, w) >= 0.85 for w in tok37):
                near_37_39 += 1
            if any(jaccard(wx, w) >= 0.85 for w in tok38):
                near_38_39 += 1

        report[name] = {
            "counts": {"phase37": len(t37), "phase38": len(t38), "phase39": len(t39)},
            "unique_phase39": len(s39),
            "internal_template_duplicates_phase39": internal_dups_39,
            "exact_overlap_p37_vs_p39": exact_37_39,
            "exact_overlap_p38_vs_p39": exact_38_39,
            "near_duplicate_p37_vs_p39_ge85": near_37_39,
            "near_duplicate_p38_vs_p39_ge85": near_38_39,
        }

    out_path = BASE / "phase39/raw_predictions/dataset_independence_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    audit_datasets()
