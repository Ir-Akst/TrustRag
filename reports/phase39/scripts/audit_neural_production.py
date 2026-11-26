#!/usr/bin/env python3
"""Phase 39 Independent Production Neural Inference & Lifecycle Audit."""

import concurrent.futures
import json
import resource
import time
from pathlib import Path

from trustrag.engine.schemas import EvidenceDocument
from trustrag.guardrails.input_guardrail import InputGuardrail
from trustrag.serving.service import ProductionQueryRequest, TrustRAGService
from trustrag.verification.grounded_verifier import EvidenceGroundedVerifier

OUT_DIR = Path("reports/phase39/raw_predictions")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def percentile(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return round(s[f], 3)
    return round(s[f] + (k - f) * (s[c] - s[f]), 3)


def run_production_audit() -> None:
    corpus = [
        EvidenceDocument(
            doc_id=f"doc_{i}",
            text=f"Scientific domain corpus document #{i}. Pure water has boiling point 100 C and freezes at 0 C at standard 1 atm pressure.",
        )
        for i in range(25)
    ]
    service = TrustRAGService(documents=corpus)
    g1 = InputGuardrail()

    # 1. Profile A: Deterministic CPU (Cold + Warm)
    req_cold_a = ProductionQueryRequest(
        query="What is the freezing point of water according to document #0?",
        top_k=3,
        enable_neural_verification=False,
    )
    t0 = time.perf_counter()
    resp_cold_a = service.handle_query(req_cold_a)
    cold_a_ms = round((time.perf_counter() - t0) * 1000.0, 3)

    lat_a = []
    modes_a = set()
    for i in range(1, 21):
        req = ProductionQueryRequest(
            query=f"What is the freezing point of water according to document #{i}?",
            top_k=3,
            enable_neural_verification=False,
        )
        t0 = time.perf_counter()
        resp = service.handle_query(req)
        lat_a.append((time.perf_counter() - t0) * 1000.0)
        modes_a.add(resp.inference_mode)

    # 2. Profile B: Live Neural DeBERTa CPU (Instrumented forward passes)
    counters = {"nli_calls": 0, "nli_ms": 0.0, "torch_forward_calls": 0}
    orig_predict = EvidenceGroundedVerifier._predict_nli_pair

    def counted_predict(self, premise: str, hypothesis: str):
        # Hook the underlying HuggingFace model forward once loaded
        if self._model is not None and not getattr(self._model, "_p39_hooked", False):
            orig_fwd = self._model.forward

            def counted_fwd(*args, **kwargs):
                counters["torch_forward_calls"] += 1
                return orig_fwd(*args, **kwargs)

            self._model.forward = counted_fwd
            self._model._p39_hooked = True

        ts = time.perf_counter()
        out = orig_predict(self, premise, hypothesis)
        counters["nli_ms"] += (time.perf_counter() - ts) * 1000.0
        counters["nli_calls"] += 1
        return out

    EvidenceGroundedVerifier._predict_nli_pair = counted_predict

    rss_before_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    cpu_before = time.process_time()

    # Cold-start neural request (includes DeBERTa model load)
    req_cold_b = ProductionQueryRequest(
        query="What is the boiling point of pure water according to document #0?",
        top_k=3,
        enable_neural_verification=True,
    )
    t0 = time.perf_counter()
    resp_cold_b = service.handle_query(req_cold_b)
    cold_b_ms = round((time.perf_counter() - t0) * 1000.0, 3)
    cold_b_nli_calls = counters["nli_calls"]
    cold_b_torch_fwds = counters["torch_forward_calls"]

    # Reset counters for warm requests
    counters["nli_calls"] = 0
    counters["nli_ms"] = 0.0
    counters["torch_forward_calls"] = 0

    lat_b_full = []
    lat_g1_only = []
    modes_b = set()

    for i in range(1, 16):
        q = f"What is the boiling point of pure water according to document #{i}?"
        tg1 = time.perf_counter()
        g1.evaluate(q)
        lat_g1_only.append((time.perf_counter() - tg1) * 1000.0)

        req = ProductionQueryRequest(query=q, top_k=3, enable_neural_verification=True)
        t0 = time.perf_counter()
        resp = service.handle_query(req)
        lat_b_full.append((time.perf_counter() - t0) * 1000.0)
        modes_b.add(resp.inference_mode)

    cpu_elapsed = round(time.process_time() - cpu_before, 3)
    rss_after_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    EvidenceGroundedVerifier._predict_nli_pair = orig_predict

    # 3. Lifecycle Stress: Concurrency, Timeout, Cancellation, Shutdown
    conc_ok = 0
    conc_modes = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futs = [
            pool.submit(
                service.handle_query,
                ProductionQueryRequest(
                    query=f"What is the boiling point of water #{idx}?",
                    top_k=2,
                    enable_neural_verification=(idx % 2 == 0),
                ),
            )
            for idx in range(12)
        ]
        for fut in concurrent.futures.as_completed(futs):
            r = fut.result()
            if r is not None and r.status in ("OK", "ABSTAINED", "COMPLETED"):
                conc_ok += 1
                conc_modes.add(r.inference_mode)

    # Timeout test
    t_resp = service.handle_query(
        ProductionQueryRequest(
            query="What is the boiling point of water?",
            top_k=5,
            enable_neural_verification=True,
            request_timeout_seconds=0.0001,
        )
    )

    # Cancellation test (ThreadPoolExecutor future cancellation on queued tasks)
    cancelled_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        f_block = pool.submit(
            service.handle_query,
            ProductionQueryRequest(query="What is the boiling point of water?", top_k=3, enable_neural_verification=True),
        )
        f_cancel = pool.submit(
            service.handle_query,
            ProductionQueryRequest(query="What is the freezing point of water?", top_k=3, enable_neural_verification=True),
        )
        if f_cancel.cancel():
            cancelled_count += 1
        f_block.result()

    # Shutdown test
    service.shutdown()
    sd_resp = service.handle_query(
        ProductionQueryRequest(query="What is the boiling point of water?", top_k=2)
    )

    n_warm_b = len(lat_b_full)
    summary = {
        "workstream": "Production Neural Inference & Lifecycle Audit",
        "profile_a_deterministic": {
            "cold_start_ms": cold_a_ms,
            "warm_requests": len(lat_a),
            "reported_modes": sorted(modes_a),
            "mean_ms": round(sum(lat_a) / len(lat_a), 3),
            "p50_ms": percentile(lat_a, 50),
            "p90_ms": percentile(lat_a, 90),
            "p95_ms": percentile(lat_a, 95),
            "p99_ms": percentile(lat_a, 99),
        },
        "profile_b_neural_deberta": {
            "cold_start_ms": cold_b_ms,
            "cold_start_nli_calls": cold_b_nli_calls,
            "cold_start_torch_forwards": cold_b_torch_fwds,
            "warm_requests": n_warm_b,
            "warm_nli_calls_total": counters["nli_calls"],
            "warm_torch_forwards_total": counters["torch_forward_calls"],
            "forward_passes_per_request": round(counters["nli_calls"] / n_warm_b, 2),
            "reported_modes": sorted(modes_b),
            "g1_mean_ms": round(sum(lat_g1_only) / len(lat_g1_only), 3),
            "neural_nli_mean_per_request_ms": round(counters["nli_ms"] / n_warm_b, 3),
            "neural_nli_mean_per_pass_ms": round(counters["nli_ms"] / max(1, counters["nli_calls"]), 3),
            "full_request_mean_ms": round(sum(lat_b_full) / n_warm_b, 3),
            "p50_ms": percentile(lat_b_full, 50),
            "p90_ms": percentile(lat_b_full, 90),
            "p95_ms": percentile(lat_b_full, 95),
            "p99_ms": percentile(lat_b_full, 99),
            "cpu_time_sec": cpu_elapsed,
            "peak_rss_mb": round(rss_after_kb / 1024.0, 2),
            "rss_delta_mb": round((rss_after_kb - rss_before_kb) / 1024.0, 2),
        },
        "lifecycle_stress": {
            "concurrency_12_requests_ok": conc_ok,
            "concurrency_modes": sorted(conc_modes),
            "timeout_status": t_resp.status,
            "timeout_g1_decision": t_resp.g1_decision,
            "timeout_abstained": t_resp.abstained,
            "cancellation_queued_future_cancelled": cancelled_count == 1,
            "shutdown_status": sd_resp.status,
            "shutdown_g1_decision": sd_resp.g1_decision,
            "shutdown_abstained": sd_resp.abstained,
        },
    }

    with open(OUT_DIR / "neural_production_audit_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run_production_audit()
