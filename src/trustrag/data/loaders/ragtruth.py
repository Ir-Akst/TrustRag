"""RAGTruth hallucination detection benchmark adapter for TrustRAG.

Source: https://github.com/ParticleMedia/RAGTruth
License: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Union

from trustrag.data.acquisition.local import LocalFileImporter
from trustrag.data.base import BaseAdapter, DatasetMetadata
from trustrag.data.exceptions import AcquisitionError, ValidationError
from trustrag.data.schemas import ClaimVerificationRecord

LABEL_MAP: Dict[str, str] = {
    "hallucinated": "HALLUCINATED",
    "hallucination": "HALLUCINATED",
    "true": "HALLUCINATED",
    "1": "HALLUCINATED",
    "factual": "FACTUAL",
    "non-hallucinated": "FACTUAL",
    "false": "FACTUAL",
    "0": "FACTUAL",
}


class RAGTruthAdapter(BaseAdapter):
    """Adapter for RAGTruth benchmark: word-level and sentence-level hallucination detection."""

    metadata = DatasetMetadata(
        name="ragtruth",
        category="hallucination",
        description="RAGTruth: Hallucination detection benchmark for Retrieval-Augmented Generation across QA, Summarization, and Data-to-Text",
        source_uri="https://github.com/ParticleMedia/RAGTruth",
        license="MIT",
        access_type="open",
        record_type="ClaimVerificationRecord",
        paper_reference="Niu et al., 2024 (ACL/EMNLP)",
        known_limitations="Requires structured responses from multiple LLMs; spans annotated by crowdworkers",
        default_config="qa",
        default_splits=["train", "validation", "test"],
        permitted_for_training=True,
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
        if self.offline:
            raise AcquisitionError(
                f"RAGTruth dataset file '{target}' unavailable in offline mode. "
                "Provide a local_path or import raw data from https://github.com/ParticleMedia/RAGTruth"
            )
        # Marked as local-import preferred
        raise AcquisitionError(
            "RAGTruth requires cloning or downloading files from https://github.com/ParticleMedia/RAGTruth. "
            f"Please place dataset files in '{self.cache_dir}' or specify local_path."
        )

    def load_raw(self) -> Iterator[Dict[str, Any]]:
        target_path = self.local_path or (self.cache_dir / f"{self.split}.jsonl")
        if not target_path or not target_path.exists():
            # Check for alternative file in cache_dir
            alt = self.cache_dir / "ragtruth.jsonl"
            if alt.exists():
                target_path = alt
            else:
                self.acquire()

        yield from LocalFileImporter.read_records(target_path, limit=self.limit)

    def transform(self, raw_item: Dict[str, Any]) -> Iterator[ClaimVerificationRecord]:
        rid = str(raw_item.get("id") or raw_item.get("sample_id") or "")
        passage = str(raw_item.get("passage") or raw_item.get("source_info") or raw_item.get("context") or "")
        response = str(raw_item.get("response") or raw_item.get("generation") or raw_item.get("claim") or "")

        # Determine label
        raw_label = raw_item.get("label")
        if raw_label is None:
            # Check for labels list or span annotations
            labels_list = raw_item.get("labels")
            if isinstance(labels_list, list):
                # If any hallucination spans exist
                raw_label = "hallucinated" if len(labels_list) > 0 else "factual"
            elif raw_item.get("has_hallucination") is not None:
                raw_label = raw_item.get("has_hallucination")
            else:
                raise ValidationError(f"Missing hallucination label in RAGTruth record: {raw_item}")

        key = str(raw_label).strip().lower()
        if key not in LABEL_MAP:
            raise ValidationError(
                f"Unknown label '{raw_label}' in RAGTruth record. Allowed source values: {list(LABEL_MAP.keys())}"
            )

        mapped_label = LABEL_MAP[key]

        yield ClaimVerificationRecord(
            record_id=rid or f"ragtruth_{hash(response)}",
            document=passage,
            claim=response,
            label=mapped_label,
            justification=raw_item.get("justification"),
            source_dataset=self.metadata.name,
            source_split=self.split,
            source_id=rid,
            metadata={
                "task": raw_item.get("task_type") or raw_item.get("task"),
                "model": raw_item.get("model"),
            },
        )


__all__ = ["RAGTruthAdapter"]

