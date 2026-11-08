"""MS MARCO dataset adapter for TrustRAG.

Source: microsoft/ms_marco
License: Microsoft Research License / CC-BY-4.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Union

from trustrag.data.acquisition.hf import HFAcquisitionHelper
from trustrag.data.acquisition.local import LocalFileImporter
from trustrag.data.base import BaseAdapter, DatasetMetadata
from trustrag.data.schemas import QueryRecord


class MSMarcoAdapter(BaseAdapter):
    """Adapter for Microsoft MARCO question answering and passage ranking benchmark."""

    metadata = DatasetMetadata(
        name="ms_marco",
        category="rag_qa",
        description="Microsoft Machine Reading Comprehension dataset based on Bing queries",
        source_uri="microsoft/ms_marco",
        license="Microsoft Research License",
        access_type="open",
        record_type="QueryRecord",
        paper_reference="Nguyen et al., 2016 (NeurIPS Workshop)",
        known_limitations="Real-world noisy Bing web queries; non-commercial license",
        default_config="v1.1",
        default_splits=["train", "validation", "test"],
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
            config_name=self.config_name or "v1.1",
            cache_dir=self.cache_dir,
            limit=self.limit,
            offline=self.offline,
        )

    def transform(self, raw_item: Dict[str, Any]) -> Iterator[QueryRecord]:
        qid = str(raw_item.get("query_id") or raw_item.get("id") or "")
        query = str(raw_item.get("query") or "")

        # Extract answers
        answers = raw_item.get("answers", [])
        answer_text: Optional[str] = None
        if isinstance(answers, list) and answers:
            answer_text = str(answers[0])
        elif isinstance(answers, str):
            answer_text = answers

        # Extract selected passage ids if present
        passages = raw_item.get("passages", {})
        relevant_doc_ids: list[str] = []
        if isinstance(passages, dict):
            is_selected = passages.get("is_selected", [])
            for idx, sel in enumerate(is_selected):
                if sel == 1:
                    relevant_doc_ids.append(f"{qid}_p{idx}")

        yield QueryRecord(
            query_id=qid,
            query=query,
            source_dataset=self.metadata.name,
            source_split=self.split,
            source_id=qid,
            metadata={"query_type": raw_item.get("query_type")},
            relevant_document_ids=relevant_doc_ids,
            answer=answer_text,
        )


__all__ = ["MSMarcoAdapter"]

