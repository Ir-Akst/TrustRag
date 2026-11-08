"""Unit tests for text preprocessing, Unicode normalization, and deduplication."""

from trustrag.data.preprocessing import (
    DeduplicationReport,
    DuplicateDetector,
    clean_text,
    is_empty_text,
    normalize_text,
    normalize_whitespace_single_line,
)


def test_unicode_normalization_nfkc():
    # Full-width characters and ligatures
    raw = "Ｔｅｓｔ ﬃ ﬀ"
    cleaned = clean_text(raw)
    assert cleaned == "Test ffi ff"


def test_whitespace_normalization_and_punctuation_preservation():
    raw = "   This   is   a   test...\n\n\n\nWith multiple   spaces! Do not delete: 'negation' or punctuation?!   "
    cleaned = clean_text(raw)
    # Punctuation and negation must be strictly preserved
    assert "..." in cleaned
    assert "Do not delete: 'negation' or punctuation?!" in cleaned
    # Multiple empty lines should collapse safely
    assert "\n\n" in cleaned
    assert "\n\n\n" not in cleaned
    assert not cleaned.startswith(" ")
    assert not cleaned.endswith(" ")


def test_normalize_whitespace_single_line():
    raw = "Line 1\n\nLine 2\t\tLine 3"
    assert normalize_whitespace_single_line(raw) == "Line 1 Line 2 Line 3"


def test_empty_text_detection():
    assert is_empty_text("") is True
    assert is_empty_text("   \n\t  ") is True
    assert is_empty_text(None) is True
    assert is_empty_text("valid content") is False


def test_recursive_normalize_text():
    data = {
        "title": "  Ｔｅｓｔ Title  ",
        "nested": {
            "query": "What is   this?  ",
            "items": [" item １ ", " item ２ "],
        },
        "count": 42,
    }
    normalized = normalize_text(data)
    assert normalized["title"] == "Test Title"
    assert normalized["nested"]["query"] == "What is this?"
    assert normalized["nested"]["items"] == ["item 1", "item 2"]
    assert normalized["count"] == 42


def test_duplicate_detector():
    detector = DuplicateDetector()

    # First record
    is_unique_1 = detector.check_and_add(record_id="rec_1", content_hash="hash_abc")
    assert is_unique_1 is True

    # Second record with different hash
    is_unique_2 = detector.check_and_add(record_id="rec_2", content_hash="hash_xyz")
    assert is_unique_2 is True

    # Duplicate of first record
    is_unique_3 = detector.check_and_add(record_id="rec_3", content_hash="hash_abc")
    assert is_unique_3 is False

    report = detector.get_report()
    assert report.total_records == 3
    assert report.unique_records == 2
    assert report.duplicate_records == 1
    assert "hash_abc" in report.duplicates_by_hash
    assert report.duplicates_by_hash["hash_abc"] == ["rec_1", "rec_3"]
    assert report.duplicate_ratio == 1 / 3

    # Reset
    detector.reset()
    assert detector.get_report().total_records == 0

