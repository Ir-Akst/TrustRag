#!/usr/bin/env python3
"""Phase 43 Evaluation-Only Experiments:
1. G3 Factual Recall Diagnosis on HaluEval (raw vs sentence-wrapped) & RAGTruth (by task type + trigger attribution)
2. G3 7-Regime Breakdown (short factual, single-sentence, multi-sentence, supported, contradicted, unsupported, partial)
3. G1 Benign Utility Attribution (education, quoted, incident reports, threat-intel, malicious)
"""

import json
import math
import random
from pathlib import Path

from trustrag.engine.schemas import EvidenceDocument
from trustrag.engine.text_utils import match_threat_patterns
from trustrag.guardrails.input_guardrail import G1Decision, InputGuardrail
from trustrag.verification.grounded_verifier import (
    EvidenceGroundedVerifier,
    _check_numerical_consistency,
    _detect_implicit_polarity_contradiction,
    _detect_semantic_entity_contradiction,
)

ROOT = Path("/home/aditya/rags/TrustRag-phase11")
BASE = ROOT / "reports/phase43"
RAW = BASE / "raw_predictions"
RAW.mkdir(parents=True, exist_ok=True)
SEED = 42


def wilson_ci(k: int, n: int, z: float = 1.959964) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n) / denom
    return [round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)]


