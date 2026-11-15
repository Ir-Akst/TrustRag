"""Acquisition package for TrustRAG datasets.

Provides loaders for remote Hugging Face datasets and local JSON, JSONL, CSV, and Parquet files.
"""

from .downloader import (
    CANONICAL_SOURCES,
    DatasetArtifactEntry,
    DatasetDownloader,
    DatasetManifest,
    compute_file_sha256,
)
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
    "DatasetDownloader",
    "DatasetManifest",
    "DatasetArtifactEntry",
    "CANONICAL_SOURCES",
    "compute_file_sha256",
    "PRIORITY_TIERS",
    "CONFIGURED_TARGETS",
]

