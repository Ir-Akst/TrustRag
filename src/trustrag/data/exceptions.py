"""Dataset engineering core exceptions for TrustRAG.

All dataset-related exceptions inherit from :class:`trustrag.exceptions.DatasetError`.
"""

from __future__ import annotations

from trustrag.exceptions import DatasetError


class DataError(DatasetError):
    """Base class for dataset-related errors in TrustRAG."""
    pass


class AcquisitionError(DataError):
    """Raised when acquiring a dataset fails (e.g., network, auth, missing source)."""
    pass


class ValidationError(DataError):
    """Raised when a record or configuration does not conform to the expected schema or rules."""
    pass


class DuplicateRecordError(DataError):
    """Raised when duplicate detection encounters an unrecoverable conflict."""
    pass


class SplitError(DataError):
    """Raised when dataset splitting encounters leakage, invalid ratios, or missing groups."""
    pass


class StorageError(DataError):
    """Raised when saving or loading processed datasets fails."""
    pass


class ManifestError(DataError):
    """Raised when generating, reading, or validating dataset manifests fails."""
    pass


class UsageIsolationError(ValidationError):
    """Raised when a dataset is used in a prohibited workflow (e.g. eval-only data in training)."""
    pass


__all__ = [
    "DataError",
    "AcquisitionError",
    "ValidationError",
    "DuplicateRecordError",
    "SplitError",
    "StorageError",
    "ManifestError",
    "UsageIsolationError",
]
