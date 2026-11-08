"""Acquisition package for TrustRAG datasets.

Provides loaders for remote Hugging Face datasets and local JSON, JSONL, CSV, and Parquet files.
"""

from .hf import HFAcquisitionHelper
from .local import LocalFileImporter
from .manager import (
    CONFIGURED_TARGETS,
    PRIORITY_TIERS,
    AcquisitionAuditEntry,
    AcquisitionManager,
)

__all__ = [
    "HFAcquisitionHelper",
    "LocalFileImporter",
    "AcquisitionManager",
    "AcquisitionAuditEntry",
    "PRIORITY_TIERS",
    "CONFIGURED_TARGETS",
]

