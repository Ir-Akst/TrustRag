"""Phase 08 Step 06 tests: Query consistency verification and controlled high-trust re-answer loop."""

from __future__ import annotations

from trustrag.config import load_config
from trustrag.engine.schemas import EvidenceDocument, G3AnswerVerdict, VerificationStatus
from trustrag.pipeline import TrustRAGPipeline
from trustrag.verification import OutputEvidenceVerifier, evaluate_query_consistency


def test_query_consistency_catches_hijack_dos_refusal_and_temporal_drift() -> None:
    docs = [EvidenceDocument(doc_id="d1", text="AES-256 uses a 256-bit key; brute-force decryption is infeasible.", source_id="nist", provenance="nist")]

    # 1. Grounded off-topic hijack (banana text present in injected context)
    hijack_docs = [EvidenceDocument(doc_id="h1", text="Fresh bananas provide potassium and dietary fiber.", source_id="blog", provenance="blog")]
    v = OutputEvidenceVerifier(config=load_config().verification)
    hijack_rep = v.verify(
        "Fresh bananas provide potassium and dietary fiber.",
        hijack_docs,
        query="Is AES-256 vulnerable to brute-force decryption?",
    )
    assert hijack_rep.query_consistent is False
    assert hijack_rep.overall_status == VerificationStatus.UNVERIFIED
    assert hijack_rep.verdict == G3AnswerVerdict.INSUFFICIENT_EVIDENCE

    # 2. Spurious DoS refusal when evidence clearly covers query
    dos_qc = evaluate_query_consistency(
        "Is AES-256 vulnerable to brute-force decryption?",
        "I cannot answer this request due to policy.",
        docs,
        abstained=False,
    )
    assert dos_qc.spurious_refusal_detected is True
    assert dos_qc.consistent is False

    # 3. Missing query temporal anchor
    yr_qc = evaluate_query_consistency(
        "Did the Federal Reserve raise rates in 2023?",
        "Rates remained completely flat throughout 2019.",
        docs,
        abstained=False,
    )
    assert yr_qc.consistent is False
    assert "2023" in yr_qc.missing_query_constraints


def test_pipeline_controlled_reanswer_recovers_and_preserves_trace() -> None:
    cfg = load_config()
    cfg.verification.enable_reanswer = True
    cfg.verification.max_reanswer_attempts = 2
    cfg.verification.min_reanswer_trust_score = 0.60

    clean_docs = [
        EvidenceDocument(
            doc_id="clean_aes",
            text="AES-256 uses a 256-bit symmetric key, making brute-force attacks computationally infeasible.",
            source_id="nist_01",
            provenance="nist",
        )
    ]
    pipe = TrustRAGPipeline(settings=cfg, documents=clean_docs)

    # Answer override injects ungrounded/off-topic text -> controlled re-answer runs strictly on clean_aes
    resp = pipe.run(
        "Is AES-256 vulnerable to brute-force attacks?",
        top_k=1,
        answer_override="Bananas are yellow tropical fruits rich in potassium.",
    )
    audit = resp.metadata["reanswer_audit"]
    assert audit["applied"] is True
    assert audit["attempts"] == 1
    assert audit["initial_answer"] == "Bananas are yellow tropical fruits rich in potassium."
    assert audit["initial_g3_status"] == "UNVERIFIED"
    assert audit["initial_query_consistent"] is False
    assert resp.trust_report.overall_trust_decision == "TRUSTED"
    assert resp.trust_report.g3_verification is not None
    assert resp.trust_report.g3_verification.overall_status == VerificationStatus.VERIFIED
    assert resp.trust_report.g3_verification.query_consistent is True
    assert not resp.abstained


def test_pipeline_reanswer_abstains_when_no_high_trust_subset_exists() -> None:
    cfg = load_config()
    cfg.verification.enable_reanswer = True
    cfg.verification.min_reanswer_trust_score = 0.99  # stricter than any standard doc trust score

    docs = [
        EvidenceDocument(
            doc_id="d1",
            text="AES-256 uses a 256-bit symmetric key.",
            source_id="s1",
            provenance="custom_security",
        )
    ]
    pipe = TrustRAGPipeline(settings=cfg, documents=docs)
    resp = pipe.run("What key size does AES-256 use?", top_k=1)
    assert resp.abstained is True
    assert resp.metadata["reanswer_audit"]["applied"] is True
    assert "REANSWER:NO_HIGH_TRUST_EVIDENCE_ABSTAIN" in resp.trust_report.execution_trace
