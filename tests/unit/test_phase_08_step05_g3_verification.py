"""Phase 08 Step 05 tests: G3 enhanced verification, multi-doc bridging, trust weighting, and model judge."""

from __future__ import annotations

import json

from trustrag.config import VerificationConfig
from trustrag.config.engine_config import SRMConfig
from trustrag.engine.schemas import EvidenceDocument, G3AnswerVerdict, SRMRequest
from trustrag.srm import HuggingFaceLocalSRMBackend, SRMClient
from trustrag.verification.output_verifier import OutputEvidenceVerifier


def test_g3_enhanced_numeric_temporal_table_temp_and_multidoc() -> None:
    v = OutputEvidenceVerifier(config=VerificationConfig(enabled=True))

    # 1. Unitless counted noun conflict -> CONTRADICTED
    c_num = v.verify(
        "The trial enrolled 500 patients across 10 hospitals.",
        [EvidenceDocument(doc_id="d1", text="The trial enrolled 50 patients across 10 hospitals.")],
    )
    assert c_num.verdict == G3AnswerVerdict.CONTRADICTED

    # 2. Temporal retirement contradiction -> CONTRADICTED
    c_tmp = v.verify(
        "Dr. Rao currently serves as chair in 2026.",
        [EvidenceDocument(doc_id="d2", text="Dr. Rao served as chair in 2019 before retiring in 2021.")],
    )
    assert c_tmp.verdict == G3AnswerVerdict.CONTRADICTED

    # 3. Temperature C <-> F conversion -> SUPPORTED
    c_unit = v.verify(
        "Water boils at 212 degrees Fahrenheit.",
        [EvidenceDocument(doc_id="d3", text="At standard pressure, water boils at 100 degrees Celsius.")],
    )
    assert c_unit.verdict == G3AnswerVerdict.SUPPORTED

    # 4. Markdown shorthand 14M vs 14000000 -> SUPPORTED
    c_tbl = v.verify(
        "Tokyo has a population of 14000000.",
        [EvidenceDocument(doc_id="d4", text="| City | Population |\n|---|---|\n| Tokyo | 14M |\n| Kyoto | 1.4M |")],
    )
    assert c_tbl.verdict == G3AnswerVerdict.SUPPORTED

    # 5. Multi-document 2-hop bridging -> SUPPORTED
    c_mhop = v.verify(
        "Alice lives in France.",
        [
            EvidenceDocument(doc_id="m1", text="Alice lives in Paris."),
            EvidenceDocument(doc_id="m2", text="Paris is located in France."),
        ],
    )
    assert c_mhop.verdict == G3AnswerVerdict.SUPPORTED


def test_g3_passage_trust_weighting_and_model_citation_guard() -> None:
    # 1. Passage with low G2 trust cannot yield unqualified SUPPORTED
    v = OutputEvidenceVerifier(config=VerificationConfig(enabled=True))
    low_t = v.verify(
        "Paris is the capital of France.",
        [EvidenceDocument(doc_id="low1", text="Paris is the capital of France.")],
        doc_trust_scores={"low1": 0.42},
        min_passage_trust=0.60,
    )
    assert low_t.verdict == G3AnswerVerdict.UNCERTAIN

    # 2. Model-backed G3 requires verified substring citation; unverified citations blocked
    class _Tok:
        eos_token_id = 2
        pad_token_id = 2

        def __init__(self, payload: dict) -> None:  # type: ignore[no-untyped-def]
            self.payload = payload

        def __call__(self, text: str, return_tensors: str = "pt") -> dict[str, list[list[int]]]:
            return {"input_ids": [[1, 2]]}

        def decode(self, ids, skip_special_tokens: bool = True) -> str:  # type: ignore[no-untyped-def]
            return json.dumps(self.payload)

    class _Mdl:
        def generate(self, **kw):  # type: ignore[no-untyped-def]
            return [[1, 2, 3]]

    verified_payload = {
        "verdict": "TRUSTWORTHY",
        "reasoning_trace": "Cited span confirms claim.",
        "confidence": 0.90,
        "claim_judgments": [
            {
                "claim_id": "c1",
                "claim_text": "Aspirin slows platelet clumping.",
                "outcome": "SUPPORTS",
                "hallucination_category": "GROUNDED",
                "evidence_ids": ["med1"],
                "cited_spans": ["acetylsalicylic acid inhibits thrombocyte aggregation"],
                "confidence": 0.90,
                "rationale": "Clinical mechanism paraphrase.",
            }
        ],
    }
    cfg = SRMConfig(backend="hf_local", model_name="fake-srm", fallback_on_error=False)
    ok_client = SRMClient(
        config=cfg,
        backend=HuggingFaceLocalSRMBackend(cfg, loader_override=lambda _c: (_Mdl(), _Tok(verified_payload), "cpu")),
    )
    v_model = OutputEvidenceVerifier(config=VerificationConfig(enabled=True), srm_client=ok_client)
    res_ok = v_model.verify(
        "Aspirin slows platelet clumping.",
        [EvidenceDocument(doc_id="med1", text="Clinical pharmacology shows acetylsalicylic acid inhibits thrombocyte aggregation.")],
    )
    assert res_ok.verdict == G3AnswerVerdict.SUPPORTED

    bad_payload = {
        "verdict": "TRUSTWORTHY",
        "reasoning_trace": "Fake citation.",
        "confidence": 0.99,
        "claim_judgments": [
            {
                "claim_id": "c1",
                "claim_text": "Unicorn enzymes cure flu.",
                "outcome": "SUPPORTS",
                "hallucination_category": "GROUNDED",
                "evidence_ids": ["med1"],
                "cited_spans": ["fabricated span not inside evidence"],
                "confidence": 0.99,
                "rationale": "Hallucinated justification.",
            }
        ],
    }
    bad_client = SRMClient(
        config=cfg,
        backend=HuggingFaceLocalSRMBackend(cfg, loader_override=lambda _c: (_Mdl(), _Tok(bad_payload), "cpu")),
    )
    v_bad = OutputEvidenceVerifier(config=VerificationConfig(enabled=True), srm_client=bad_client)
    res_bad = v_bad.verify(
        "Unicorn enzymes cure flu.",
        [EvidenceDocument(doc_id="med1", text="Clinical pharmacology shows acetylsalicylic acid inhibits thrombocyte aggregation.")],
    )
    assert res_bad.verdict == G3AnswerVerdict.INSUFFICIENT_EVIDENCE
    _ = SRMRequest(query="q", candidate_answer="a")
