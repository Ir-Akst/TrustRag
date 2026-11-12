"""Reproducible audit and evaluation harness for external research benchmarks.

Phase 08 Step 08 covers:
- RAGTruth (hallucination / span verification)
- LLM-AggreFact (gated hallucination benchmark; eval-only)
- RSB (RAG Security Bench; local-import pending verification)
- HaluEval-QA (hallucination benchmark)
- Natural Questions, HotpotQA, MS-MARCO (QA & retrieval benchmarks)

Strict research integrity guarantees:
- Never downloads datasets automatically when offline=True.
- Never fabricates metrics for blocked/unavailable corpora (BLOCKED != PASS).
- Explicitly reports when local sample fixtures (< min_research_records) exist
  vs full benchmark parity (parity_claimed stays False on smoke subsets).
"""

from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from trustrag.config.engine_config import MSDConfig, VerificationConfig
from trustrag.data.acquisition.manager import CONFIGURED_TARGETS
from trustrag.data.base import NormalizedRecord
from trustrag.data.exceptions import AcquisitionError, ValidationError
from trustrag.data.registry import get_adapter_class, get_dataset_metadata
from trustrag.data.schemas import ClaimVerificationRecord, QueryRecord, SecurityRecord
from trustrag.detection.msd import MultiSignalDetector
from trustrag.engine.schemas import EvidenceDocument
from trustrag.srm.client import SRMClient
from trustrag.verification.output_verifier import OutputEvidenceVerifier

EXTERNAL_RESEARCH_BENCHMARKS: tuple[str, ...] = (
    "ragtruth",
    "llm_aggrefact",
    "rsb",
    "halueval",
    "natural_questions",
    "hotpotqa",
    "ms_marco",
)

BenchmarkStatus = Literal["COMPLETED", "PARTIALLY_READY", "READY", "BLOCKED"]


class DatasetIntegritySummary(BaseModel):
    """Provenance, schema, duplicate, and split-leakage checks for one benchmark."""

    dataset_name: str
    category: str
    source_uri: str
    license: str
    access_type: str
    paper_reference: str | None = None
    record_type: str
    permitted_for_training: bool
    permitted_for_evaluation: bool
    canonical_target_count: int | None = None
    local_file_paths: list[str] = Field(default_factory=list)
    active_split: str | None = None
    loaded_count: int = 0
    unique_content_hashes: int = 0
    duplicate_count: int = 0
    cross_split_leakage_count: int = 0
    label_distribution: dict[str, int] = Field(default_factory=dict)
    schema_errors: list[str] = Field(default_factory=list)
    known_limitations: str | None = None


class ExternalBenchmarkResult(BaseModel):
    """Execution and integrity outcome for a single external research benchmark."""

    dataset_name: str
    status: BenchmarkStatus
    parity_claimed: bool = False
    reason: str
    seed: int = 42
    evaluated_records: int = 0
    srm_backend_used: str = "disabled"
    metrics: dict[str, float | int | str | None] = Field(default_factory=dict)
    integrity: DatasetIntegritySummary


class ExternalBenchmarkSuiteReport(BaseModel):
    """Aggregated audit and evaluation summary across all 7 research benchmarks."""

    seed: int = 42
    offline: bool = True
    min_research_records: int = 100
    status_counts: dict[str, int] = Field(default_factory=dict)
    results: list[ExternalBenchmarkResult] = Field(default_factory=list)


def _discover_local_files(
    name: str,
    *,
    raw_base_dir: Path,
    processed_base_dir: Path,
    local_path: Path | None,
) -> list[Path]:
    found: list[Path] = []
    if local_path is not None and local_path.exists():
        found.append(local_path)
    for base in (raw_base_dir / name, processed_base_dir / name):
        if base.exists() and base.is_dir():
            for child in sorted(base.iterdir()):
                if (
                    child.is_file()
                    and child.suffix.lower() in {".jsonl", ".json", ".parquet", ".csv"}
                    and child not in found
                ):
                    found.append(child)
    return found


def _select_eval_file(files: list[Path], split: str) -> Path | None:
    if not files:
        return None
    for candidate in files:
        if candidate.name == f"{split}.jsonl":
            return candidate
    for candidate in files:
        if split in candidate.name and "raw_" not in candidate.name:
            return candidate
    non_raw = [f for f in files if not f.name.startswith("raw_")]
    return non_raw[0] if non_raw else files[0]


