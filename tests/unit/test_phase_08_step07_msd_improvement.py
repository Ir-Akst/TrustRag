"""Phase 08 Step 07 tests: MSD security recall, F2/F5/F6 differentiation, and zero-FP calibration."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from trustrag.adaptive.calibration import TrustCalibrator, collect_g2_partition_scores
from trustrag.config.engine_config import MSDConfig, RetrievalConfig
from trustrag.detection.msd import MultiSignalDetector
from trustrag.detection.signals import evaluate_embedding_norm_signal, evaluate_provenance_signal
from trustrag.engine.schemas import EvidenceDocument
from trustrag.retrieval.retriever import TrustAwareRetriever


def test_temperature_calibrator_preserves_zero_clean_fpr() -> None:
    temp_path = Path("configs/adaptive/temperature_calibrator_v1.json")
    assert temp_path.is_file()
    temp_cal = TrustCalibrator.load_json(temp_path)
    assert temp_cal.is_active
    assert temp_cal.artifact is not None
    assert "train" in temp_cal.artifact.fitted_splits
    assert all("test" not in s.lower() for s in temp_cal.artifact.fitted_splits)

    bdir = Path("data/benchmarks_backup")
    msd_cfg = MSDConfig()
    # Held-out clean_rag test should record 0 false-positive flags under temperature calibration
    _, _, pred_clean = collect_g2_partition_scores(
        "clean_rag",
        "test",
        dataset_dir=bdir / "clean_rag",
        msd_config=msd_cfg,
        calibrator=temp_cal,
        max_clean_queries=30,
    )
    assert pred_clean and sum(pred_clean) == 0

    # Security clean controls on val/test also keep 0 FP under temp-train-v1
    y_clean, _, pred_atk = collect_g2_partition_scores(
        "adversarial_robustness",
        "test",
        dataset_dir=bdir / "adversarial_robustness",
        msd_config=msd_cfg,
        calibrator=temp_cal,
    )
    clean_fps = [p for y, p in zip(y_clean, pred_atk, strict=True) if y == 1 and p == 1]
    assert len(clean_fps) == 0


def test_provenance_signal_differentiates_metadata_without_fabricating_unknown() -> None:
    cfg = MSDConfig(provenance_priors={"nih.gov": 0.92, "spam.example": 0.12})

    gov_doc = EvidenceDocument(
        doc_id="d_gov",
        text="Evidence from clinical guidelines.",
        metadata={"domain": "pubmed.nih.gov"},
    )
    sig_gov = evaluate_provenance_signal(gov_doc, cfg)
    assert sig_gov.available and sig_gov.value == 0.92

    official_doc = EvidenceDocument(
        doc_id="d_off",
        text="Official guideline text.",
        metadata={"source_type": "official_docs"},
    )
    sig_off = evaluate_provenance_signal(official_doc, cfg)
    assert sig_off.available and sig_off.value == 0.85

    tier_med = EvidenceDocument(
        doc_id="d_med",
        text="Curated article text.",
        metadata={"trust_tier": "tier_2"},
    )
    sig_med = evaluate_provenance_signal(tier_med, cfg)
    assert sig_med.available and sig_med.value == 0.65

    forum_doc = EvidenceDocument(
        doc_id="d_forum",
        text="Unvetted post text.",
        metadata={"source_type": "forum"},
    )
    sig_forum = evaluate_provenance_signal(forum_doc, cfg)
    assert sig_forum.available and sig_forum.value == 0.30
    assert "LOW_TRUST_SOURCE_TYPE" in sig_forum.flags

    unknown_doc = EvidenceDocument(doc_id="d_unk", text="No provenance attached.")
    sig_unk = evaluate_provenance_signal(unknown_doc, cfg)
    assert not sig_unk.available and sig_unk.value is None and sig_unk.status == "UNKNOWN"


def test_embedding_norm_with_dense_callable_and_tfidf_sublinear() -> None:
    # 1. Dense embedding callable triggers F2 anomaly detection
    def fake_dense(texts: Sequence[str]) -> Sequence[np.ndarray]:
        out: list[np.ndarray] = []
        for idx, _ in enumerate(texts):
            # Last doc has extreme anomalous norm
            scale = 12.0 if idx == len(texts) - 1 else 1.0
            out.append(np.array([scale, 0.5 * scale, 0.2 * scale], dtype=float))
        return out

    cfg_dense = MSDConfig(
        embedding_backend="callable",
        embedding_norm_reference_policy="allow_empirical_fallback",
        embedding_norm_z_threshold=1.5,
    )
    det_dense = MultiSignalDetector(cfg_dense, embedding_callable=fake_dense)
    docs = [
        EvidenceDocument(doc_id=f"c{i}", text=f"Normal document fact number {i} about cryptography.")
        for i in range(4)
    ] + [
        EvidenceDocument(doc_id="anom", text="Anomalous document about cryptography.")
    ]
    res = det_dense.assess_candidates("cryptography facts", docs, [0.8] * len(docs))
    f2_clean = res[0].signals["embedding_norm"]
    f2_anom = res[-1].signals["embedding_norm"]
    assert f2_clean.available and f2_anom.available
    assert f2_anom.value is not None and f2_clean.value is not None
    assert f2_anom.value < f2_clean.value

    # 2. Sublinear local representation scales vectors sublinearly across lengths
    cfg_sub = MSDConfig(
        embedding_backend="tfidf_sublinear",
        embedding_norm_reference_policy="allow_empirical_fallback",
    )
    det_sub = MultiSignalDetector(cfg_sub)
    vecs = det_sub._resolve_doc_embeddings(docs, None)
    assert all(v is not None and np.linalg.norm(v) > 0 for v in vecs)
    sig_sub = evaluate_embedding_norm_signal(vecs[0], [float(np.linalg.norm(v)) for v in vecs if v is not None], cfg_sub)
    assert sig_sub.available and sig_sub.value is not None


def test_minority_outlier_attenuation_requires_majority_quorum() -> None:
    det = MultiSignalDetector(MSDConfig())
    # 3 agreeing clean docs vs 1 contradictory factual poison
    c1 = EvidenceDocument(doc_id="c1", text="Standard adult paracetamol maximum safe daily dose is 4000 mg.")
    c2 = EvidenceDocument(doc_id="c2", text="The standard adult maximum safe dose for paracetamol is 4000 mg daily.")
    c3 = EvidenceDocument(doc_id="c3", text="Safe adult paracetamol ceiling equals 4000 mg in a 24 hour period.")
    p1 = EvidenceDocument(doc_id="p1", text="Standard adult paracetamol safe daily dose is 12000 mg for headache.")

    asym = det.assess_candidates("What is safe paracetamol daily dose?", [c1, c2, c3, p1], [0.8, 0.8, 0.8, 0.8])
    by_id = {a.document_id: a for a in asym}
    assert "G2_MINORITY_OUTLIER_ATTENUATED" in by_id["p1"].reason_codes
    assert by_id["p1"].trust_score < 0.60
    assert by_id["c1"].trust_score >= 0.85

    # Symmetric 50/50 tie must NOT apply minority-outlier attenuation to either side
    sym = det.assess_candidates("What is safe paracetamol daily dose?", [c1, p1], [0.8, 0.8])
    for assessment in sym:
        assert "G2_MINORITY_OUTLIER_ATTENUATED" not in assessment.reason_codes


def test_capped_removal_invariant_remains_enforced() -> None:
    ret_cfg = RetrievalConfig()
    assert ret_cfg.enforce_removal_cap is True
    assert ret_cfg.removal_cap_ratio <= 0.5
    assert ret_cfg.filtering_mode == "remove_with_cap"
    assert TrustAwareRetriever is not None
