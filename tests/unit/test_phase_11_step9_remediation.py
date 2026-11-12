"""Unit & regression tests for Phase 11 Step 9 targeted remediation (DEF-13..DEF-16)."""

from __future__ import annotations

import pytest

from trustrag.engine.text_utils import extract_numbers_and_units
from trustrag.guardrails.paraphraser import validate_paraphrase
from trustrag.verification.output_verifier import (
    EvidenceDocument,
    G3AnswerVerdict,
    OutputEvidenceVerifier,
)


class TestDef13ParaphraseStopwordAndBridgeDrift:
    """DEF-13: Stopword/bridge overlap must not mask attribute substitutions."""

    @pytest.mark.parametrize(
        ("orig", "cand"),
        [
            (
                "What is the distance between London and Paris?",
                "What is the flight time between London and Paris?",
            ),
            (
                "What is the law about copyright?",
                "What is the history about copyright?",
            ),
            (
                "What is the difference between machine learning and deep learning?",
                "What is the similarity between machine learning and deep learning?",
            ),
            (
                "Where is glucose stored inside the cell?",
                "Where is glucose stored outside the cell?",
            ),
            (
                "What happens before cell division?",
                "What happens after cell division?",
            ),
        ],
    )
    def test_rejects_bridge_masked_and_preposition_drift(self, orig: str, cand: str) -> None:
        res = validate_paraphrase(orig, cand, min_similarity=0.30)
        assert res.accepted is False

    @pytest.mark.parametrize(
        ("orig", "cand"),
        [
            (
                "How is the distance between London and Paris measured?",
                "What measures the distance between London and Paris?",
            ),
            (
                "What is copyright law about?",
                "Explain the law regarding copyright.",
            ),
        ],
    )
    def test_preserves_legitimate_bridge_paraphrases(self, orig: str, cand: str) -> None:
        res = validate_paraphrase(orig, cand, min_similarity=0.30)
        assert res.accepted is True


class TestDef14LowercaseVerbPredicateDrift:
    """DEF-14: Anchorless lowercase verb/relation swaps must be rejected while preserving valid verb forms."""

    @pytest.mark.parametrize(
        ("orig", "cand"),
        [
            ("What treats malaria?", "What prevents malaria?"),
            ("What treats anemia?", "What causes anemia?"),
            ("What treats tuberculosis?", "What diagnoses tuberculosis?"),
            ("What reduces inflammation?", "What monitors inflammation?"),
            ("What controls blood sugar?", "What measures blood sugar?"),
        ],
    )
    def test_rejects_anchorless_verb_drift(self, orig: str, cand: str) -> None:
        res = validate_paraphrase(orig, cand, min_similarity=0.30)
        assert res.accepted is False

    @pytest.mark.parametrize(
        ("orig", "cand"),
        [
            ("What reduces inflammation?", "What lowers inflammation?"),
            ("What treats malaria?", "What cures malaria?"),
            ("What treats malaria?", "How is malaria treated?"),
            ("Who built the bridge?", "Who constructed the bridge?"),
        ],
    )
    def test_preserves_legitimate_verb_paraphrases(self, orig: str, cand: str) -> None:
        res = validate_paraphrase(orig, cand, min_similarity=0.30)
        assert res.accepted is True


