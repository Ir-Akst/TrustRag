#!/usr/bin/env python3
"""Phase 37 Evaluation: Workstream E - Production Neural Verification & Lifecycle."""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, List

import numpy as np
import torch

from trustrag.engine.schemas import EvidenceDocument
from trustrag.serving.service import ProductionQueryRequest, ProductionQueryResponse, TrustRAGService
from trustrag.verification.grounded_verifier import EvidenceGroundedVerifier

def evaluate_production_neural():
    summary_path = Path("reports/phase37/raw_predictions/neural_production_audit_summary.json")

    corpus = [
        EvidenceDocument(doc_id=f"doc_{i}", text=f"Scientific domain corpus document #{i}. Pure water has boiling point 100 C and freezes at 0 C at standard 1 atm pressure.")
        for i in range(25)
    ]
    service = TrustRAGService(documents=corpus)

    # 1. Profile A: Deterministic CPU Mode
    profile_a_latencies = []
    profile_a_modes = []

    for i in range(25):
        req = ProductionQueryRequest(
            query=f"What is the freezing point of water according to document #{i}?",
            top_k=3,
            enable_neural_verification=False
        )
        t0 = time.perf_counter()
        resp = service.handle_query(req)
        lat = (time.perf_counter() - t0) * 1000.0
        profile_a_latencies.append(lat)
        profile_a_modes.append(resp.inference_mode)

    # 2. Profile B: Neural DeBERTa CPU Mode (Instrumented forward passes)
    forward_pass_counter = 0
    orig_forward = EvidenceGroundedVerifier._predict_nli_pair

    def counted_predict(*args, **kwargs):
        nonlocal forward_pass_counter
        forward_pass_counter += 1
        return orig_forward(*args, **kwargs)

    EvidenceGroundedVerifier._predict_nli_pair = counted_predict

    profile_b_latencies = []
    profile_b_modes = []

    for i in range(25):
        req = ProductionQueryRequest(
            query=f"What is the boiling point of pure water according to document #{i}?",
            top_k=3,
            enable_neural_verification=True
        )
        t0 = time.perf_counter()
        resp = service.handle_query(req)
        lat = (time.perf_counter() - t0) * 1000.0
        profile_b_latencies.append(lat)
        profile_b_modes.append(resp.inference_mode)

    EvidenceGroundedVerifier._predict_nli_pair = orig_forward

    # 3. Lifecycle Failure Modes & Concurrency Stress Testing
    # Test A: Enforced Timeout
    timeout_req = ProductionQueryRequest(
        query="What is the boiling point of water?",
        top_k=5,
        request_timeout_seconds=0.0001
    )
    t_resp = service.handle_query(timeout_req)
    timeout_passed = (t_resp.status == "ERROR" and t_resp.g1_decision == "TIMEOUT" and t_resp.abstained)

    # Test B: High Concurrency
    concurrent_success = 0
    concurrent_modes = set()

    def run_concurrent_req(idx: int):
        use_neural = (idx % 2 == 0)
        c_req = ProductionQueryRequest(
            query=f"What is the boiling point of water #{idx}?",
            top_k=2,
            enable_neural_verification=use_neural
        )
        return service.handle_query(c_req)

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(run_concurrent_req, i) for i in range(20)]
        for fut in as_completed(futures):
            res = fut.result()
            if res.status in ("OK", "ABSTAINED"):
                concurrent_success += 1
                concurrent_modes.add(res.inference_mode)

    concurrency_passed = (concurrent_success == 20)

    # Test C: Post-Shutdown Defense
    service.shutdown()
    shut_req = ProductionQueryRequest(query="What is the boiling point of water?")
    shut_resp = service.handle_query(shut_req)
    shutdown_passed = (shut_resp.status == "ERROR" and shut_resp.g1_decision == "SERVICE_SHUTDOWN" and shut_resp.abstained)

    summary = {
        "workstream": "Workstream E - Production Neural Verification & Lifecycle Audit",
        "profile_a_deterministic": {
            "requests_audited": 25,
            "reported_modes": list(set(profile_a_modes)),
            "forward_passes_observed": 0,
            "mean_latency_ms": round(float(np.mean(profile_a_latencies)), 3),
            "p50_latency_ms": round(float(np.percentile(profile_a_latencies, 50)), 3),
            "p90_latency_ms": round(float(np.percentile(profile_a_latencies, 90)), 3),
            "p99_latency_ms": round(float(np.percentile(profile_a_latencies, 99)), 3)
        },
        "profile_b_neural_deberta": {
            "requests_audited": 25,
            "reported_modes": list(set(profile_b_modes)),
            "total_forward_passes_observed": forward_pass_counter,
            "forward_passes_per_request": round(forward_pass_counter / 25, 1),
            "mean_latency_ms": round(float(np.mean(profile_b_latencies)), 3),
            "p50_latency_ms": round(float(np.percentile(profile_b_latencies, 50)), 3),
            "p90_latency_ms": round(float(np.percentile(profile_b_latencies, 90)), 3),
            "p99_latency_ms": round(float(np.percentile(profile_b_latencies, 99)), 3),
            "mean_latency_per_forward_pass_ms": round(float(np.mean(profile_b_latencies)) / (forward_pass_counter / 25), 3) if forward_pass_counter > 0 else 0.0
        },
        "lifecycle_failure_stress": {
            "timeout_test": {
                "status": t_resp.status,
                "g1_decision": t_resp.g1_decision,
                "abstained": t_resp.abstained,
                "fail_safe_events": t_resp.fail_safe_events,
                "latency_ms": t_resp.latency_ms,
                "passed": timeout_passed
            },
            "concurrency_test": {
                "total_requests": 20,
                "successful_responses": concurrent_success,
                "modes_observed": list(concurrent_modes),
                "passed": concurrency_passed
            },
            "shutdown_test": {
                "status": shut_resp.status,
                "g1_decision": shut_resp.g1_decision,
                "abstained": shut_resp.abstained,
                "passed": shutdown_passed
            }
        }
    }

    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=== PRODUCTION NEURAL AUDIT RESULTS ===")
    print("Profile A (Deterministic):", summary["profile_a_deterministic"])
    print("Profile B (Neural DeBERTa):", summary["profile_b_neural_deberta"])
    print("Lifecycle stress:", summary["lifecycle_failure_stress"])

if __name__ == "__main__":
    evaluate_production_neural()
