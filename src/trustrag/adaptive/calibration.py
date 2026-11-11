"""Controlled, deterministic G2 trust-score calibration for Phase 05."""

from __future__ import annotations

import logging
import math
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import expit, logit
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from trustrag.adaptive.schemas import (
    CalibrationArtifact,
    CalibrationEvaluationReport,
    CalibrationMethod,
    ReliabilityBin,
)
from trustrag.config import MSDConfig, load_config
from trustrag.detection import MultiSignalDetector
from trustrag.engine.schemas import EvidenceDocument
from trustrag.engine.text_utils import compute_lexical_overlap
from trustrag.evaluation.loader import load_evaluation_partition
from trustrag.evaluation.metrics import compute_binary_classification_metrics

LOGGER = logging.getLogger(__name__)


def _assert_non_test_splits(splits: Sequence[str]) -> None:
    """Enforce zero test-set leakage during calibration fitting."""
    for split_name in splits:
        if "test" in split_name.strip().lower():
            raise ValueError(
                f"Split hygiene violation: calibration must never fit on test split '{split_name}'."
            )


def compute_reliability_diagram(
    y_true_clean: Sequence[int],
    probs_clean: Sequence[float],
    n_bins: int = 5,
) -> list[ReliabilityBin]:
    """Compute fixed-width reliability bins comparing predicted P(clean) to empirical clean frequency."""
    if len(y_true_clean) != len(probs_clean):
        raise ValueError("y_true_clean and probs_clean must have equal length.")
    bins: list[ReliabilityBin] = []
    for b in range(n_bins):
        lo = b / n_bins
        hi = (b + 1) / n_bins
        idxs = [
            i
            for i, p in enumerate(probs_clean)
            if (lo <= p < hi) or (b == n_bins - 1 and p == 1.0)
        ]
        if not idxs:
            bins.append(
                ReliabilityBin(
                    bin_index=b,
                    lower_bound=round(lo, 4),
                    upper_bound=round(hi, 4),
                    count=0,
                )
            )
            continue
        avg_conf = sum(probs_clean[i] for i in idxs) / len(idxs)
        avg_acc = sum(y_true_clean[i] for i in idxs) / len(idxs)
        bins.append(
            ReliabilityBin(
                bin_index=b,
                lower_bound=round(lo, 4),
                upper_bound=round(hi, 4),
                count=len(idxs),
                mean_confidence=round(float(avg_conf), 4),
                empirical_clean_rate=round(float(avg_acc), 4),
                calibration_gap=round(float(abs(avg_conf - avg_acc)), 4),
            )
        )
    return bins


def compute_calibration_metrics(
    y_true_clean: Sequence[int],
    probs_clean: Sequence[float],
    n_bins: int = 5,
) -> dict[str, float]:
    """Compute Brier score and Expected Calibration Error (ECE) for trust_score vs is_clean."""
    if not y_true_clean:
        return {"brier_score": 0.0, "ece": 0.0}
    if len(y_true_clean) != len(probs_clean):
        raise ValueError("y_true_clean and probs_clean must have equal length.")
    brier = sum((p - y) ** 2 for y, p in zip(y_true_clean, probs_clean, strict=False)) / len(y_true_clean)
    n = len(y_true_clean)
    bins = compute_reliability_diagram(y_true_clean, probs_clean, n_bins=n_bins)
    ece = 0.0
    for rbin in bins:
        if rbin.count > 0 and rbin.calibration_gap is not None:
            ece += (rbin.count / n) * rbin.calibration_gap
    return {"brier_score": round(float(brier), 4), "ece": round(float(ece), 4)}


