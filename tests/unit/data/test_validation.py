"""Unit tests for record quality and schema validation."""

from trustrag.data.schemas import (
    ClaimVerificationRecord,
    DocumentRecord,
    QueryRecord,
    SecurityRecord,
)
from trustrag.data.validation import RecordValidator


def test_validator_valid_records():
    validator = RecordValidator(dataset_name="test_valid")

    doc = DocumentRecord(document_id="d1", text="Valid text content", source_dataset="test")
    query = QueryRecord(query_id="q1", query="Valid question?", source_dataset="test")
    claim = ClaimVerificationRecord(record_id="c1", document="Doc", claim="Claim", label="SUPPORTED", source_dataset="test")
    sec = SecurityRecord(record_id="s1", passage="Passage text", clean_poison_label="CLEAN", source_dataset="test")

    assert validator.validate(doc) is True
    assert validator.validate(query) is True
    assert validator.validate(claim) is True
    assert validator.validate(sec) is True

    rep = validator.get_report()
    assert rep.total_checked == 4
    assert rep.valid_count == 4
    assert rep.invalid_count == 0
    assert rep.is_valid is True


def test_validator_empty_text():
    validator = RecordValidator(dataset_name="test_empty")
    # Empty query record (using object construction directly)
    empty_q = QueryRecord(query_id="q_empty", query=" ", source_dataset="test")

    is_valid = validator.validate(empty_q)
    assert is_valid is False

    rep = validator.get_report()
    assert rep.empty_count == 1
    assert rep.is_valid is False


def test_validator_unknown_labels():
    validator = RecordValidator(dataset_name="test_labels")

    bad_claim = ClaimVerificationRecord(
        record_id="c_bad",
        document="Context",
        claim="Claim",
        label="INVALID_CLAIM_LABEL",
        source_dataset="test",
    )
    assert validator.validate(bad_claim) is False

    bad_sec = SecurityRecord(
        record_id="s_bad",
        passage="Some text",
        clean_poison_label="CORRUPTED_LABEL",
        source_dataset="test",
    )
    assert validator.validate(bad_sec) is False

    rep = validator.get_report()
    assert rep.label_error_count == 2
    assert rep.is_valid is False