class TestDef15TemporalAndEntitySlotSeparation:
    """DEF-15: Disjoint temporal anchors and short designators must not trigger false contradictions."""

    def setup_method(self) -> None:
        self.verifier = OutputEvidenceVerifier()

    def test_disjoint_years_do_not_falsely_contradict_temperature(self) -> None:
        r1 = self.verifier.verify(
            "Temperature is 0°C in 2024.",
            [EvidenceDocument(doc_id="d1", text="Temperature was 5°C in 2020.")],
        )
        r2 = self.verifier.verify(
            "Temperature was 5°C in 2020.",
            [EvidenceDocument(doc_id="d1", text="Temperature is 0°C in 2024.")],
        )
        assert r1.verdict == G3AnswerVerdict.INSUFFICIENT_EVIDENCE
        assert r2.verdict == G3AnswerVerdict.INSUFFICIENT_EVIDENCE

    def test_disjoint_years_and_iso_dates_with_units_are_insufficient(self) -> None:
        r_rain = self.verifier.verify(
            "Rainfall was 50 mm in 2020.",
            [EvidenceDocument(doc_id="d1", text="Rainfall was 80 mm in 2024.")],
        )
        r_date = self.verifier.verify(
            "Sensor A recorded 5°C on 2024-01-10.",
            [EvidenceDocument(doc_id="d1", text="Sensor A recorded 12°C on 2024-02-10.")],
        )
        assert r_rain.verdict == G3AnswerVerdict.INSUFFICIENT_EVIDENCE
        assert r_date.verdict == G3AnswerVerdict.INSUFFICIENT_EVIDENCE

    def test_same_year_conflict_and_event_year_conflict_remain_contradicted(self) -> None:
        r_same_year = self.verifier.verify(
            "Temperature was 0°C in 2020.",
            [EvidenceDocument(doc_id="d1", text="Temperature was 5°C in 2020.")],
        )
        r_event = self.verifier.verify(
            "The Eiffel Tower was completed in 1899.",
            [EvidenceDocument(doc_id="d1", text="The Eiffel Tower was completed in 1889.")],
        )
        assert r_same_year.verdict == G3AnswerVerdict.CONTRADICTED
        assert r_event.verdict == G3AnswerVerdict.CONTRADICTED

    def test_short_entity_slots_sensor_a_vs_sensor_b_do_not_conflict_or_falsely_support(self) -> None:
        r_diff = self.verifier.verify(
            "Sensor B is 0°C.",
            [EvidenceDocument(doc_id="d1", text="Sensor A is 5°C.")],
        )
        r_same_val_diff_id = self.verifier.verify(
            "Sensor B is 5°C.",
            [EvidenceDocument(doc_id="d1", text="Sensor A is 5°C.")],
        )
        r_device = self.verifier.verify(
            "Device 2 measured 120 kPa.",
            [EvidenceDocument(doc_id="d1", text="Device 1 measured 100 kPa.")],
        )
        assert r_diff.verdict == G3AnswerVerdict.INSUFFICIENT_EVIDENCE
        assert r_same_val_diff_id.verdict == G3AnswerVerdict.INSUFFICIENT_EVIDENCE
        assert r_device.verdict == G3AnswerVerdict.INSUFFICIENT_EVIDENCE

    def test_same_short_entity_slot_supports_and_contradicts_correctly(self) -> None:
        r_sup = self.verifier.verify(
            "Sensor A is 5°C.",
            [EvidenceDocument(doc_id="d1", text="Sensor A is 5°C.")],
        )
        r_con = self.verifier.verify(
            "Sensor A is 0°C.",
            [EvidenceDocument(doc_id="d1", text="Sensor A is 5°C.")],
        )
        assert r_sup.verdict == G3AnswerVerdict.SUPPORTED
        assert r_con.verdict == G3AnswerVerdict.CONTRADICTED


class TestDef16MeasurementUnitCompatibility:
    """DEF-16: Incompatible physical units must not trigger false contradictions; compatible units convert."""

    def setup_method(self) -> None:
        self.verifier = OutputEvidenceVerifier()

    def test_unit_extraction_preserves_mm_kpa_celsius_without_breaking_million_shorthand(self) -> None:
        assert extract_numbers_and_units("London recorded 10°C.") == [("10", "c")]
        assert extract_numbers_and_units("London recorded 50 mm rainfall.") == [("50", "mm")]
        assert extract_numbers_and_units("Pressure reached 101 kPa.") == [("101", "kpa")]
        assert extract_numbers_and_units("Tokyo | 14M") == []

    def test_incompatible_physical_dimensions_are_insufficient_evidence(self) -> None:
        r_c_mm = self.verifier.verify(
            "London recorded 10°C.",
            [EvidenceDocument(doc_id="d1", text="London recorded 50 mm rainfall.")],
        )
        r_mm_c = self.verifier.verify(
            "London recorded 50 mm rainfall.",
            [EvidenceDocument(doc_id="d1", text="London recorded 10°C.")],
        )
        r_kmh_kpa = self.verifier.verify(
            "Station Alpha recorded 80 kmh.",
            [EvidenceDocument(doc_id="d1", text="Station Alpha recorded 101 kPa.")],
        )
        assert r_c_mm.verdict == G3AnswerVerdict.INSUFFICIENT_EVIDENCE
        assert r_mm_c.verdict == G3AnswerVerdict.INSUFFICIENT_EVIDENCE
        assert r_kmh_kpa.verdict == G3AnswerVerdict.INSUFFICIENT_EVIDENCE

    def test_compatible_length_units_support_and_contradict_across_scales(self) -> None:
        r_sup = self.verifier.verify(
            "London recorded 50 mm rainfall.",
            [EvidenceDocument(doc_id="d1", text="London recorded 5 cm rainfall.")],
        )
        r_con = self.verifier.verify(
            "London recorded 50 mm rainfall.",
            [EvidenceDocument(doc_id="d1", text="London recorded 8 cm rainfall.")],
        )
        assert r_sup.verdict == G3AnswerVerdict.SUPPORTED
        assert r_con.verdict == G3AnswerVerdict.CONTRADICTED
        # Cross-defect combination: disjoint slot + disjoint year + different values
        r_cross = self.verifier.verify(
            "Sensor B was 0°C in 2024.",
            [EvidenceDocument(doc_id="d1", text="Sensor A was 5°C in 2020.")],
        )
        assert r_cross.verdict == G3AnswerVerdict.INSUFFICIENT_EVIDENCE

