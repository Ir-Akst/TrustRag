"""Render human-readable Markdown summaries from Phase10ExperimentBundle."""

from __future__ import annotations

from trustrag.evaluation.experiments.phase10_runner import Phase10ExperimentBundle


def render_markdown_summary(bundle: Phase10ExperimentBundle) -> str:
    """Format a Phase10ExperimentBundle into concise Markdown tables."""
    lines: list[str] = [
        f"# Phase 10 Experiment Summary (`{bundle.experiment_id}`)",
        "",
        f"- **Git Commit:** `{bundle.git_commit}`",
        f"- **Config Hash:** `{bundle.config_hash}`",
        f"- **Seed:** `{bundle.seed}`",
        f"- **Started:** `{bundle.started_at}`",
        f"- **Completed:** `{bundle.completed_at}`",
        "",
        "## Comparative Baselines",
    ]
    for ds_name, ds_data in bundle.comparative_baselines.items():
        lines.append(f"\n### Dataset: `{ds_name}`")
        lines.append("| Profile | n | Accuracy | Precision | Recall | F1 | FPR | ASR | Mean ms |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        for prof, pdata in ds_data["profiles"].items():
            sm = pdata["security_metrics"]
            om = pdata["operational_metrics"]
            lines.append(
                f"| `{prof}` | {pdata['sample_count']} | {sm.get('accuracy')} | "
                f"{sm.get('precision')} | {sm.get('recall')} | {sm.get('f1')} | "
                f"{sm.get('fpr')} | {sm.get('asr')} | {om.get('mean_ms')} |"
            )
    return "\n".join(lines) + "\n"
