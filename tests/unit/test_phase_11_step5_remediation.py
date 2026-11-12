"""Permanent Step 5 regression tests for DEF-08 (attribute drift) and DEF-09 (signed negative numbers)."""

from __future__ import annotations

from trustrag.config.engine_config import VerificationConfig
from trustrag.engine.schemas import EvidenceDocument
from trustrag.engine.text_utils import extract_numbers_and_units
from trustrag.guardrails.paraphraser import validate_paraphrase
from trustrag.verification.output_verifier import OutputEvidenceVerifier


def test_def08_bidirectional_attribute_drift_and_legitimate_paraphrases() -> None:
    negative_pairs = [
        ("What is the capital of France?", "What is the population of France?"),
        ("What is the population of France?", "What is the capital of France?"),
        ("When was Apple founded?", "Where is Apple headquartered?"),
        ("Where is Apple headquartered?", "When was Apple founded?"),
        ("What is the largest city in Japan?", "What is the oldest city in Japan?"),
        ("What is the oldest city in Japan?", "What is the largest city in Japan?"),
        ("What is the cause of inflation?", "What is the consequence of inflation?"),
        ("What is the consequence of inflation?", "What is the cause of inflation?"),
        ("What is Albert Einstein's date of birth?", "What is Albert Einstein's date of death?"),
        ("What is Albert Einstein's date of death?", "What is Albert Einstein's date of birth?"),
        ("What is the capital of France?", "What is the currency of France?"),
    ]
    for orig, cand in negative_pairs:
        res = validate_paraphrase(orig, cand, min_similarity=0.30)
        assert res.accepted is False, f"False acceptance: {orig!r} -> {cand!r}"

    positive_pairs = [
        ("What is the capital of France?", "Which city serves as France's capital?"),
        ("What is the capital of France?", "what is the capital city of France, please?"),
        ("When was the Eiffel Tower built?", "In what year was the Eiffel Tower constructed?"),
        ("How does photosynthesis convert sunlight?", "How is sunlight converted by photosynthesis?"),
        ("What is the population of Tokyo?", "How large is Tokyo's population?"),
    ]
    for orig, cand in positive_pairs:
        res = validate_paraphrase(orig, cand, min_similarity=0.30)
        assert res.accepted is True, f"False rejection: {orig!r} -> {cand!r}: {res.rejection_reasons}"


def test_def09_signed_negative_extraction_and_g3_classification() -> None:
    # 1. Extraction preserves negative signs only when preceded by boundary/space, not hyphens/dates
    assert extract_numbers_and_units("Temperature dropped to -10°C.")[0][0] == "-10"
    assert extract_numbers_and_units("Value is -0°C.")[0][0] == "0"
    assert extract_numbers_and_units("AES-256 and well-known 2024-05-12")[0][0] == "256"
    assert [n for n, _ in extract_numbers_and_units("From 2018-2020")] == ["2018", "2020"]

    # 2. Full G3 verification
    v = OutputEvidenceVerifier(config=VerificationConfig())

    def verdict(ans: str, ev: str) -> str:
        rep = v.verify(answer_text=ans, trusted_documents=[EvidenceDocument(doc_id="d1", text=ev)], query=ans)
        return rep.overall_status.to_answer_verdict().value

    assert verdict("Temperature rose to 10°C.", "Temperature dropped to -10°C.") == "CONTRADICTED"
    assert verdict("Temperature dropped to -10°C.", "Temperature dropped to -10°C.") == "SUPPORTED"
    assert verdict("Water freezes at 0°C.", "Water freezes at -0°C.") == "SUPPORTED"
    assert verdict("The sensor reads -40°C.", "The sensor reads -40°F.") == "SUPPORTED"
    assert verdict("The sensor reads -10°C.", "The sensor reads 14°F.") == "SUPPORTED"
    assert verdict("Profit changed by -5%.", "Profit changed by 5%.") == "CONTRADICTED"
    assert verdict("Profit changed by -5%.", "Profit changed by -5%.") == "SUPPORTED"
    assert verdict("AES-256 uses a 256-bit key.", "AES-256 uses a 256-bit key.") == "SUPPORTED"

