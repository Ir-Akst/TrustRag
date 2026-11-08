"""LLM-AggreFact benchmark adapter for TrustRAG.

Source: lytang/LLM-AggreFact (Hugging Face Gated) / https://github.com/Liyan06/MiniCheck
License: CC-BY-ND-4.0
Access: Gated (Requires HF user agreement; STRICTLY prohibited for pretraining/fine-tuning!)
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
    "0": "FACTUAL",
    "support": "FACTUAL",
    "supported": "FACTUAL",
    "false": "FACTUAL",  # In some datasets, false means not hallucinated
    "hallucinated": "HALLUCINATED",
    "1": "HALLUCINATED",
    "refute": "HALLUCINATED",
    "refuted": "HALLUCINATED",
    "true": "HALLUCINATED",  # true means hallucination present
}


class LLMAggreFactAdapter(BaseAdapter):
    """Adapter for LLM-AggreFact: unified benchmark for LLM fact-checking and hallucination detection."""

    metadata = DatasetMetadata(
        name="llm_aggrefact",
        category="hallucination",
        description="LLM-AggreFact: Multi-dataset unified benchmark for fact-checking LLM outputs on grounding documents",
        source_uri="lytang/LLM-AggreFact",
        license="CC-BY-ND-4.0",
        access_type="gated",
        record_type="ClaimVerificationRecord",
        paper_reference="Tang et al., 2024 (EMNLP) 'MiniCheck'",
        known_limitations=(
            "Gated Hugging Face dataset requiring user agreement. "
            "RESTRICTION: Benchmark evaluation only; MUST NOT be used for training or fine-tuning."
        ),
        default_config="default",
        default_splits=["test"],
        permitted_for_training=False,  # CRITICAL RESTRICTION
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
                f"LLM-AggreFact unavailable in offline mode without local files at '{target}'. "
                "Download the gated benchmark from https://huggingface.co/datasets/lytang/LLM-AggreFact "
                "after accepting terms, and specify local_path."
            )

        # Attempt to load from HF hub
        return self.cache_dir

    def load_raw(self) -> Iterator[Dict[str, Any]]:
        if self.local_path and self.local_path.exists():
            yield from LocalFileImporter.read_records(self.local_path, limit=self.limit)
            return

        target_file = self.cache_dir / f"{self.split}.jsonl"
        if target_file.exists():
            yield from LocalFileImporter.read_records(target_file, limit=self.limit)
            return

        # Attempt HF hub acquisition
        try:
            yield from HFAcquisitionHelper.load_hf_records(
                self.metadata.source_uri,
                split=self.split,
                config_name=self.config_name,
                cache_dir=self.cache_dir,
                limit=self.limit,
                offline=self.offline,
            )
        except AcquisitionError as e:
            if "gated repo" in str(e).lower() or "403" in str(e):
                raise AcquisitionError(
                    "LLM-AggreFact is a gated dataset (CC-BY-ND-4.0). "
                    "You must log in to Hugging Face and accept the dataset agreement at "
                    "https://huggingface.co/datasets/lytang/LLM-AggreFact, or provide a local_path "
                    f"to pre-downloaded files: {e}"
                )
            raise

    def transform(self, raw_item: Dict[str, Any]) -> Iterator[ClaimVerificationRecord]:
        rid = str(raw_item.get("id") or raw_item.get("sample_id") or "")
        doc = str(raw_item.get("doc") or raw_item.get("document") or raw_item.get("context") or "")
        claim = str(raw_item.get("claim") or raw_item.get("sentence") or raw_item.get("response") or "")

        raw_label = raw_item.get("label")
        if raw_label is None:
            raise ValidationError(f"Missing label in LLM-AggreFact record: {raw_item}")

        key = str(raw_label).strip().lower()
        if key not in LABEL_MAP:
            raise ValidationError(
                f"Unknown label '{raw_label}' in LLM-AggreFact record. Allowed source values: {list(LABEL_MAP.keys())}"
            )

        mapped_label = LABEL_MAP[key]

        yield ClaimVerificationRecord(
            record_id=rid or f"aggrefact_{hash(claim)}",
            document=doc,
            claim=claim,
            label=mapped_label,
            source_dataset=self.metadata.name,
            source_split=self.split,
            source_id=rid,
            metadata={
                "subset": raw_item.get("dataset") or raw_item.get("benchmark"),
                "license_restriction": "EVALUATION_ONLY_NO_TRAINING",
            },
        )


__all__ = ["LLMAggreFactAdapter"]