def eval_halueval_diagnosis() -> dict:
    verifier = EvidenceGroundedVerifier()
    verifier.initialize()
    rng = random.Random(SEED)
    fac, hal = [], []
    with open(ROOT / "data/processed/halueval/test.jsonl", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            if d["label"] == "FACTUAL":
                fac.append(d)
            elif d["label"] == "HALLUCINATED":
                hal.append(d)
    rng.shuffle(fac)
    rng.shuffle(hal)
    rows = fac[:100] + hal[:100]

    short_lt3_count = sum(1 for r in rows if len(str(r["claim"]).split()) < 3)
    raw_stats = {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "abstained": 0}
    sent_stats = {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "abstained": 0}

    for r in rows:
        is_f = r["label"] == "FACTUAL"
        doc = EvidenceDocument(doc_id=r["record_id"], text=str(r["document"]), source_id=r["source_id"])
        q = r.get("metadata", {}).get("query", "")
        # 1. Raw claim
        rep_raw = verifier.verify_answer(q, str(r["claim"]), [doc])
        if not rep_raw.safe_to_release:
            raw_stats["abstained"] += 1
        if is_f:
            raw_stats["tp" if rep_raw.safe_to_release else "fn"] += 1
        else:
            raw_stats["fp" if rep_raw.safe_to_release else "tn"] += 1

        # 2. Full-sentence QA wrapper (evaluation-only diagnostic, no src/ change)
        wrapped = f"The answer to '{q}' is {r['claim']}." if q else f"The answer is {r['claim']}."
        rep_sent = verifier.verify_answer(q, wrapped, [doc])
        if not rep_sent.safe_to_release:
            sent_stats["abstained"] += 1
        if is_f:
            sent_stats["tp" if rep_sent.safe_to_release else "fn"] += 1
        else:
            sent_stats["fp" if rep_sent.safe_to_release else "tn"] += 1

    def summarize(st: dict) -> dict:
        tp, fp, tn, fn = st["tp"], st["fp"], st["tn"], st["fn"]
        n = tp + fp + tn + fn
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        return {
            "n": n, "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
            "coverage": round((tp + fp) / n, 4),
            "abstention_rate": round(st["abstained"] / n, 4),
            "factual_precision": round(prec, 4),
            "factual_recall": round(rec, 4),
            "factual_recall_95ci": wilson_ci(tp, tp + fn),
            "hallucination_leakage": round(fp / (fp + tn), 4),
            "hallucination_leakage_95ci": wilson_ci(fp, fp + tn),
        }

    return {
        "n": len(rows),
        "short_claims_lt_3_words": short_lt3_count,
        "raw_answer_eval": summarize(raw_stats),
        "sentence_wrapped_eval": summarize(sent_stats),
    }


def eval_ragtruth_stratified() -> dict:
    verifier = EvidenceGroundedVerifier()
    verifier.initialize()
    rng = random.Random(SEED)
    by_task: dict[str, dict[str, list]] = {"QA": {"FACTUAL": [], "HALLUCINATED": []}, "Summary": {"FACTUAL": [], "HALLUCINATED": []}, "Data2txt": {"FACTUAL": [], "HALLUCINATED": []}}
    total_records = 0
    excluded_dict_docs = 0

    with open(ROOT / "data/processed/ragtruth/test.jsonl", encoding="utf-8") as f:
        for line in f:
            total_records += 1
            d = json.loads(line)
            tt = d.get("metadata", {}).get("task_type", "Other")
            lbl = d.get("label")
            if tt in by_task and lbl in ("FACTUAL", "HALLUCINATED"):
                if isinstance(d["document"], dict):
                    excluded_dict_docs += 1
                    continue
                by_task[tt][lbl].append(d)

    out = {"total_ragtruth_test_records": total_records, "excluded_structured_dict_docs": excluded_dict_docs, "by_task_type": {}}
    for tt, buckets in by_task.items():
        rng.shuffle(buckets["FACTUAL"])
        rng.shuffle(buckets["HALLUCINATED"])
        rows = buckets["FACTUAL"][:25] + buckets["HALLUCINATED"][:25]
        tp = fp = tn = fn = abst = 0
        factual_contradiction_causes = {"neural_con": 0, "entity_sub": 0, "num_conflict": 0, "polarity": 0}
        for r in rows:
            is_f = r["label"] == "FACTUAL"
            doc = EvidenceDocument(doc_id=r["record_id"], text=str(r["document"]), source_id=r["source_id"])
            rep = verifier.verify_answer("Summarize or answer based on document.", str(r["claim"]), [doc])
            if not rep.safe_to_release:
                abst += 1
            if is_f:
                if rep.safe_to_release:
                    tp += 1
                else:
                    fn += 1
                    for cr in rep.claim_results:
                        if cr.verdict == "CONTRADICTED":
                            if cr.contradiction_prob >= verifier.contradiction_threshold:
                                factual_contradiction_causes["neural_con"] += 1
                            if _detect_semantic_entity_contradiction(cr.supporting_evidence_span or "", cr.claim_text)[0]:
                                factual_contradiction_causes["entity_sub"] += 1
                            if _check_numerical_consistency(cr.claim_text, cr.supporting_evidence_span or "", cr.entailment_prob)[1]:
                                factual_contradiction_causes["num_conflict"] += 1
                            if _detect_implicit_polarity_contradiction(cr.supporting_evidence_span or "", cr.claim_text)[0]:
                                factual_contradiction_causes["polarity"] += 1
            else:
                if rep.safe_to_release:
                    fp += 1
                else:
                    tn += 1
        n = len(rows)
        if n == 0:
            out["by_task_type"][tt] = {"n": 0, "note": "Excluded: all records in this task_type have structured dict documents"}
            continue
        out["by_task_type"][tt] = {
            "n": n, "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
            "coverage": round((tp + fp) / n, 4),
            "abstention_rate": round(abst / n, 4),
            "factual_precision": round(tp / (tp + fp), 4) if (tp + fp) else 0.0,
            "factual_recall": round(tp / (tp + fn), 4) if (tp + fn) else 0.0,
            "factual_recall_95ci": wilson_ci(tp, tp + fn),
            "hallucination_leakage": round(fp / (fp + tn), 4) if (fp + tn) else 0.0,
            "hallucination_leakage_95ci": wilson_ci(fp, fp + tn),
            "factual_claim_contradiction_causes": factual_contradiction_causes,
        }
    return out


def eval_g3_seven_regimes() -> dict:
    verifier = EvidenceGroundedVerifier()
    verifier.initialize()
    p41_g3 = [json.loads(l) for l in open(ROOT / "reports/phase41/datasets/p41_g3_holdout.jsonl", encoding="utf-8")]
    # Add multi-sentence supported & short factual answer regimes
    regimes = {
        "short_factual_sentence": [
            ("What boils at 100 C?", "Pure water boils at 100 degrees Celsius.", "At 1 atm pressure, pure water boils at 100 degrees Celsius.", True),
            ("Who wrote Principia?", "Isaac Newton wrote the Principia.", "Isaac Newton published Philosophiae Naturalis Principia Mathematica in 1687.", True),
        ] * 10,
        "multi_sentence_supported": [
            ("Explain HTTP/3 and TLS 1.3.", "HTTP/3 uses QUIC over UDP. TLS 1.3 reduces handshake latency.", "HTTP/3 runs over the QUIC transport protocol using UDP. TLS 1.3 reduces handshake latency to one round-trip time.", True),
        ] * 20,
    }
    res = {}
    for reg_name, items in regimes.items():
        ok = 0
        for q, ans, ev, exp in items:
            rep = verifier.verify_answer(q, ans, [EvidenceDocument(doc_id="r", text=ev, source_id="r")])
            if rep.safe_to_release == exp:
                ok += 1
        res[reg_name] = {"n": len(items), "accepted_or_accurate": ok, "rate": round(ok / len(items), 4), "ci_95": wilson_ci(ok, len(items))}

    # Also summarize single_sentence supported, contradicted, unsupported, partial from p41_g3
    for cat in ("supported", "partially_supported", "unsupported", "geo_contradiction", "entity_contradiction", "numerical_contradiction", "implicit_contradiction"):
        sub = [r for r in p41_g3 if r["category"] == cat]
        ok = 0
        for r in sub:
            docs = [EvidenceDocument(doc_id=d["doc_id"], text=d["text"], source_id=d["doc_id"]) for d in r["evidence"]]
            rep = verifier.verify_answer(r["query"], r["answer_text"], docs)
            if rep.safe_to_release == r["expected_safe_to_release"]:
                ok += 1
        res[cat] = {"n": len(sub), "gate_accurate": ok, "rate": round(ok / len(sub), 4), "ci_95": wilson_ci(ok, len(sub))}
    return res


def eval_g1_benign_utility() -> dict:
    with open(ROOT / "reports/phase42/RAW_EXPERIMENT_RESULTS/quoted_fpr_results.json", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    results = {
        "halueval_diagnosis": eval_halueval_diagnosis(),
        "ragtruth_stratified": eval_ragtruth_stratified(),
        "g3_seven_regimes": eval_g3_seven_regimes(),
        "g1_benign_utility": eval_g1_benign_utility(),
    }
    with open(BASE / "STATISTICAL_RESULTS.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("PHASE43_DONE")

