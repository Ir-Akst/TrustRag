"""HotpotQA dataset adapter for TrustRAG.

Source: hotpotqa/hotpot_qa
License: CC-BY-SA-4.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Union

from trustrag.data.acquisition.hf import HFAcquisitionHelper
from trustrag.data.acquisition.local import LocalFileImporter
from trustrag.data.base import BaseAdapter, DatasetMetadata
from trustrag.data.schemas import QueryRecord


class HotpotQAAdapter(BaseAdapter):
    """Adapter for HotpotQA multi-hop question answering benchmark."""

    metadata = DatasetMetadata(
        name="hotpotqa",
        category="rag_qa",
        description="HotpotQA multi-hop reasoning benchmark with supporting Wikipedia facts",
        source_uri="hotpotqa/hotpot_qa",
        license="CC-BY-SA-4.0",
        access_type="open",
        record_type="QueryRecord",
        paper_reference="Yang et al., 2018 (EMNLP)",
        known_limitations="Requires multi-hop reasoning; distractors synthetic",
        default_config="distractor",
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
            config_name=self.config_name or "distractor",
            cache_dir=self.cache_dir,
            limit=self.limit,
            offline=self.offline,
        )

    def transform(self, raw_item: Dict[str, Any]) -> Iterator[QueryRecord]:
        qid = str(raw_item.get("id") or raw_item.get("_id") or "")
        question = str(raw_item.get("question") or "")
        answer = str(raw_item.get("answer") or "")

        # Extract supporting fact titles as relevant document ids
        relevant_doc_ids: list[str] = []
        supporting_facts = raw_item.get("supporting_facts", {})
        if isinstance(supporting_facts, dict) and "title" in supporting_facts:
            relevant_doc_ids = [str(t) for t in supporting_facts["title"]]
        elif isinstance(supporting_facts, list):
            for fact in supporting_facts:
                if isinstance(fact, (list, tuple)) and len(fact) > 0:
                    relevant_doc_ids.append(str(fact[0]))

        yield QueryRecord(
            query_id=qid,
            query=question,
            source_dataset=self.metadata.name,
            source_split=self.split,
            source_id=qid,
            metadata={
                "level": raw_item.get("level"),
                "type": raw_item.get("type"),
            },
            relevant_document_ids=relevant_doc_ids,
            answer=answer if answer else None,
        )


__all__ = ["HotpotQAAdapter"]