class TrustCalibrator:
    """Deterministic post-hoc calibrator mapping raw G2 trust_score -> calibrated P(clean)."""

    def __init__(self, artifact: CalibrationArtifact | None = None) -> None:
        self.artifact = artifact
        self._corrupted = False
        if artifact is not None and not artifact.verify_integrity():
            self._corrupted = True
            LOGGER.warning(
                "CalibrationArtifact checksum mismatch detected; reverting safely to raw scores",
                extra={"version": artifact.version},
            )

    @property
    def is_active(self) -> bool:
        """Whether a valid, non-NONE calibration artifact is active."""
        return (
            not self._corrupted
            and self.artifact is not None
            and self.artifact.method != CalibrationMethod.NONE
        )

    @classmethod
    def fit(
        cls,
        raw_trust_scores: Sequence[float],
        y_true_clean: Sequence[int],
        *,
        method: CalibrationMethod | str = CalibrationMethod.PLATT,
        fitted_datasets: Sequence[str] = (),
        fitted_splits: Sequence[str] = ("train",),
        version: str = "cal-v1.0.0",
        class_weight: str | None = None,
        use_logit_transform: bool = True,
        fit_seed: int = 42,
        clip_eps: float = 1e-4,
    ) -> TrustCalibrator:
        """Fit a deterministic calibration artifact strictly on non-test splits."""
        _assert_non_test_splits(fitted_splits)
        resolved_method = CalibrationMethod(method)
        if len(raw_trust_scores) != len(y_true_clean):
            raise ValueError("raw_trust_scores and y_true_clean must have equal length.")
        if len(raw_trust_scores) < 10:
            raise ValueError("At least 10 labeled samples are required for calibration fitting.")

        x_raw = np.asarray(raw_trust_scores, dtype=float)
        y = np.asarray(y_true_clean, dtype=int)
        if not np.all(np.isfinite(x_raw)):
            raise ValueError("raw_trust_scores contains non-finite values.")
        if set(y.tolist()) != {0, 1}:
            raise ValueError("Calibration requires both clean (1) and poisoned (0) labels.")

        x_clipped = np.clip(x_raw, clip_eps, 1.0 - clip_eps)
        clean_cnt = int(np.sum(y == 1))
        atk_cnt = int(np.sum(y == 0))

        kwargs: dict[str, Any] = {
            "version": version,
            "method": resolved_method,
            "fitted_datasets": list(fitted_datasets),
            "fitted_splits": list(fitted_splits),
            "fit_seed": fit_seed,
            "sample_count": len(y),
            "clean_count": clean_cnt,
            "attack_count": atk_cnt,
            "class_weight": class_weight,
            "use_logit_transform": use_logit_transform,
            "clip_eps": clip_eps,
        }

        if resolved_method == CalibrationMethod.PLATT:
            features = (
                logit(x_clipped).reshape(-1, 1)
                if use_logit_transform
                else x_clipped.reshape(-1, 1)
            )
            lr = LogisticRegression(
                C=1.0,
                class_weight=class_weight,
                solver="lbfgs",
                random_state=fit_seed,
                max_iter=1000,
            )
            lr.fit(features, y)
            coef = float(lr.coef_[0][0])
            intercept = float(lr.intercept_[0])
            kwargs["platt_coef"] = round(coef, 8)
            kwargs["platt_intercept"] = round(intercept, 8)
        elif resolved_method == CalibrationMethod.ISOTONIC:
            iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
            iso.fit(x_clipped, y)
            kwargs["isotonic_x_thresholds"] = [round(float(v), 8) for v in iso.X_thresholds_]
            kwargs["isotonic_y_thresholds"] = [round(float(v), 8) for v in iso.y_thresholds_]
        elif resolved_method == CalibrationMethod.TEMPERATURE:
            x_logit = logit(x_clipped)

            def _nll(temp: float) -> float:
                probs = np.clip(expit(x_logit / temp), 1e-6, 1.0 - 1e-6)
                return -float(np.mean(y * np.log(probs) + (1 - y) * np.log(1.0 - probs)))

            res = minimize_scalar(_nll, bounds=(0.1, 10.0), method="bounded")
            kwargs["temperature"] = round(float(res.x), 8)

        artifact = CalibrationArtifact(**kwargs)
        return cls(artifact=artifact)

    def calibrate_score(self, raw_score: float) -> tuple[float, bool]:
        """Map raw G2 trust score to calibrated P(clean), failing safely back to raw_score."""
        if not math.isfinite(raw_score):
            return 0.5, True
        clamped_raw = min(1.0, max(0.0, float(raw_score)))
        if not self.is_active or self.artifact is None:
            return round(clamped_raw, 4), self._corrupted

        try:
            art = self.artifact
            if not art.verify_integrity():
                self._corrupted = True
                return round(clamped_raw, 4), True

            eps = art.clip_eps
            clipped = min(1.0 - eps, max(eps, clamped_raw))

            if art.method == CalibrationMethod.PLATT:
                assert art.platt_coef is not None and art.platt_intercept is not None
                x_val = math.log(clipped / (1.0 - clipped)) if art.use_logit_transform else clipped
                z = art.platt_coef * x_val + art.platt_intercept
                prob = float(expit(z))
            elif art.method == CalibrationMethod.ISOTONIC:
                prob = float(
                    np.interp(
                        clipped,
                        np.asarray(art.isotonic_x_thresholds, dtype=float),
                        np.asarray(art.isotonic_y_thresholds, dtype=float),
                    )
                )
            elif art.method == CalibrationMethod.TEMPERATURE:
                assert art.temperature is not None and art.temperature > 0.0
                x_logit = math.log(clipped / (1.0 - clipped))
                prob = float(expit(x_logit / art.temperature))
            else:
                return round(clamped_raw, 4), False

            if not math.isfinite(prob):
                return round(clamped_raw, 4), True
            return round(min(1.0, max(0.0, prob)), 4), False
        except Exception as exc:
            LOGGER.warning("Calibration inference failed safely: %s", exc)
            return round(clamped_raw, 4), True

    def calibrate_batch(self, raw_scores: Sequence[float]) -> list[float]:
        """Deterministically calibrate a sequence of raw trust scores."""
        return [self.calibrate_score(s)[0] for s in raw_scores]

    def save_json(self, path: str | Path) -> Path:
        """Persist versioned calibration artifact as validated JSON."""
        if self.artifact is None:
            raise ValueError("Cannot save empty TrustCalibrator without an artifact.")
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(self.artifact.model_dump_json(indent=2), encoding="utf-8")
        return dest

    @classmethod
    def load_json(cls, path: str | Path) -> TrustCalibrator:
        """Load calibration artifact safely; returns failing-safe fallback calibrator on corruption."""
        src = Path(path)
        if not src.is_file():
            raise FileNotFoundError(f"Calibration artifact not found: {src}")
        raw_text = src.read_text(encoding="utf-8")
        artifact = CalibrationArtifact.model_validate_json(raw_text)
        if not artifact.verify_integrity():
            raise ValueError(f"Corrupted calibration artifact checksum at {src}")
        return cls(artifact=artifact)


