#!/usr/bin/env python3
"""Phase 36 Evaluation: Workstream F - Frontend & Backend Integration."""

from __future__ import annotations

import json
import urllib.request
import urllib.parse
from pathlib import Path

def evaluate_frontend_backend():
    summary_path = Path("reports/phase36/raw_predictions/frontend_backend_e2e_summary.json")

    endpoints = [
        {"name": "health_check", "url": "http://127.0.0.1:8000/api/v1/health", "method": "GET", "payload": None},
        {"name": "service_root_health", "url": "http://127.0.0.1:8000/health", "method": "GET", "payload": None},
        {
            "name": "pipeline_execution",
            "url": "http://127.0.0.1:8000/api/v1/pipeline/execute",
            "method": "POST",
            "payload": {"query": "What is the capital of France?", "top_k": 3}
        },
        {
            "name": "g3_verify_endpoint",
            "url": "http://127.0.0.1:8000/api/v1/g3/verify",
            "method": "POST",
            "payload": {
                "query": "Where was Marie Curie born?",
                "answer": "Marie Curie was born in Warsaw, Poland.",
                "documents": [{"doc_id": "doc_1", "text": "Marie Curie was born in Warsaw in the Russian partition of Poland.", "score": 0.95}]
            }
        },
        {"name": "frontend_root", "url": "http://127.0.0.1:8000/", "method": "GET", "payload": None}
    ]

    results = []
    all_passed = True

    for ep in endpoints:
        url = ep["url"]
        method = ep["method"]
        data = ep["payload"]
        try:
            req_data = json.dumps(data).encode("utf-8") if data else None
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"} if data else {},
                method=method
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                status_code = response.getcode()
                body = response.read().decode("utf-8")
                try:
                    parsed_body = json.loads(body)
                except Exception:
                    parsed_body = body[:200]
                results.append({
                    "test": ep["name"],
                    "endpoint": url,
                    "status_code": status_code,
                    "data": parsed_body,
                    "passed": (status_code == 200)
                })
        except Exception as exc:
            results.append({
                "test": ep["name"],
                "endpoint": url,
                "status_code": 500,
                "error": str(exc),
                "passed": False
            })
            all_passed = False

    summary = {
        "workstream": "Workstream F - Frontend & Backend E2E Integration",
        "tests_executed": len(endpoints),
        "all_tests_passed": all_passed,
        "detailed_results": results
    }

    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"E2E Integration Complete: {len([r for r in results if r.get('passed')])}/{len(endpoints)} passed.")

if __name__ == "__main__":
    evaluate_frontend_backend()

