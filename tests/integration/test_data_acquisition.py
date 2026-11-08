"""Integration tests for remote dataset acquisition from official repositories.

These tests require deliberate invocation and network connectivity:
    pytest -m integration
"""

import pytest

from trustrag.data.registry import load_dataset


@pytest.mark.integration
def test_boolq_sample_acquisition():
    """Verify live acquisition of a small smoke sample from Google BoolQ on Hugging Face."""
    records = list(load_dataset("boolq", split="validation", limit=5))
    assert len(records) == 5
    assert records[0].source_dataset == "boolq"
    assert records[0].query
    assert records[0].content_hash


@pytest.mark.integration
def test_squad_sample_acquisition():
    """Verify live acquisition of a small smoke sample from SQuAD on Hugging Face."""
    records = list(load_dataset("squad", split="validation", limit=5))
    assert len(records) == 5
    assert records[0].source_dataset == "squad"
    assert records[0].query
    assert records[0].content_hash
