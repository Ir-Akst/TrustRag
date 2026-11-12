"""Isolated experimental harness for Paper C (FilterRAG & ML-FilterRAG) evaluation.

This module MUST remain decoupled from production defaults in configs/base.yaml
(msd.enable_freq_density=False). It provides:
1. Genuine FilterRAG evaluation with a user/model-supplied SLM intermediate-answer
   callable ``a_j = SLM(q_i, d_j)`` (marked BLOCKED offline when no SLM exists).
2. Explicitly labeled offline extractive-sentence proxy mode for reproducing the
   Phase 07 Freq-Density negative/proxy finding (extractive proxy != live SLM).
3. ML-FilterRAG lightweight LogisticRegression classifier trained strictly on train splits.
4. 4-way comparative benchmark across Original RAG, TrustRAG MSD, FilterRAG /
   ML-FilterRAG, and Combined MSD + FilterRAG (measuring both adversarial detection
   and clean passage preservation / utility).
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_fscore_support, roc_auc_score

from trustrag.adaptive.calibration import TrustCalibrator
from trustrag.config.engine_config import MSDConfig
from trustrag.detection.msd import MultiSignalDetector
from trustrag.detection.signals import evaluate_freq_density_heuristic
from trustrag.engine.schemas import EvidenceDocument
from trustrag.engine.text_utils import compute_lexical_overlap, split_sentences
from trustrag.evaluation.loader import load_evaluation_partition

SLMAnswerCallable = Callable[[str, EvidenceDocument], str]


class FilterRAGFeatures(BaseModel):
    """Feature vector extracted per candidate passage for FilterRAG / ML-FilterRAG."""

    doc_id: str
    is_attack: int
    freq_density: float
    query_match: float
    retrieval_score: float
    token_count_norm: float
    intermediate_answer_mode: Literal["live_slm", "extractive_proxy"]


class DefenseComparisonRow(BaseModel):
    """Metrics for one defense variant across security + clean preservation splits."""

    variant_name: str
    status: Literal["COMPLETED", "PROXY_ONLY", "BLOCKED"]
    notes: str = ""
    roc_auc: float | None = None
    pr_auc: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    security_clean_fpr: float | None = None
    clean_rag_retention_rate: float | None = None
    clean_rag_fp: int | None = None
    clean_rag_total: int | None = None


class FilterRAGComparisonReport(BaseModel):
    """End-to-end comparative report for Paper C (FilterRAG vs TrustRAG MSD)."""

    slm_available: bool
    evaluation_mode: str
    selected_eps: float
    seed: int = 42
    train_samples: int = 0
    val_samples: int = 0
    test_sec_samples: int = 0
    test_clean_samples: int = 0
    variants: list[DefenseComparisonRow] = Field(default_factory=list)


def extractive_intermediate_answer(query: str, doc: EvidenceDocument) -> str:
    """Offline extractive proxy: select single highest query-overlapping sentence.

    Explicitly NOT equivalent to Paper C generative SLM intermediate answers.
    """
    sents = split_sentences(doc.text or "")
    if not sents:
        return ""
    return max(sents, key=lambda s: compute_lexical_overlap(query, s))


def compute_freq_density(
    query: str,
    doc: EvidenceDocument,
    *,
    intermediate_answer: str | None = None,
    slm_answer_callable: SLMAnswerCallable | None = None,
) -> float:
    """Compute FilterRAG Freq-Density using existing signal implementation."""
    cfg = MSDConfig(enable_freq_density=True)
    detail = evaluate_freq_density_heuristic(
        query,
        doc,
        cfg,
        intermediate_answer=intermediate_answer,
        answer_callable=slm_answer_callable,
    )
    return float(detail.value) if (detail.available and detail.value is not None) else 0.0


def _build_security_groups(
    dataset_name: str,
    split: str,
    dataset_dir: Path,
) -> list[tuple[str, list[EvidenceDocument], list[int], list[float]]]:
    part = load_evaluation_partition(dataset_name, split=split, dataset_dir=dataset_dir / dataset_name)
    grouped: dict[str, list[object]] = defaultdict(list)
    seen_ids: set[str] = set()
    for r in part.records:
        rec_id = getattr(r, "record_id", None)
        if rec_id and rec_id in seen_ids:
            continue
        if rec_id:
            seen_ids.add(str(rec_id))
        q = str(getattr(r, "target_query", None) or "default_query")
        grouped[q].append(r)

    groups: list[tuple[str, list[EvidenceDocument], list[int], list[float]]] = []
    for q, recs in grouped.items():
        docs: list[EvidenceDocument] = []
        y_atk: list[int] = []
        rels: list[float] = []
        for r in recs:
            d = EvidenceDocument.from_record(r)
            if d is None:
                continue
            lbl = str(getattr(r, "clean_poison_label", "") or "").strip().lower()
            fam = str(getattr(r, "attack_family", "UNKNOWN") or "UNKNOWN")
            is_atk = 1 if (lbl == "poisoned" and fam != "BENIGN_INSTRUCTION_LIKE") else 0
            docs.append(d)
            y_atk.append(is_atk)
            rels.append(max(0.1, compute_lexical_overlap(q, d.text)))
        if docs:
            groups.append((q, docs, y_atk, rels))
    return groups


def _build_clean_groups(
    split: str,
    dataset_dir: Path,
    max_queries: int = 30,
) -> list[tuple[str, list[EvidenceDocument], list[int], list[float]]]:
    part = load_evaluation_partition("clean_rag", split=split, dataset_dir=dataset_dir / "clean_rag")
    clean_docs = [
        d for d in (EvidenceDocument.from_record(r) for r in part.records) if d is not None
    ][:5]
    if not clean_docs:
        return []
    groups: list[tuple[str, list[EvidenceDocument], list[int], list[float]]] = []
    for r in part.records[:max_queries]:
        q = str(getattr(r, "query", "") or "")
        rels = [max(0.1, compute_lexical_overlap(q, d.text)) for d in clean_docs]
        groups.append((q, clean_docs, [0] * len(clean_docs), rels))
    return groups


def extract_filterrag_features(
    groups: Sequence[tuple[str, list[EvidenceDocument], list[int], list[float]]],
    *,
    slm_answer_callable: SLMAnswerCallable | None = None,
    use_extractive_proxy: bool = False,
) -> list[FilterRAGFeatures]:
    """Extract Freq-Density + auxiliary features across query candidate groups."""
    if slm_answer_callable is None and not use_extractive_proxy:
        raise RuntimeError(
            "FilterRAG requires a live slm_answer_callable (unless use_extractive_proxy=True is explicitly requested)."
        )
    mode: Literal["live_slm", "extractive_proxy"] = (
        "live_slm" if slm_answer_callable is not None else "extractive_proxy"
    )
    ans_fn = slm_answer_callable if slm_answer_callable is not None else extractive_intermediate_answer

    rows: list[FilterRAGFeatures] = []
    for q, docs, labels, rels in groups:
        for d, lbl, rel in zip(docs, labels, rels, strict=True):
            ans = ans_fn(q, d)
            fd = compute_freq_density(q, d, intermediate_answer=ans)
            tok_len = len((d.text or "").split())
            rows.append(
                FilterRAGFeatures(
                    doc_id=d.doc_id,
                    is_attack=lbl,
                    freq_density=fd,
                    query_match=compute_lexical_overlap(q, d.text),
                    retrieval_score=rel,
                    token_count_norm=min(1.0, math.log1p(tok_len) / 6.0),
                    intermediate_answer_mode=mode,
                )
            )
    return rows


class MLFilterRAGModel:
    """Lightweight LogisticRegression Paper-C filter fitted strictly on non-test splits."""

    def __init__(self, random_state: int = 42) -> None:
        self._clf = LogisticRegression(random_state=random_state, max_iter=500, class_weight="balanced")
        self.fitted = False

    @staticmethod
    def _to_matrix(features: Sequence[FilterRAGFeatures]) -> np.ndarray:
        return np.array(
            [
                [f.freq_density, f.query_match, f.retrieval_score, f.token_count_norm]
                for f in features
            ],
            dtype=float,
        )

    def fit(self, train_features: Sequence[FilterRAGFeatures], split_name: str = "train") -> MLFilterRAGModel:
        if "test" in split_name.lower():
            raise ValueError("Refusing to fit ML-FilterRAG on any test split.")
        y = np.array([f.is_attack for f in train_features], dtype=int)
        if set(y.tolist()) != {0, 1}:
            raise ValueError("ML-FilterRAG training requires both clean (0) and attack (1) samples.")
        x = self._to_matrix(train_features)
        self._clf.fit(x, y)
        self.fitted = True
        return self

    def predict_attack_probs(self, features: Sequence[FilterRAGFeatures]) -> list[float]:
        if not self.fitted:
            raise RuntimeError("MLFilterRAGModel must be fit before prediction.")
        x = self._to_matrix(features)
        probs = self._clf.predict_proba(x)[:, 1]
        return [float(p) for p in probs]


def _score_binary_predictions(
    y_true: Sequence[int],
    attack_scores: Sequence[float],
    pred_flags: Sequence[int],
) -> tuple[float | None, float | None, float, float, float, float]:
    y_arr = np.asarray(y_true, dtype=int)
    s_arr = np.asarray(attack_scores, dtype=float)
    p_arr = np.asarray(pred_flags, dtype=int)
    roc = float(roc_auc_score(y_arr, s_arr)) if len(set(y_arr.tolist())) == 2 else None
    pr = float(average_precision_score(y_arr, s_arr)) if len(set(y_arr.tolist())) == 2 else None
    prec, rec, f1, _ = precision_recall_fscore_support(y_arr, p_arr, average="binary", zero_division=0)
    fp = int(np.sum((y_arr == 0) & (p_arr == 1)))
    clean_tot = int(np.sum(y_arr == 0))
    fpr = fp / clean_tot if clean_tot else 0.0
    return (
        round(roc, 4) if roc is not None else None,
        round(pr, 4) if pr is not None else None,
        round(float(prec), 4),
        round(float(rec), 4),
        round(float(f1), 4),
        round(fpr, 4),
    )


def compare_filterrag_defenses(
    dataset_dir: str | Path = "data/benchmarks_backup",
    *,
    slm_answer_callable: SLMAnswerCallable | None = None,
    allow_extractive_proxy: bool = False,
    calibrator_path: str | Path | None = "configs/adaptive/temperature_calibrator_v1.json",
    seed: int = 42,
    eps_grid: Sequence[float] = (0.30, 0.50, 0.70, 0.85, 0.95),
) -> FilterRAGComparisonReport:
    """Compare Original RAG, TrustRAG MSD, FilterRAG, ML-FilterRAG, and Combined MSD+FilterRAG."""
    bdir = Path(dataset_dir)
    train_groups = (
        _build_security_groups("knowledge_poisoning", "train", bdir)
        + _build_security_groups("adversarial_robustness", "train", bdir)
        + _build_clean_groups("train", bdir, max_queries=25)
    )
    val_groups = (
        _build_security_groups("knowledge_poisoning", "val", bdir)
        + _build_security_groups("adversarial_robustness", "val", bdir)
    )
    test_sec_groups = (
        _build_security_groups("knowledge_poisoning", "test", bdir)
        + _build_security_groups("adversarial_robustness", "test", bdir)
    )
    test_clean_groups = _build_clean_groups("test", bdir, max_queries=30)

    train_n = sum(len(g[1]) for g in train_groups)
    val_n = sum(len(g[1]) for g in val_groups)
    test_sec_n = sum(len(g[1]) for g in test_sec_groups)
    test_clean_n = sum(len(g[1]) for g in test_clean_groups)

    y_sec_test = [y for g in test_sec_groups for y in g[2]]

    # 1. Original RAG baseline (accept all retrieved docs)
    orig_roc, orig_pr, orig_prec, orig_rec, orig_f1, orig_fpr = _score_binary_predictions(
        y_sec_test,
        [0.0] * len(y_sec_test),
        [0] * len(y_sec_test),
    )
    orig_row = DefenseComparisonRow(
        variant_name="Original_RAG",
        status="COMPLETED",
        notes="No adversarial passage filtering applied.",
        roc_auc=orig_roc,
        pr_auc=orig_pr,
        precision=orig_prec,
        recall=orig_rec,
        f1=orig_f1,
        security_clean_fpr=orig_fpr,
        clean_rag_retention_rate=1.0,
        clean_rag_fp=0,
        clean_rag_total=test_clean_n,
    )

    # 2. TrustRAG MSD (with zero-FP temperature calibrator when present)
    cal_p = Path(calibrator_path) if calibrator_path is not None else None
    cal = TrustCalibrator.load_json(cal_p) if cal_p is not None and cal_p.exists() else None
    detector = MultiSignalDetector(MSDConfig(), calibrator=cal)
    msd_sec_scores: list[float] = []
    msd_sec_preds: list[int] = []
    for q, docs, _y, rels in test_sec_groups:
        for a in detector.assess_candidates(q, docs, rels):
            msd_sec_scores.append(1.0 - a.trust_score)
            msd_sec_preds.append(1 if a.trust_score < detector.config.trust_threshold else 0)
    msd_clean_fp = 0
    for q, docs, _y, rels in test_clean_groups:
        for a in detector.assess_candidates(q, docs, rels):
            if a.trust_score < detector.config.trust_threshold:
                msd_clean_fp += 1
    m_roc, m_pr, m_prec, m_rec, m_f1, m_fpr = _score_binary_predictions(
        y_sec_test, msd_sec_scores, msd_sec_preds
    )
    msd_row = DefenseComparisonRow(
        variant_name="TrustRAG_MSD",
        status="COMPLETED",
        notes=f"Calibrator: {cal_p.name if (cal is not None and cal_p is not None) else 'none'}.",
        roc_auc=m_roc,
        pr_auc=m_pr,
        precision=m_prec,
        recall=m_rec,
        f1=m_f1,
        security_clean_fpr=m_fpr,
        clean_rag_retention_rate=round(1.0 - (msd_clean_fp / test_clean_n if test_clean_n else 0.0), 4),
        clean_rag_fp=msd_clean_fp,
        clean_rag_total=test_clean_n,
    )

    # 3 & 4. FilterRAG / ML-FilterRAG / Combined MSD+FilterRAG
    if slm_answer_callable is None and not allow_extractive_proxy:
        blocked_variants = [
            orig_row,
            msd_row,
            DefenseComparisonRow(
                variant_name="FilterRAG_Threshold_SLM",
                status="BLOCKED",
                notes="Live SLM intermediate-answer generator a_j=SLM(q_i,d_j) unavailable offline; pass allow_extractive_proxy=True only for proxy reproducibility.",
            ),
            DefenseComparisonRow(
                variant_name="ML_FilterRAG_SLM",
                status="BLOCKED",
                notes="Live SLM unavailable offline.",
            ),
            DefenseComparisonRow(
                variant_name="Combined_MSD_FilterRAG",
                status="BLOCKED",
                notes="Requires live SLM (or explicit proxy mode).",
            ),
        ]
        return FilterRAGComparisonReport(
            slm_available=False,
            evaluation_mode="BLOCKED_NO_LIVE_SLM",
            selected_eps=0.10,
            seed=seed,
            train_samples=train_n,
            val_samples=val_n,
            test_sec_samples=test_sec_n,
            test_clean_samples=test_clean_n,
            variants=blocked_variants,
        )

    use_proxy = slm_answer_callable is None
    status_label: Literal["COMPLETED", "PROXY_ONLY"] = "PROXY_ONLY" if use_proxy else "COMPLETED"
    eval_mode = "extractive_proxy" if use_proxy else "live_slm"

    train_feats = extract_filterrag_features(
        train_groups, slm_answer_callable=slm_answer_callable, use_extractive_proxy=use_proxy
    )
    val_feats = extract_filterrag_features(
        val_groups, slm_answer_callable=slm_answer_callable, use_extractive_proxy=use_proxy
    )
    test_sec_feats = extract_filterrag_features(
        test_sec_groups, slm_answer_callable=slm_answer_callable, use_extractive_proxy=use_proxy
    )
    test_clean_feats = extract_filterrag_features(
        test_clean_groups, slm_answer_callable=slm_answer_callable, use_extractive_proxy=use_proxy
    )

    # Tune FilterRAG threshold eps strictly on val_groups (maximizing val F1)
    y_val = [f.is_attack for f in val_feats]
    best_eps = float(eps_grid[0])
    best_val_f1 = -1.0
    for eps in eps_grid:
        val_preds = [1 if f.freq_density < eps else 0 for f in val_feats]
        _, _, vf1, _ = precision_recall_fscore_support(y_val, val_preds, average="binary", zero_division=0)
        if float(vf1) > best_val_f1:
            best_val_f1 = float(vf1)
            best_eps = float(eps)

    # Threshold FilterRAG on held-out test
    fr_sec_scores = [1.0 - f.freq_density for f in test_sec_feats]
    fr_sec_preds = [1 if f.freq_density < best_eps else 0 for f in test_sec_feats]
    fr_clean_fp = sum(1 for f in test_clean_feats if f.freq_density < best_eps)
    fr_roc, fr_pr, fr_prec, fr_rec, fr_f1, fr_fpr = _score_binary_predictions(
        y_sec_test, fr_sec_scores, fr_sec_preds
    )
    fr_row = DefenseComparisonRow(
        variant_name="FilterRAG_Threshold",
        status=status_label,
        notes=f"Mode={eval_mode}; eps={best_eps:.2f} tuned on val.",
        roc_auc=fr_roc,
        pr_auc=fr_pr,
        precision=fr_prec,
        recall=fr_rec,
        f1=fr_f1,
        security_clean_fpr=fr_fpr,
        clean_rag_retention_rate=round(1.0 - (fr_clean_fp / test_clean_n if test_clean_n else 0.0), 4),
        clean_rag_fp=fr_clean_fp,
        clean_rag_total=test_clean_n,
    )

    # ML-FilterRAG trained strictly on train_feats
    ml_model = MLFilterRAGModel(random_state=seed).fit(train_feats, split_name="train")
    ml_sec_probs = ml_model.predict_attack_probs(test_sec_feats)
    ml_sec_preds = [1 if p >= 0.50 else 0 for p in ml_sec_probs]
    ml_clean_probs = ml_model.predict_attack_probs(test_clean_feats)
    ml_clean_fp = sum(1 for p in ml_clean_probs if p >= 0.50)
    ml_roc, ml_pr, ml_prec, ml_rec, ml_f1, ml_fpr = _score_binary_predictions(
        y_sec_test, ml_sec_probs, ml_sec_preds
    )
    ml_row = DefenseComparisonRow(
        variant_name="ML_FilterRAG",
        status=status_label,
        notes=f"LogisticRegression fitted on train (n={len(train_feats)}); mode={eval_mode}.",
        roc_auc=ml_roc,
        pr_auc=ml_pr,
        precision=ml_prec,
        recall=ml_rec,
        f1=ml_f1,
        security_clean_fpr=ml_fpr,
        clean_rag_retention_rate=round(1.0 - (ml_clean_fp / test_clean_n if test_clean_n else 0.0), 4),
        clean_rag_fp=ml_clean_fp,
        clean_rag_total=test_clean_n,
    )

    # Combined MSD + FilterRAG (OR gate union: flag if MSD flags OR FilterRAG threshold flags)
    comb_sec_scores = [0.75 * m + 0.25 * fr for m, fr in zip(msd_sec_scores, fr_sec_scores, strict=True)]
    comb_sec_preds = [1 if (m == 1 or f == 1) else 0 for m, f in zip(msd_sec_preds, fr_sec_preds, strict=True)]
    comb_clean_fp = 0
    clean_idx = 0
    for q, docs, _y, rels in test_clean_groups:
        for a in detector.assess_candidates(q, docs, rels):
            fr_flag = 1 if test_clean_feats[clean_idx].freq_density < best_eps else 0
            if a.trust_score < detector.config.trust_threshold or fr_flag == 1:
                comb_clean_fp += 1
            clean_idx += 1
    c_roc, c_pr, c_prec, c_rec, c_f1, c_fpr = _score_binary_predictions(
        y_sec_test, comb_sec_scores, comb_sec_preds
    )
    comb_row = DefenseComparisonRow(
        variant_name="Combined_MSD_FilterRAG",
        status=status_label,
        notes=f"Logical union of TrustRAG MSD and FilterRAG (eps={best_eps:.2f}, mode={eval_mode}).",
        roc_auc=c_roc,
        pr_auc=c_pr,
        precision=c_prec,
        recall=c_rec,
        f1=c_f1,
        security_clean_fpr=c_fpr,
        clean_rag_retention_rate=round(1.0 - (comb_clean_fp / test_clean_n if test_clean_n else 0.0), 4),
        clean_rag_fp=comb_clean_fp,
        clean_rag_total=test_clean_n,
    )

    return FilterRAGComparisonReport(
        slm_available=not use_proxy,
        evaluation_mode=eval_mode,
        selected_eps=best_eps,
        seed=seed,
        train_samples=train_n,
        val_samples=val_n,
        test_sec_samples=test_sec_n,
        test_clean_samples=test_clean_n,
        variants=[orig_row, msd_row, fr_row, ml_row, comb_row],
    )
