#!/usr/bin/env python3
"""
Phase 31: Latency and Deployment Truthfulness Profiler
Audits execution profiles without conflating them:
- Profile 0: G1 Standalone Latency (Deterministic regex & normalization)
- Profile 1: Full Deterministic Serving Pipeline (G1 + TF-IDF Retrieval + G2 MSD + Generator)
- Profile 2: Offline Neural NLI Latency (DeBERTa-v3-small CPU inference)
- Profile 3: Live Serving Neural Latency (Audit truthfulness: Neural NLI is NOT active in live serving)
Measures P50, P90, P99, mean, min, max, CPU and memory usage.
"""

from __future__ import annotations

import json
import os
import time
import psutil
import torch
from pathlib import Path
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from trustrag.config.engine_config import GuardrailsConfig, MSDConfig
from trustrag.guardrails.input_guardrail import InputGuardrail
from trustrag.detection.msd import MultiSignalDetector
from trustrag.serving.service import TrustRAGService, ProductionQueryRequest
from trustrag.engine.schemas import EvidenceDocument

def compute_percentiles(latencies: list[float]) -> dict[str, float]:
    sorted_lat = sorted(latencies)
    n = len(sorted_lat)
    p50 = sorted_lat[int(0.50 * n)]
    p90 = sorted_lat[int(0.90 * n)]
    p99 = sorted_lat[int(0.99 * n)]
    return {
        "p50_ms": round(p50, 4),
        "p90_ms": round(p90, 4),
        "p99_ms": round(p99, 4),
        "mean_ms": round(sum(latencies) / n, 4),
        "min_ms": round(min(latencies), 4),
        "max_ms": round(max(latencies), 4),
        "samples": n
    }

def run_latency_audit():
    print("=== EXECUTING LATENCY AND DEPLOYMENT TRUTHFULNESS AUDIT ===")
    process = psutil.Process()
    cpu_initial = psutil.cpu_percent(interval=0.1)
    mem_initial_mb = process.memory_info().rss / (1024 * 1024)

    queries = [
        "What is the capital of France?",
        "How does AES-256 encryption secure data in transit?",
        "Explain the Raft consensus protocol in distributed clusters.",
        "What are the best practices for container security in Kubernetes?",
        "Summarize the European Union Artificial Intelligence Act compliance guidelines."
    ] * 20 # 100 queries

    docs = [
        EvidenceDocument(doc_id=f"doc_{i}", text=f"Enterprise security reference document #{i}: AES-256 provides military-grade confidentiality across all network nodes.", score=0.9)
        for i in range(10)
    ]

    # --- Profile 0: G1 Standalone ---
    print("\nBenchmarking Profile 0: G1 Standalone Guardrail...")
    g1 = InputGuardrail(GuardrailsConfig())
    g1_latencies = []
    # Warmup
    for q in queries[:5]:
        g1.evaluate(q)

    for q in queries:
        t0 = time.perf_counter()
        g1.evaluate(q)
        g1_latencies.append((time.perf_counter() - t0) * 1000.0)

    p0_stats = compute_percentiles(g1_latencies)
    print(f"  P0 (G1 Standalone): P50={p0_stats['p50_ms']}ms | P99={p0_stats['p99_ms']}ms | Mean={p0_stats['mean_ms']}ms")

    # --- Profile 1: Full Deterministic CPU Serving Pipeline ---
    print("\nBenchmarking Profile 1: Full Deterministic CPU Serving Pipeline...")
    service = TrustRAGService(documents=docs)
    service_latencies = []
    # Warmup
    for q in queries[:5]:
        service.handle_query(ProductionQueryRequest(query=q))

    for q in queries:
        t0 = time.perf_counter()
        service.handle_query(ProductionQueryRequest(query=q))
        service_latencies.append((time.perf_counter() - t0) * 1000.0)

    p1_stats = compute_percentiles(service_latencies)
    print(f"  P1 (Deterministic Serving): P50={p1_stats['p50_ms']}ms | P99={p1_stats['p99_ms']}ms | Mean={p1_stats['mean_ms']}ms")

    # --- Profile 2: Offline Neural NLI Inference (DeBERTa-v3-small on CPU) ---
    print("\nBenchmarking Profile 2: Offline DeBERTa-v3-small Neural NLI on CPU...")
    checkpoint_dir = "/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch"
    tokenizer = AutoTokenizer.from_pretrained(checkpoint_dir)
    model = AutoModelForSequenceClassification.from_pretrained(checkpoint_dir)
    model.eval()

    nli_latencies = []
    pairs = [(q, docs[0].text) for q in queries[:50]]
    # Warmup
    for premise, hypo in pairs[:3]:
        inputs = tokenizer(premise, hypo, return_tensors="pt", truncation=True, max_length=128)
        with torch.no_grad():
            model(**inputs)

    for premise, hypo in pairs:
        inputs = tokenizer(premise, hypo, return_tensors="pt", truncation=True, max_length=128)
        t0 = time.perf_counter()
        with torch.no_grad():
            outputs = model(**inputs)
        nli_latencies.append((time.perf_counter() - t0) * 1000.0)

    p2_stats = compute_percentiles(nli_latencies)
    print(f"  P2 (Offline Neural NLI CPU): P50={p2_stats['p50_ms']}ms | P99={p2_stats['p99_ms']}ms | Mean={p2_stats['mean_ms']}ms")

    # Resource measurements
    mem_final_mb = process.memory_info().rss / (1024 * 1024)
    cpu_final = psutil.cpu_percent(interval=0.1)

    deployment_audit = {
        "benchmark": "Phase 31 Latency and Deployment Truthfulness Profiling",
        "hardware": {
            "cpu_cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
            "initial_memory_rss_mb": round(mem_initial_mb, 2),
            "final_memory_rss_mb": round(mem_final_mb, 2),
            "memory_delta_mb": round(mem_final_mb - mem_initial_mb, 2)
        },
        "profiles": {
            "profile_0_g1_standalone": {
                "description": "Deterministic G1 input guardrail (regex, normalization, security heuristics)",
                "active_in_production": True,
                "latency_metrics": p0_stats
            },
            "profile_1_deterministic_serving": {
                "description": "Full production pipeline with deterministic fallback (G1 + TF-IDF retrieval + G2 MSD + generation)",
                "active_in_production": True,
                "latency_metrics": p1_stats
            },
            "profile_2_offline_neural_nli": {
                "description": "Frozen DeBERTa-v3-small neural NLI forward pass on CPU (batch=1, max_len=128)",
                "active_in_production": False,
                "note": "Evaluated strictly offline in research harness; NOT wired into live production server serving loop.",
                "latency_metrics": p2_stats
            },
            "profile_3_live_serving_neural_nli": {
                "description": "Live production neural serving",
                "active_in_production": False,
                "truthfulness_statement": "TRUTHFUL AUDIT FINDING: Live API server runs with SRM backend='disabled' (deterministic CPU fallback active). Neural DeBERTa weights are NOT executed during live /api/v1/pipeline/execute requests."
            }
        }
    }

    out_json = Path("reports/phase31/raw_predictions/latency_benchmark_profiles.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(deployment_audit, f, indent=2)

    print(f"\nLatency profiling complete. Report saved to {out_json}")

if __name__ == "__main__":
    run_latency_audit()
