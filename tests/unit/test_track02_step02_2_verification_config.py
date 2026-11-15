"""Tests for G3 VerificationConfig validation and strict threshold sensitivity (Track 1, Step 2.2)."""

import pytest
from trustrag.config.engine_config import VerificationConfig
from trustrag.engine.schemas import EvidenceDocument
from trustrag.exceptions import ConfigurationError
from trustrag.verification.output_verifier import OutputEvidenceVerifier


def test_verification_config_rejects_unsupported_keys() -> None:
    """Ensure unsupported keys (such as legacy evidence_threshold) raise ConfigurationError."""
    with pytest.raises(ConfigurationError) as exc_info:
        VerificationConfig(evidence_threshold=0.70)
    assert "extra_forbidden" in str(exc_info.value) or "extra inputs are not permitted" in str(exc_info.value).lower()

    with pytest.raises(ConfigurationError) as exc_info2:
        VerificationConfig(claim_threshold=0.75)
    assert "extra_forbidden" in str(exc_info2.value) or "extra inputs are not permitted" in str(exc_info2.value).lower()


def test_default_vs_strict_config_effective_values() -> None:
    """Confirm default and strict configurations have genuinely distinct min_support_coverage."""
    default_cfg = VerificationConfig()
    strict_cfg = VerificationConfig(min_support_coverage=0.80)

    assert default_cfg.min_support_coverage == 0.65
    assert strict_cfg.min_support_coverage == 0.80
    assert default_cfg.min_support_coverage != strict_cfg.min_support_coverage


def test_decision_function_reads_configured_coverage() -> None:
    """Verify OutputEvidenceVerifier initializes with and reads the configured min_support_coverage."""
    strict_cfg = VerificationConfig(min_support_coverage=0.85)
    verifier = OutputEvidenceVerifier(strict_cfg)
    assert verifier.config.min_support_coverage == 0.85


def test_deterministic_input_verdict_changes_with_threshold() -> None:
    """Demonstrate a deterministic input whose verdict changes from SUPPORTED to INSUFFICIENT_EVIDENCE
    when min_support_coverage increases from 0.65 to 0.80."""
    default_verifier = OutputEvidenceVerifier(
        VerificationConfig(enable_query_consistency=False, min_support_coverage=0.65)
    )
    strict_verifier = OutputEvidenceVerifier(
        VerificationConfig(enable_query_consistency=False, min_support_coverage=0.80)
    )

    # Document contains partial overlap with claim:
    # 7 out of 10 key terms matched -> coverage = 0.70
    doc_text = (
        "The quick brown fox jumps over the lazy dog in the sunny meadow. "
        "The animal was seen running near the wooden fence."
    )
    doc = EvidenceDocument(
        doc_id="test_doc_01",
        text=doc_text,
        source_dataset="unit_test",
        source_id="1",
        provenance="unit_test",
    )

    # Claim shares approximately 70-75% tokens with the evidence sentence
    claim = "The quick brown fox jumps over the lazy dog near the wooden fence."

    rep_default = default_verifier.verify(claim, [doc])
    rep_strict = strict_verifier.verify(claim, [doc])

    # With coverage ~0.70-0.75:
    # At threshold 0.65, this should be SUPPORTED / PARTIALLY_SUPPORTED
    # At threshold 0.80, this must be rejected (INSUFFICIENT_EVIDENCE / NOT_ENOUGH_EVIDENCE)
    assert rep_default.verdict.value in ("SUPPORTED", "PARTIALLY_SUPPORTED")
    assert rep_strict.verdict.value in ("INSUFFICIENT_EVIDENCE", "UNCERTAIN")
    assert rep_default.verdict.value != rep_strict.verdict.value


def test_default_config_behavior_unchanged() -> None:
    """Confirm production default configuration retains exact baseline behavior."""
    def_cfg = VerificationConfig()
    assert def_cfg.enabled is True
    assert def_cfg.min_support_coverage == 0.65
    assert def_cfg.min_relevance_for_check == 0.10
    assert def_cfg.strict_numeric_matching is True
    assert def_cfg.strict_negation_check is True
    assert def_cfg.enable_query_consistency is True
    assert def_cfg.min_query_consistency_score == 0.12
