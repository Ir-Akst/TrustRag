"""Typed Pydantic schemas for TrustRAG Phase 03 defense engine and end-to-end pipeline."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, PrivateAttr, model_validator

from trustrag.data.schemas import (
    ClaimVerificationRecord,
    DocumentRecord,
    QueryRecord,
    SecurityRecord,
    compute_content_hash,
)
from trustrag.data.taxonomy import ClaimVerificationLabel, DocumentSecurityLabel


# ---------------------------------------------------------------------------
# G1: Input Guardrail Schemas
# ---------------------------------------------------------------------------

class G1Decision(str, Enum):
    """Structured decision emitted by G1 Input Guardrail."""

    ALLOW = "ALLOW"
    FLAG = "FLAG"
    BLOCK = "BLOCK"


class G1ReasonCode(str, Enum):
    """Deterministic reason codes for G1 Input Guardrail findings."""

    G1_CLEAN = "G1_CLEAN"
    G1_EMPTY_INPUT = "G1_EMPTY_INPUT"
    G1_EXCESSIVE_LENGTH = "G1_EXCESSIVE_LENGTH"
    G1_OBFUSCATION_DETECTED = "G1_OBFUSCATION_DETECTED"
    G1_PROMPT_INJECTION = "G1_PROMPT_INJECTION"
    G1_ROLE_HIJACK = "G1_ROLE_HIJACK"
    G1_MALICIOUS_COMMAND = "G1_MALICIOUS_COMMAND"
    G1_DOS_TRIGGER = "G1_DOS_TRIGGER"
    G1_SUSPICIOUS_META_PATTERN = "G1_SUSPICIOUS_META_PATTERN"


class G1MatchDetail(BaseModel):
    """Details of a matched guardrail pattern or anomaly."""

    rule_name: str
    reason_code: G1ReasonCode
    severity: float = Field(ge=0.0, le=1.0)
    matched_snippet: str
    is_heuristic: bool = True


class G1Assessment(BaseModel):
    """Full audit assessment produced by G1 Input Guardrail."""

    decision: G1Decision
    risk_score: float = Field(ge=0.0, le=1.0)
    original_input: str
    normalized_input: str
    reason_codes: List[G1ReasonCode] = Field(default_factory=list)
    matches: List[G1MatchDetail] = Field(default_factory=list)
    explanation: str
    audit_hash: str


# ---------------------------------------------------------------------------
# Retrieval & G2: Multi-Signal Detector (MSD) Schemas
# ---------------------------------------------------------------------------

class DocumentTrustDecision(str, Enum):
    """Retrieval trust decision emitted by G2 Multi-Signal Detector."""

    TRUST = "TRUST"
    DOWNRANK = "DOWNRANK"
    FILTER = "FILTER"


class EvidenceDocument(BaseModel):
    """Unified runtime document representation for retrieval, G2, generation, and G3.

    Preserves source identifiers and provenance for complete evidence traceability
    without exposing benchmark ground-truth poison labels to detectors.
    """

    doc_id: str
    text: str
    source_dataset: str = "local"
    source_id: Optional[str] = None
    provenance: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content_hash: str = ""

    @model_validator(mode="before")
    @classmethod
    def compute_hash(cls, data: Any) -> Any:
        if isinstance(data, dict) and not data.get("content_hash"):
            text = str(data.get("text") or "")
            if text:
                data["content_hash"] = compute_content_hash(text)
        return data

    @classmethod
    def from_record(cls, rec: Any, idx: int = 0) -> Optional["EvidenceDocument"]:
        """Adapt existing Phase 01/02 records into EvidenceDocument without leaking ground-truth labels."""
        if isinstance(rec, EvidenceDocument):
            if not rec.content_hash and rec.text:
                rec.content_hash = compute_content_hash(rec.text)
            return rec

        if isinstance(rec, DocumentRecord):
            return cls(
                doc_id=rec.document_id,
                text=rec.text,
                source_dataset=rec.source_dataset,
                source_id=rec.source_id or rec.document_id,
                provenance=rec.provenance,
                metadata=dict(rec.metadata),
                content_hash=rec.content_hash or compute_content_hash(rec.text),
            )

        if isinstance(rec, SecurityRecord):
            text = (rec.passage or rec.document or "").strip()
            if not text:
                return None
            # Strip benchmark ground-truth labels from runtime metadata so G2 cannot cheat.
            safe_meta = {
                k: v
                for k, v in rec.metadata.items()
                if k not in {"clean_poison_label", "expected_security_outcome", "poisoning_method"}
            }
            if rec.target_query:
                safe_meta["benchmark_target_query"] = rec.target_query
            return cls(
                doc_id=rec.record_id,
                text=text,
                source_dataset=rec.source_dataset,
                source_id=rec.source_id or rec.record_id,
                provenance=rec.provenance,
                metadata=safe_meta,
                content_hash=rec.content_hash or compute_content_hash(text),
            )

        if isinstance(rec, QueryRecord):
            passage = str(rec.metadata.get("passage") or "").strip()
            if not passage:
                return None
            safe_meta = {k: v for k, v in rec.metadata.items() if k != "passage"}
            return cls(
                doc_id=f"{rec.query_id}_doc",
                text=passage,
                source_dataset=rec.source_dataset,
                source_id=rec.source_id or rec.query_id,
                provenance=f"dataset:{rec.source_dataset}",
                metadata=safe_meta,
                content_hash=compute_content_hash(passage),
            )

        if isinstance(rec, ClaimVerificationRecord):
            if not rec.document.strip():
                return None
            return cls(
                doc_id=f"{rec.record_id}_doc",
                text=rec.document,
                source_dataset=rec.source_dataset,
                source_id=rec.source_id or rec.record_id,
                provenance=f"dataset:{rec.source_dataset}",
                metadata=dict(rec.metadata),
                content_hash=compute_content_hash(rec.document),
            )

        if isinstance(rec, dict):
            text = str(rec.get("text") or rec.get("passage") or rec.get("document") or "").strip()
            if not text:
                raw_meta = rec.get("metadata")
                if isinstance(raw_meta, dict) and raw_meta.get("passage"):
                    text = str(raw_meta["passage"]).strip()
            if not text:
                return None
            doc_id = str(rec.get("doc_id") or rec.get("document_id") or rec.get("record_id") or rec.get("query_id") or f"doc_{idx}")
            raw_meta = rec.get("metadata") if isinstance(rec.get("metadata"), dict) else {}
            safe_meta = {
                k: v
                for k, v in raw_meta.items()
                if k not in {"clean_poison_label", "expected_security_outcome", "poisoning_method", "passage"}
            }
            return cls(
                doc_id=doc_id,
                text=text,
                source_dataset=str(rec.get("source_dataset") or "local"),
                source_id=rec.get("source_id"),
                provenance=rec.get("provenance"),
                metadata=safe_meta,
                content_hash=str(rec.get("content_hash") or compute_content_hash(text)),
            )

        return None


class SignalDetail(BaseModel):
    """Structured individual signal evaluation conforming to Phase 03 Step 8 schema."""

    signal_id: str = Field(description="Signal identifier (F1..F6 or supplementary tag)")
    signal_name: str
    available: bool
    value: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Normalized signal trust contribution in [0.0, 1.0] (higher = safer), or None if unavailable",
    )
    raw_value: Optional[float] = Field(
        default=None,
        description="Unnormalized measurement preserved for auditing (e.g., raw cosine, L2 norm, perplexity)",
    )
    z_score: Optional[float] = Field(
        default=None,
        description="Reference z-score when normalized via reference distribution",
    )
    configured_weight: float = Field(default=0.0, ge=0.0)
    effective_weight: float = Field(default=0.0, ge=0.0)
    is_heuristic: bool = Field(description="True if rule/heuristic signal; False if model/statistical/metadata")
    status: str = Field(default="AVAILABLE", description="AVAILABLE, UNAVAILABLE, or UNKNOWN")
    basis: str = Field(description="Explicit documentation of what this signal measures")
    explanation: str
    flags: List[str] = Field(default_factory=list)

    @property
    def score(self) -> float:
        """Backwards-compatible numeric accessor."""
        return float(self.value) if self.value is not None else 0.5


# Alias preserved for backwards compatibility
SignalScore = SignalDetail


class G2DocumentAssessment(BaseModel):
    """Complete G2 Multi-Signal assessment conforming to Phase 03 Step 8 output schema."""

    document_id: str
    source_id: Optional[str] = None
    provenance: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    trust_score: float = Field(ge=0.0, le=1.0)
    decision: DocumentSecurityLabel
    signals: Dict[str, SignalDetail] = Field(default_factory=dict)
    supplementary_heuristics: Dict[str, SignalDetail] = Field(default_factory=dict)
    available_signals_count: int = 0
    available_weight_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    missing_signal_policy: str = "coverage_attenuated"
    config_snapshot: Dict[str, Any] = Field(default_factory=dict)
    reason_codes: List[str] = Field(default_factory=list)
    original_retrieval_score: Optional[float] = None
    adjusted_retrieval_score: Optional[float] = None
    original_rank: Optional[int] = None
    adjusted_rank: Optional[int] = None
    removed_by_cap: bool = False
    conflict_detected: bool = False
    conflicting_doc_ids: List[str] = Field(default_factory=list)
    instruction_risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    content_hash: str = ""

    @property
    def doc_id(self) -> str:
        """Backwards-compatible alias for document_id."""
        return self.document_id

    @property
    def relevance_score(self) -> float:
        """Backwards-compatible alias for original_retrieval_score."""
        return float(self.original_retrieval_score or 0.0)

    @property
    def combined_score(self) -> float:
        """Backwards-compatible alias for adjusted_retrieval_score."""
        return float(self.adjusted_retrieval_score or 0.0)


class RetrievalResult(BaseModel):
    """Result of trust-aware retrieval combining initial ranking, G2 MSD, and floor(K/2) removal cap."""

    query: str
    total_indexed: int
    requested_top_k: int = 0
    candidate_count: int
    removal_cap_k: int = 0
    removal_cap_limit: int = 0
    removal_cap_applied: bool = False
    filtering_mode: str = "remove_with_cap"
    trusted_documents: List[EvidenceDocument] = Field(default_factory=list)
    removed_documents: List[EvidenceDocument] = Field(default_factory=list)
    filtered_documents: List[EvidenceDocument] = Field(default_factory=list)
    assessments: List[G2DocumentAssessment] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Answer Generation Schemas
# ---------------------------------------------------------------------------

class GeneratedAnswer(BaseModel):
    """Structured output produced by the RAG AnswerGenerator."""

    answer_text: str
    abstained: bool = False
    abstention_reason: Optional[str] = None
    cited_doc_ids: List[str] = Field(default_factory=list)
    generator_mode: str = "extractive"


# ---------------------------------------------------------------------------
# G3: Output Evidence Verification Schemas
# ---------------------------------------------------------------------------

class EvidenceOutcome(str, Enum):
    """Legacy-compatible claim-level outcome emitted by G3 & consumed by SRM."""

    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    NOT_ENOUGH_EVIDENCE = "NOT_ENOUGH_EVIDENCE"
    UNCERTAIN = "UNCERTAIN"

    def to_taxonomy_label(self) -> ClaimVerificationLabel:
        """Map to Phase 02 ClaimVerificationLabel taxonomy."""
        if self == EvidenceOutcome.SUPPORTS:
            return ClaimVerificationLabel.SUPPORTED
        if self == EvidenceOutcome.CONTRADICTS:
            return ClaimVerificationLabel.CONTRADICTED
        return ClaimVerificationLabel.NOT_ENOUGH_EVIDENCE

    def to_claim_verdict(self) -> "G3ClaimVerdict":
        """Map legacy EvidenceOutcome to canonical Step 4 G3ClaimVerdict."""
        if self == EvidenceOutcome.SUPPORTS:
            return G3ClaimVerdict.SUPPORTED
        if self == EvidenceOutcome.CONTRADICTS:
            return G3ClaimVerdict.CONTRADICTED
        if self == EvidenceOutcome.UNCERTAIN:
            return G3ClaimVerdict.UNCERTAIN
        return G3ClaimVerdict.INSUFFICIENT


class G3ClaimVerdict(str, Enum):
    """Canonical Step 4 claim-level evidence verification verdict."""

    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT = "INSUFFICIENT"
    UNCERTAIN = "UNCERTAIN"


class G3AnswerVerdict(str, Enum):
    """Canonical Step 4 answer-level evidence verification verdict."""

    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNCERTAIN = "UNCERTAIN"


class VerificationStatus(str, Enum):
    """Overall pipeline-compatible answer verification status from G3."""

    VERIFIED = "VERIFIED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTED = "CONTRADICTED"
    UNCERTAIN = "UNCERTAIN"
    ABSTAINED = "ABSTAINED"

    def to_answer_verdict(self) -> G3AnswerVerdict:
        """Map VerificationStatus to canonical Step 4 G3AnswerVerdict."""
        if self == VerificationStatus.VERIFIED:
            return G3AnswerVerdict.SUPPORTED
        if self == VerificationStatus.PARTIALLY_SUPPORTED:
            return G3AnswerVerdict.PARTIALLY_SUPPORTED
        if self == VerificationStatus.CONTRADICTED:
            return G3AnswerVerdict.CONTRADICTED
        if self == VerificationStatus.UNCERTAIN:
            return G3AnswerVerdict.UNCERTAIN
        return G3AnswerVerdict.INSUFFICIENT_EVIDENCE


class EvidenceReference(BaseModel):
    """Traceable pointer from an answer claim to a retrieved evidence span."""

    doc_id: str
    source_id: Optional[str] = None
    source_dataset: Optional[str] = None
    provenance: Optional[str] = None
    matched_span: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    polarity_match: bool
    numeric_match: bool
    coverage_score: float = Field(ge=0.0, le=1.0)
    alignment_note: str
    span_outcome: Optional[str] = None


class ClaimVerificationItem(BaseModel):
    """Verification outcome and evidence trace for a single atomic answer claim."""

    claim_id: str
    claim_text: str
    outcome: EvidenceOutcome
    verdict: Optional[G3ClaimVerdict] = None
    confidence: float = Field(ge=0.0, le=1.0)
    unsupported_flag: bool
    supporting_evidence_refs: List[EvidenceReference] = Field(default_factory=list)
    contradicting_evidence_refs: List[EvidenceReference] = Field(default_factory=list)
    evidence_refs: List[EvidenceReference] = Field(default_factory=list)
    explanation: str

    @model_validator(mode="after")
    def _populate_canonical_verdict(self) -> "ClaimVerificationItem":
        if self.verdict is None:
            object.__setattr__(self, "verdict", self.outcome.to_claim_verdict())
        return self


class G3VerificationReport(BaseModel):
    """Structured verification report produced by G3 OutputEvidenceVerifier."""

    overall_status: VerificationStatus
    verdict: Optional[G3AnswerVerdict] = None
    total_claims: int
    supported_count: int
    contradicted_count: int
    not_enough_evidence_count: int
    insufficient_count: Optional[int] = None
    uncertain_count: int = 0
    unsupported_claims: List[str] = Field(default_factory=list)
    uncertain_claims: List[str] = Field(default_factory=list)
    claims: List[ClaimVerificationItem] = Field(default_factory=list)
    summary: str

    @model_validator(mode="after")
    def _populate_canonical_report_fields(self) -> "G3VerificationReport":
        if self.verdict is None:
            object.__setattr__(self, "verdict", self.overall_status.to_answer_verdict())
        if self.insufficient_count is None:
            object.__setattr__(self, "insufficient_count", self.not_enough_evidence_count)
        return self


# ---------------------------------------------------------------------------
# SRM: Small Reasoning Model (HalluGuard-inspired) Schemas
# ---------------------------------------------------------------------------

class SRMExecutionStatus(str, Enum):
    """Execution outcome of the SRM reasoning invocation."""

    SUCCESS = "SUCCESS"
    FALLBACK = "FALLBACK"
    TIMEOUT = "TIMEOUT"
    UNAVAILABLE = "UNAVAILABLE"
    DISABLED = "DISABLED"


class SRMClaimJudgment(BaseModel):
    """Per-claim reasoning judgment produced by SRM or deterministic fallback."""

    claim_text: str
    outcome: EvidenceOutcome
    rationale: str


class SRMRequest(BaseModel):
    """Explicit input schema sent to SRM backends."""

    query: str
    candidate_answer: str
    evidence_passages: List[Dict[str, str]] = Field(default_factory=list)
    g2_trust_scores: Dict[str, float] = Field(default_factory=dict)
    g3_claim_outcomes: List[Dict[str, Any]] = Field(default_factory=list)
    task_type: str = "trust_and_hallucination_review"


class SRMResponse(BaseModel):
    """Explicit output schema emitted by SRM backends or deterministic fallback."""

    verdict: str = Field(description="TRUSTWORTHY, CAUTION, UNTRUSTWORTHY, or REFUSE")
    reasoning_trace: str
    claim_judgments: List[SRMClaimJudgment] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    backend_used: str
    model_name: str
    execution_status: SRMExecutionStatus
    latency_ms: float = Field(ge=0.0)
    is_fallback: bool
    error_detail: Optional[str] = None


# ---------------------------------------------------------------------------
# Complete Pipeline Output Schemas
# ---------------------------------------------------------------------------

class TrustReport(BaseModel):
    """Aggregated defense report spanning G1, G2, G3, and SRM stages."""

    g1_assessment: G1Assessment
    retrieval_summary: Dict[str, Any] = Field(default_factory=dict)
    g2_assessments: List[G2DocumentAssessment] = Field(default_factory=list)
    g3_verification: Optional[G3VerificationReport] = None
    srm_response: Optional[SRMResponse] = None
    overall_trust_decision: str = Field(
        description="High-level decision: TRUSTED, FLAGGED, BLOCKED, UNVERIFIED, CONTRADICTED, or ABSTAINED"
    )
    execution_trace: List[str] = Field(default_factory=list)


class PipelineResponse(BaseModel):
    """Final user-facing and audit-grade output from TrustRAGPipeline.

    Distinction between public user-displayable fields and trusted in-process diagnostics:
    - ``answer``, ``evidence``, ``trust_report``, and ``safe_to_display`` govern public serialization
      (``model_dump()``, ``model_dump_json()``, and CLI output). Security-quarantined documents, raw
      quarantined answers, quarantined document metadata, and raw F4 threat snippets are omitted from
      these public fields.
    - Detailed quarantine payloads are held in Pydantic private state (``_diagnostic_quarantine``) and
      returned solely by :meth:`get_diagnostics`. Because the TrustRAG core library has no built-in
      identity/authentication layer, ``get_diagnostics(authorized=True)`` is a trusted in-process
      explicit opt-in guard (not an authentication or cryptographic authorization boundary) and must
      never be exposed to public CLI/API serializers.
    """

    query: str
    answer: str
    abstained: bool
    blocked_by_guardrail: bool
    safe_to_display: bool = True
    unsafe_output_quarantined: bool = False
    evidence: List[EvidenceDocument] = Field(default_factory=list)
    trust_report: TrustReport
    metadata: Dict[str, Any] = Field(default_factory=dict)

    _diagnostic_quarantine: Dict[str, Any] = PrivateAttr(default_factory=dict)

    def __init__(self, **data: Any) -> None:
        quarantined_answer = data.pop("quarantined_answer", None)
        quarantined_evidence = data.pop("quarantined_evidence", None)
        diag_payload = data.pop("diagnostic_quarantine", None)
        super().__init__(**data)
        if diag_payload is not None:
            self._diagnostic_quarantine = dict(diag_payload)
        else:
            ev_list = list(quarantined_evidence or [])
            self._diagnostic_quarantine = {
                "quarantined_answer": quarantined_answer,
                "quarantined_evidence": ev_list,
                "quarantined_doc_ids": [d.doc_id for d in ev_list],
                "raw_g2_assessments": [],
            }

    def get_diagnostics(self, *, authorized: bool = False) -> Dict[str, Any]:
        """Return unredacted internal quarantine diagnostics for trusted in-process callers.

        Note: ``authorized`` is an explicit caller-controlled opt-in guard preventing accidental
        exposure in automated serialization; it is NOT an authentication or RBAC boundary.
        """
        if not authorized:
            raise PermissionError(
                "Quarantined diagnostics withheld by default; pass authorized=True only in trusted in-process auditing contexts."
            )
        ev_list = list(self._diagnostic_quarantine.get("quarantined_evidence") or [])
        return {
            "quarantined_answer": self._diagnostic_quarantine.get("quarantined_answer"),
            "quarantined_evidence": ev_list,
            "quarantined_doc_ids": list(
                self._diagnostic_quarantine.get("quarantined_doc_ids") or [d.doc_id for d in ev_list]
            ),
            "raw_g2_assessments": list(self._diagnostic_quarantine.get("raw_g2_assessments") or []),
            "unsafe_output_quarantined": self.unsafe_output_quarantined,
            "overall_trust_decision": self.trust_report.overall_trust_decision,
        }


__all__ = [
    "G1Decision",
    "G1ReasonCode",
    "G1MatchDetail",
    "G1Assessment",
    "DocumentSecurityLabel",
    "DocumentTrustDecision",
    "EvidenceDocument",
    "SignalDetail",
    "SignalScore",
    "G2DocumentAssessment",
    "RetrievalResult",
    "GeneratedAnswer",
    "EvidenceOutcome",
    "G3ClaimVerdict",
    "G3AnswerVerdict",
    "VerificationStatus",
    "EvidenceReference",
    "ClaimVerificationItem",
    "G3VerificationReport",
    "SRMExecutionStatus",
    "SRMClaimJudgment",
    "SRMRequest",
    "SRMResponse",
    "TrustReport",
    "PipelineResponse",
]
