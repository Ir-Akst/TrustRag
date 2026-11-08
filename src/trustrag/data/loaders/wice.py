"""WiCE fine-grained entailment dataset adapter for TrustRAG.

Source: https://github.com/ryokamoi/wice
License: ODC-BY (annotations) / CC-BY-SA (Wikipedia text)
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
    "supported": "SUPPORTED",
    "support": "SUPPORTED",
    "entailment": "SUPPORTED",
    "entailed": "SUPPORTED",
    "1": "SUPPORTED",
    "refuted": "REFUTED",
    "refute": "REFUTED",
    "contradiction": "REFUTED",
    "0": "REFUTED",
    "not_enough_info": "NOT_ENOUGH_INFO",
    "neutral": "NOT_ENOUGH_INFO",
    "nei": "NOT_ENOUGH_INFO",
}


class WiCEAdapter(BaseAdapter):
    """Adapter for WiCE: Real-world fine-grained entailment for claim verification."""

    metadata = DatasetMetadata(
        name="wice",
        category="hallucination",
        description="WiCE: Real-world fine-grained entailment for claims in Wikipedia with sentence and sub-sentence evidence alignment",
        source_uri="https://github.com/ryokamoi/wice",
        license="ODC-BY / CC-BY-SA",
        access_type="open",
        record_type="ClaimVerificationRecord",
        paper_reference="Kamoi et al., 2023 (EMNLP)",
        known_limitations="Wikipedia-derived claims; fine-grained sub-sentence alignment annotations",
        default_config="claim",
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
                f"WiCE dataset file '{target}' unavailable in offline mode. "
                "Download files from https://github.com/ryokamoi/wice or pass local_path."
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

        # Attempt community HF loader if available
        try:
            yield from HFAcquisitionHelper.load_hf_records(
                "jon-tow/wice",
                split=self.split,
                config_name=self.config_name,
                cache_dir=self.cache_dir,
                limit=self.limit,
                offline=self.offline,
            )
        except Exception:
            raise AcquisitionError(
                "WiCE dataset not found locally. Please clone or download data files from "
                "https://github.com/ryokamoi/wice and specify local_path or save to "
                f"'{self.cache_dir}'."
            )

    def transform(self, raw_item: Dict[str, Any]) -> Iterator[ClaimVerificationRecord]:
        rid = str(raw_item.get("id") or raw_item.get("claim_id") or "")
        claim = str(raw_item.get("claim") or raw_item.get("hypothesis") or "")

        # Extract document/evidence
        doc = ""
        evidence = raw_item.get("evidence") or raw_item.get("premise") or raw_item.get("document")
        if isinstance(evidence, list):
            doc = "\n".join(str(e) for e in evidence)
        elif evidence:
            doc = str(evidence)

        raw_label = raw_item.get("label")
        if raw_label is None:
            raise ValidationError(f"Missing label in WiCE record: {raw_item}")

        key = str(raw_label).strip().lower()
        if key not in LABEL_MAP:
            raise ValidationError(
                f"Unknown label '{raw_label}' in WiCE record. Allowed source values: {list(LABEL_MAP.keys())}"
            )

        mapped_label = LABEL_MAP[key]

        yield ClaimVerificationRecord(
            record_id=rid or f"wice_{hash(claim)}",
            document=doc,
            claim=claim,
            label=mapped_label,
            justification=str(raw_item.get("alignment") or ""),
            source_dataset=self.metadata.name,
            source_split=self.split,
            source_id=rid,
            metadata={"metadata": raw_item.get("metadata", {})},
        )


__all__ = ["WiCEAdapter"]

