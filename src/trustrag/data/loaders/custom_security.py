"""Custom TrustRAG security and corpus poisoning dataset adapter.

Schema for future custom attack examples and defense benchmark datasets.
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


class CustomSecurityAdapter(BaseAdapter):
    """Adapter for custom TrustRAG security examples (clean vs. adversarial/poisoned)."""

    metadata = DatasetMetadata(
        name="custom_security",
        category="security",
        description="Custom TrustRAG security benchmark: paired clean and poisoned corpus passages for defense evaluation",
        source_uri="trustrag/internal_security",
        license="MIT",
        access_type="local_only",
        record_type="SecurityRecord",
        paper_reference="TrustRAG Research Paper Reference",
        known_limitations="Custom curated or synthetic adversarial examples",
        default_config="default",
        default_splits=["train", "validation", "test"],
        permitted_for_training=True,
        permitted_for_evaluation=True,
    )

    def __init__(
        self,
        *,
        split: str = "train",
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
            f"Custom security dataset file not found at '{target}'. "
            "Please provide a path via local_path or create data in the cache directory."
        )

    def load_raw(self) -> Iterator[Dict[str, Any]]:
        target_path = self.local_path or (self.cache_dir / f"{self.split}.jsonl")
        if not target_path or not target_path.exists():
            self.acquire()

        yield from LocalFileImporter.read_records(target_path, limit=self.limit)

    def transform(self, raw_item: Dict[str, Any]) -> Iterator[SecurityRecord]:
        rid = str(raw_item.get("record_id") or raw_item.get("id") or "")
        passage = str(raw_item.get("passage") or raw_item.get("document") or raw_item.get("text") or "")
        attack_family = raw_item.get("attack_family") or "corpus_poisoning"
        attack_subtype = raw_item.get("attack_subtype") or "targeted_injection"
        target_query = raw_item.get("target_query") or raw_item.get("query")
        target_behavior = raw_item.get("target_behavior")
        source_id = str(raw_item.get("source_id") or raw_item.get("parent_document_id") or rid)

        raw_label = raw_item.get("clean_poison_label") or raw_item.get("label") or raw_item.get("is_poisoned")
        if raw_label is None:
            raise ValidationError(f"Missing clean/poison label in security record: {raw_item}")

        key = str(raw_label).strip().lower()
        if key not in LABEL_MAP:
            raise ValidationError(
                f"Unknown security label '{raw_label}'. Allowed: {list(LABEL_MAP.keys())}"
            )

        mapped_label = LABEL_MAP[key]

        yield SecurityRecord(
            record_id=rid,
            passage=passage,
            attack_family=str(attack_family),
            attack_subtype=str(attack_subtype),
            clean_poison_label=mapped_label,
            trigger_metadata=raw_item.get("trigger_metadata") or raw_item.get("trigger"),
            target_query=str(target_query) if target_query else None,
            target_behavior=str(target_behavior) if target_behavior else None,
            provenance=raw_item.get("provenance") or "TrustRAG_Security_Suite",
            source_dataset=self.metadata.name,
            source_id=source_id,
            metadata={"metadata": raw_item.get("metadata", {})},
        )


__all__ = ["CustomSecurityAdapter"]

