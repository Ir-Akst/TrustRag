"""Data engineering subpackage for TrustRAG.

Phase 01: Dataset Engineering foundation providing acquisition, normalization,
quality validation, deduplication, leakage-resistant splitting, storage,
and manifest maintenance.
"""

from .acquisition import (
    CONFIGURED_TARGETS,
    PRIORITY_TIERS,
    AcquisitionAuditEntry,
    AcquisitionManager,
    HFAcquisitionHelper,
    LocalFileImporter,
)
from .base import BaseAdapter, DatasetMetadata, ProcessingStats
from .benchmarks import (
    BENCHMARK_CATEGORIES,
    PROVENANCE_STRING,
    BenchmarkBuilder,
    generate_security_benchmark_pairs,
)
from .exceptions import (
    AcquisitionError,
    DataError,
    DuplicateRecordError,
    ManifestError,
    SplitError,
    StorageError,
    UsageIsolationError,
    ValidationError,
)
from .isolation import (
    DatasetUsageCategory,
    DatasetUsageValidator,
    EVALUATION_USAGE_CATEGORIES,
    TRAINING_USAGE_CATEGORIES,
)
from .manifest import DatasetManifest, ManifestFileEntry, ManifestManager
from .preprocessing import (
    DeduplicationReport,
    DuplicateDetector,
    clean_text,
    is_empty_text,
    normalize_text,
)
from .quality import DatasetQualityAuditor, DatasetQualityReport
from .registry import (
    get_adapter_class,
    get_dataset_metadata,
    list_datasets,
    load_dataset,
)
from .resource import (
    ResourceManager,
    StorageTierReport,
    format_bytes,
)
from .schemas import (
    ClaimVerificationRecord,
    DocumentRecord,
    QueryRecord,
    SecurityRecord,
    compute_content_hash,
)
from .splitting import (
    LeakageResistantSplitter,
    SplitConfig,
    SplitStatistics,
)
from .storage import DatasetStorage, compute_file_sha256
from .taxonomy import (
    AttackFamily,
    ClaimVerificationLabel,
    DocumentSecurityLabel,
    normalize_attack_family,
    normalize_claim_label,
    normalize_security_label,
)
from .validation import RecordValidator, ValidationReport

__all__ = [
    # Schemas
    "DocumentRecord",
    "QueryRecord",
    "ClaimVerificationRecord",
    "SecurityRecord",
    "compute_content_hash",
    # Base
    "BaseAdapter",
    "DatasetMetadata",
    "ProcessingStats",
    # Registry
    "list_datasets",
    "get_adapter_class",
    "get_dataset_metadata",
    "load_dataset",
    # Exceptions
    "DataError",
    "AcquisitionError",
    "ValidationError",
    "DuplicateRecordError",
    "SplitError",
    "StorageError",
    "ManifestError",
    "UsageIsolationError",
    # Preprocessing
    "clean_text",
    "normalize_text",
    "is_empty_text",
    "DuplicateDetector",
    "DeduplicationReport",
    # Validation & Quality
    "RecordValidator",
    "ValidationReport",
    "DatasetQualityReport",
    "DatasetQualityAuditor",
    # Taxonomy
    "ClaimVerificationLabel",
    "DocumentSecurityLabel",
    "AttackFamily",
    "normalize_claim_label",
    "normalize_security_label",
    "normalize_attack_family",
    # Splitting
    "LeakageResistantSplitter",
    "SplitConfig",
    "SplitStatistics",
    # Isolation & Usage Controls
    "DatasetUsageCategory",
    "TRAINING_USAGE_CATEGORIES",
    "EVALUATION_USAGE_CATEGORIES",
    "DatasetUsageValidator",
    # Storage & Resource Management
    "DatasetStorage",
    "compute_file_sha256",
    "DatasetManifest",
    "ManifestFileEntry",
    "ManifestManager",
    "format_bytes",
    "StorageTierReport",
    "ResourceManager",
    # Acquisition
    "HFAcquisitionHelper",
    "LocalFileImporter",
    "AcquisitionManager",
    "AcquisitionAuditEntry",
    "PRIORITY_TIERS",
    "CONFIGURED_TARGETS",
    # Benchmarks
    "BENCHMARK_CATEGORIES",
    "BenchmarkBuilder",
    "PROVENANCE_STRING",
    "generate_security_benchmark_pairs",
]
