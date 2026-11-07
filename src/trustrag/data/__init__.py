# src/trustrag/data/__init__.py
"""Data engineering subpackage for TrustRAG.

Exports the primary public functions for dataset loading.
"""

from .registry import list_datasets, load_dataset

__all__ = ["list_datasets", "load_dataset"]

