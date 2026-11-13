"""CLI entrypoint for running the end-to-end TrustRAG Phase 03 defense pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from trustrag.pipeline.trustrag_pipeline import TrustRAGPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trustrag-pipeline",
        description="TrustRAG Phase 03 End-to-End Defense Pipeline Runner",
    )
    parser.add_argument(
        "--corpus",
        default="data/benchmarks/clean_rag/test.jsonl",
        help="Path to local JSONL corpus/benchmark file",
    )
    parser.add_argument(
        "--query",
        default="",
        help="User query to evaluate through G1 -> Retrieval/G2 -> Generation -> G3 -> SRM",
    )
    parser.add_argument("--top-k", type=int, default=3, help="Number of trusted documents to select")
    parser.add_argument("--limit", type=int, default=200, help="Max records to index from corpus JSONL")
    parser.add_argument("--json", action="store_true", help="Emit full PipelineResponse as formatted JSON")
    parser.add_argument("--adaptive", action="store_true", help="Run via Phase 05/06 adaptive TrustRAGService")
    parser.add_argument(
        "--calibrator",
        default="configs/adaptive/temperature_calibrator_v1.json",
        help="Optional calibration JSON artifact used with --adaptive",
    )
    parser.add_argument("--health", action="store_true", help="Print service health/readiness JSON and exit")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    corpus_path = Path(args.corpus)
    if not corpus_path.is_file():
        print(f"Error: Corpus file not found at '{corpus_path}'.", file=sys.stderr)
        return 1

    if not args.health and not args.query.strip():
        parser.error("--query is required unless --health is specified.")

    if args.adaptive or args.health:
        from trustrag.serving import ProductionQueryRequest, TrustRAGService

        cal_path = args.calibrator if Path(args.calibrator).is_file() else None
        service = TrustRAGService.from_jsonl(
            corpus_path,
            limit=args.limit,
            adaptive=bool(args.adaptive),
            calibrator_path=cal_path,
        )
        if args.health:
            print(service.health().model_dump_json(indent=2))
            return 0
        resp = service.handle_query(ProductionQueryRequest(query=args.query, top_k=args.top_k))
        if args.json:
            print(resp.model_dump_json(indent=2))
        else:
            print(
                f"[{resp.status}] mode={resp.adaptive_mode} g1={resp.g1_decision} "
                f"g3={resp.g3_verdict} lat={resp.latency_ms}ms\nAnswer: {resp.answer}"
            )
        return 0

    pipeline = TrustRAGPipeline.from_jsonl(corpus_path, limit=args.limit)
    response = pipeline.run(args.query, top_k=args.top_k)

    if args.json:
        print(response.model_dump_json(indent=2))
        return 0

    tr = response.trust_report
    print("=" * 80)
    print("TrustRAG End-to-End Defense Pipeline Report")
    print("=" * 80)
    print(f"Original Query:        {response.query}")
    print(f"Overall Decision:      {tr.overall_trust_decision}")
    print(f"Blocked by Guardrail:  {response.blocked_by_guardrail}")
    print(f"Abstained:             {response.abstained}")
    print(f"G1 Decision:           {tr.g1_assessment.decision.value} (risk={tr.g1_assessment.risk_score})")
    print(f"G1 Reason Codes:       {[c.value for c in tr.g1_assessment.reason_codes]}")
    print(f"Retrieval Summary:     {tr.retrieval_summary}")
    print(f"Final Answer:\n  {response.answer}")
    print("-" * 80)
    if response.evidence:
        print(f"Trusted Evidence ({len(response.evidence)} doc(s)):")
        for doc in response.evidence:
            print(f"  - [{doc.doc_id}] (source={doc.source_dataset}, source_id={doc.source_id}): {doc.text[:140]}...")
    if tr.g3_verification:
        print("-" * 80)
        g3_v = tr.g3_verification.verdict.value if tr.g3_verification.verdict else tr.g3_verification.overall_status.value
        print(f"G3 Verification:       {g3_v} / {tr.g3_verification.overall_status.value} ({tr.g3_verification.summary})")
        for c in tr.g3_verification.claims:
            cv = c.verdict.value if c.verdict else c.outcome.value
            print(f"  * {c.claim_id}: {cv} (conf={c.confidence:.2f}) -> {c.claim_text}")
    if tr.srm_response:
        print("-" * 80)
        print(
            f"SRM Verification:      verdict={tr.srm_response.verdict}, "
            f"backend={tr.srm_response.backend_used}, status={tr.srm_response.execution_status.value}, "
            f"fallback={tr.srm_response.is_fallback}"
        )
        print(f"SRM Trace:             {tr.srm_response.reasoning_trace}")
    print("-" * 80)
    print(f"Execution Trace:       {' -> '.join(tr.execution_trace)}")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())

