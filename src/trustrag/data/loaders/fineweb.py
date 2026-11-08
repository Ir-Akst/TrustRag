"""FineWeb training corpus adapter for TrustRAG.

Source: HuggingFaceFW/fineweb
License: Open Data Commons Attribution License (ODC-By) 1.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Union

from trustrag.data.acquisition.hf import HFAcquisitionHelper
from trustrag.data.acquisition.local import LocalFileImporter
from trustrag.data.base import BaseAdapter, DatasetMetadata
from trustrag.data.schemas import DocumentRecord


class FineWebAdapter(BaseAdapter):
    """Adapter for FineWeb: large-scale web crawl corpus for training and retrieval grounding."""

    metadata = DatasetMetadata(
        name="fineweb",
        category="training_corpus",
        description="FineWeb: High-quality English web dataset filtered and deduplicated from Common Crawl",
        source_uri="HuggingFaceFW/fineweb",
        license="ODC-By-1.0",
        access_type="open",
        record_type="DocumentRecord",
        paper_reference="Penedo et al., 2024 (Hugging Face)",
        known_limitations="Massive web crawl corpus; must only sample small subsets with strict record limits",
        default_config="sample-10BT",
        default_splits=["train"],
        permitted_for_training=True,
        permitted_for_evaluation=False,  # Treat as training corpus, not evaluation benchmark
    )

    def __init__(
        self,
        *,
        split: str = "train",
        limit: Optional[int] = 100,  # Default to safe small limit
        cache_dir: Optional[Union[str, Path]] = None,
        offline: bool = False,
        local_path: Optional[Union[str, Path]] = None,
        config_name: Optional[str] = "sample-10BT",
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
        return self.cache_dir

    def load_raw(self) -> Iterator[Dict[str, Any]]:
        if self.local_path and self.local_path.exists():
            yield from LocalFileImporter.read_records(self.local_path, limit=self.limit)
            return

        # Uses streaming=True to ensure the multi-terabyte dataset is NEVER downloaded fully
        yield from HFAcquisitionHelper.load_hf_records(
            self.metadata.source_uri,
            split=self.split,
            config_name=self.config_name or "sample-10BT",
            cache_dir=self.cache_dir,
            limit=self.limit,
            offline=self.offline,
            streaming=True,
        )

    def transform(self, raw_item: Dict[str, Any]) -> Iterator[DocumentRecord]:
        doc_id = str(raw_item.get("id") or raw_item.get("doc_id") or "")
        text = str(raw_item.get("text") or raw_item.get("content") or "")

        yield DocumentRecord(
            document_id=doc_id,
            text=text,
            source_dataset=self.metadata.name,
            source_split=self.split,
            source_id=doc_id,
            metadata={
                "url": raw_item.get("url"),
                "date": raw_item.get("date"),
                "dump": raw_item.get("dump"),
            },
            license="ODC-By-1.0",
            provenance="HuggingFaceFW/fineweb",
        )


__all__ = ["FineWebAdapter"]