def collect_g2_partition_scores(
    dataset_name: str,
    split: str,
    *,
    dataset_dir: str | Path,
    msd_config: MSDConfig | None = None,
    calibrator: TrustCalibrator | None = None,
    max_clean_queries: int = 30,
) -> tuple[list[int], list[float], list[int]]:
    """Run MultiSignalDetector across a benchmark split to obtain (y_clean, trust_scores, pred_attack).

    Supports both security datasets (adversarial_robustness / knowledge_poisoning) and
    clean RAG datasets (clean_rag) so calibration can balance clean deployment priors.
    """
    part = load_evaluation_partition(dataset_name, split=split, dataset_dir=dataset_dir)
    cfg_msd = (msd_config or load_config().msd).model_copy(deep=True)
    detector = MultiSignalDetector(config=cfg_msd, calibrator=calibrator)

    y_clean: list[int] = []
    trust_scores: list[float] = []
    pred_attack: list[int] = []

    if dataset_name == "clean_rag":
        clean_docs = [
            d
            for d in (EvidenceDocument.from_record(r) for r in part.records)
            if d is not None
        ]
        if not clean_docs:
            return y_clean, trust_scores, pred_attack
        cand = clean_docs[:5]
        for r in part.records[:max_clean_queries]:
            q = getattr(r, "query", "") or ""
            rels = [max(0.1, compute_lexical_overlap(q, d.text)) for d in cand]
            assessments = detector.assess_candidates(q, cand, rels)
            for a in assessments:
                y_clean.append(1)
                trust_scores.append(a.trust_score)
                pred_attack.append(1 if a.trust_score < cfg_msd.trust_threshold else 0)
        return y_clean, trust_scores, pred_attack

    grouped: dict[str, list[Any]] = defaultdict(list)
    seen_ids: set[str] = set()
    for r in part.records:
        rec_id = getattr(r, "record_id", None)
        if rec_id and rec_id in seen_ids:
            continue
        if rec_id:
            seen_ids.add(rec_id)
        q = getattr(r, "target_query", None) or "default_query"
        grouped[q].append(r)

    for q, recs in grouped.items():
        docs: list[EvidenceDocument] = []
        gt_clean: list[int] = []
        for r in recs:
            d = EvidenceDocument.from_record(r)
            if d is None:
                continue
            docs.append(d)
            lbl = str(getattr(r, "clean_poison_label", "") or "").strip().lower()
            fam = str(getattr(r, "attack_family", "UNKNOWN") or "UNKNOWN")
            is_atk = 1 if (lbl == "poisoned" and fam != "BENIGN_INSTRUCTION_LIKE") else 0
            gt_clean.append(1 - is_atk)
        if not docs:
            continue
        rels = [max(0.1, compute_lexical_overlap(q, d.text)) for d in docs]
        assessments = detector.assess_candidates(q, docs, rels)
        for is_clean_lbl, a in zip(gt_clean, assessments, strict=False):
            y_clean.append(is_clean_lbl)
            trust_scores.append(a.trust_score)
            pred_attack.append(1 if a.trust_score < cfg_msd.trust_threshold else 0)

    return y_clean, trust_scores, pred_attack


