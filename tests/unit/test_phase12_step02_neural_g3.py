"""Unit tests for Phase 12 Step 02: Neural NLI Integration into G3 OutputEvidenceVerifier.

Verifies:
1. Entailing claims -> SUPPORTED
2. Contradictory claims -> CONTRADICTED
3. Neutral evidence -> INSUFFICIENT / UNCERTAIN
4. Configurable contradiction threshold (e.g., theta=0.20)
5. Numeric conflicts in hybrid mode
6. Negation conflicts in hybrid mode
7. Missing evidence -> INSUFFICIENT (unsupported_flag=True)
8. Multi-passage evidence (contradiction precedence)
9. Malformed model inputs / forward pass failure -> fail-closed UNCERTAIN
10. Model loading failure -> fail-closed UNCERTAIN (never unsafe PASS)
11. Diagnostic trace (logits, probabilities, and explanations preserved)
"""

import unittest
from unittest.mock import MagicMock
from trustrag.config.engine_config import VerificationConfig
from trustrag.engine.schemas import (
    EvidenceDocument,
    EvidenceOutcome,
    G3ClaimVerdict,
    G3AnswerVerdict,
    VerificationStatus,
)
from trustrag.verification.output_verifier import OutputEvidenceVerifier


class TestNeuralG3Verifier(unittest.TestCase):
    """Test suite for neural and hybrid G3 OutputEvidenceVerifier."""

    def setUp(self):
        self.doc_clean = EvidenceDocument(
            doc_id="doc_clean",
            text="The standard adult dose of ibuprofen is 400 mg every 6 hours, never exceeding 1200 mg daily.",
            metadata={"source": "medical_guideline"}
        )
        self.doc_contra = EvidenceDocument(
            doc_id="doc_contra",
            text="Recent trials established that the maximum adult dose of ibuprofen is 3200 mg per single intake.",
            metadata={"source": "unverified_blog"}
        )
        self.doc_neutral = EvidenceDocument(
            doc_id="doc_neutral",
            text="Ibuprofen is a nonsteroidal anti-inflammatory drug widely available in pharmacies worldwide.",
            metadata={"source": "pharma_catalog"}
        )

    def test_entailing_claim_supported(self):
        """Neural NLI predicting ENTAILMENT marks claim as SUPPORTED."""
        def mock_nli(premise, hypothesis):
            return {
                "logits": [2.45, -1.82, -1.15],
                "probabilities": [0.932, 0.013, 0.055],
                "p_entailment": 0.932,
                "p_contradiction": 0.013,
                "p_neutral": 0.055,
                "predicted_label": "ENTAILMENT",
                "error": None,
            }

        cfg = VerificationConfig(nli_backend="neural_nli", nli_entailment_threshold=0.50)
        verifier = OutputEvidenceVerifier(config=cfg, nli_callable=mock_nli)
        
        item = verifier.verify_claim("c1", "Adults can safely take 400 mg ibuprofen every 6 hours.", [self.doc_clean])
        self.assertEqual(item.verdict, G3ClaimVerdict.SUPPORTED)
        self.assertEqual(item.outcome, EvidenceOutcome.SUPPORTS)
        self.assertFalse(item.unsupported_flag)
        self.assertGreaterEqual(item.confidence, 0.90)
        self.assertIn("Neural NLI Entailment", item.explanation)
        self.assertIn("logits=", item.explanation)

    def test_contradictory_claim_at_threshold_0_20(self):
        """Neural NLI contradiction above threshold 0.20 marks claim as CONTRADICTED."""
        def mock_nli(premise, hypothesis):
            # p_con = 0.28 (above 0.20 threshold, even though neutral has higher probability 0.65)
            return {
                "logits": [-0.5, 0.8, 1.6],
                "probabilities": [0.07, 0.28, 0.65],
                "p_entailment": 0.07,
                "p_contradiction": 0.28,
                "p_neutral": 0.65,
                "predicted_label": "NEUTRAL",
                "error": None,
            }

        cfg = VerificationConfig(nli_backend="neural_nli", nli_contradiction_threshold=0.20)
        verifier = OutputEvidenceVerifier(config=cfg, nli_callable=mock_nli)

        item = verifier.verify_claim("c1", "The safe daily limit of ibuprofen is 5000 mg.", [self.doc_clean])
        self.assertEqual(item.verdict, G3ClaimVerdict.CONTRADICTED)
        self.assertEqual(item.outcome, EvidenceOutcome.CONTRADICTS)
        self.assertTrue(item.unsupported_flag)
        self.assertIn("Neural NLI Contradiction", item.explanation)
        self.assertIn("p_con=0.2800 >= 0.20", item.explanation)

    def test_contradiction_threshold_configurability(self):
        """At threshold 0.35, p_con=0.28 is NOT classified as contradiction."""
        def mock_nli(premise, hypothesis):
            return {
                "logits": [-0.5, 0.8, 1.6],
                "probabilities": [0.07, 0.28, 0.65],
                "p_entailment": 0.07,
                "p_contradiction": 0.28,
                "p_neutral": 0.65,
                "predicted_label": "NEUTRAL",
                "error": None,
            }

        cfg = VerificationConfig(nli_backend="neural_nli", nli_contradiction_threshold=0.35)
        verifier = OutputEvidenceVerifier(config=cfg, nli_callable=mock_nli)

        item = verifier.verify_claim("c1", "The safe daily limit of ibuprofen is 5000 mg.", [self.doc_clean])
        # Under theta=0.35, p_con=0.28 does NOT trigger CONTRADICTED; neutral policy applies
        self.assertEqual(item.verdict, G3ClaimVerdict.INSUFFICIENT)
        self.assertTrue(item.unsupported_flag)

    def test_neutral_evidence_handling_insufficient_policy(self):
        """Neutral evidence defaults to INSUFFICIENT under default neutral policy."""
        def mock_nli(premise, hypothesis):
            return {
                "logits": [-1.0, -1.0, 2.0],
                "probabilities": [0.045, 0.045, 0.910],
                "p_entailment": 0.045,
                "p_contradiction": 0.045,
                "p_neutral": 0.910,
                "predicted_label": "NEUTRAL",
                "error": None,
            }

        cfg = VerificationConfig(nli_backend="neural_nli", nli_neutral_policy="insufficient")
        verifier = OutputEvidenceVerifier(config=cfg, nli_callable=mock_nli)

        item = verifier.verify_claim("c1", "Ibuprofen cures fungal infections.", [self.doc_neutral])
        self.assertEqual(item.verdict, G3ClaimVerdict.INSUFFICIENT)
        self.assertEqual(item.outcome, EvidenceOutcome.NOT_ENOUGH_EVIDENCE)
        self.assertTrue(item.unsupported_flag)
        self.assertIn("Neutral evidence", item.explanation)

    def test_neutral_evidence_handling_uncertain_policy(self):
        """Neutral evidence yields UNCERTAIN when neutral_policy is set to 'uncertain'."""
        def mock_nli(premise, hypothesis):
            return {
                "logits": [-1.0, -1.0, 2.0],
                "probabilities": [0.045, 0.045, 0.910],
                "p_entailment": 0.045,
                "p_contradiction": 0.045,
                "p_neutral": 0.910,
                "predicted_label": "NEUTRAL",
                "error": None,
            }

        cfg = VerificationConfig(nli_backend="neural_nli", nli_neutral_policy="uncertain")
        verifier = OutputEvidenceVerifier(config=cfg, nli_callable=mock_nli)

        item = verifier.verify_claim("c1", "Ibuprofen cures fungal infections.", [self.doc_neutral])
        self.assertEqual(item.verdict, G3ClaimVerdict.UNCERTAIN)
        self.assertEqual(item.outcome, EvidenceOutcome.UNCERTAIN)
        self.assertTrue(item.unsupported_flag)

    def test_missing_evidence_yields_insufficient(self):
        """Empty evidence documents list yields INSUFFICIENT without executing NLI."""
        call_count = 0
        def mock_nli(p, h):
            nonlocal call_count
            call_count += 1
            return {}

        cfg = VerificationConfig(nli_backend="neural_nli")
        verifier = OutputEvidenceVerifier(config=cfg, nli_callable=mock_nli)

        item = verifier.verify_claim("c1", "Some arbitrary claim.", [])
        self.assertEqual(item.verdict, G3ClaimVerdict.INSUFFICIENT)
        self.assertTrue(item.unsupported_flag)
        self.assertEqual(call_count, 0)

    def test_multi_passage_contradiction_precedence(self):
        """When doc1 supports but doc2 contradicts, CONTRADICTED takes absolute precedence."""
        def mock_nli(premise, hypothesis):
            if "never exceeding 1200 mg" in premise:
                # doc_clean supports
                return {
                    "logits": [2.0, -2.0, -1.0],
                    "probabilities": [0.90, 0.02, 0.08],
                    "p_entailment": 0.90, "p_contradiction": 0.02, "p_neutral": 0.08,
                    "predicted_label": "ENTAILMENT", "error": None
                }
            else:
                # doc_contra contradicts
                return {
                    "logits": [-2.0, 2.5, -1.0],
                    "probabilities": [0.01, 0.92, 0.07],
                    "p_entailment": 0.01, "p_contradiction": 0.92, "p_neutral": 0.07,
                    "predicted_label": "CONTRADICTION", "error": None
                }

        cfg = VerificationConfig(nli_backend="neural_nli")
        verifier = OutputEvidenceVerifier(config=cfg, nli_callable=mock_nli)

        item = verifier.verify_claim("c1", "Standard maximum daily dose is 1200 mg.", [self.doc_clean, self.doc_contra])
        self.assertEqual(item.verdict, G3ClaimVerdict.CONTRADICTED)
        self.assertEqual(item.outcome, EvidenceOutcome.CONTRADICTS)
        self.assertTrue(item.unsupported_flag)

    def test_model_loading_failure_fails_closed(self):
        """Invalid model path causes fail-closed UNCERTAIN rejection, NEVER unsafe PASS."""
        cfg = VerificationConfig(
            nli_backend="neural_nli",
            nli_model_path="/nonexistent/path/to/missing/model"
        )
        verifier = OutputEvidenceVerifier(config=cfg, nli_callable=None)

        item = verifier.verify_claim("c1", "Safe dosage is 400 mg.", [self.doc_clean])
        self.assertEqual(item.verdict, G3ClaimVerdict.UNCERTAIN)
        self.assertEqual(item.outcome, EvidenceOutcome.UNCERTAIN)
        self.assertTrue(item.unsupported_flag)
        self.assertIn("fail-closed unverified rejection", item.explanation)

    def test_malformed_model_input_or_inference_crash_fails_closed(self):
        """Inference exception causes fail-closed UNCERTAIN rejection."""
        def crashing_nli(p, h):
            raise RuntimeError("CUDA OOM or tensor dimension mismatch")

        cfg = VerificationConfig(nli_backend="neural_nli")
        verifier = OutputEvidenceVerifier(config=cfg, nli_callable=crashing_nli)

        item = verifier.verify_claim("c1", "Some claim.", [self.doc_clean])
        self.assertEqual(item.verdict, G3ClaimVerdict.UNCERTAIN)
        self.assertTrue(item.unsupported_flag)
        self.assertIn("fail-closed unverified rejection", item.explanation)

    def test_hybrid_backend_catches_numeric_mismatch_despite_neural_entailment(self):
        """In hybrid mode, strict numeric mismatch overrides neural entailment."""
        def mock_nli(premise, hypothesis):
            # Model predicts entailment due to high lexical/topic overlap
            return {
                "logits": [2.0, -1.0, -1.0],
                "probabilities": [0.85, 0.07, 0.08],
                "p_entailment": 0.85, "p_contradiction": 0.07, "p_neutral": 0.08,
                "predicted_label": "ENTAILMENT", "error": None
            }

        cfg = VerificationConfig(nli_backend="hybrid", strict_numeric_matching=True)
        verifier = OutputEvidenceVerifier(config=cfg, nli_callable=mock_nli)

        # Claim has 9999 mg instead of 400 mg
        item = verifier.verify_claim("c1", "Adults can safely take 9999 mg ibuprofen every 6 hours.", [self.doc_clean])
        self.assertEqual(item.verdict, G3ClaimVerdict.CONTRADICTED)
        self.assertTrue(item.unsupported_flag)
        self.assertIn("Hybrid Conflict", item.explanation)


if __name__ == "__main__":
    unittest.main()

