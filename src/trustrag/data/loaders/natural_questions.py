"""Natural Questions (NQ) dataset adapter for TrustRAG.

Source: google-research-datasets/natural_questions
License: CC-BY-SA-3.0 / Apache-2.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Union

from trustrag.data.acquisition.hf import HFAcquisitionHelper
from trustrag.data.acquisition.local import LocalFileImporter
from trustrag.data.base import BaseAdapter, DatasetMetadata
from trustrag.data.schemas import QueryRecord


class NaturalQuestionsAdapter(BaseAdapter):
    """Adapter for Google's Natural Questions benchmark."""

    metadata = DatasetMetadata(
        name="natural_questions",
        category="rag_qa",
        description="Google Natural Questions: queries and human-annotated answers from Wikipedia",
        source_uri="google-research-datasets/natural_questions",
        license="CC-BY-SA-3.0",
        access_type="open",
        record_type="QueryRecord",
        paper_reference="Kwiatkowski et al., 2019 (TACL)",
        known_limitations="Wikipedia articles from 2019; HTML markup in raw tokens",
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
            config_name=self.config_name,
            cache_dir=self.cache_dir,
            limit=self.limit,
            offline=self.offline,
        )

    def transform(self, raw_item: Dict[str, Any]) -> Iterator[QueryRecord]:
        # Handle both standard NQ formats and simplified local JSON formats
        question_dict = raw_item.get("question", {})
        if isinstance(question_dict, dict):
            query_text = question_dict.get("text", "")
        else:
            query_text = str(raw_item.get("question") or raw_item.get("query") or "")

        qid = str(raw_item.get("id") or raw_item.get("example_id") or raw_item.get("query_id") or "")

        # Extract answer if present
        answer: Optional[str] = None
        annotations = raw_item.get("annotations", [])
        if isinstance(annotations, list) and annotations:
            ann = annotations[0]
            if isinstance(ann, dict):
                short_answers = ann.get("short_answers", [])
                if short_answers and isinstance(short_answers, list):
                    first_sa = short_answers[0]
                    if isinstance(first_sa, dict):
                        answer = first_sa.get("text")
        if not answer:
            answer = raw_item.get("answer") or raw_item.get("reference_answer")

        doc_ids: list[str] = []
        doc_url = raw_item.get("document", {}).get("url") if isinstance(raw_item.get("document"), dict) else None
        if doc_url:
            doc_ids.append(str(doc_url))

        yield QueryRecord(
            query_id=qid,
            query=query_text,
            source_dataset=self.metadata.name,
            source_split=self.split,
            source_id=qid,
            metadata={"document_title": raw_item.get("document", {}).get("title") if isinstance(raw_item.get("document"), dict) else None},
            relevant_document_ids=doc_ids,
            answer=answer,
        )


__all__ = ["NaturalQuestionsAdapter"]

