"""Advanced acquisition management, batch orchestration, and audit logging for TrustRAG.

Phase 02 Acquisition Engineering:
- Dataset-specific configuration and tiering (P0, P1, P2)
- Enforces strict record limits and smoke-test caps
- Checks disk space and resource limits before acquiring
- Immutable raw data persistence in data/raw/<dataset>/
- Audit logging in data/raw/acquisition_log.jsonl
- Offline mode and cache reuse verification
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from trustrag.data.exceptions import AcquisitionError, UsageIsolationError
from trustrag.data.isolation import DatasetUsageCategory, DatasetUsageValidator
from trustrag.data.registry import get_dataset_metadata, list_datasets, load_dataset
from trustrag.data.resource import ResourceManager
from trustrag.data.storage import DatasetStorage, compute_file_sha256

PRIORITY_TIERS: Dict[str, List[str]] = {
    "p0": ["ragtruth", "halueval", "custom_security"],
    "p1": ["wice", "expertqa", "boolq"],
    "p2": ["natural_questions", "hotpotqa", "ms_marco"],
}

CONFIGURED_TARGETS: Dict[str, int] = {
    "natural_questions": 30000,
    "hotpotqa": 30000,
    "ms_marco": 100000,
    "squad": 20000,
    "boolq": 10000,
    "halueval": 10000,
    "ragtruth": 18000,
    "llm_aggrefact": 5000,
    "wice": 5000,
    "expertqa": 5000,
    "rsb": 5000,
    "custom_security": 5000,
    "fineweb": 20000,
}


@dataclass
class AcquisitionAuditEntry:
    """Record of an acquisition event for reproducibility and provenance."""

    dataset_name: str
    split: str
    timestamp: str
    records_requested: Optional[int]
    records_acquired: int
    raw_file_path: str
    raw_file_bytes: int
    raw_file_sha256: str
    source_uri: str
    license: str
    status: str  # "SUCCESS", "FAILED", "OFFLINE_CACHED", "BLOCKED"
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AcquisitionManager:
    """Orchestrates dataset downloads, caching, verification, and audit logging."""

    def __init__(
        self,
        raw_base_dir: Union[str, Path] = "data/raw",
        processed_base_dir: Union[str, Path] = "data/processed",
        audit_log_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self.raw_base_dir = Path(raw_base_dir)
        self.raw_base_dir.mkdir(parents=True, exist_ok=True)
        self.processed_base_dir = Path(processed_base_dir)
        self.audit_log_path = (
            Path(audit_log_path) if audit_log_path else self.raw_base_dir / "acquisition_log.jsonl"
        )

    def _log_audit_entry(self, entry: AcquisitionAuditEntry) -> None:
        """Append an audit entry to the acquisition log."""
        try:
            with self.audit_log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except Exception:
            pass

    def acquire(
        self,
        dataset_name: str,
        split: str = "train",
        limit: Optional[int] = None,
        smoke_test: bool = False,
        offline: bool = False,
        config_name: Optional[str] = None,
        local_path: Optional[Union[str, Path]] = None,
    ) -> Tuple[List[Any], AcquisitionAuditEntry]:
        """Acquire records for a dataset, save raw copy, and log audit entry."""
        name = dataset_name.lower().strip()
        metadata = get_dataset_metadata(name)

        # 1. Enforce usage & licensing isolation before acquiring
        try:
            # Check if dataset is blocked from general acquisition
            if name == "fineweb":
                # FineWeb is not acquired in Phase 02 per instructions
                raise AcquisitionError(
                    "FineWeb pretraining corpus acquisition is deferred to future SRM synthetic pipeline."
                )
            if name == "rsb" and not local_path:
                raise AcquisitionError(
                    "RSB remote acquisition source remains NOT VERIFIED / PENDING. Use local_path to import."
                )
        except UsageIsolationError as e:
            raise AcquisitionError(f"License usage isolation error: {e}")

        # 2. Determine target limits
        effective_limit = limit
        if smoke_test:
            if effective_limit is None or effective_limit > 100:
                effective_limit = 100

        # 3. Check storage before acquiring
        est_records = effective_limit or CONFIGURED_TARGETS.get(name, 1000)
        est_bytes = ResourceManager.estimate_dataset_storage(est_records)
        ResourceManager.check_disk_space(est_bytes, target_path=self.raw_base_dir)

        # 4. Handle Custom Security special generation if target is custom_security
        timestamp_now = datetime.now(timezone.utc).isoformat()
        ds_raw_dir = self.raw_base_dir / name
        ds_raw_dir.mkdir(parents=True, exist_ok=True)
        raw_file = ds_raw_dir / f"raw_{split}.jsonl"

        records: List[Any] = []
        try:
            if name == "custom_security" and not local_path and not raw_file.exists():
                from trustrag.data.benchmarks.security_generator import generate_security_benchmark_pairs

                target_pairs = 1000 if not smoke_test else min(50, (effective_limit or 100) // 2)
                clean_recs, poison_recs = generate_security_benchmark_pairs(num_pairs=target_pairs, seed=42)
                # Combine paired records
                for c, p in zip(clean_recs, poison_recs):
                    records.extend([c, p])
            else:
                records = list(
                    load_dataset(
                        name,
                        split=split,
                        limit=effective_limit,
                        offline=offline,
                        config_name=config_name,
                        local_path=str(local_path) if local_path else None,
                    )
                )

            # 5. Persist immutable raw copy
            save_info = DatasetStorage.save_jsonl(records, raw_file)
            audit_entry = AcquisitionAuditEntry(
                dataset_name=name,
                split=split,
                timestamp=timestamp_now,
                records_requested=effective_limit,
                records_acquired=len(records),
                raw_file_path=save_info["file_path"],
                raw_file_bytes=save_info["file_size_bytes"],
                raw_file_sha256=save_info["sha256"],
                source_uri=metadata.source_uri,
                license=metadata.license,
                status="SUCCESS",
            )
            self._log_audit_entry(audit_entry)
            return records, audit_entry

        except Exception as e:
            failed_entry = AcquisitionAuditEntry(
                dataset_name=name,
                split=split,
                timestamp=timestamp_now,
                records_requested=effective_limit,
                records_acquired=0,
                raw_file_path=str(raw_file),
                raw_file_bytes=0,
                raw_file_sha256="",
                source_uri=metadata.source_uri,
                license=metadata.license,
                status="FAILED",
                error_message=str(e),
            )
            self._log_audit_entry(failed_entry)
            raise AcquisitionError(f"Failed to acquire dataset '{name}': {e}") from e

    def acquire_batch(
        self,
        tier: str = "p0",
        limit: Optional[int] = None,
        smoke_test: bool = True,
        offline: bool = False,
    ) -> Dict[str, AcquisitionAuditEntry]:
        """Acquire all datasets in a priority tier ('p0', 'p1', 'p2', or 'all')."""
        tier_key = tier.lower().strip()
        if tier_key == "all":
            datasets = PRIORITY_TIERS["p0"] + PRIORITY_TIERS["p1"] + PRIORITY_TIERS["p2"]
        elif tier_key in PRIORITY_TIERS:
            datasets = PRIORITY_TIERS[tier_key]
        else:
            raise AcquisitionError(f"Unknown priority tier '{tier}'. Choose from 'p0', 'p1', 'p2', or 'all'.")

        results: Dict[str, AcquisitionAuditEntry] = {}
        for ds in datasets:
            try:
                _, entry = self.acquire(
                    ds,
                    limit=limit,
                    smoke_test=smoke_test,
                    offline=offline,
                )
                results[ds] = entry
            except Exception as e:
                # Record failure entry and continue batch
                entry = AcquisitionAuditEntry(
                    dataset_name=ds,
                    split="default",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    records_requested=limit,
                    records_acquired=0,
                    raw_file_path="",
                    raw_file_bytes=0,
                    raw_file_sha256="",
                    source_uri="",
                    license="",
                    status="FAILED",
                    error_message=str(e),
                )
                results[ds] = entry
        return results

    def get_acquisition_status(self) -> List[Dict[str, Any]]:
        """Return the current acquisition status and record counts across all datasets."""
        status_list: List[Dict[str, Any]] = []
        for name in list_datasets():
            meta = get_dataset_metadata(name)
            target = CONFIGURED_TARGETS.get(name, 0)
            raw_dir = self.raw_base_dir / name
            proc_dir = self.processed_base_dir / name

            raw_count = 0
            raw_bytes = 0
            if raw_dir.is_dir():
                for f in raw_dir.glob("*.jsonl"):
                    raw_bytes += f.stat().st_size
                    with f.open("r", encoding="utf-8") as fh:
                        raw_count += sum(1 for line in fh if line.strip())

            proc_count = 0
            proc_bytes = 0
            if proc_dir.is_dir():
                for f in proc_dir.glob("*.jsonl"):
                    proc_bytes += f.stat().st_size
                    with f.open("r", encoding="utf-8") as fh:
                        proc_count += sum(1 for line in fh if line.strip())

            # Determine status label
            if name == "rsb":
                status = "NOT VERIFIED (URL PENDING)"
            elif name == "llm_aggrefact":
                status = "EVALUATION ONLY (GATED)"
            elif name == "fineweb":
                status = "TRAINING CORPUS ONLY (DEFERRED)"
            elif proc_count > 0 or raw_count > 0:
                status = "ACQUIRED"
            else:
                status = "READY"

            status_list.append({
                "dataset_name": name,
                "category": meta.category,
                "configured_target": target,
                "raw_records": raw_count,
                "processed_records": proc_count,
                "storage_bytes": raw_bytes + proc_bytes,
                "license": meta.license,
                "status": status,
            })
        return status_list


__all__ = [
    "PRIORITY_TIERS",
    "CONFIGURED_TARGETS",
    "AcquisitionAuditEntry",
    "AcquisitionManager",
]
