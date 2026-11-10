"""End-to-end TrustRAG Phase 03 defense pipeline.

Connects the complete defense flow:
User Query -> G1 Input Guardrail -> Retrieval -> G2 Multi-Signal Trust Assessment
-> Trusted Evidence Context -> Answer Generation -> G3 Claim-Level Verification
-> SRM-Assisted Reasoning -> Final Answer with Evidence and Trust Report.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Sequence, Set, Union

from trustrag.config.settings import Settings, load_config
from trustrag.data.taxonomy import DocumentSecurityLabel
from trustrag.detection.msd import MultiSignalDetector
from trustrag.engine.schemas import (
    G1Decision,
    G2DocumentAssessment,
    PipelineResponse,
    SRMRequest,
    TrustReport,
    VerificationStatus,
)
from trustrag.generation.generator import AnswerGenerator
from trustrag.guardrails.input_guardrail import InputGuardrail
from trustrag.retrieval.retriever import TrustAwareRetriever
from trustrag.srm.client import SRMClient
from trustrag.utils.logging import get_logger
from trustrag.utils.repro import set_random_seed
from trustrag.verification.output_verifier import OutputEvidenceVerifier

LOGGER = get_logger(__name__)


def _is_security_quarantined_assessment(assessment: G2DocumentAssessment) -> bool:
    """Return True if a G2 assessment indicates poisoned, obfuscated, or instruction-risk evidence."""
    if assessment.decision == DocumentSecurityLabel.POISONED:
        return True
    if assessment.decision == DocumentSecurityLabel.UNCERTAIN and (
        "DOC_OBFUSCATION" in assessment.reason_codes
        or assessment.instruction_risk_score > 0.0
        or any(rc.startswith("DOC_") for rc in assessment.reason_codes)
    ):
        return True
    return False


def _sanitize_public_g2_assessment(
    assessment: G2DocumentAssessment,
    *,
    quarantined_or_filtered: bool,
) -> G2DocumentAssessment:
    """Return a public-safe G2DocumentAssessment free of raw quarantined metadata or raw threat snippets."""
    sanitized = assessment.model_copy(deep=True)
    if quarantined_or_filtered or sanitized.removed_by_cap or _is_security_quarantined_assessment(sanitized):
        sanitized.metadata = {"redacted_for_security": True} if assessment.metadata else {}
    inst_sig = sanitized.signals.get("instruction_content")
    if inst_sig is not None and (inst_sig.flags or sanitized.instruction_risk_score > 0.0):
        # Guarantee zero attacker payload or mock snippet echoes leak via instruction signal explanation
        inst_sig.explanation = (
            f"Sanitized F4 summary: adversarial/obfuscation flags={inst_sig.flags}, "
            f"risk_score={round(sanitized.instruction_risk_score, 4)}."
        )
    return sanitized


class TrustRAGPipeline:
    """Main entry point executing the integrated G1 -> Retrieval/G2 -> Generation -> G3 -> SRM pipeline."""

    def __init__(
        self,
        *,
        settings: Optional[Settings] = None,
        documents: Optional[Sequence[Any]] = None,
        guardrail: Optional[InputGuardrail] = None,
        retriever: Optional[TrustAwareRetriever] = None,
        generator: Optional[AnswerGenerator] = None,
        verifier: Optional[OutputEvidenceVerifier] = None,
        srm_client: Optional[SRMClient] = None,
    ) -> None:
        self.settings = settings or load_config()
        set_random_seed(self.settings.app.random_seed)

        self.guardrail = guardrail or InputGuardrail(config=self.settings.guardrails)
        detector = MultiSignalDetector(config=self.settings.msd)
        self.retriever = retriever or TrustAwareRetriever(
            documents=documents,
            retrieval_config=self.settings.retrieval,
            msd_config=self.settings.msd,
            detector=detector,
        )
        self.generator = generator or AnswerGenerator(config=self.settings.generation)
        self.verifier = verifier or OutputEvidenceVerifier(config=self.settings.verification)
        self.srm_client = srm_client or SRMClient(
            config=self.settings.srm,
            llm_config=self.settings.llm,
        )

    @classmethod
    def from_jsonl(
        cls,
        corpus_path: Union[str, Path],
        *,
        settings: Optional[Settings] = None,
        limit: Optional[int] = None,
    ) -> "TrustRAGPipeline":
        """Instantiate pipeline and index documents from a local TrustRAG JSONL dataset."""
        cfg = settings or load_config()
        retriever = TrustAwareRetriever.from_jsonl(
            corpus_path,
            limit=limit,
            retrieval_config=cfg.retrieval,
            msd_config=cfg.msd,
        )
        return cls(settings=cfg, retriever=retriever)

    def run(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
        answer_override: Optional[str] = None,
    ) -> PipelineResponse:
        """Execute the full end-to-end TrustRAG defense flow for a user query."""
        trace: List[str] = []

        # 1. G1 Input Guardrail
        g1 = self.guardrail.evaluate(query)
        trace.append(f"G1:{g1.decision.value}(risk={g1.risk_score})")

        if g1.decision == G1Decision.BLOCK:
            trace.append("PIPELINE:BLOCKED_AT_G1")
            report = TrustReport(
                g1_assessment=g1,
                retrieval_summary={"status": "skipped_due_to_g1_block", "total_indexed": self.retriever.document_count},
                g2_assessments=[],
                g3_verification=None,
                srm_response=None,
                overall_trust_decision="BLOCKED",
                execution_trace=trace,
            )
            return PipelineResponse(
                query=g1.original_input,
                answer=f"Request blocked by G1 Input Guardrail ({', '.join(c.value for c in g1.reason_codes)}).",
                abstained=True,
                blocked_by_guardrail=True,
                safe_to_display=False,
                unsafe_output_quarantined=False,
                evidence=[],
                trust_report=report,
                metadata={"g1_audit_hash": g1.audit_hash, "safe_to_display": False},
            )

        # 2 & 3. Retrieval + G2 Multi-Signal Trust Assessment
        retrieval_res = self.retriever.retrieve_trusted(g1.normalized_input, top_k=top_k)
        trusted_docs = retrieval_res.trusted_documents
        trace.append(
            f"RETRIEVAL+G2:candidates={retrieval_res.candidate_count},trusted={len(trusted_docs)},filtered={len(retrieval_res.filtered_documents)}"
        )

        # Pre-generation fail-closed evidence gate: quarantine G2 POISONED, security-UNCERTAIN,
        # and unassessed documents BEFORE generation, G3, and SRM.
        trusted_doc_ids = {d.doc_id for d in trusted_docs}
        assessed_by_doc_id = {a.document_id: a for a in retrieval_res.assessments}
        trusted_assessments = [assessed_by_doc_id[d.doc_id] for d in trusted_docs if d.doc_id in assessed_by_doc_id]
        unassessed_doc_ids: Set[str] = {d.doc_id for d in trusted_docs if d.doc_id not in assessed_by_doc_id}
        poisoned_doc_ids: Set[str] = {
            a.document_id for a in trusted_assessments if a.decision == DocumentSecurityLabel.POISONED
        }
        uncertain_security_doc_ids: Set[str] = {
            a.document_id
            for a in trusted_assessments
            if a.decision == DocumentSecurityLabel.UNCERTAIN and _is_security_quarantined_assessment(a)
        }
        quarantined_doc_ids: Set[str] = poisoned_doc_ids | uncertain_security_doc_ids | unassessed_doc_ids
        trusted_has_poisoned = bool(poisoned_doc_ids)
        trusted_has_uncertain_security = bool(uncertain_security_doc_ids)
        trusted_has_unassessed = bool(unassessed_doc_ids)
        trusted_has_conflict = any(a.conflict_detected for a in trusted_assessments)
        trusted_has_other_uncertain = any(
            a.decision == DocumentSecurityLabel.UNCERTAIN and a.document_id not in quarantined_doc_ids
            for a in trusted_assessments
        )

        admissible_docs = [d for d in trusted_docs if d.doc_id not in quarantined_doc_ids]
        quarantined_docs = [d for d in trusted_docs if d.doc_id in quarantined_doc_ids]
        admissible_doc_ids = {d.doc_id for d in admissible_docs}

        if trusted_has_poisoned:
            trace.append("G2:POISONED_CONTEXT_GUARD")
        if trusted_has_uncertain_security:
            trace.append("G2:UNCERTAIN_OBFUSCATION_OR_INSTRUCTION_GUARD")
        if trusted_has_unassessed:
            trace.append("G2:UNASSESSED_DOCUMENT_QUARANTINE")
        if trusted_has_conflict:
            trace.append("G2:CONFLICT_GUARD")
        elif trusted_has_other_uncertain:
            trace.append("G2:UNCERTAIN_EVIDENCE_GUARD")
        if quarantined_docs:
            trace.append(
                f"G2:PRE_GENERATION_EVIDENCE_GATE(quarantined={len(quarantined_docs)},admissible={len(admissible_docs)})"
            )

        # 4. Answer Generation strictly from post-gate admissible evidence
        gen = self.generator.generate(
            g1.normalized_input,
            admissible_docs,
            answer_override=answer_override,
        )
        trace.append(f"GENERATION:mode={gen.generator_mode},abstained={gen.abstained}")

        # 5. G3 Claim-Level Output Evidence Verification strictly against admissible evidence
        g3_report = self.verifier.verify(
            gen.answer_text,
            admissible_docs,
            abstained=gen.abstained,
        )
        trace.append(
            f"G3:{g3_report.overall_status.value}(verdict={g3_report.verdict.value if g3_report.verdict else g3_report.overall_status.value},claims={g3_report.total_claims},sup={g3_report.supported_count},con={g3_report.contradicted_count},ins={g3_report.insufficient_count},unc={g3_report.uncertain_count})"
        )

        # 6. SRM-Assisted Reasoning strictly on admissible evidence passages
        srm_request = SRMRequest(
            query=g1.normalized_input,
            candidate_answer=gen.answer_text,
            evidence_passages=[{"doc_id": d.doc_id, "text": d.text} for d in admissible_docs],
            g2_trust_scores={
                a.doc_id: a.trust_score
                for a in retrieval_res.assessments
                if a.document_id in admissible_doc_ids
            },
            g3_claim_outcomes=[
                {
                    "claim_id": c.claim_id,
                    "claim_text": c.claim_text,
                    "outcome": c.outcome.value,
                    "verdict": c.verdict.value if c.verdict else c.outcome.value,
                    "explanation": c.explanation,
                }
                for c in g3_report.claims
            ],
        )
        srm_resp = self.srm_client.reason(srm_request)
        trace.append(
            f"SRM:{srm_resp.verdict}(status={srm_resp.execution_status.value},fallback={srm_resp.is_fallback})"
        )

        # 7. Final Overall Trust Decision (security quarantine takes precedence over generator/fallback SRM abstention)
        if g3_report.overall_status == VerificationStatus.CONTRADICTED:
            overall_decision = "CONTRADICTED"
        elif trusted_has_poisoned or trusted_has_uncertain_security or trusted_has_unassessed:
            # Explicit pre-generation security guard: surviving G2 POISONED, obfuscation/instruction-risk
            # UNCERTAIN, or unassessed documents must yield FLAGGED even when zero admissible docs cause
            # abstention/REFUSE or when external SRM returns TRUSTWORTHY.
            overall_decision = "FLAGGED"
        elif gen.abstained:
            overall_decision = "ABSTAINED"
        elif srm_resp.verdict in {"UNTRUSTWORTHY", "REFUSE"}:
            overall_decision = "CONTRADICTED"
        elif g1.decision == G1Decision.FLAG or trusted_has_conflict:
            overall_decision = "FLAGGED"
        elif (
            g3_report.overall_status
            in {VerificationStatus.UNVERIFIED, VerificationStatus.PARTIALLY_SUPPORTED, VerificationStatus.UNCERTAIN}
            or srm_resp.verdict == "CAUTION"
            or trusted_has_other_uncertain
        ):
            overall_decision = "UNVERIFIED"
        else:
            overall_decision = "TRUSTED"

        # 8. Safe Public Output & Private Diagnostic Quarantine Policy
        unsafe_output_quarantined = bool(quarantined_docs)
        diag_quarantined_answer: Optional[str] = None
        public_answer = gen.answer_text
        public_evidence = list(admissible_docs)
        public_abstained = bool(gen.abstained)

        if unsafe_output_quarantined:
            if not gen.abstained:
                diag_quarantined_answer = gen.answer_text
            public_abstained = True
            public_answer = (
                "Output withheld for safety: surviving retrieved context contains security-quarantined "
                "or unassessed document(s) excluded prior to generation. Detailed diagnostics are held "
                "exclusively for trusted in-process inspection via get_diagnostics(authorized=True)."
            )
            trace.append("OUTPUT:QUARANTINED_POISONED_CONTEXT")

        safe_to_display = (overall_decision == "TRUSTED") and not unsafe_output_quarantined
        trace.append(f"FINAL:{overall_decision}")

        filtered_doc_ids = {d.doc_id for d in retrieval_res.filtered_documents}
        public_g2_assessments = [
            _sanitize_public_g2_assessment(
                a,
                quarantined_or_filtered=(a.document_id in quarantined_doc_ids or a.document_id in filtered_doc_ids),
            )
            for a in retrieval_res.assessments
        ]

        retrieval_summary = {
            "total_indexed": retrieval_res.total_indexed,
            "requested_top_k": retrieval_res.requested_top_k,
            "candidate_count": retrieval_res.candidate_count,
            "removal_cap_k": retrieval_res.removal_cap_k,
            "removal_cap_limit": retrieval_res.removal_cap_limit,
            "removal_cap_applied": retrieval_res.removal_cap_applied,
            "trusted_count": len(trusted_docs),
            "admissible_count": len(admissible_docs),
            "quarantined_count": len(quarantined_docs),
            "filtered_count": len(retrieval_res.filtered_documents),
            "filtered_doc_ids": [d.doc_id for d in retrieval_res.filtered_documents],
        }

        report = TrustReport(
            g1_assessment=g1,
            retrieval_summary=retrieval_summary,
            g2_assessments=public_g2_assessments,
            g3_verification=g3_report,
            srm_response=srm_resp,
            overall_trust_decision=overall_decision,
            execution_trace=trace,
        )

        LOGGER.info(
            "End-to-end TrustRAG pipeline run completed",
            extra={
                "overall_decision": overall_decision,
                "g1_decision": g1.decision.value,
                "trusted_evidence_count": len(trusted_docs),
                "admissible_evidence_count": len(admissible_docs),
                "quarantined_evidence_count": len(quarantined_docs),
                "filtered_count": len(retrieval_res.filtered_documents),
                "g3_status": g3_report.overall_status.value,
                "srm_status": srm_resp.execution_status.value,
                "unsafe_output_quarantined": unsafe_output_quarantined,
                "safe_to_display": safe_to_display,
            },
        )

        out_meta: dict[str, Any] = {
            "cited_doc_ids": gen.cited_doc_ids,
            "generator_mode": gen.generator_mode,
            "srm_backend": srm_resp.backend_used,
            "srm_model": srm_resp.model_name,
            "safe_to_display": safe_to_display,
            "unsafe_output_quarantined": unsafe_output_quarantined,
        }
        if unsafe_output_quarantined:
            out_meta["quarantined_doc_ids"] = sorted(quarantined_doc_ids)

        diagnostic_payload = {
            "quarantined_answer": diag_quarantined_answer,
            "quarantined_evidence": list(quarantined_docs),
            "quarantined_doc_ids": sorted(quarantined_doc_ids),
            "raw_g2_assessments": list(retrieval_res.assessments),
        }

        return PipelineResponse(
            query=g1.original_input,
            answer=public_answer,
            abstained=public_abstained,
            blocked_by_guardrail=False,
            safe_to_display=safe_to_display,
            unsafe_output_quarantined=unsafe_output_quarantined,
            evidence=public_evidence,
            trust_report=report,
            metadata=out_meta,
            diagnostic_quarantine=diagnostic_payload,
        )


__all__ = ["TrustRAGPipeline"]