def evaluate_calibrator_on_partition(
    dataset_name: str,
    split: str,
    *,
    dataset_dir: str | Path,
    calibrator: TrustCalibrator | None = None,
    msd_config: MSDConfig | None = None,
    n_bins: int = 5,
) -> CalibrationEvaluationReport:
    """Evaluate raw or calibrated G2 trust scores on any evaluation split (without fitting)."""
    y_clean, trust_scores, pred_attack = collect_g2_partition_scores(
        dataset_name,
        split=split,
        dataset_dir=dataset_dir,
        msd_config=msd_config,
        calibrator=calibrator,
    )
    cal = compute_calibration_metrics(y_clean, trust_scores, n_bins=n_bins)
    bins = compute_reliability_diagram(y_clean, trust_scores, n_bins=n_bins)
    y_atk = [1 - y for y in y_clean]
    clf = compute_binary_classification_metrics(
        y_atk,
        pred_attack,
        y_scores=[1.0 - p for p in trust_scores],
    )
    method = (
        calibrator.artifact.method
        if calibrator is not None and calibrator.artifact is not None and calibrator.is_active
        else CalibrationMethod.NONE
    )
    return CalibrationEvaluationReport(
        method=method,
        dataset_name=dataset_name,
        split=split,
        sample_count=len(y_clean),
        clean_count=sum(y_clean),
        attack_count=sum(y_atk),
        brier_score=cal["brier_score"],
        ece=cal["ece"],
        precision=clf["precision"],
        recall=clf["recall"],
        f1=clf["f1"],
        fpr=clf["fpr"],
        fnr=clf["fnr"],
        roc_auc=clf["roc_auc"],
        pr_auc=clf["pr_auc"],
        reliability_bins=bins,
    )


__all__ = [
    "TrustCalibrator",
    "collect_g2_partition_scores",
    "compute_calibration_metrics",
    "compute_reliability_diagram",
    "evaluate_calibrator_on_partition",
]

