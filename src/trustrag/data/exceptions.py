"""Dataset engineering core exceptions for TrustRAG.
"""

class DataError(Exception):
    """Base class for dataset‑related errors."""
    pass

class AcquisitionError(DataError):
    """Raised when acquiring a dataset fails (e.g., network, auth)."""
    pass

class ValidationError(DataError):
    """Raised when a record does not conform to the expected schema."""
    pass

class DuplicateRecordError(DataError):
    """Raised when duplicate detection encounters an unrecoverable conflict."""
    pass

