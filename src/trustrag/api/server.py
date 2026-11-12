"""CLI server runner for TrustRAG Phase 09 Web API and Dashboard."""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence

from aiohttp import web

from trustrag.api.app import create_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run TrustRAG Web API & Dashboard Server")
    parser.add_argument("--host", default=os.environ.get("TRUSTRAG_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("TRUSTRAG_PORT", "8000")))
    parser.add_argument("--corpus-path", default=os.environ.get("TRUSTRAG_CORPUS_PATH"))
    parser.add_argument("--audit-log-path", default=os.environ.get("TRUSTRAG_AUDIT_LOG", "logs/audit_events.jsonl"))
    parser.add_argument("--frontend-dir", default=os.environ.get("TRUSTRAG_FRONTEND_DIR", "frontend"))
    parser.add_argument("--env", default=os.environ.get("TRUSTRAG_ENV", "development"))
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    app = create_app(
        corpus_path=args.corpus_path,
        audit_log_path=args.audit_log_path,
        frontend_dir=args.frontend_dir,
        environment=args.env,
    )
    web.run_app(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
