"""Dataset registry and loader orchestration.

The registry maps a logical dataset identifier (e.g., ``"natural_questions"``) to a
concrete :class:`BaseAdapter` subclass that knows how to acquire and preprocess the
raw source.  The public function :func:`load_dataset` uses the registry to create
an adapter instance and returns an iterator of normalized Pydantic records.
"""

from __future__ import annotations

from typing import Dict, Iterable, Iterator, Type

from .base import BaseAdapter
from .exceptions import AcquisitionError, DataError

# Concrete adapters are imported lazily to avoid heavy optional dependencies at
# import time.  The mapping contains the fully‑qualified class name; the class is
# imported only when the dataset is requested.
_REGISTRY: Dict[str, str] = {
    # RAG QA datasets
    "natural_questions": "trustrag.data.loaders.natural_questions.NaturalQuestionsAdapter",
    "hotpotqa": "trustrag.data.loaders.hotpotqa.HotpotQAAdapter",
    "ms_marco": "trustrag.data.loaders.ms_marco.MSMarcoAdapter",
    "squad": "trustrag.data.loaders.squad.SQuADAdapter",
    "boolq": "trustrag.data.loaders.boolq.BoolQAdapter",
    # Hallucination verification datasets – placeholders (local import adapters)
    "halueval": "trustrag.data.loaders.halueval.HaluEvalAdapter",
    # Security / poisoning datasets – placeholders
    "rsb": "trustrag.data.loaders.rsb.RSBAdapter",
    # Training corpus – FineWeb (sample adapter)
    "fineweb": "trustrag.data.loaders.fineweb.FineWebAdapter",
}


def _resolve_adapter(class_path: str) -> Type[BaseAdapter]:
    module_path, class_name = class_path.rsplit(".", 1)
    module = __import__(module_path, fromlist=[class_name])
    adapter_cls = getattr(module, class_name)
    if not issubclass(adapter_cls, BaseAdapter):
        raise AcquisitionError(f"Adapter {class_path} is not a BaseAdapter subclass")
    return adapter_cls


def list_datasets() -> Iterator[str]:
    """Yield all registered dataset identifiers."""
    return iter(_REGISTRY.keys())


def load_dataset(
    name: str,
    *,
    limit: int | None = None,
    split: str = "train",
    offline: bool = False,
) -> Iterator[BaseAdapter]:
    """Load a dataset by name and yield normalized records.

    Parameters
    ----------
    name: str
        Logical dataset identifier (as used in the registry).
    limit: int | None
        Maximum number of records to emit. ``None`` means no limit.
    split: str
        Desired split name; adapters may ignore if the source does not have splits.
    offline: bool
        If ``True`` enforce offline mode – adapters should use cached data or raise
        if the source is unavailable.
    """
    if name not in _REGISTRY:
        raise AcquisitionError(f"Dataset '{name}' is not registered")
    adapter_cls = _resolve_adapter(_REGISTRY[name])
    adapter = adapter_cls(split=split, limit=limit, offline=offline)
    return adapter.process()

