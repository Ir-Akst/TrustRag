"""RSB (RAG Security Bench) dataset adapter for TrustRAG.

Source: arXiv:2505.18543 ("Benchmarking Poisoning Attacks against Retrieval-Augmented Generation")
License: Pending verification / Academic research reference
Access: Local import interface (no public direct download URL)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Union

from trustrag.data.acquisition.local import LocalFileImporter
from trustrag.data.base import BaseAdapter, DatasetMetadata
from trustrag.data.exceptions import AcquisitionError, ValidationError
from trustrag.data.schemas import SecurityRecord

LABEL_MAP: Dict[str, str] = {
    "clean": "CLEAN",
    "benign": "CLEAN",
    "0": "CLEAN",
    "false": "CLEAN",
    "poisoned": "POISONED",
    "poison": "POISONED",
    "attack": "POISONED",
    "1": "POISONED",
    "true": "POISONED",
}


class RSBAdapter(BaseAdapter):
    """Adapter for RSB (RAG Security Bench) poisoning and defense evaluation."""

    metadata = DatasetMetadata(
        name="rsb",
        category="security",
        description="RSB: Unified benchmark for evaluating 13 poisoning attacks and 7 defenses across RAG architectures",
        source_uri="arXiv:2505.18543",
        license="Academic Research / Pending Verification",
        access_type="pending_verification",
        record_type="SecurityRecord",
        paper_reference="Zhang et al., 2025 (arXiv:2505.18543)",
        known_limitations=(
            "No public standalone download URL available at this time. "
            "Local import adapter provided for user-supplied RSB benchmark runs."
        ),
        default_config="targeted_poisoning",
        default_splits=["train", "validation", "test"],
        permitted_for_training=False,  # Security attack evaluation only
        permitted_for_evaluation=True,
    )

    def __init__(
        self,
        *,
        split: str = "test",
        limit: Optional[int] = None,
        cache_dir: Optional[Union[str, Path]] = None,
        offline: bool = False,
        local_path: Optional[Union[str, Path]] = None,
        config_name: Optional[str] = None,
    ) -> None:
        super().__init__(
            split=split,
            limit=limit,
            cache_dir=cache_dir,
            offline=offline,
            config_name=config_name,
        )
        self.local_path = Path(local_path) if local_path else None

    def acquire(self) -> Any:
        if self.local_path and self.local_path.exists():
            return self.local_path

        target = self.cache_dir / f"{self.split}.jsonl"
        if target.exists():
            return target

        raise AcquisitionError(
            "RSB benchmark dataset does not host a verified public direct download link. "
            "Per research integrity guidelines, remote acquisition is marked as pending. "
            f"Please supply benchmark files via local_path or place them in '{self.cache_dir}'."
        )

    def load_raw(self) -> Iterator[Dict[str, Any]]:
        target_path = self.local_path or (self.cache_dir / f"{self.split}.jsonl")
        if not target_path or not target_path.exists():
            self.acquire()

        yield from LocalFileImporter.read_records(target_path, limit=self.limit)

    def transform(self, raw_item: Dict[str, Any]) -> Iterator[SecurityRecord]:
        rid = str(raw_item.get("id") or raw_item.get("record_id") or "")
        passage = str(raw_item.get("passage") or raw_item.get("document") or raw_item.get("text") or "")
        attack_family = raw_item.get("attack_family") or raw_item.get("attack_type")
        attack_subtype = raw_item.get("attack_subtype") or raw_item.get("method")
        target_query = raw_item.get("target_query") or raw_item.get("query")
        target_behavior = raw_item.get("target_behavior") or raw_item.get("target_answer")

        raw_label = raw_item.get("label") or raw_item.get("clean_poison_label") or raw_item.get("is_poisoned")
        mapped_label: Optional[str] = None
        if raw_label is not None:
            key = str(raw_label).strip().lower()
            if key not in LABEL_MAP:
                raise ValidationError(
                    f"Unknown security label '{raw_label}' in RSB record. Allowed source values: {list(LABEL_MAP.keys())}"
                )
            mapped_label = LABEL_MAP[key]

        yield SecurityRecord(
            record_id=rid or f"rsb_{hash(passage)}",
            passage=passage,
            attack_family=str(attack_family) if attack_family else "corpus_poisoning",
            attack_subtype=str(attack_subtype) if attack_subtype else None,
            clean_poison_label=mapped_label,
            trigger_metadata=raw_item.get("trigger_metadata") or raw_item.get("trigger"),
            target_query=str(target_query) if target_query else None,
            target_behavior=str(target_behavior) if target_behavior else None,
            provenance=raw_item.get("provenance") or "RSB_Benchmark",
            source_dataset=self.metadata.name,
            source_id=rid,
            metadata={"metadata": raw_item.get("metadata", {})},
        )


__all__ = ["RSBAdapter"]

