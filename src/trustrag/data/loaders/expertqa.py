"""ExpertQA factuality benchmark adapter for TrustRAG.

Source: https://github.com/chaitanyamalaviya/ExpertQA / cmalaviya/expertqa
License: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Union

from trustrag.data.acquisition.hf import HFAcquisitionHelper
from trustrag.data.acquisition.local import LocalFileImporter
from trustrag.data.base import BaseAdapter, DatasetMetadata
from trustrag.data.exceptions import AcquisitionError, ValidationError
from trustrag.data.schemas import ClaimVerificationRecord

LABEL_MAP: Dict[str, str] = {
    "factual": "FACTUAL",
    "attributed": "FACTUAL",
    "supported": "FACTUAL",
    "true": "FACTUAL",
    "1": "FACTUAL",
    "hallucinated": "HALLUCINATED",
    "unattributed": "HALLUCINATED",
    "refuted": "HALLUCINATED",
    "unsupported": "HALLUCINATED",
    "false": "HALLUCINATED",
    "0": "HALLUCINATED",
    "ambiguous": "NOT_ENOUGH_INFO",
}


class ExpertQAAdapter(BaseAdapter):
    """Adapter for ExpertQA: expert-curated questions and factual attribution evaluations."""

    metadata = DatasetMetadata(
        name="expertqa",
        category="hallucination",
        description="ExpertQA: Multi-domain factuality dataset evaluated by certified domain experts across 32 fields",
        source_uri="https://github.com/chaitanyamalaviya/ExpertQA",
        license="MIT",
        access_type="open",
        record_type="ClaimVerificationRecord",
        paper_reference="Malaviya et al., 2024 (TACL)",
        known_limitations="Requires deep domain expert validation; spans evaluated against search results",
        default_config="default",
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
        target = self.cache_dir / f"{self.split}.jsonl"
        if target.exists():
            return target
        if self.offline:
            raise AcquisitionError(
                f"ExpertQA dataset file '{target}' unavailable in offline mode. "
                "Download files from https://github.com/chaitanyamalaviya/ExpertQA or pass local_path."
            )
        return self.cache_dir

    def load_raw(self) -> Iterator[Dict[str, Any]]:
        if self.local_path and self.local_path.exists():
            yield from LocalFileImporter.read_records(self.local_path, limit=self.limit)
            return

        target_file = self.cache_dir / f"{self.split}.jsonl"
        if target_file.exists():
            yield from LocalFileImporter.read_records(target_file, limit=self.limit)
            return

        # Attempt to load from HF mirror if available
        try:
            yield from HFAcquisitionHelper.load_hf_records(
                "cmalaviya/expertqa",
                split=self.split,
                config_name=self.config_name,
                cache_dir=self.cache_dir,
                limit=self.limit,
                offline=self.offline,
            )
        except Exception:
            raise AcquisitionError(
                "ExpertQA raw files not found. Download 'r2_compiled_anon.jsonl' from "
                "https://github.com/chaitanyamalaviya/ExpertQA and pass via local_path."
            )

    def transform(self, raw_item: Dict[str, Any]) -> Iterator[ClaimVerificationRecord]:
        rid = str(raw_item.get("id") or raw_item.get("question_id") or "")
        doc = str(raw_item.get("evidence") or raw_item.get("source_passage") or raw_item.get("context") or "")
        claim = str(raw_item.get("claim") or raw_item.get("answer") or "")

        raw_label = raw_item.get("label") or raw_item.get("attribution_label")
        if raw_label is None:
            # Check for expert rating score or binary flag
            score = raw_item.get("expert_rating")
            if score is not None:
                raw_label = "factual" if float(score) >= 3.0 else "hallucinated"
            else:
                raise ValidationError(f"Missing label or rating in ExpertQA record: {raw_item}")

        key = str(raw_label).strip().lower()
        if key not in LABEL_MAP:
            raise ValidationError(
                f"Unknown label '{raw_label}' in ExpertQA record. Allowed source values: {list(LABEL_MAP.keys())}"
            )

        mapped_label = LABEL_MAP[key]

        yield ClaimVerificationRecord(
            record_id=rid or f"expertqa_{hash(claim)}",
            document=doc,
            claim=claim,
            label=mapped_label,
            justification=raw_item.get("expert_notes"),
            source_dataset=self.metadata.name,
            source_split=self.split,
            source_id=rid,
            metadata={"field": raw_item.get("field")},
        )


__all__ = ["ExpertQAAdapter"]

