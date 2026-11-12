"""Preserved read-only Step 8 adversarial reproductions for newly observed edge findings."""

from __future__ import annotations

from trustrag.config.engine_config import VerificationConfig
from trustrag.engine.schemas import EvidenceDocument
from trustrag.guardrails.paraphraser import validate_paraphrase
from trustrag.verification.output_verifier import OutputEvidenceVerifier


def main() -> None:
    p1 = validate_paraphrase(
        "What is the distance between London and Paris?",
        "What is the flight time between London and Paris?",
        min_similarity=0.30,
    )
    p2 = validate_paraphrase(
        "What is the law about copyright?",
        "What is the history about copyright?",
        min_similarity=0.30,
    )
    p3 = validate_paraphrase(
        "What treats malaria?",
        "What prevents malaria?",
        min_similarity=0.30,
    )
    print("DEF-13 (between/and stopword leakage):", p1.accepted, p1.semantic_similarity, p1.rejection_reasons)
    print("DEF-13 (about stopword leakage):", p2.accepted, p2.semantic_similarity, p2.rejection_reasons)
    print("DEF-14 (anchorless verb substitution):", p3.accepted, p3.semantic_similarity, p3.rejection_reasons)

    v = OutputEvidenceVerifier(config=VerificationConfig())
    for label, claim, ev in [
        ("DEF-15a (temporal year stripped in single_topic_num_shared)", "Temperature was 5°C in 2020.", "Temperature is 0°C in 2024."),
        ("DEF-15b (1-char entity identifier ignored)", "Sensor A is 5°C.", "Sensor B is 0°C."),
        ("DEF-16 (mm not parsed as unit vs unitless 10C)", "London recorded 50 mm rainfall.", "London recorded 10°C."),
    ]:
        rep = v.verify(answer_text=claim, trusted_documents=[EvidenceDocument(doc_id="d1", text=ev)], query=claim)
        print(f"{label}: {rep.overall_status.to_answer_verdict().value} | {rep.claims[0].explanation}")


if __name__ == "__main__":
    main()