def _load_records_safe(
    name: str,
    *,
    split: str,
    local_file: Path,
    limit: int | None,
    cache_dir: Path,
) -> tuple[list[NormalizedRecord], list[str]]:
    adapter_cls = get_adapter_class(name)
    adapter = adapter_cls(
        split=split,
        limit=limit,
        cache_dir=cache_dir,
        offline=True,
        local_path=local_file,
    )
    records: list[NormalizedRecord] = []
    errors: list[str] = []
    try:
        for raw_item in adapter.load_raw():
            try:
                for rec in adapter.transform(raw_item):
                    records.append(rec)
            except (ValidationError, ValueError, KeyError, TypeError) as exc:
                errors.append(str(exc))
    except (AcquisitionError, OSError, ValueError) as exc:
        errors.append(str(exc))
    return records, errors


def _extract_label_key(rec: NormalizedRecord) -> str | None:
    if isinstance(rec, ClaimVerificationRecord):
        return rec.label
    if isinstance(rec, SecurityRecord):
        return rec.clean_poison_label or rec.attack_family
    return None


def _compute_binary_classification_metrics(
    y_true: list[int],
    y_pred: list[int],
) -> dict[str, float | int]:
    tp = sum(1 for yt, yp in zip(y_true, y_pred, strict=True) if yt == 1 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred, strict=True) if yt == 0 and yp == 0)
    fp = sum(1 for yt, yp in zip(y_true, y_pred, strict=True) if yt == 0 and yp == 1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred, strict=True) if yt == 1 and yp == 0)
    total = len(y_true)
    accuracy = (tp + tn) / total if total else 0.0
    tpr = tp / (tp + fn) if (tp + fn) else 0.0
    tnr = tn / (tn + fp) if (tn + fp) else 0.0
    balanced_accuracy = 0.5 * (tpr + tnr) if ((tp + fn) and (tn + fp)) else accuracy
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tpr
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    return {
        "accuracy": round(accuracy, 4),
        "balanced_accuracy": round(balanced_accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "fpr": round(fpr, 4),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def audit_external_benchmark(
    name: str,
    *,
    raw_base_dir: str | Path = "data/raw",
    processed_base_dir: str | Path = "data/processed",
    local_path: str | Path | None = None,
    split: str = "test",
    limit: int | None = None,
    min_research_records: int = 100,
) -> tuple[DatasetIntegritySummary, list[NormalizedRecord], BenchmarkStatus, str]:
    """Inspect metadata, local files, schema conformance, duplicates, and cross-split leakage."""
    meta = get_dataset_metadata(name)
    raw_dir = Path(raw_base_dir)
    proc_dir = Path(processed_base_dir)
    loc = Path(local_path) if local_path is not None else None

    files = _discover_local_files(
        name,
        raw_base_dir=raw_dir,
        processed_base_dir=proc_dir,
        local_path=loc,
    )
    summary = DatasetIntegritySummary(
        dataset_name=meta.name,
        category=meta.category,
        source_uri=meta.source_uri,
        license=meta.license,
        access_type=meta.access_type,
        paper_reference=meta.paper_reference,
        record_type=meta.record_type,
        permitted_for_training=meta.permitted_for_training,
        permitted_for_evaluation=meta.permitted_for_evaluation,
        canonical_target_count=CONFIGURED_TARGETS.get(meta.name),
        local_file_paths=[str(p) for p in files],
        known_limitations=meta.known_limitations,
    )

    if not files:
        reason = (
            f"No cached corpus files found locally under '{raw_dir / name}' or '{proc_dir / name}' "
            f"(access_type='{meta.access_type}', source='{meta.source_uri}'). "
            "Remote acquisition disabled in offline verification mode."
        )
        return summary, [], "BLOCKED", reason

    eval_file = _select_eval_file(files, split)
    if eval_file is None:
        return summary, [], "BLOCKED", "No usable local dataset file found."

    records, errors = _load_records_safe(
        name,
        split=split,
        local_file=eval_file,
        limit=limit,
        cache_dir=raw_dir / name,
    )
    summary.active_split = split
    summary.schema_errors = errors
    summary.loaded_count = len(records)

    hashes = [r.content_hash for r in records if r.content_hash]
    unique_hashes = set(hashes)
    summary.unique_content_hashes = len(unique_hashes)
    summary.duplicate_count = max(0, len(hashes) - len(unique_hashes))

    labels = Counter(lbl for r in records if (lbl := _extract_label_key(r)) is not None)
    summary.label_distribution = dict(labels)

    # Check leakage against any non-eval split cached in raw_dir/name (e.g. train.jsonl)
    train_candidates = [f for f in files if f != eval_file and "train" in f.name and "raw_" not in f.name]
    leak_hashes: set[str] = set()
    for tf in train_candidates:
        tr_recs, _ = _load_records_safe(
            name,
            split="train",
            local_file=tf,
            limit=limit,
            cache_dir=raw_dir / name,
        )
        tr_hash_set = {r.content_hash for r in tr_recs if r.content_hash}
        leak_hashes.update(unique_hashes & tr_hash_set)
    summary.cross_split_leakage_count = len(leak_hashes)

    if errors or not records:
        return (
            summary,
            records,
            "BLOCKED",
            f"Adapter validation failed or produced 0 records from '{eval_file}' ({len(errors)} error(s)).",
        )

    if len(records) < min_research_records:
        return (
            summary,
            records,
            "PARTIALLY_READY",
            (
                f"Local file '{eval_file.name}' validated ({len(records)} records), below research "
                f"scale threshold ({min_research_records} vs canonical target "
                f"{summary.canonical_target_count}); full research parity remains BLOCKED offline."
            ),
        )

    return (
        summary,
        records,
        "READY",
        f"Local corpus file '{eval_file.name}' validated cleanly ({len(records)} records).",
    )


def run_external_benchmark(
    name: str,
    *,
    raw_base_dir: str | Path = "data/raw",
    processed_base_dir: str | Path = "data/processed",
    local_path: str | Path | None = None,
    split: str = "test",
    limit: int | None = None,
    seed: int = 42,
    min_research_records: int = 100,
    srm_client: SRMClient | None = None,
) -> ExternalBenchmarkResult:
    """Audit and deterministically evaluate an external benchmark if local data is available."""
    summary, records, audit_status, audit_reason = audit_external_benchmark(
        name,
        raw_base_dir=raw_base_dir,
        processed_base_dir=processed_base_dir,
        local_path=local_path,
        split=split,
        limit=limit,
        min_research_records=min_research_records,
    )
    srm_backend = srm_client.config.backend if srm_client is not None else "disabled"

    if audit_status == "BLOCKED":
        return ExternalBenchmarkResult(
            dataset_name=name,
            status="BLOCKED",
            parity_claimed=False,
            reason=audit_reason,
            seed=seed,
            evaluated_records=0,
            srm_backend_used=srm_backend,
            metrics={},
            integrity=summary,
        )

    # Evaluate deterministically according to record schema
    first = records[0]
    if isinstance(first, ClaimVerificationRecord):
        verifier = OutputEvidenceVerifier(
            VerificationConfig(enable_query_consistency=False),
            srm_client=srm_client,
        )
        y_true: list[int] = []
        y_pred: list[int] = []
        false_supported = 0
        hallucinated_total = 0

        for idx, rec in enumerate(records):
            if not isinstance(rec, ClaimVerificationRecord):
                continue
            doc = EvidenceDocument(
                doc_id=rec.record_id or f"{name}_{idx}",
                text=rec.document,
                source_dataset=rec.source_dataset,
                source_id=rec.source_id or "",
                provenance=rec.source_dataset,
            )
            # Claim text is deterministic input; inspect verifier claim grounding directly
            rep = verifier.verify(rec.claim, [doc], query=str(rec.metadata.get("query") or ""))
            is_hallucinated = 1 if rec.label.upper() == "HALLUCINATED" else 0
            pred_hallucinated = 1 if rep.verdict != "SUPPORTED" else 0
            y_true.append(is_hallucinated)
            y_pred.append(pred_hallucinated)
            if is_hallucinated == 1:
                hallucinated_total += 1
                if rep.verdict == "SUPPORTED":
                    false_supported += 1

        metrics: dict[str, float | int | str | None] = dict(
            _compute_binary_classification_metrics(y_true, y_pred)
        )
        metrics["false_supported_rate"] = round(
            false_supported / hallucinated_total if hallucinated_total else 0.0,
            4,
        )
        final_status: BenchmarkStatus = "COMPLETED" if len(records) >= min_research_records else "PARTIALLY_READY"
        return ExternalBenchmarkResult(
            dataset_name=name,
            status=final_status,
            parity_claimed=False,
            reason=audit_reason,
            seed=seed,
            evaluated_records=len(y_true),
            srm_backend_used=srm_backend,
            metrics=metrics,
            integrity=summary,
        )

    if isinstance(first, SecurityRecord):
        detector = MultiSignalDetector(MSDConfig())
        y_true_sec: list[int] = []
        y_pred_sec: list[int] = []
        grouped: dict[str, list[SecurityRecord]] = {}
        for rec in records:
            if isinstance(rec, SecurityRecord):
                grouped.setdefault(rec.target_query or "default_query", []).append(rec)

        for q, group in grouped.items():
            docs = [
                EvidenceDocument(
                    doc_id=r.record_id or f"{name}_{i}",
                    text=r.passage or r.document or "",
                    source_dataset=r.source_dataset,
                    source_id=r.source_id or "",
                    provenance=r.provenance or r.source_dataset,
                )
                for i, r in enumerate(group)
            ]
            assessments = detector.assess_candidates(q, docs, [0.75] * len(docs))
            for r, a in zip(group, assessments, strict=True):
                is_poison = 1 if (r.clean_poison_label or "").upper() == "POISONED" else 0
                pred_poison = 1 if a.trust_score < detector.config.trust_threshold else 0
                y_true_sec.append(is_poison)
                y_pred_sec.append(pred_poison)

        sec_metrics: dict[str, float | int | str | None] = dict(
            _compute_binary_classification_metrics(y_true_sec, y_pred_sec)
        )
        final_sec_status: BenchmarkStatus = "COMPLETED" if len(records) >= min_research_records else "PARTIALLY_READY"
        return ExternalBenchmarkResult(
            dataset_name=name,
            status=final_sec_status,
            parity_claimed=False,
            reason=audit_reason,
            seed=seed,
            evaluated_records=len(y_true_sec),
            srm_backend_used=srm_backend,
            metrics=sec_metrics,
            integrity=summary,
        )

    # QueryRecord (NQ / HotpotQA / MS-MARCO)
    with_ans = sum(1 for r in records if isinstance(r, QueryRecord) and bool(r.answer))
    with_rel_docs = sum(1 for r in records if isinstance(r, QueryRecord) and bool(r.relevant_document_ids))
    # Query-only QA benchmark without bundled passage corpus can validate schema, not full retrieval parity
    qa_status: BenchmarkStatus = (
        "COMPLETED" if (len(records) >= min_research_records and with_rel_docs > 0 and with_ans > 0) else "PARTIALLY_READY"
    )
    return ExternalBenchmarkResult(
        dataset_name=name,
        status=qa_status,
        parity_claimed=False,
        reason=audit_reason,
        seed=seed,
        evaluated_records=len(records),
        srm_backend_used=srm_backend,
        metrics={
            "query_count": len(records),
            "with_reference_answer": with_ans,
            "with_relevant_doc_ids": with_rel_docs,
            "dataset_digest": hashlib.sha256(
                "|".join(r.content_hash for r in records[:100]).encode("utf-8")
            ).hexdigest()[:16],
        },
        integrity=summary,
    )


def run_all_external_benchmarks(
    benchmarks: tuple[str, ...] = EXTERNAL_RESEARCH_BENCHMARKS,
    *,
    raw_base_dir: str | Path = "data/raw",
    processed_base_dir: str | Path = "data/processed",
    seed: int = 42,
    min_research_records: int = 100,
    srm_client: SRMClient | None = None,
) -> ExternalBenchmarkSuiteReport:
    """Audit and execute all configured external research benchmarks."""
    results = [
        run_external_benchmark(
            name,
            raw_base_dir=raw_base_dir,
            processed_base_dir=processed_base_dir,
            seed=seed,
            min_research_records=min_research_records,
            srm_client=srm_client,
        )
        for name in benchmarks
    ]
    counts: Counter[str] = Counter(str(r.status) for r in results)
    return ExternalBenchmarkSuiteReport(
        seed=seed,
        offline=True,
        min_research_records=min_research_records,
        status_counts=dict(counts),
        results=results,
    )
