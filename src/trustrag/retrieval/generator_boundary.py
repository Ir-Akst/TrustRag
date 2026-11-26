"""Phase 40 Priority Zero: Centralized Fail-Closed Generator-Boundary Enforcement.

Protects the exact serialized context that reaches the generator:
- Preserves trust and provenance metadata on every retrieved document.
- Wraps retrieved evidence in explicit untrusted-data boundaries.
- Runs pre-serialization sanitization (multi-line blocks, split instructions, obfuscated headers).
- Performs independent pre-invocation revalidation on the exact final serialized context.
- Fails closed with structured security events if unsafe instructions reach the boundary.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from trustrag.engine.schemas import EvidenceDocument
from trustrag.engine.text_utils import detect_obfuscation, fold_mixed_script_confusables
from trustrag.retrieval.document_firewall import DocumentInjectionFirewall, QuarantinedSpan
from trustrag.utils.logging import get_logger

LOGGER = get_logger(__name__)


@dataclass
class BoundarySecurityEvent:
    """Structured security event emitted by GeneratorBoundaryEnforcer."""
    allowed: bool
    action: str  # "ALLOW", "SANITIZE_AND_ALLOW", "FAIL_CLOSED_BLOCK"
    quarantined_count: int
    boundary_revalidation_passed: bool
    reason: str
    blocked_patterns: List[str] = field(default_factory=list)
    doc_ids_retained: List[str] = field(default_factory=list)
    doc_ids_blocked: List[str] = field(default_factory=list)


@dataclass
class BoundaryEnforcementResult:
    """Validated, serialized context and sanitized documents ready for generator invocation."""
    safe_documents: List[EvidenceDocument]
    serialized_context: str
    quarantined_spans: List[QuarantinedSpan]
    security_event: BoundarySecurityEvent
    fail_closed_triggered: bool = False


class GeneratorBoundaryEnforcer:
    """Centralized, fail-closed boundary enforcer immediately before generator invocation."""

    def __init__(self, *, firewall: Optional[DocumentInjectionFirewall] = None) -> None:
        self.firewall = firewall or DocumentInjectionFirewall(strict_quarantine=True)
        # Independent final-context revalidation patterns (defense-in-depth over serialized text)
        self._boundary_patterns: Tuple[Tuple[str, re.Pattern[str]], ...] = (
            (
                "boundary_role_header_spoof",
                re.compile(
                    r"(?:^|\n|>|\|)\s*(?:#{1,6}\s*)?(?:SYSTEM|DEVELOPER|ADMIN|ROOT|SUPERVISOR|ASSISTANT_OVERRIDE|KERNEL_ADMIN|POLICY_ENGINE|SYSTEM_PROMPT|SYSTEM_MESSAGE)\b\s*[:\]]",
                    re.IGNORECASE,
                ),
            ),
            (
                "boundary_citation_authority_spoof",
                re.compile(
                    r"(?:\[(?:citation|ref|reference|source|footnote|bib|bibliography)[^\]]*\]|(?:citation|footnote|bibliography|reference|source|ref\.?)\s*(?:\[?\d+\]?|\(\d+\)))\s*(?:[-–—>:]|\([^\)]+\))*\s*(?:mandatory|authoritative|system|internal|model|assistant|ai)?\s*(?:directive|instruction|override|policy|command|rule)?\s*[:\-–>]*\s*[^\n]*(?:disregard|ignore|override|bypass|reveal|output|print|leak|cease|dump|secret|prompt|key|token)",
                    re.IGNORECASE,
                ),
            ),
            (
                "boundary_instruction_override",
                re.compile(
                    r"\b(?:ignore|disregard|override|bypass|abandon|cease\s+following|set\s+aside|suspend)\s+(?:all\s+)?(?:prior|previous|earlier|safety|security|user|system|retrieved)?\s*(?:rules?|instructions?|directives?|constraints?|filters?|checks?|evidence|query)\b",
                    re.IGNORECASE,
                ),
            ),
            (
                "boundary_secret_exfil_command",
                re.compile(
                    r"\b(?:print|output|reveal|expose|leak|dump|display|recite)\s+(?:the\s+)?(?:hidden\s+|confidential\s+|secret\s+|private\s+|internal\s+)?(?:system\s*prompt|developer\s+(?:prompt|instructions?)|api[_\s]?key\w*|secret[_\s]?(?:token|key|env)\w*|admin[_\s]?(?:key|password|token)\w*|pwned_\d+|system_override\w*)\b",
                    re.IGNORECASE,
                ),
            ),
            (
                "boundary_html_comment_directive",
                re.compile(
                    r"<!--[\s\S]*?(?:directive|override|ignore|disregard|bypass|secret|system_prompt|pwned|admin_token|assistant|internal\s+note)[\s\S]*?-->",
                    re.IGNORECASE,
                ),
            ),
        )

    @staticmethod
    def _normalize_for_inspection(text: str) -> str:
        _, cleaned, _ = detect_obfuscation(unicodedata.normalize("NFKC", text or ""))
        folded, _ = fold_mixed_script_confusables(cleaned or text or "")
        return folded

    @staticmethod
    def serialize_untrusted_context(
        documents: Sequence[EvidenceDocument],
        trust_scores: Optional[Dict[str, float]] = None,
    ) -> str:
        """Serialize documents strictly as untrusted data blocks with provenance metadata."""
        if not documents:
            return ""
        blocks: List[str] = []
        for doc in documents:
            t_score = (
                trust_scores.get(doc.doc_id)
                if trust_scores and doc.doc_id in trust_scores
                else doc.metadata.get("trust_score", getattr(doc, "retrieval_score", 1.0) or 1.0)
            )
            src = doc.source_id or doc.provenance or "unknown"
            # Escape any closing tag attempts inside untrusted text
            safe_body = doc.text.replace("</untrusted_evidence>", "&lt;/untrusted_evidence&gt;")
            blocks.append(
                f'<untrusted_evidence doc_id="{doc.doc_id}" source="{src}" trust_score="{float(t_score):.3f}">\n'
                f"{safe_body}\n"
                f"</untrusted_evidence>"
            )
        return "\n\n".join(blocks)

    def validate_serialized_context(self, serialized_context: str) -> Tuple[bool, List[str]]:
        """Independently inspect the exact serialized context before generator invocation."""
        if not serialized_context.strip():
            return True, []
        # Inspect inside each untrusted_evidence block
        norm_ctx = self._normalize_for_inspection(serialized_context)
        hits: List[str] = []
        for name, pat in self._boundary_patterns:
            if pat.search(norm_ctx):
                hits.append(name)
        return len(hits) == 0, hits

    def enforce(
        self,
        documents: Sequence[EvidenceDocument],
        *,
        trust_scores: Optional[Dict[str, float]] = None,
    ) -> BoundaryEnforcementResult:
        """Sanitize, serialize as untrusted data, and fail-closed revalidate before generation."""
        if not documents:
            ev = BoundarySecurityEvent(
                allowed=True,
                action="ALLOW",
                quarantined_count=0,
                boundary_revalidation_passed=True,
                reason="Empty document set; no untrusted context serialized.",
            )
            return BoundaryEnforcementResult(
                safe_documents=[],
                serialized_context="",
                quarantined_spans=[],
                security_event=ev,
                fail_closed_triggered=False,
            )

        # Stage 1: Sanitize documents via DocumentInjectionFirewall (preserving trust/provenance metadata)
        clean_docs, quarantined = self.firewall.sanitize_retrieved_documents(list(documents))

        # Preserve trust score metadata explicitly
        for d in clean_docs:
            if trust_scores and d.doc_id in trust_scores:
                d.metadata["trust_score"] = trust_scores[d.doc_id]
            d.metadata["untrusted_data_wrapped"] = True

        # Stage 2: Cross-document split instruction check on combined admissible text
        if len(clean_docs) > 1:
            combined = " ".join(d.text for d in clean_docs)
            norm_combined = self._normalize_for_inspection(combined)
            # Check if split fragments across documents form an override/exfil directive
            has_split_override = bool(
                re.search(
                    r"(?:step\s*1|part\s*a|first)[^.]{0,80}(?:disregard|ignore|bypass|override)[^.]{0,120}(?:step\s*2|part\s*b|then|next)[^.]{0,80}(?:print|output|reveal|secret|token|key|prompt)",
                    norm_combined,
                    re.IGNORECASE,
                )
            )
            if has_split_override:
                ev = BoundarySecurityEvent(
                    allowed=False,
                    action="FAIL_CLOSED_BLOCK",
                    quarantined_count=len(quarantined),
                    boundary_revalidation_passed=False,
                    reason="Cross-document split instruction detected across retrieved passages; failing closed.",
                    blocked_patterns=["cross_document_split_instruction"],
                    doc_ids_blocked=[d.doc_id for d in clean_docs],
                )
                LOGGER.warning("Generator boundary fail-closed triggered", extra={"reason": ev.reason})
                return BoundaryEnforcementResult(
                    safe_documents=[],
                    serialized_context="",
                    quarantined_spans=quarantined,
                    security_event=ev,
                    fail_closed_triggered=True,
                )

        # Stage 3: Serialize strictly as untrusted data and revalidate per-document & final context
        verified_docs: List[EvidenceDocument] = []
        blocked_ids: List[str] = []
        all_hits: List[str] = []

        for d in clean_docs:
            single_ctx = self.serialize_untrusted_context([d], trust_scores=trust_scores)
            ok, hits = self.validate_serialized_context(single_ctx)
            if ok:
                verified_docs.append(d)
            else:
                blocked_ids.append(d.doc_id)
                all_hits.extend(hits)

        serialized = self.serialize_untrusted_context(verified_docs, trust_scores=trust_scores)
        final_ok, final_hits = self.validate_serialized_context(serialized)
        if not final_ok:
            # Fail-closed: refuse to pass unsafe context to generator
            all_hits.extend(final_hits)
            ev = BoundarySecurityEvent(
                allowed=False,
                action="FAIL_CLOSED_BLOCK",
                quarantined_count=len(quarantined),
                boundary_revalidation_passed=False,
                reason=f"Final serialized context failed boundary revalidation ({sorted(set(all_hits))}); failing closed.",
                blocked_patterns=sorted(set(all_hits)),
                doc_ids_blocked=[d.doc_id for d in documents],
            )
            LOGGER.warning("Generator boundary fail-closed triggered", extra={"blocked_patterns": ev.blocked_patterns})
            return BoundaryEnforcementResult(
                safe_documents=[],
                serialized_context="",
                quarantined_spans=quarantined,
                security_event=ev,
                fail_closed_triggered=True,
            )

        action = "SANITIZE_AND_ALLOW" if (quarantined or blocked_ids) else "ALLOW"
        ev = BoundarySecurityEvent(
            allowed=True,
            action=action,
            quarantined_count=len(quarantined),
            boundary_revalidation_passed=True,
            reason="Context sanitized and passed independent pre-invocation boundary revalidation.",
            blocked_patterns=sorted(set(all_hits)),
            doc_ids_retained=[d.doc_id for d in verified_docs],
            doc_ids_blocked=blocked_ids,
        )
        return BoundaryEnforcementResult(
            safe_documents=verified_docs,
            serialized_context=serialized,
            quarantined_spans=quarantined,
            security_event=ev,
            fail_closed_triggered=False,
        )
