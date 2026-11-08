"""Stanford Question Answering Dataset (SQuAD) adapter for TrustRAG.

Source: rajpurkar/squad
License: CC-BY-SA-4.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Union

from trustrag.data.acquisition.hf import HFAcquisitionHelper
from trustrag.data.acquisition.local import LocalFileImporter
from trustrag.data.base import BaseAdapter, DatasetMetadata
from trustrag.data.schemas import QueryRecord


class SQuADAdapter(BaseAdapter):
    """Adapter for the Stanford Question Answering Dataset (SQuAD)."""

    metadata = DatasetMetadata(
        name="squad",
        category="rag_qa",
        description="Stanford Question Answering Dataset on Wikipedia articles",
        source_uri="rajpurkar/squad",
        license="CC-BY-SA-4.0",
        access_type="open",
        record_type="QueryRecord",
        paper_reference="Rajpurkar et al., 2016 (EMNLP)",
        known_limitations="Crowdsourced queries; answers are exact text spans in context",
        default_config="plain_text",
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
            config_name=self.config_name or "plain_text",
            cache_dir=self.cache_dir,
            limit=self.limit,
            offline=self.offline,
        )

    def transform(self, raw_item: Dict[str, Any]) -> Iterator[QueryRecord]:
        qid = str(raw_item.get("id") or "")
        query = str(raw_item.get("question") or "")
        context = str(raw_item.get("context") or "")
        title = str(raw_item.get("title") or "")

        # Extract answer
        answer_text: Optional[str] = None
        answers = raw_item.get("answers", {})
        if isinstance(answers, dict) and "text" in answers and answers["text"]:
            answer_text = str(answers["text"][0])
        elif isinstance(answers, list) and answers:
            answer_text = str(answers[0])

        yield QueryRecord(
            query_id=qid,
            query=query,
            source_dataset=self.metadata.name,
            source_split=self.split,
            source_id=qid,
            metadata={
                "title": title,
                "context": context,
            },
            relevant_document_ids=[title] if title else [],
            answer=answer_text,
        )


__all__ = ["SQuADAdapter"]

