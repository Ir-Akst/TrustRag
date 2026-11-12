"""Reproducible CLI runner for TrustRAG Phase 10 evaluation & ablation suite."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from trustrag.evaluation.experiments.phase10_runner import run_all_phase10_experiments  # noqa: E402
from trustrag.evaluation.reporting.generator import render_markdown_summary  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TrustRAG Phase 10 Evaluation & Ablation Suite")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run-tag", default=None)
    args = parser.parse_args()

    bundle = run_all_phase10_experiments(ROOT, seed=args.seed, run_tag=args.run_tag)
    out_dir = ROOT / bundle.output_dir
    summary_md = render_markdown_summary(bundle)
    (out_dir / "summary.md").write_text(summary_md, encoding="utf-8")

    print(
        json.dumps(
            {
                "experiment_id": bundle.experiment_id,
                "output_dir": bundle.output_dir,
                "git_commit": bundle.git_commit,
                "config_hash": bundle.config_hash,
                "seed": bundle.seed,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
