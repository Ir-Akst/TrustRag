"""Dataset registry and loader orchestration for TrustRAG.

The registry maps logical dataset identifiers (e.g. ``"natural_questions"``, ``"ragtruth"``)
to concrete :class:`BaseAdapter` classes and provides inspection, loading, and
preprocessing pipelines.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterator, List, Optional, Type, Union

from .base import BaseAdapter, DatasetMetadata, NormalizedRecord
from .exceptions import AcquisitionError

logger = logging.getLogger(__name__)

# Complete registry of all 13 supported datasets across all 4 categories
_REGISTRY: Dict[str, str] = {
    # Category A: RAG & Question-Answering
    "natural_questions": "trustrag.data.loaders.natural_questions.NaturalQuestionsAdapter",
    "hotpotqa": "trustrag.data.loaders.hotpotqa.HotpotQAAdapter",
    "ms_marco": "trustrag.data.loaders.ms_marco.MSMarcoAdapter",
    "squad": "trustrag.data.loaders.squad.SQuADAdapter",
    "boolq": "trustrag.data.loaders.boolq.BoolQAdapter",
    # Category B: Hallucination & Claim-Verification
    "halueval": "trustrag.data.loaders.halueval.HaluEvalAdapter",
    "ragtruth": "trustrag.data.loaders.ragtruth.RAGTruthAdapter",
    "llm_aggrefact": "trustrag.data.loaders.llm_aggrefact.LLMAggreFactAdapter",
    "wice": "trustrag.data.loaders.wice.WiCEAdapter",
    "expertqa": "trustrag.data.loaders.expertqa.ExpertQAAdapter",
    # Category C: Security & Poisoning
    "rsb": "trustrag.data.loaders.rsb.RSBAdapter",
    "custom_security": "trustrag.data.loaders.custom_security.CustomSecurityAdapter",
    # Category D: Training Corpus
    "fineweb": "trustrag.data.loaders.fineweb.FineWebAdapter",
}


def _resolve_adapter(class_path: str) -> Type[BaseAdapter]:
    """Resolve an adapter class dynamically from its module path."""
    module_path, class_name = class_path.rsplit(".", 1)
    module = __import__(module_path, fromlist=[class_name])
    adapter_cls = getattr(module, class_name)
    if not issubclass(adapter_cls, BaseAdapter):
        raise AcquisitionError(f"Adapter {class_path} is not a BaseAdapter subclass")
    return adapter_cls


def list_datasets() -> List[str]:
    """Return all registered dataset identifiers."""
    return list(_REGISTRY.keys())


def get_adapter_class(name: str) -> Type[BaseAdapter]:
    """Retrieve the adapter class for a registered dataset name."""
    clean_name = name.lower().strip()
    if clean_name not in _REGISTRY:
        raise AcquisitionError(
            f"Dataset '{name}' is not registered. Available datasets: {list(_REGISTRY.keys())}"
        )
    return _resolve_adapter(_REGISTRY[clean_name])


def get_dataset_metadata(name: str) -> DatasetMetadata:
    """Retrieve metadata for a registered dataset."""
    adapter_cls = get_adapter_class(name)
    return adapter_cls.metadata


def load_dataset(
    name: str,
    *,
    split: str = "train",
    limit: Optional[int] = None,
    offline: bool = False,
    local_path: Optional[str] = None,
    config_name: Optional[str] = None,
    deduplicate: bool = True,
    clean: bool = True,
) -> Iterator[NormalizedRecord]:
    """Load a dataset by name and yield normalized, validated records.

    Parameters
    ----------
    name: str
        Logical dataset identifier (as registered in registry).
    split: str
        Desired split name (e.g. 'train', 'validation', 'test').
    limit: int | None
        Maximum records to yield.
    offline: bool
        Whether to enforce offline mode.
    local_path: str | None
        Optional local file path for direct import.
    config_name: str | None
        Optional configuration/subset name.
    deduplicate: bool
        Whether to deduplicate using content hash.
    clean: bool
        Whether to apply safe text normalization.

    Yields
    ------
    NormalizedRecord
        Validated Pydantic model record.
    """
    adapter_cls = get_adapter_class(name)
    adapter = adapter_cls(
        split=split,
        limit=limit,
        offline=offline,
        local_path=local_path,
        config_name=config_name,
    )
    return adapter.process(deduplicate=deduplicate, clean=clean)


__all__ = [
    "list_datasets",
    "get_adapter_class",
    "get_dataset_metadata",
    "load_dataset",
]
