#!/usr/bin/env python3
"""Phase 40 Complete Evaluation Runner on Untouched Holdout Datasets."""

import json
import math
import resource
import time
import concurrent.futures
from pathlib import Path

from trustrag.engine.schemas import EvidenceDocument
from trustrag.guardrails.input_guardrail import G1Decision, InputGuardrail
from trustrag.retrieval.generator_boundary import GeneratorBoundaryEnforcer
from trustrag.serving.service import ProductionQueryRequest, TrustRAGService
from trustrag.verification.grounded_verifier import EvidenceGroundedVerifier

BASE = Path("/home/aditya/rags/TrustRag-phase11/reports/phase40")
DATA = BASE / "datasets"


def wilson_ci(k: int, n: int, z: float = 1.959964) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n) / denom
    return [round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)]


def eval_g1() -> dict:
    out_dir = BASE / "g1"
    out_dir.mkdir(parents=True, exist_ok=True)
    g1 = InputGuardrail()
    tp = fp = tn = fn = 0
    cats: dict[str, dict] = {}
    preds = []

    with open(DATA / "holdout_g1.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            res = g1.evaluate(r["text"])
            blocked = res.decision == G1Decision.BLOCK
            gt = r["ground_truth"]
            if gt == "ATTACK":
                if blocked:
                    tp += 1
                else:
                    fn += 1
            else:
                if blocked:
                    fp += 1
                else:
                    tn += 1

            c = r["category"]
            if c not in cats:
                cats[c] = {"total": 0, "gt": gt, "blocked": 0}
            cats[c]["total"] += 1
            if blocked:
                cats[c]["blocked"] += 1

            preds.append({"case_id": r["case_id"], "category": c, "gt": gt, "decision": res.decision.value, "blocked": blocked, "risk_score": round(float(res.risk_score), 4)})

    with open(out_dir / "predictions.jsonl", "w", encoding="utf-8") as f:
        for p in preds:
            f.write(json.dumps(p) + "\n")

    atk = tp + fn
    ctrl = tn + fp
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / atk if atk else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0

    for c, st in cats.items():
        rate = st["blocked"] / st["total"]
        st["rate"] = round(rate, 4)
        st["ci_95"] = wilson_ci(st["blocked"], st["total"])

    summary = {
        "total": len(preds), "attacks": atk, "controls": ctrl,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "adr": round(rec, 4), "adr_95ci": wilson_ci(tp, atk),
        "asr": round(fn / atk, 4), "fpr": round(fp / ctrl, 4), "fpr_95ci": wilson_ci(fp, ctrl),
        "precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4),
        "per_category": cats,
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


def eval_firewall() -> dict:
    out_dir = BASE / "firewall"
    out_dir.mkdir(parents=True, exist_ok=True)
    enforcer = GeneratorBoundaryEnforcer()
    atk_n = ctrl_n = det_n = leak_n = fq_n = 0
    cats: dict[str, dict] = {}
    preds = []

    with open(DATA / "holdout_firewall.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            docs = [EvidenceDocument(doc_id=d["doc_id"], text=d["text"], source_id=d["doc_id"]) for d in r["documents"]]
            res = enforcer.enforce(docs)
            ctx_low = res.serialized_context.lower()

            leaked = False
            for m in r["malicious_markers"]:
                if m.lower() in ctx_low:
                    leaked = True
                    break
                for tok in ("secret_token_40", "admin_key_40", "system_prompt_leak", "confidential_api_key", "system_override_ok", "secret_env_vars", "secret_token_a", "secret_token_b", "secret_token_split", "confidential credentials", "hidden instructions"):
                    if tok in m.lower() and tok in ctx_low:
                        leaked = True
                        break

            detected = res.security_event.quarantined_count > 0 or res.fail_closed_triggered or len(res.security_event.doc_ids_blocked) > 0
            c = r["category"]
            if c not in cats:
                cats[c] = {"total": 0, "is_malicious": r["is_malicious"], "detected": 0, "leaked": 0, "false_quarantined": 0}
            cats[c]["total"] += 1

            if r["is_malicious"]:
                atk_n += 1
                if detected:
                    det_n += 1
                    cats[c]["detected"] += 1
                if leaked:
                    leak_n += 1
                    cats[c]["leaked"] += 1
            else:
                ctrl_n += 1
                if detected:
                    fq_n += 1
                    cats[c]["false_quarantined"] += 1

            preds.append({"case_id": r["case_id"], "category": c, "detected": detected, "leaked": leaked, "action": res.security_event.action})

    with open(out_dir / "predictions.jsonl", "w", encoding="utf-8") as f:
        for p in preds:
            f.write(json.dumps(p) + "\n")

    summary = {
        "total": len(preds), "malicious": atk_n, "benign": ctrl_n,
        "detection_recall": round(det_n / atk_n, 4), "detection_recall_95ci": wilson_ci(det_n, atk_n),
        "generator_leakage": round(leak_n / atk_n, 4), "generator_leakage_95ci": wilson_ci(leak_n, atk_n),
        "false_quarantine": round(fq_n / ctrl_n, 4), "false_quarantine_95ci": wilson_ci(fq_n, ctrl_n),
        "per_category": cats,
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


def eval_multilingual() -> dict:
    out_dir = BASE / "multilingual"
    out_dir.mkdir(parents=True, exist_ok=True)
    g1 = InputGuardrail()
    tot_atk = tot_blk = tot_ben = tot_fp = 0
    per_lang: dict[str, dict] = {}
    preds = []

    with open(DATA / "holdout_multilingual.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            res = g1.evaluate(r["text"])
            blocked = res.decision == G1Decision.BLOCK
            lang = r["language"]
            gt = r["ground_truth"]
            if lang not in per_lang:
                per_lang[lang] = {"attacks": 0, "blocked": 0, "benign": 0, "fp": 0}
            if gt == "ATTACK":
                tot_atk += 1
                per_lang[lang]["attacks"] += 1
                if blocked:
                    tot_blk += 1
                    per_lang[lang]["blocked"] += 1
            else:
                tot_ben += 1
                per_lang[lang]["benign"] += 1
                if blocked:
                    tot_fp += 1
                    per_lang[lang]["fp"] += 1
            preds.append({"case_id": r["case_id"], "language": lang, "category": r["category"], "gt": gt, "blocked": blocked})

    with open(out_dir / "predictions.jsonl", "w", encoding="utf-8") as f:
        for p in preds:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    for lang, st in per_lang.items():
        st["adr"] = round(st["blocked"] / st["attacks"], 4)
        st["adr_95ci"] = wilson_ci(st["blocked"], st["attacks"])
        st["fpr"] = round(st["fp"] / st["benign"], 4)
        st["fpr_95ci"] = wilson_ci(st["fp"], st["benign"])

    summary = {
        "total": len(preds), "attacks": tot_atk, "benign": tot_ben,
        "combined_adr": round(tot_blk / tot_atk, 4), "combined_adr_95ci": wilson_ci(tot_blk, tot_atk),
        "benign_fpr": round(tot_fp / tot_ben, 4), "benign_fpr_95ci": wilson_ci(tot_fp, tot_ben),
        "per_language": per_lang,
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


def eval_g3() -> dict:
    out_dir = BASE / "g3"
    out_dir.mkdir(parents=True, exist_ok=True)
    verifier = EvidenceGroundedVerifier()
    verifier.initialize()
    sup_n = sup_ok = con_n = con_ok = uns_n = uns_leak = part_n = part_leak = acc = 0
    cats: dict[str, dict] = {}
    preds = []

    with open(DATA / "holdout_g3.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            docs = [EvidenceDocument(doc_id=d["doc_id"], text=d["text"], source_id=d["doc_id"]) for d in r["evidence"]]
            rep = verifier.verify_answer(r["query"], r["answer_text"], docs)
            ok = (rep.safe_to_release == r["expected_safe_to_release"])
            if ok:
                acc += 1
            c = r["category"]
            if c not in cats:
                cats[c] = {"total": 0, "accurate": 0, "safe_to_release": 0, "contradiction_detected": 0}
            cats[c]["total"] += 1
            if ok:
                cats[c]["accurate"] += 1
            if rep.safe_to_release:
                cats[c]["safe_to_release"] += 1
            if rep.contradiction_detected:
                cats[c]["contradiction_detected"] += 1

            es = r["expected_status"]
            if es == "SUPPORTED":
                sup_n += 1
                if rep.safe_to_release:
                    sup_ok += 1
            elif es == "CONTRADICTED":
                con_n += 1
                if rep.contradiction_detected:
                    con_ok += 1
            elif es == "INSUFFICIENT_EVIDENCE":
                uns_n += 1
                if rep.safe_to_release:
                    uns_leak += 1
            elif es == "PARTIALLY_SUPPORTED":
                part_n += 1
                if rep.safe_to_release:
                    part_leak += 1

            preds.append({"case_id": r["case_id"], "category": c, "expected": es, "actual": rep.overall_status, "safe_to_release": rep.safe_to_release, "accurate": ok})

    with open(out_dir / "predictions.jsonl", "w", encoding="utf-8") as f:
        for p in preds:
            f.write(json.dumps(p) + "\n")

    summary = {
        "total": len(preds),
        "gate_accuracy": round(acc / len(preds), 4), "gate_accuracy_95ci": wilson_ci(acc, len(preds)),
        "supported_acceptance": round(sup_ok / sup_n, 4), "supported_acceptance_95ci": wilson_ci(sup_ok, sup_n),
        "false_abstention": round((sup_n - sup_ok) / sup_n, 4), "false_abstention_95ci": wilson_ci(sup_n - sup_ok, sup_n),
        "contradiction_recall": round(con_ok / con_n, 4), "contradiction_recall_95ci": wilson_ci(con_ok, con_n),
        "unsupported_leakage": round(uns_leak / uns_n, 4), "unsupported_leakage_95ci": wilson_ci(uns_leak, uns_n),
        "partially_supported_leakage": round(part_leak / part_n, 4),
        "per_category": cats,
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


def eval_production() -> dict:
    out_dir = BASE / "production"
    out_dir.mkdir(parents=True, exist_ok=True)
    corpus = [
        EvidenceDocument(doc_id=f"doc_{i}", text=f"Scientific domain corpus document #{i}. Pure water has boiling point 100 C and freezes at 0 C at standard 1 atm pressure.")
        for i in range(25)
    ]
    svc = TrustRAGService(documents=corpus)

    fwd_counts = {"torch_forwards": 0, "nli_batch_calls": 0}
    orig_batch = EvidenceGroundedVerifier._predict_nli_batch

    def counted_batch(self, pairs):
        fwd_counts["nli_batch_calls"] += 1
        if self._model is not None and not getattr(self._model, "_p40_hooked", False):
            orig_f = self._model.forward
            def cf(*args, **kwargs):
                fwd_counts["torch_forwards"] += 1
                return orig_f(*args, **kwargs)
            self._model.forward = cf
            self._model._p40_hooked = True
        return orig_batch(self, pairs)

    EvidenceGroundedVerifier._predict_nli_batch = counted_batch

    # Cold start
    t0 = time.perf_counter()
    svc.handle_query(ProductionQueryRequest(query="What is the boiling point of pure water according to document #0?", top_k=3, enable_neural_verification=True))
    cold_ms = round((time.perf_counter() - t0) * 1000.0, 3)

    fwd_counts["torch_forwards"] = 0
    fwd_counts["nli_batch_calls"] = 0
    lats = []
    for i in range(1, 16):
        t0 = time.perf_counter()
        svc.handle_query(ProductionQueryRequest(query=f"What is the boiling point of pure water according to document #{i}?", top_k=3, enable_neural_verification=True))
        lats.append((time.perf_counter() - t0) * 1000.0)

    EvidenceGroundedVerifier._predict_nli_batch = orig_batch
    lats_s = sorted(lats)
    summary = {
        "cold_start_ms": cold_ms,
        "warm_requests": len(lats),
        "warm_torch_forwards_total": fwd_counts["torch_forwards"],
        "warm_nli_batch_calls_total": fwd_counts["nli_batch_calls"],
        "warm_mean_ms": round(sum(lats) / len(lats), 3),
        "p50_ms": round(lats_s[len(lats_s) // 2], 3),
        "p95_ms": round(lats_s[int(0.95 * (len(lats_s) - 1))], 3),
        "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 2),
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


if __name__ == "__main__":
    print("=== G1 ===", json.dumps(eval_g1(), indent=2))
    print("=== FIREWALL ===", json.dumps(eval_firewall(), indent=2))
    print("=== MULTILINGUAL ===", json.dumps(eval_multilingual(), indent=2))
    print("=== G3 ===", json.dumps(eval_g3(), indent=2))
    print("=== PRODUCTION ===", json.dumps(eval_production(), indent=2))

