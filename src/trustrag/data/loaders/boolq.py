"""Google BoolQ dataset adapter for TrustRAG.

Source: google/boolq
License: CC-BY-SA-3.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Union

from trustrag.data.acquisition.hf import HFAcquisitionHelper
from trustrag.data.acquisition.local import LocalFileImporter
from trustrag.data.base import BaseAdapter, DatasetMetadata
from trustrag.data.schemas import QueryRecord


class BoolQAdapter(BaseAdapter):
    """Adapter for Google's BoolQ boolean question answering benchmark."""

    metadata = DatasetMetadata(
        name="boolq",
        category="rag_qa",
        description="Google BoolQ: naturally occurring yes/no queries with Wikipedia passages",
        source_uri="google/boolq",
        license="CC-BY-SA-3.0",
        access_type="open",
        record_type="QueryRecord",
        paper_reference="Clark et al., 2019 (NAACL)",
        known_limitations="Binary yes/no answers only",
        default_config="default",
        default_splits=["train", "validation"],
        permitted_for_training=True,
        permitted_for_evaluation=True,
    )

    def __init__(
        self,
        *,
        split: str = "validation",
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
        return self.cache_dir

    def load_raw(self) -> Iterator[Dict[str, Any]]:
        if self.local_path and self.local_path.exists():
            yield from LocalFileImporter.read_records(self.local_path, limit=self.limit)
            return

        yield from HFAcquisitionHelper.load_hf_records(
            self.metadata.source_uri,
            split=self.split,
            config_name=self.config_name or "default",
            cache_dir=self.cache_dir,
            limit=self.limit,
            offline=self.offline,
        )

    def transform(self, raw_item: Dict[str, Any]) -> Iterator[QueryRecord]:
        question = str(raw_item.get("question") or raw_item.get("query") or "")
        meta_dict = raw_item.get("metadata", {}) if isinstance(raw_item.get("metadata"), dict) else {}
        title = str(raw_item.get("title") or meta_dict.get("title") or "")
        passage = str(raw_item.get("passage") or meta_dict.get("passage") or "")
        answer_val = raw_item.get("answer")

        # Map boolean answer to string representation
        if isinstance(answer_val, bool):
            answer_str = "yes" if answer_val else "no"
        elif answer_val is not None:
            answer_str = str(answer_val).lower()
        else:
            answer_str = None

        qid = str(raw_item.get("id") or f"{title}_{question[:30]}")

        yield QueryRecord(
            query_id=qid,
            query=question,
            source_dataset=self.metadata.name,
            source_split=self.split,
            source_id=qid,
            metadata={
                "title": title,
                "passage": passage,
            },
            relevant_document_ids=[title] if title else [],
            answer=answer_str,
        )


__all__ = ["BoolQAdapter"]
