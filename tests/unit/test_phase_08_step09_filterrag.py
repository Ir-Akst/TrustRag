"""Phase 08 Step 09 tests: isolated FilterRAG & ML-FilterRAG experimental harness."""

from __future__ import annotations

import pytest

from trustrag.config import load_config
from trustrag.engine.schemas import EvidenceDocument
from trustrag.evaluation.filterrag_experiment import (
    FilterRAGFeatures,
    MLFilterRAGModel,
    compare_filterrag_defenses,
    compute_freq_density,
    extract_filterrag_features,
)


def test_production_base_config_keeps_freq_density_disabled() -> None:
    cfg = load_config()
    assert cfg.msd.enable_freq_density is False


def test_offline_default_marks_slm_filterrag_blocked() -> None:
    report = compare_filterrag_defenses()
    assert report.slm_available is False
    assert report.evaluation_mode == "BLOCKED_NO_LIVE_SLM"
    by_name = {v.variant_name: v for v in report.variants}
    assert by_name["Original_RAG"].status == "COMPLETED"
    assert by_name["TrustRAG_MSD"].status == "COMPLETED"
    assert by_name["FilterRAG_Threshold_SLM"].status == "BLOCKED"
    assert by_name["ML_FilterRAG_SLM"].status == "BLOCKED"
    assert by_name["Combined_MSD_FilterRAG"].status == "BLOCKED"


def test_injectable_slm_callable_and_ml_filterrag_split_guard() -> None:
    def mock_slm(query: str, doc: EvidenceDocument) -> str:
        # Concentrate query/answer words cleanly when doc looks factual; simulate divergence otherwise
        if "ignore previous instructions" in doc.text.lower():
            return "unrelated fallback response about weather"
        return f"{query} {' '.join(doc.text.split()[:6])}"

    report = compare_filterrag_defenses(slm_answer_callable=mock_slm)
    assert report.slm_available is True
    assert report.evaluation_mode == "live_slm"
    by_name = {v.variant_name: v for v in report.variants}
    assert by_name["FilterRAG_Threshold"].status == "COMPLETED"
    assert by_name["ML_FilterRAG"].status == "COMPLETED"
    assert by_name["Combined_MSD_FilterRAG"].status == "COMPLETED"

    # Guard: calling extract without callable or explicit proxy flag fails
    with pytest.raises(RuntimeError):
        extract_filterrag_features([])

    # Guard: ML-FilterRAG refuses fitting on test split
    dummy = [
        FilterRAGFeatures(
            doc_id="c1",
            is_attack=0,
            freq_density=0.5,
            query_match=0.6,
            retrieval_score=0.7,
            token_count_norm=0.4,
            intermediate_answer_mode="live_slm",
        ),
        FilterRAGFeatures(
            doc_id="p1",
            is_attack=1,
            freq_density=0.1,
            query_match=0.2,
            retrieval_score=0.3,
            token_count_norm=0.8,
            intermediate_answer_mode="live_slm",
        ),
    ]
    with pytest.raises(ValueError, match="test split"):
        MLFilterRAGModel().fit(dummy, split_name="test")


def test_extractive_proxy_comparison_surfaces_clean_retention_tradeoff() -> None:
    report = compare_filterrag_defenses(allow_extractive_proxy=True)
    assert report.slm_available is False
    assert report.evaluation_mode == "extractive_proxy"
    by_name = {v.variant_name: v for v in report.variants}
    assert by_name["TrustRAG_MSD"].clean_rag_retention_rate == 1.0
    assert by_name["FilterRAG_Threshold"].status == "PROXY_ONLY"
    # Verify proxy helper directly on sample passage
    fd = compute_freq_density(
        "boiling point water",
        EvidenceDocument(doc_id="d1", text="Water boils at 100 degrees Celsius."),
        intermediate_answer="Water boils at 100 Celsius.",
    )
    assert 0.0 <= fd <= 1.0
