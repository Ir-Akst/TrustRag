"""Permanent Step 7 regression tests for DEF-10, DEF-11, and DEF-12."""

from __future__ import annotations

from trustrag.config.engine_config import VerificationConfig
from trustrag.engine.schemas import EvidenceDocument
from trustrag.guardrails.paraphraser import validate_paraphrase
from trustrag.verification.output_verifier import OutputEvidenceVerifier


def test_def10_lowercase_subject_attribute_drift_and_legitimate_paraphrases() -> None:
    """DEF-10: Reject attribute-head drift even when subject entity is lowercase."""
    negative_pairs = [
        ("Who is the inventor of penicillin?", "Who is the discoverer of penicillin?"),
        ("Who is the discoverer of penicillin?", "Who is the inventor of penicillin?"),
        ("Who is the founder of linux?", "Who is the owner of linux?"),
        ("Who is the owner of linux?", "Who is the founder of linux?"),
        ("What is the diameter of earth?", "What is the mass of earth?"),
        ("What is the melting point of iron?", "What is the boiling point of iron?"),
        ("What is the price of gold?", "What is the weight of gold?"),
        ("What is the capital of france?", "What is the population of france?"),
        ("Who is the creator of python?", "Who is the maintainer of python?"),
        ("Who invented penicillin?", "Who discovered penicillin?"),
        ("What is penicillin's inventor?", "What is penicillin's discoverer?"),
    ]
    for orig, cand in negative_pairs:
        res = validate_paraphrase(orig, cand, min_similarity=0.30)
        assert res.accepted is False, f"False acceptance: {orig!r} -> {cand!r}"
        assert "PARAPHRASE_ATTRIBUTE_DRIFT" in res.rejection_reasons

    positive_pairs = [
        ("What is the capital of France?", "Which city serves as France's capital?"),
        ("What is the boiling point of water?", "What is water's boiling point?"),
        ("What is the price of gold?", "What is the cost of gold?"),
        ("When was the Eiffel Tower built?", "In what year was the Eiffel Tower constructed?"),
        ("What is the maximum safe daily dose of Paracetamol in 2026?", "what daily dose limit applies for Paracetamol in 2026?"),
        ("How does photosynthesis convert sunlight?", "How is sunlight converted by photosynthesis?"),
    ]
    for orig, cand in positive_pairs:
        res = validate_paraphrase(orig, cand, min_similarity=0.30)
        assert res.accepted is True, f"False rejection: {orig!r} -> {cand!r}: {res.rejection_reasons}"


def test_def11_cross_entity_numeric_and_temperature_non_contradiction() -> None:
    """DEF-11: Disjoint entities must return INSUFFICIENT_EVIDENCE, never false CONTRADICTED."""
    verifier = OutputEvidenceVerifier(config=VerificationConfig())

    def verdict(ans: str, ev: str) -> str:
        rep = verifier.verify(answer_text=ans, trusted_documents=[EvidenceDocument(doc_id="d1", text=ev)], query=ans)
        return rep.overall_status.to_answer_verdict().value

    assert verdict("London recorded -10°C.", "Paris recorded 10°C.") == "INSUFFICIENT_EVIDENCE"
    assert verdict("In London, temperature was -10°C.", "In Paris, temperature was 10°C.") == "INSUFFICIENT_EVIDENCE"
    assert verdict("London recorded 50 mm rainfall.", "Paris recorded 100 mm rainfall.") == "INSUFFICIENT_EVIDENCE"
    assert verdict("London recorded -10°C.", "London recorded 10°C.") == "CONTRADICTED"
    assert verdict("London recorded -10°C.", "London recorded 14°F.") == "SUPPORTED"
    assert verdict("Water boils at 212 degrees Fahrenheit.", "At standard pressure, water boils at 100 degrees Celsius.") == "SUPPORTED"


def test_def12_short_numeric_and_positive_vs_zero_classification() -> None:
    """DEF-12: Short single-topic numeric claims classify conflicts as CONTRADICTED cleanly."""
    verifier = OutputEvidenceVerifier(config=VerificationConfig())

    def verdict(ans: str, ev: str) -> str:
        rep = verifier.verify(answer_text=ans, trusted_documents=[EvidenceDocument(doc_id="d1", text=ev)], query=ans)
        return rep.overall_status.to_answer_verdict().value

    assert verdict("Temperature is 5°C.", "Temperature is 0°C.") == "CONTRADICTED"
    assert verdict("Temperature is 5°C.", "Temperature is 5°C.") == "SUPPORTED"
    assert verdict("Temperature is 5°C.", "Temperature is 41°F.") == "SUPPORTED"
    assert verdict("Temperature is -10°C.", "Temperature is 14°F.") == "SUPPORTED"
    assert verdict("Dose is 500mg.", "Dose is 100mg.") == "CONTRADICTED"
    assert verdict("Weight is 70kg.", "Weight is 50kg.") == "CONTRADICTED"
    # Ensure unrelated subjects sharing only a generic verb or lacking topic alignment stay INSUFFICIENT_EVIDENCE
    assert verdict("Temperature is 5°C.", "Humidity is 0°C.") == "INSUFFICIENT_EVIDENCE"
    assert verdict("The bridge was built in 2018.", "The house was built in 1998.") == "INSUFFICIENT_EVIDENCE"

