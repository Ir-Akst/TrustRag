"""TrustRAG Research Completion - Track 1, Step 2.2: Corrected Benchmark Baseline Evaluation.

Executes deterministic, reproducible baseline evaluations for:
1. G3 Claim Verification on RAGTruth (test split: 2,700 records)
   - no_verification
   - default_g3 (min_support_coverage = 0.65)
   - strict_g3 (min_support_coverage = 0.80)
2. G3 Claim Verification on HaluEval (test split: 3,000 records)
   - no_verification
   - default_g3 (min_support_coverage = 0.65)
   - strict_g3 (min_support_coverage = 0.80)
3. Full 5-outcome accounting and dual safety metrics (strict & partial-inclusive)
4. TrustAwareRetriever Evaluation on HotpotQA (validation: 7,405 queries)
5. TrustAwareRetriever Evaluation on MS MARCO (validation: 10,047 queries)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("track02_eval")

# Ensure src is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from trustrag.config.engine_config import VerificationConfig
from trustrag.engine.schemas import EvidenceDocument
from trustrag.retrieval.retriever import TrustAwareRetriever
from trustrag.verification.output_verifier import OutputEvidenceVerifier


VALID_FIVE_OUTCOMES = (
    "SUPPORTED",
    "CONTRADICTED",
    "PARTIALLY_SUPPORTED",
    "INSUFFICIENT_EVIDENCE",
    "UNCERTAIN",
)


def compute_binary_metrics(tp: int, tn: int, fp: int, fn: int) -> Dict[str, Any]:
    """Compute standard binary classification metrics from a confusion matrix."""
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total else 0.0
    tpr = tp / (tp + fn) if (tp + fn) else 0.0  # Recall of positive class
    tnr = tn / (tn + fp) if (tn + fp) else 0.0  # Specificity (Recall of negative class)
    balanced_acc = 0.5 * (tpr + tnr)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tpr
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "balanced_accuracy": round(balanced_acc, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "fpr": round(fpr, 4),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "total": total,
    }


def evaluate_g3_split(
    dataset_name: str,
    data_path: Path,
    verifier: Optional[OutputEvidenceVerifier],
    baseline_mode: str = "default_g3",
    effective_config: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Evaluate G3 verifier on a canonical JSONL test split with explicit 5-outcome accounting."""
    logger.info("Evaluating G3 on %s (file=%s, mode=%s)...", dataset_name, data_path.name, baseline_mode)

    records: List[Dict[str, Any]] = []
    with open(data_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if limit and idx >= limit:
                break
            records.append(json.loads(line))

    predictions: List[Dict[str, Any]] = []
    verdict_counts: Counter[str] = Counter()
    hallucinated_total = 0
    factual_total = 0

    t0 = time.time()
    for idx, rec in enumerate(records):
        rec_id = str(rec.get("record_id") or f"{dataset_name}_{idx}")
        doc_text = str(rec.get("document") or rec.get("passage") or "")
        claim_text = str(rec.get("claim") or rec.get("response") or "")
        label = str(rec.get("label", "")).strip().upper()

        is_hallucinated = 1 if label == "HALLUCINATED" else 0
        if is_hallucinated:
            hallucinated_total += 1
        else:
            factual_total += 1

        confidence = 0.5
        coverage_score = 0.0
        explanation = ""
        status_str = ""

        if baseline_mode == "no_verification":
            verdict = "SUPPORTED"
            confidence = 1.0
            coverage_score = 1.0
            explanation = "Baseline: no verification performed (always accept)."
            status_str = "PASSED"
        else:
            assert verifier is not None, "Verifier must be provided for verification modes"
            doc = EvidenceDocument(
                doc_id=rec_id,
                text=doc_text,
                source_dataset=dataset_name,
                source_id=str(rec.get("source_id", "")),
                provenance=dataset_name,
            )
            query_ctx = str(rec.get("metadata", {}).get("query", ""))
            rep = verifier.verify(claim_text, [doc], query=query_ctx)
            verdict = rep.verdict.value if hasattr(rep.verdict, "value") else str(rep.verdict)
            status_str = rep.overall_status.value if hasattr(rep.overall_status, "value") else str(rep.overall_status)
            if rep.claims:
                confidence = rep.claims[0].confidence
                explanation = rep.claims[0].explanation
                if rep.claims[0].supporting_evidence_refs:
                    ref0 = rep.claims[0].supporting_evidence_refs[0]
                    coverage_score = ref0.coverage_score if hasattr(ref0, "coverage_score") else ref0.get("coverage_score", 0.0)

        # Enforce 5-outcome validity
        if verdict not in VALID_FIVE_OUTCOMES:
            raise ValueError(f"Unrecognized verdict outcome: '{verdict}' on record {rec_id}")

        verdict_counts[verdict] += 1

        # Policy 1: All-Record Conservative Defense Policy (Positive = Hallucinated/Unverified)
        # Negative (0) = Certified SUPPORTED; Positive (1) = Anything non-supported
        pred_conservative = 0 if verdict == "SUPPORTED" else 1

        # Policy 2: Strict Decisive-Only Classification Policy
        # Only evaluated on SUPPORTED (0) vs CONTRADICTED (1); None if non-decisive
        pred_decisive: Optional[int] = None
        if verdict == "SUPPORTED":
            pred_decisive = 0
        elif verdict == "CONTRADICTED":
            pred_decisive = 1

        # Failure classification for conservative defense
        failure_type: Optional[str] = None
        if is_hallucinated == 1 and verdict == "SUPPORTED":
            failure_type = "FALSE_SUPPORTED"
        elif is_hallucinated == 1 and verdict == "PARTIALLY_SUPPORTED":
            failure_type = "PARTIAL_UNSAFE_ACCEPTANCE"
        elif is_hallucinated == 0 and verdict == "CONTRADICTED":
            failure_type = "FALSE_CONTRADICTION"
        elif is_hallucinated == 0 and verdict == "PARTIALLY_SUPPORTED":
            failure_type = "FACTUAL_PARTIALLY_SUPPORTED"
        elif is_hallucinated == 0 and verdict in ("INSUFFICIENT_EVIDENCE", "UNCERTAIN"):
            failure_type = "INSUFFICIENT_EVIDENCE_ON_FACTUAL"

        pred_entry = {
            "record_id": rec_id,
            "dataset": dataset_name,
            "mode": baseline_mode,
            "claim": claim_text,
            "document_preview": doc_text[:160] + ("..." if len(doc_text) > 160 else ""),
            "ground_truth_label": label,
            "g3_verdict": verdict,
            "overall_status": status_str,
            "confidence": round(confidence, 4),
            "coverage_score": round(coverage_score, 4),
            "effective_configuration": effective_config or {},
            "explanation": explanation,
            "is_correct_conservative": (is_hallucinated == pred_conservative),
            "is_correct_decisive": (is_hallucinated == pred_decisive) if pred_decisive is not None else None,
            "failure_type": failure_type,
        }
        predictions.append(pred_entry)

    elapsed = time.time() - t0
    total_records = len(records)

    # Assert five-outcome completeness
    assert total_records == sum(verdict_counts[o] for o in VALID_FIVE_OUTCOMES), (
        f"Accounting error: total {total_records} != sum of outcomes {sum(verdict_counts.values())}"
    )

    # Outcome counts
    c_sup = verdict_counts["SUPPORTED"]
    c_cont = verdict_counts["CONTRADICTED"]
    c_part = verdict_counts["PARTIALLY_SUPPORTED"]
    c_ie = verdict_counts["INSUFFICIENT_EVIDENCE"]
    c_unc = verdict_counts["UNCERTAIN"]

    explicit_decisive_count = c_sup + c_cont
    strict_abstention_count = c_ie + c_unc
    partial_support_count = c_part
    non_full_support_count = total_records - c_sup

    # Safety metrics
    # Strict FSR: Hallucinated assigned exactly SUPPORTED / all hallucinated
    hallucinated_recs = [p for p in predictions if p["ground_truth_label"] == "HALLUCINATED"]
    factual_recs = [p for p in predictions if p["ground_truth_label"] == "FACTUAL"]

    strict_fs_count = sum(1 for p in hallucinated_recs if p["g3_verdict"] == "SUPPORTED")
    strict_fsr = strict_fs_count / hallucinated_total if hallucinated_total else 0.0

    # Partial-inclusive unsafe acceptance: Hallucinated assigned SUPPORTED or PARTIALLY_SUPPORTED
    partial_unsafe_count = sum(1 for p in hallucinated_recs if p["g3_verdict"] in ("SUPPORTED", "PARTIALLY_SUPPORTED"))
    partial_inclusive_unsafe_rate = partial_unsafe_count / hallucinated_total if hallucinated_total else 0.0

    # FCR: Factual assigned exactly CONTRADICTED / all factual
    fc_count = sum(1 for p in factual_recs if p["g3_verdict"] == "CONTRADICTED")
    fcr = fc_count / factual_total if factual_total else 0.0

    # Partial-inclusive factual rejection: Factual assigned CONTRADICTED or PARTIALLY_SUPPORTED
    partial_rejection_count = sum(1 for p in factual_recs if p["g3_verdict"] in ("CONTRADICTED", "PARTIALLY_SUPPORTED"))
    partial_inclusive_rejection_rate = partial_rejection_count / factual_total if factual_total else 0.0

    # Policy 1 metrics: Conservative defense (all records)
    y_true_all = [1 if p["ground_truth_label"] == "HALLUCINATED" else 0 for p in predictions]
    y_pred_all = [0 if p["g3_verdict"] == "SUPPORTED" else 1 for p in predictions]
    tp_all = sum(1 for yt, yp in zip(y_true_all, y_pred_all) if yt == 1 and yp == 1)
    tn_all = sum(1 for yt, yp in zip(y_true_all, y_pred_all) if yt == 0 and yp == 0)
    fp_all = sum(1 for yt, yp in zip(y_true_all, y_pred_all) if yt == 0 and yp == 1)
    fn_all = sum(1 for yt, yp in zip(y_true_all, y_pred_all) if yt == 1 and yp == 0)
    metrics_conservative = compute_binary_metrics(tp_all, tn_all, fp_all, fn_all)

    # Policy 2 metrics: Strict decisive-only (excluding partial and abstentions)
    decisive_preds = [p for p in predictions if p["g3_verdict"] in ("SUPPORTED", "CONTRADICTED")]
    y_true_dec = [1 if p["ground_truth_label"] == "HALLUCINATED" else 0 for p in decisive_preds]
    y_pred_dec = [0 if p["g3_verdict"] == "SUPPORTED" else 1 for p in decisive_preds]
    tp_dec = sum(1 for yt, yp in zip(y_true_dec, y_pred_dec) if yt == 1 and yp == 1)
    tn_dec = sum(1 for yt, yp in zip(y_true_dec, y_pred_dec) if yt == 0 and yp == 0)
    fp_dec = sum(1 for yt, yp in zip(y_true_dec, y_pred_dec) if yt == 0 and yp == 1)
    fn_dec = sum(1 for yt, yp in zip(y_true_dec, y_pred_dec) if yt == 1 and yp == 0)
    metrics_decisive = compute_binary_metrics(tp_dec, tn_dec, fp_dec, fn_dec)

    summary_metrics = {
        "dataset_name": dataset_name,
        "split": "test",
        "baseline_mode": baseline_mode,
        "effective_configuration": effective_config or {},
        "evaluated_records": total_records,
        "runtime_seconds": round(elapsed, 2),
        "throughput_records_per_sec": round(total_records / elapsed, 1) if elapsed else 0.0,
        "ground_truth_distribution": {
            "FACTUAL": factual_total,
            "HALLUCINATED": hallucinated_total,
        },
        "five_outcome_distribution": {
            "SUPPORTED": c_sup,
            "CONTRADICTED": c_cont,
            "PARTIALLY_SUPPORTED": c_part,
            "INSUFFICIENT_EVIDENCE": c_ie,
            "UNCERTAIN": c_unc,
        },
        "coverage_metrics": {
            "explicit_decisive_coverage": round(explicit_decisive_count / total_records, 4),
            "explicit_decisive_count": explicit_decisive_count,
            "explicit_decisive_ratio": f"{explicit_decisive_count}/{total_records}",
            "partial_support_coverage": round(partial_support_count / total_records, 4),
            "partial_support_count": partial_support_count,
            "partial_support_ratio": f"{partial_support_count}/{total_records}",
            "strict_abstention_rate": round(strict_abstention_count / total_records, 4),
            "strict_abstention_count": strict_abstention_count,
            "strict_abstention_ratio": f"{strict_abstention_count}/{total_records}",
            "inclusive_decisive_coverage": round((explicit_decisive_count + partial_support_count) / total_records, 4),
            "inclusive_decisive_count": explicit_decisive_count + partial_support_count,
            "non_full_support_rate": round(non_full_support_count / total_records, 4),
            "non_full_support_count": non_full_support_count,
        },
        "safety_metrics": {
            "strict_false_supported_rate": round(strict_fsr, 4),
            "strict_false_supported_count": strict_fs_count,
            "strict_false_supported_ratio": f"{strict_fs_count}/{hallucinated_total}",
            "partial_inclusive_unsafe_acceptance_rate": round(partial_inclusive_unsafe_rate, 4),
            "partial_inclusive_unsafe_acceptance_count": partial_unsafe_count,
            "partial_inclusive_unsafe_acceptance_ratio": f"{partial_unsafe_count}/{hallucinated_total}",
            "false_contradiction_rate": round(fcr, 4),
            "false_contradiction_count": fc_count,
            "false_contradiction_ratio": f"{fc_count}/{factual_total}",
            "partial_inclusive_factual_rejection_rate": round(partial_inclusive_rejection_rate, 4),
            "partial_inclusive_factual_rejection_count": partial_rejection_count,
            "partial_inclusive_factual_rejection_ratio": f"{partial_rejection_count}/{factual_total}",
            "hallucinated_total": hallucinated_total,
            "factual_total": factual_total,
        },
        "classification_conservative_policy": {
            "policy_description": "Conservative defense policy: SUPPORTED = 0 (Factual), all other outcomes = 1 (Hallucinated/Unverified).",
            "metrics": metrics_conservative,
        },
        "classification_decisive_policy": {
            "policy_description": "Decisive-only policy: Evaluated strictly on records with verdict in (SUPPORTED, CONTRADICTED). Non-decisive excluded.",
            "evaluated_count": len(decisive_preds),
            "excluded_count": total_records - len(decisive_preds),
            "coverage": round(len(decisive_preds) / total_records, 4),
            "metrics": metrics_decisive,
        },
    }

    logger.info(
        "%s [%s] evaluated (%d recs in %.1fs). Strict FSR=%.4f (%s), Partial-Inclusive Unsafe=%.4f (%s), FCR=%.4f (%s)",
        dataset_name,
        baseline_mode,
        total_records,
        elapsed,
        strict_fsr,
        summary_metrics["safety_metrics"]["strict_false_supported_ratio"],
        partial_inclusive_unsafe_rate,
        summary_metrics["safety_metrics"]["partial_inclusive_unsafe_acceptance_ratio"],
        fcr,
        summary_metrics["safety_metrics"]["false_contradiction_ratio"],
    )

    return summary_metrics, predictions


def evaluate_hotpotqa_retrieval(
    parquet_path: Path,
    limit: Optional[int] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Evaluate candidate reranking on HotpotQA distractor validation split (7,405 queries)."""
    logger.info("Evaluating HotpotQA candidate retrieval from %s...", parquet_path.name)
    df = pd.read_parquet(parquet_path)
    if limit:
        df = df.iloc[:limit]

    r_at_1_sum = 0.0
    r_at_5_sum = 0.0
    r_at_10_sum = 0.0
    mrr_at_10_sum = 0.0

    predictions: List[Dict[str, Any]] = []
    skipped_queries: List[Dict[str, Any]] = []

    t0 = time.time()
    for idx, row in df.iterrows():
        qid = str(row["id"])
        q = str(row["question"])
        gold_titles = set(row["supporting_facts"]["title"])
        if not gold_titles:
            skipped_queries.append({"query_id": qid, "reason": "No gold supporting titles annotated"})
            continue

        ctx = row["context"]
        docs: List[EvidenceDocument] = []
        for title, sents in zip(ctx["title"], ctx["sentences"], strict=True):
            text = f"{title}. {' '.join(sents)}"
            docs.append(
                EvidenceDocument(
                    doc_id=title,
                    text=text,
                    source_dataset="hotpotqa",
                    source_id=qid,
                    provenance="hotpotqa",
                )
            )

        retriever = TrustAwareRetriever(docs)
        candidates = retriever.retrieve_candidates(q, top_n=10)
        retrieved_ids = [d.doc_id for d, _ in candidates]

        hits_1 = len(gold_titles.intersection(retrieved_ids[:1]))
        hits_5 = len(gold_titles.intersection(retrieved_ids[:5]))
        hits_10 = len(gold_titles.intersection(retrieved_ids[:10]))

        r1 = hits_1 / len(gold_titles)
        r5 = hits_5 / len(gold_titles)
        r10 = hits_10 / len(gold_titles)

        mrr = 0.0
        for rank, rid in enumerate(retrieved_ids[:10], start=1):
            if rid in gold_titles:
                mrr = 1.0 / rank
                break

        r_at_1_sum += r1
        r_at_5_sum += r5
        r_at_10_sum += r10
        mrr_at_10_sum += mrr

        predictions.append({
            "query_id": qid,
            "query": q,
            "gold_supporting_titles": sorted(list(gold_titles)),
            "candidate_corpus_size": len(docs),
            "retrieved_top10": retrieved_ids,
            "recall_at_1": round(r1, 4),
            "recall_at_5": round(r5, 4),
            "recall_at_10": round(r10, 4),
            "mrr_at_10": round(mrr, 4),
        })

    elapsed = time.time() - t0
    evaluated_count = len(predictions)

    metrics = {
        "dataset_name": "hotpotqa",
        "split": "validation",
        "evaluated_queries": evaluated_count,
        "skipped_queries": len(skipped_queries),
        "candidate_pool_per_query": 10,
        "runtime_seconds": round(elapsed, 2),
        "queries_per_second": round(evaluated_count / elapsed, 1) if elapsed else 0.0,
        "recall_at_1": round(r_at_1_sum / evaluated_count, 4) if evaluated_count else 0.0,
        "recall_at_5": round(r_at_5_sum / evaluated_count, 4) if evaluated_count else 0.0,
        "recall_at_10": round(r_at_10_sum / evaluated_count, 4) if evaluated_count else 0.0,
        "mrr_at_10": round(mrr_at_10_sum / evaluated_count, 4) if evaluated_count else 0.0,
        "canonical_full_corpus_status": "BLOCKED",
        "canonical_full_corpus_missing": "Canonical 5.23M Wikipedia passage archive (hotpot_corpus.tsv, ~2.5 GB)",
        "configuration": {
            "retriever": "TrustAwareRetriever (TF-IDF + Lexical Overlap)",
            "evaluation_scope": "Distractor candidate re-ranking (10 candidate passages per query)",
            "corpus_mode": "local_distractor_candidates",
        },
    }

    return metrics, predictions


def evaluate_msmarco_retrieval(
    parquet_path: Path,
    limit: Optional[int] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Evaluate candidate reranking on MS MARCO v1.1 validation split (10,047 queries)."""
    logger.info("Evaluating MS MARCO candidate retrieval from %s...", parquet_path.name)
    df = pd.read_parquet(parquet_path)
    if limit:
        df = df.iloc[:limit]

    r_at_1_sum = 0.0
    r_at_5_sum = 0.0
    r_at_10_sum = 0.0
    mrr_at_10_sum = 0.0

    predictions: List[Dict[str, Any]] = []
    skipped_queries: List[Dict[str, Any]] = []

    t0 = time.time()
    for idx, row in df.iterrows():
        qid = str(row["query_id"])
        q = str(row["query"])
        passages = row["passages"]["passage_text"]
        is_sel = row["passages"]["is_selected"]

        gold_indices = {f"p_{j}" for j, sel in enumerate(is_sel) if sel == 1}
        if not gold_indices:
            skipped_queries.append({"query_id": qid, "reason": "No relevant passage selected (is_selected all 0)"})
            continue

        docs = [
            EvidenceDocument(
                doc_id=f"p_{j}",
                text=p_text,
                source_dataset="ms_marco",
                source_id=qid,
                provenance="ms_marco",
            )
            for j, p_text in enumerate(passages)
        ]

        retriever = TrustAwareRetriever(docs)
        candidates = retriever.retrieve_candidates(q, top_n=10)
        retrieved_ids = [d.doc_id for d, _ in candidates]

        hits_1 = len(gold_indices.intersection(retrieved_ids[:1]))
        hits_5 = len(gold_indices.intersection(retrieved_ids[:5]))
        hits_10 = len(gold_indices.intersection(retrieved_ids[:10]))

        r1 = hits_1 / len(gold_indices)
        r5 = hits_5 / len(gold_indices)
        r10 = hits_10 / len(gold_indices)

        mrr = 0.0
        for rank, rid in enumerate(retrieved_ids[:10], start=1):
            if rid in gold_indices:
                mrr = 1.0 / rank
                break

        r_at_1_sum += r1
        r_at_5_sum += r5
        r_at_10_sum += r10
        mrr_at_10_sum += mrr

        predictions.append({
            "query_id": qid,
            "query": q,
            "gold_passage_ids": sorted(list(gold_indices)),
            "candidate_corpus_size": len(docs),
            "retrieved_top10": retrieved_ids,
            "recall_at_1": round(r1, 4),
            "recall_at_5": round(r5, 4),
            "recall_at_10": round(r10, 4),
            "mrr_at_10": round(mrr, 4),
        })

    elapsed = time.time() - t0
    evaluated_count = len(predictions)

    metrics = {
        "dataset_name": "ms_marco",
        "split": "validation",
        "evaluated_queries": evaluated_count,
        "skipped_queries": len(skipped_queries),
        "runtime_seconds": round(elapsed, 2),
        "queries_per_second": round(evaluated_count / elapsed, 1) if elapsed else 0.0,
        "recall_at_1": round(r_at_1_sum / evaluated_count, 4) if evaluated_count else 0.0,
        "recall_at_5": round(r_at_5_sum / evaluated_count, 4) if evaluated_count else 0.0,
        "recall_at_10": round(r_at_10_sum / evaluated_count, 4) if evaluated_count else 0.0,
        "mrr_at_10": round(mrr_at_10_sum / evaluated_count, 4) if evaluated_count else 0.0,
        "canonical_full_corpus_status": "BLOCKED",
        "canonical_full_corpus_missing": "Canonical 8.84M passage collection (collection.tsv / collection.tar.gz ~3.2 GB) and official qrels.dev.small.tsv",
        "configuration": {
            "retriever": "TrustAwareRetriever (TF-IDF + Lexical Overlap)",
            "evaluation_scope": "Candidate search snippet re-ranking (6 to 10 candidates per query)",
            "corpus_mode": "local_candidate_snippets",
        },
    }

    return metrics, predictions


def main() -> None:
    parser = argparse.ArgumentParser(description="Track 1 Step 2.2 Corrected Benchmark Evaluator")
    parser.add_argument("--limit-g3", type=int, default=None, help="Limit G3 evaluation records for quick smoke tests")
    parser.add_argument("--limit-retrieval", type=int, default=None, help="Limit retrieval queries for quick smoke tests")
    parser.add_argument("--skip-retrieval", action="store_true", help="Skip retrieval rerun if already verified")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "reports/research_completion/track02_step02_2_corrected_baselines",
        help="Target output directory",
    )
    args = parser.parse_args()

    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    base_data_dir = REPO_ROOT / "data"
    ragtruth_test = base_data_dir / "processed" / "ragtruth" / "test.jsonl"
    halueval_test = base_data_dir / "processed" / "halueval" / "test.jsonl"
    hotpotqa_val = base_data_dir / "raw" / "hotpotqa" / "hotpotqa_val_distractor.parquet"
    msmarco_val = base_data_dir / "raw" / "ms_marco" / "ms_marco_val_v1.1.parquet"

    # Preflight assertion
    for p in (ragtruth_test, halueval_test, hotpotqa_val, msmarco_val):
        if not p.exists():
            logger.error("Required dataset file missing: %s", p)
            sys.exit(1)

    logger.info("Initializing verifier configurations...")
    # Effective Configurations
    effective_configs = {
        "no_verification": {
            "policy": "pass_through_always_accept",
            "description": "Baseline: always certifes response as SUPPORTED without evidence checking.",
        },
        "default_g3": {
            "enabled": True,
            "min_support_coverage": 0.65,
            "min_relevance_for_check": 0.10,
            "strict_numeric_matching": True,
            "strict_negation_check": True,
            "enable_query_consistency": False,
        },
        "strict_g3": {
            "enabled": True,
            "min_support_coverage": 0.80,
            "min_relevance_for_check": 0.10,
            "strict_numeric_matching": True,
            "strict_negation_check": True,
            "enable_query_consistency": False,
        },
    }

    # Baseline 2: Default Production G3 Verifier (min_support_coverage = 0.65)
    default_config = VerificationConfig(
        enable_query_consistency=False,
        min_support_coverage=0.65,
    )
    default_verifier = OutputEvidenceVerifier(default_config)

    # Baseline 3: Strict Threshold G3 Verifier (min_support_coverage = 0.80)
    strict_config = VerificationConfig(
        enable_query_consistency=False,
        min_support_coverage=0.80,
    )
    strict_verifier = OutputEvidenceVerifier(strict_config)

    # -------------------------------------------------------------------------
    # 1. Evaluate RAGTruth (Test Split: 2,700 records) - All 3 modes
    # -------------------------------------------------------------------------
    logger.info("--- Evaluating RAGTruth Test Split (2,700 records) ---")
    metrics_rt_none, preds_rt_none = evaluate_g3_split(
        "ragtruth", ragtruth_test, None, baseline_mode="no_verification",
        effective_config=effective_configs["no_verification"], limit=args.limit_g3,
    )
    metrics_rt_default, preds_rt_default = evaluate_g3_split(
        "ragtruth", ragtruth_test, default_verifier, baseline_mode="default_g3",
        effective_config=effective_configs["default_g3"], limit=args.limit_g3,
    )
    metrics_rt_strict, preds_rt_strict = evaluate_g3_split(
        "ragtruth", ragtruth_test, strict_verifier, baseline_mode="strict_g3",
        effective_config=effective_configs["strict_g3"], limit=args.limit_g3,
    )

    # -------------------------------------------------------------------------
    # 2. Evaluate HaluEval (Test Split: 3,000 records) - All 3 modes
    # -------------------------------------------------------------------------
    logger.info("--- Evaluating HaluEval Test Split (3,000 records) ---")
    metrics_he_none, preds_he_none = evaluate_g3_split(
        "halueval", halueval_test, None, baseline_mode="no_verification",
        effective_config=effective_configs["no_verification"], limit=args.limit_g3,
    )
    metrics_he_default, preds_he_default = evaluate_g3_split(
        "halueval", halueval_test, default_verifier, baseline_mode="default_g3",
        effective_config=effective_configs["default_g3"], limit=args.limit_g3,
    )
    metrics_he_strict, preds_he_strict = evaluate_g3_split(
        "halueval", halueval_test, strict_verifier, baseline_mode="strict_g3",
        effective_config=effective_configs["strict_g3"], limit=args.limit_g3,
    )

    # -------------------------------------------------------------------------
    # 3. Evaluate Retrieval (or copy verified Step 2.1 results if skip_retrieval)
    # -------------------------------------------------------------------------
    step2_dir = REPO_ROOT / "reports/research_completion/track02_baseline_evaluation"
    if args.skip_retrieval and (step2_dir / "predictions_hotpotqa_retrieval.jsonl").exists():
        logger.info("Preserving verified Step 2.1 retrieval artifacts...")
        with open(step2_dir / "metrics_hotpotqa.json") as f:
            metrics_hp = json.load(f)
        with open(step2_dir / "metrics_msmarco.json") as f:
            metrics_ms = json.load(f)
        preds_hp = None
        preds_ms = None
        shutil.copy2(step2_dir / "predictions_hotpotqa_retrieval.jsonl", out_dir / "predictions_hotpotqa_retrieval.jsonl")
        shutil.copy2(step2_dir / "predictions_msmarco_retrieval.jsonl", out_dir / "predictions_msmarco_retrieval.jsonl")
    else:
        logger.info("--- Evaluating HotpotQA Validation Split (7,405 queries) ---")
        metrics_hp, preds_hp = evaluate_hotpotqa_retrieval(hotpotqa_val, limit=args.limit_retrieval)
        logger.info("--- Evaluating MS MARCO Validation Split (10,047 queries) ---")
        metrics_ms, preds_ms = evaluate_msmarco_retrieval(msmarco_val, limit=args.limit_retrieval)

    # -------------------------------------------------------------------------
    # 4. Persist Predictions & Metric Summaries
    # -------------------------------------------------------------------------
    logger.info("Saving predictions and metric summaries to %s...", out_dir)

    def write_jsonl(path: Path, items: List[Dict[str, Any]]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def write_json(path: Path, data: Any) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # Per-example predictions for all 3 modes
    write_jsonl(out_dir / "predictions_ragtruth_no_verification.jsonl", preds_rt_none)
    write_jsonl(out_dir / "predictions_ragtruth_default.jsonl", preds_rt_default)
    write_jsonl(out_dir / "predictions_ragtruth_strict.jsonl", preds_rt_strict)

    write_jsonl(out_dir / "predictions_halueval_no_verification.jsonl", preds_he_none)
    write_jsonl(out_dir / "predictions_halueval_default.jsonl", preds_he_default)
    write_jsonl(out_dir / "predictions_halueval_strict.jsonl", preds_he_strict)

    if preds_hp is not None:
        write_jsonl(out_dir / "predictions_hotpotqa_retrieval.jsonl", preds_hp)
    if preds_ms is not None:
        write_jsonl(out_dir / "predictions_msmarco_retrieval.jsonl", preds_ms)

    # Corrected metrics comprehensive file
    corrected_metrics = {
        "metadata": {
            "evaluation_task": "Track 1, Step 2.2: Corrected Baseline Re-evaluation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "repo_commit": "aba5cc9d8369f3d7a69e6fd7e81bc055173dde61",
        },
        "ragtruth": {
            "no_verification": metrics_rt_none,
            "default_g3": metrics_rt_default,
            "strict_g3": metrics_rt_strict,
        },
        "halueval": {
            "no_verification": metrics_he_none,
            "default_g3": metrics_he_default,
            "strict_g3": metrics_he_strict,
        },
        "retrieval": {
            "hotpotqa": metrics_hp,
            "ms_marco": metrics_ms,
        },
    }
    write_json(out_dir / "corrected_metrics.json", corrected_metrics)
    write_json(out_dir / "effective_configurations.json", effective_configs)

    logger.info("Evaluation completed successfully! All artifacts written to %s.", out_dir)


if __name__ == "__main__":
    main()
