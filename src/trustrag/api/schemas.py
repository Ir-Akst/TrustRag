"""Typed Pydantic v2 request/response contracts and OpenAPI 3.1 schema builder."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from trustrag.engine.schemas import SRMBackendHealth


class APIErrorResponse(BaseModel):
    """Consistent structured error response (never leaks stack traces or secrets)."""

    error: str
    code: str
    request_id: str | None = None
    details: list[str] = Field(default_factory=list)


class SystemHealthResponse(BaseModel):
    """Comprehensive system, component, SRM, dependency, and build health report."""

    status: Literal["healthy", "degraded", "not_ready"]
    ready: bool
    initialized: bool
    shut_down: bool
    version: str = "0.1.0"
    phase: str = "phase-9"
    environment: str
    auth_mode: Literal["token_required", "local_dev_unauthenticated"]
    corpus_documents: int = Field(ge=0)
    adaptive_mode: str
    calibration_active: bool
    calibration_version: str | None = None
    components: dict[str, str] = Field(default_factory=dict)
    srm_backend_configured: str
    srm_health: SRMBackendHealth | None = None
    dependencies: dict[str, bool] = Field(default_factory=dict)
    total_requests: int = Field(ge=0)
    error_requests: int = Field(ge=0)
    timeout_requests: int = Field(ge=0)
    peak_rss_mib: float | None = None
    timestamp: str


class G1AnalyzeRequest(BaseModel):
    query: str = Field(min_length=1, max_length=8192)
    enable_paraphrasing: bool | None = None


class G1AnalyzeResponse(BaseModel):
    request_id: str
    decision: str
    risk_score: float = Field(ge=0.0, le=1.0)
    attack_categories: list[str] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
    sanitized_query: str
    paraphrased_query: str | None = None
    paraphrase_accepted: bool | None = None
    paraphrase_rejection_reasons: list[str] = Field(default_factory=list)
    explanation: str
    latency_ms: float = Field(ge=0.0)


class CandidateDocInput(BaseModel):
    doc_id: str = Field(min_length=1, max_length=128)
    text: str = Field(min_length=1, max_length=16384)
    score: float = Field(default=0.75, ge=0.0, le=1.0)
    source_id: str = Field(default="", max_length=256)
    provenance: str = Field(default="unknown", max_length=256)
    metadata: dict[str, Any] = Field(default_factory=dict)


class G2AnalyzeRequest(BaseModel):
    query: str = Field(min_length=1, max_length=8192)
    documents: list[CandidateDocInput] | None = Field(default=None, max_length=25)
    top_k: int = Field(default=5, ge=1, le=20)


class SignalDetailView(BaseModel):
    signal_id: str
    signal_name: str
    available: bool
    value: float | None = None
    raw_value: float | None = None
    z_score: float | None = None
    configured_weight: float
    effective_weight: float
    is_heuristic: bool
    status: str
    explanation: str
    flags: list[str] = Field(default_factory=list)


class G2DocumentView(BaseModel):
    document_id: str
    source_id: str
    provenance: str
    trust_score: float
    decision: str
    original_retrieval_score: float | None = None
    adjusted_retrieval_score: float | None = None
    removed_by_cap: bool
    conflict_detected: bool
    conflicting_doc_ids: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    calibration_active: bool = False
    calibration_version: str | None = None
    raw_trust_score: float | None = None
    signals: dict[str, SignalDetailView] = Field(default_factory=dict)


class G2AnalyzeResponse(BaseModel):
    request_id: str
    query: str
    candidate_count: int = Field(ge=0)
    retained_doc_ids: list[str] = Field(default_factory=list)
    filtered_doc_ids: list[str] = Field(default_factory=list)
    removal_cap_ratio: float
    calibration_active: bool
    calibration_version: str | None = None
    assessments: list[G2DocumentView] = Field(default_factory=list)
    latency_ms: float = Field(ge=0.0)


class G3VerifyRequest(BaseModel):
    query: str = Field(default="", max_length=8192)
    answer: str = Field(min_length=1, max_length=16384)
    documents: list[CandidateDocInput] | None = Field(default=None, max_length=25)


class G3ClaimView(BaseModel):
    claim_id: str
    claim_text: str
    verdict: str
    confidence: float
    supporting_doc_ids: list[str] = Field(default_factory=list)
    contradicting_doc_ids: list[str] = Field(default_factory=list)
    evidence_spans: list[str] = Field(default_factory=list)
    explanation: str


class G3VerifyResponse(BaseModel):
    request_id: str
    overall_status: str
    verdict: str
    total_claims: int = Field(ge=0)
    supported_count: int = Field(ge=0)
    contradicted_count: int = Field(ge=0)
    insufficient_count: int = Field(ge=0)
    uncertain_count: int = Field(ge=0)
    abstained: bool
    query_consistent: bool | None = None
    query_consistency_reason: str | None = None
    claims: list[G3ClaimView] = Field(default_factory=list)
    latency_ms: float = Field(ge=0.0)


class PipelineExecuteRequest(BaseModel):
    query: str = Field(min_length=1, max_length=8192)
    top_k: int = Field(default=5, ge=1, le=20)
    request_timeout_seconds: float | None = Field(default=None, gt=0.0, le=30.0)


class PipelineExecuteResponse(BaseModel):
    request_id: str
    status: Literal["OK", "ABSTAINED", "BLOCKED", "ERROR"]
    answer: str
    safe_to_display: bool
    abstained: bool
    blocked_by_guardrail: bool
    g1_decision: str
    g3_verdict: str | None = None
    retained_doc_ids: list[str] = Field(default_factory=list)
    latency_ms: float = Field(ge=0.0)
    adaptive_mode: str
    threshold_reasons: list[str] = Field(default_factory=list)
    fail_safe_events: list[str] = Field(default_factory=list)


class RetrievalEvidenceRequest(BaseModel):
    query: str = Field(min_length=1, max_length=8192)
    top_k: int = Field(default=5, ge=1, le=20)


class EvidenceItemView(BaseModel):
    doc_id: str
    provenance: str
    source_id: str
    text_preview: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalEvidenceResponse(BaseModel):
    request_id: str
    query: str
    corpus_size: int = Field(ge=0)
    returned_count: int = Field(ge=0)
    items: list[EvidenceItemView] = Field(default_factory=list)


class MonitoringMetricsResponse(BaseModel):
    """Measured runtime telemetry + clearly labeled static historical Phase 08 benchmark reference."""

    telemetry_scope: str = "live_runtime_process"
    uptime_seconds: float = Field(ge=0.0)
    total_requests: int = Field(ge=0)
    error_requests: int = Field(ge=0)
    error_rate: float = Field(ge=0.0, le=1.0)
    blocked_requests: int = Field(ge=0)
    abstained_requests: int = Field(ge=0)
    timeout_requests: int = Field(ge=0)
    throughput_qps: float = Field(ge=0.0)
    latency_sample_count: int = Field(ge=0)
    min_percentile_samples: int = 5
    percentiles_available: bool
    latency_p50_ms: float | None = None
    latency_p95_ms: float | None = None
    latency_p99_ms: float | None = None
    g1_decisions: dict[str, int] = Field(default_factory=dict)
    g2_decisions: dict[str, int] = Field(default_factory=dict)
    g3_verdicts: dict[str, int] = Field(default_factory=dict)
    historical_benchmark_available: bool = False
    historical_benchmark_scope: str = "offline_cpu_static_phase08_artifact"
    historical_benchmark: dict[str, Any] = Field(default_factory=dict)


class ConfigFieldMeta(BaseModel):
    key: str
    section: str
    field: str
    current_value: Any
    default_value: Any
    value_type: str
    restart_required: bool
    description: str


class ConfigSnapshotResponse(BaseModel):
    effective_config: dict[str, Any]
    editable_fields: list[ConfigFieldMeta] = Field(default_factory=list)
    immutable_security_invariants: list[str] = Field(default_factory=list)
    backup_count: int = Field(ge=0)


class ConfigUpdateRequest(BaseModel):
    changes: dict[str, Any] = Field(min_length=1)
    confirm: bool = False
    actor: str = Field(default="operator", min_length=1, max_length=64)


class ConfigDiffEntry(BaseModel):
    key: str
    old_value: Any
    new_value: Any
    restart_required: bool


class ConfigUpdateResponse(BaseModel):
    valid: bool
    applied: bool
    requires_confirmation: bool = False
    restart_required: bool = False
    backup_path: str | None = None
    diffs: list[ConfigDiffEntry] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class AuditRecordView(BaseModel):
    seq: int
    timestamp: str
    request_id: str
    event_category: str
    component: str
    decision: str
    outcome: str
    explanation: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    entry_hash: str
    prev_hash: str


class AuditQueryResponse(BaseModel):
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    chain_valid: bool
    items: list[AuditRecordView] = Field(default_factory=list)


def generate_openapi_spec() -> dict[str, Any]:
    """Build an OpenAPI 3.1 document directly from registered Pydantic schemas."""
    models: list[type[BaseModel]] = [
        APIErrorResponse,
        SystemHealthResponse,
        G1AnalyzeRequest,
        G1AnalyzeResponse,
        G2AnalyzeRequest,
        G2AnalyzeResponse,
        G3VerifyRequest,
        G3VerifyResponse,
        PipelineExecuteRequest,
        PipelineExecuteResponse,
        RetrievalEvidenceRequest,
        RetrievalEvidenceResponse,
        MonitoringMetricsResponse,
        ConfigSnapshotResponse,
        ConfigUpdateRequest,
        ConfigUpdateResponse,
        AuditQueryResponse,
    ]
    schemas = {m.__name__: m.model_json_schema(ref_template="#/components/schemas/{model}") for m in models}
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "TrustRAG Operational API",
            "version": "0.1.0",
            "description": "Phase 09 REST API exposing G1/G2/G3 security stages, SRM health, monitoring, configuration management, and tamper-evident audit logs.",
        },
        "paths": {
            "/api/v1/health": {"get": {"summary": "System and component health", "tags": ["System"]}},
            "/api/v1/srm/health": {"get": {"summary": "SRM backend health and fallback state", "tags": ["System"]}},
            "/api/v1/g1/analyze": {"post": {"summary": "Run G1 input guardrail analysis", "tags": ["Pipeline"]}},
            "/api/v1/g2/analyze": {"post": {"summary": "Run G2 Multi-Signal Detector", "tags": ["Pipeline"]}},
            "/api/v1/g3/verify": {"post": {"summary": "Run G3 evidence verification & query consistency", "tags": ["Pipeline"]}},
            "/api/v1/evidence/retrieve": {"post": {"summary": "Retrieve corpus evidence & provenance", "tags": ["Pipeline"]}},
            "/api/v1/pipeline/execute": {"post": {"summary": "Execute full TrustRAG pipeline", "tags": ["Pipeline"]}},
            "/api/v1/monitoring/metrics": {"get": {"summary": "Measured runtime telemetry & benchmark scope", "tags": ["Monitoring"]}},
            "/api/v1/config": {"get": {"summary": "Inspect effective configuration & editable schema", "tags": ["Configuration"]}},
            "/api/v1/config/validate": {"post": {"summary": "Validate & diff proposed config changes", "tags": ["Configuration"]}},
            "/api/v1/config/apply": {"post": {"summary": "Apply confirmed config changes with backup", "tags": ["Configuration"]}},
            "/api/v1/config/restore": {"post": {"summary": "Restore documented baseline defaults", "tags": ["Configuration"]}},
            "/api/v1/audit/logs": {"get": {"summary": "Query filtered tamper-evident audit records", "tags": ["Audit"]}},
        },
        "components": {"schemas": schemas},
    }
