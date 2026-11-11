"""Reproducible experiment runner and result exporter for TrustRAG Phase 04."""

from __future__ import annotations

import csv
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from trustrag.evaluation.loader import LoadedPartition, load_evaluation_partition
from trustrag.evaluation.schemas import (
    ErrorRecord,
    ExperimentConfig,
    ExperimentResult,
    SampleOutcome,
)
from trustrag.utils.logging import get_logger
from trustrag.utils.repro import set_random_seed

LOGGER = get_logger(__name__)


class EvaluationRunner:
    """Executes deterministic, traceable evaluation runs and exports JSON/CSV artifacts."""

    def __init__(self, output_dir: str | Path = "reports/evaluation") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        config: ExperimentConfig,
        evaluate_fn: Callable[[Any], SampleOutcome],
        metrics_fn: Callable[[list[SampleOutcome], list[Any]], dict[str, Any]],
        *,
        partition: LoadedPartition | None = None,
        record_id_fn: Callable[[Any, int], str] | None = None,
        export: bool = True,
    ) -> ExperimentResult:
        """Run a full experiment over a loaded partition with deterministic seeding and error accounting."""
        set_random_seed(config.random_seed)
        exp_id = config.deterministic_id()

        loaded = partition or load_evaluation_partition(
            config.dataset_name,
            split=config.split,
            dataset_dir=config.dataset_dir,
            limit=config.limit,
        )

        is_synthetic = bool(config.is_synthetic or loaded.is_synthetic)
        errors: list[ErrorRecord] = list(loaded.invalid_records)
        outcomes: list[SampleOutcome] = []

        t0 = time.perf_counter()
        for idx, rec in enumerate(loaded.records):
            if record_id_fn is not None:
                sid = record_id_fn(rec, idx)
            else:
                sid = str(
                    getattr(rec, "record_id", None)
                    or getattr(rec, "query_id", None)
                    or getattr(rec, "document_id", None)
                    or f"sample_{idx}"
                )

            s_start = time.perf_counter()
            try:
                outcome = evaluate_fn(rec)
                if outcome.latency_ms <= 0.0:
                    outcome.latency_ms = round((time.perf_counter() - s_start) * 1000.0, 4)
                outcomes.append(outcome)
                if outcome.status == "failed":
                    errors.append(
                        ErrorRecord(
                            sample_id=outcome.sample_id or sid,
                            error_type="EvaluationFailure",
                            message=outcome.error or "Unspecified evaluation failure",
                        )
                    )
            except Exception as exc:
                elapsed_ms = round((time.perf_counter() - s_start) * 1000.0, 4)
                err_msg = f"{type(exc).__name__}: {exc}"
                outcomes.append(
                    SampleOutcome(
                        sample_id=sid,
                        status="failed",
                        latency_ms=elapsed_ms,
                        error=err_msg,
                    )
                )
                errors.append(
                    ErrorRecord(
                        sample_id=sid,
                        error_type=type(exc).__name__,
                        message=str(exc),
                    )
                )

        total_elapsed = round(time.perf_counter() - t0, 6)

        successful = [o for o in outcomes if o.status == "success"]
        failed = [o for o in outcomes if o.status == "failed"]
        skipped = [o for o in outcomes if o.status == "skipped"]
        invalid_count = len(loaded.invalid_records) + sum(1 for o in outcomes if o.status == "invalid")

        metrics = metrics_fn(successful, loaded.records)
        metrics["execution_accounting"] = {
            "total_examples": len(loaded.records) + len(loaded.invalid_records),
            "successful_examples": len(successful),
            "failed_examples": len(failed),
            "skipped_examples": len(skipped),
            "invalid_examples": invalid_count,
        }

        result = ExperimentResult(
            experiment_id=exp_id,
            experiment_name=config.experiment_name,
            dataset=config.dataset_name,
            split=config.split,
            dataset_path=str(loaded.partition_path),
            dataset_manifest_checksum=loaded.manifest_checksum,
            partition_file_sha256=loaded.partition_sha256,
            is_synthetic=is_synthetic,
            model=config.model_name,
            backend=config.backend,
            configuration=config.model_dump(mode="json"),
            random_seed=config.random_seed,
            total_examples=len(loaded.records) + len(loaded.invalid_records),
            successful_examples=len(successful),
            failed_examples=len(failed),
            skipped_examples=len(skipped),
            invalid_examples=invalid_count,
            metrics=metrics,
            execution_time_seconds=total_elapsed,
            errors=errors,
            sample_outcomes=outcomes,
        )

        LOGGER.info(
            "Phase 04 experiment completed",
            extra={
                "experiment_id": exp_id,
                "dataset": config.dataset_name,
                "split": config.split,
                "total_examples": result.total_examples,
                "successful_examples": result.successful_examples,
                "failed_examples": result.failed_examples,
                "invalid_examples": result.invalid_examples,
                "execution_time_seconds": total_elapsed,
            },
        )

        if export:
            self.export_result(result)

        return result

    def export_result(
        self,
        result: ExperimentResult,
        *,
        output_dir: str | Path | None = None,
    ) -> dict[str, Path]:
        """Export ExperimentResult to JSON, flattened metrics CSV, and per-sample CSV."""
        out = Path(output_dir) if output_dir else self.output_dir
        out.mkdir(parents=True, exist_ok=True)

        json_path = out / f"{result.experiment_id}.json"
        json_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

        metrics_csv = out / f"{result.experiment_id}_metrics.csv"
        flat_rows = _flatten_dict(result.metrics)
        with metrics_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["experiment_id", "dataset", "split", "is_synthetic", "metric", "value"])
            writer.writeheader()
            for key, val in flat_rows:
                writer.writerow(
                    {
                        "experiment_id": result.experiment_id,
                        "dataset": result.dataset,
                        "split": result.split,
                        "is_synthetic": result.is_synthetic,
                        "metric": key,
                        "value": val,
                    }
                )

        samples_csv = out / f"{result.experiment_id}_samples.csv"
        with samples_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["sample_id", "status", "latency_ms", "prediction", "ground_truth", "error"],
            )
            writer.writeheader()
            for o in result.sample_outcomes:
                writer.writerow(
                    {
                        "sample_id": o.sample_id,
                        "status": o.status,
                        "latency_ms": o.latency_ms,
                        "prediction": json.dumps(o.prediction, ensure_ascii=False)
                        if isinstance(o.prediction, (dict, list))
                        else o.prediction,
                        "ground_truth": json.dumps(o.ground_truth, ensure_ascii=False)
                        if isinstance(o.ground_truth, (dict, list))
                        else o.ground_truth,
                        "error": o.error or "",
                    }
                )

        return {"json": json_path, "metrics_csv": metrics_csv, "samples_csv": samples_csv}


def _flatten_dict(data: dict[str, Any], prefix: str = "") -> list[tuple[str, Any]]:
    """Flatten nested metrics dictionary into (dotted_key, scalar_value) pairs."""
    rows: list[tuple[str, Any]] = []
    for k, v in data.items():
        full_k = f"{prefix}.{k}" if prefix else str(k)
        if isinstance(v, dict):
            rows.extend(_flatten_dict(v, prefix=full_k))
        elif isinstance(v, list):
            rows.append((full_k, json.dumps(v, ensure_ascii=False)))
        else:
            rows.append((full_k, v))
    return rows


__all__ = ["EvaluationRunner"]
