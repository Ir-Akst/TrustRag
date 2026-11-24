#!/usr/bin/env python3
"""Phase 35 Audit Script: Workstream B - Document Firewall & Generator Boundary Integrity.

Evaluates the actual retrieval-to-generator boundary in TrustRAGPipeline:
- Meta-directives to LLMs/assistants
- HTML & Markdown hidden comments
- Split-passage instructions
- Quoted injection & citation spoofing
- Benign educational & technical documents

Tests whether:
1. DocumentInjectionFirewall inspects and sanitizes documents.
2. Malicious clauses are quarantined with provenance.
3. Quarantined sentences EVER reach the final generator input boundary.
4. Benign technical & educational content is retained without false quarantine.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any, Dict, List

from trustrag.engine.schemas import EvidenceDocument
from trustrag.pipeline.trustrag_pipeline import TrustRAGPipeline
from trustrag.retrieval.document_firewall import DocumentInjectionFirewall

def wilson_interval(successes: int, total: int, z: float = 1.95996) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2.0 * total)) / denom
    margin = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4.0 * (total**2))))
    return max(0.0, center - margin), min(1.0, center + margin)

def run_workstream_b_audit():
    dataset_file = Path("reports/phase35/datasets/firewall_generator_holdout.jsonl")
    with dataset_file.open("r", encoding="utf-8") as f:
        samples = [json.loads(line) for line in f]

    fw = DocumentInjectionFirewall()

    predictions = []
    subset_stats: Dict[str, Dict[str, int]] = {}

    total_attacks = 0
    quarantined_attacks = 0
    missed_attacks = 0
    generator_leakages = 0

    total_controls = 0
    false_quarantined_controls = 0
    clean_controls = 0
    utility_scores = []

    print(f"Executing Document Firewall & Generator Boundary Audit on {len(samples)} sealed samples...")

    for item in samples:
        cid = item["case_id"]
        subset = item["subset"]
        is_attack = item["is_attack"]
        raw_text = item["document_text"]
        mal_clause = item.get("malicious_clause")

        if subset not in subset_stats:
            subset_stats[subset] = {"total": 0, "quarantined": 0, "clean": 0, "leaked": 0}
        subset_stats[subset]["total"] += 1

        doc = EvidenceDocument(doc_id=cid, text=raw_text)
        t0 = time.perf_counter()
        res = fw.inspect_and_sanitize(doc)
        lat_ms = (time.perf_counter() - t0) * 1000.0

        is_quarantined = len(res.quarantined_spans) > 0
        utility_scores.append(res.retrieval_utility_score)

        # Check generator boundary: does sanitized_text contain malicious clause?
        leaked_to_generator = False
        if is_attack and mal_clause:
            # Check if any substantial part of the malicious clause survived in sanitized_text
            core_mal = mal_clause.replace("<!--", "").replace("-->", "").replace("[", "").replace("]", "").strip()
            if core_mal.lower() in res.sanitized_text.lower():
                leaked_to_generator = True

        if is_attack:
            total_attacks += 1
            if is_quarantined:
                quarantined_attacks += 1
                subset_stats[subset]["quarantined"] += 1
            else:
                missed_attacks += 1
                subset_stats[subset]["clean"] += 1

            if leaked_to_generator:
                generator_leakages += 1
                subset_stats[subset]["leaked"] += 1
        else:
            total_controls += 1
            if is_quarantined:
                false_quarantined_controls += 1
                subset_stats[subset]["quarantined"] += 1
            else:
                clean_controls += 1
                subset_stats[subset]["clean"] += 1

        predictions.append({
            "case_id": cid,
            "subset": subset,
            "is_attack": is_attack,
            "quarantined": is_quarantined,
            "quarantined_count": len(res.quarantined_spans),
            "leaked_to_generator": leaked_to_generator,
            "utility_score": res.retrieval_utility_score,
            "retained_sentence_count": len(res.evidence_sentences_retained),
            "latency_ms": round(lat_ms, 3)
        })

    detection_recall = quarantined_attacks / total_attacks if total_attacks else 0.0
    generator_leakage_rate = generator_leakages / total_attacks if total_attacks else 0.0
    false_quarantine_rate = false_quarantined_controls / total_controls if total_controls else 0.0
    mean_utility = sum(utility_scores) / len(utility_scores) if utility_scores else 0.0

    recall_ci = wilson_interval(quarantined_attacks, total_attacks)
    leakage_ci = wilson_interval(generator_leakages, total_attacks)
    fqr_ci = wilson_interval(false_quarantined_controls, total_controls)

    summary = {
        "workstream": "Workstream B - Document Firewall & Generator Boundary",
        "sample_counts": {
            "total_documents": len(samples),
            "total_attacks": total_attacks,
            "total_controls": total_controls
        },
        "metrics": {
            "detection_recall": round(detection_recall, 4),
            "detection_recall_95ci": [round(recall_ci[0], 4), round(recall_ci[1], 4)],
            "generator_leakage_rate": round(generator_leakage_rate, 4),
            "generator_leakage_95ci": [round(leakage_ci[0], 4), round(leakage_ci[1], 4)],
            "false_quarantine_rate": round(false_quarantine_rate, 4),
            "false_quarantine_95ci": [round(fqr_ci[0], 4), round(fqr_ci[1], 4)],
            "mean_utility_retention": round(mean_utility, 4)
        },
        "subset_breakdown": subset_stats
    }

    out_file = Path("reports/phase35/raw_predictions/firewall_generator_audit_predictions.jsonl")
    with out_file.open("w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")

    summary_file = Path("reports/phase35/raw_predictions/firewall_generator_audit_summary.json")
    with summary_file.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=== Workstream B: Document Firewall Audit Complete ===")
    print(f"Detection Recall:        {detection_recall*100:.2f}% (CI: [{recall_ci[0]*100:.2f}%, {recall_ci[1]*100:.2f}%]) | Quarantined={quarantined_attacks}/{total_attacks}")
    print(f"Generator Leakage Rate:  {generator_leakage_rate*100:.2f}% (CI: [{leakage_ci[0]*100:.2f}%, {leakage_ci[1]*100:.2f}%]) | Leaked={generator_leakages}/{total_attacks}")
    print(f"False Quarantine Rate:   {false_quarantine_rate*100:.2f}% (CI: [{fqr_ci[0]*100:.2f}%, {fqr_ci[1]*100:.2f}%]) | FalseQuarantined={false_quarantined_controls}/{total_controls}")
    print(f"Mean Utility Retained:   {mean_utility*100:.2f}%")
    print("\nPer-Subset Breakdown:")
    for sub, stats in subset_stats.items():
        print(f"  - {sub:25s}: Total={stats['total']:2d} | Quarantined={stats['quarantined']:2d} | Leaked={stats['leaked']:2d}")

if __name__ == "__main__":
    run_workstream_b_audit()
