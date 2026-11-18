#!/usr/bin/env python3
"""TrustRAG Track 2, Step 3.5: Independent Binary Generalization & Robustness Evaluation.

Role: Senior ML Evaluation Engineer & Independent Experimental Auditor
Execution Mode: Strictly Evaluation-Only (Frozen checkpoint, zero training, zero backward passes).
"""

import os
import sys
import time
import json
import math
import hashlib
from pathlib import Path
from typing import Any, Optional
from collections import defaultdict, Counter

# Enforce strict offline execution before any library import
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    confusion_matrix,
    roc_auc_score,
    precision_recall_curve,
    auc,
    brier_score_loss,
)
import psutil

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from tools.training.train_binary_classifier import (
    load_binary_dataset,
    serialize_binary_input,
    LABEL_MAP,
    MANDATORY_FIELDS,
)

CHECKPOINT_PATH = Path("/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000")
BINARY_DATASET_DIR = PROJECT_ROOT / "data/processed/sft_v2/binary"
OUTPUT_DIR = PROJECT_ROOT / "reports/research_completion/track02_step03_5_binary_generalization"
PREDICTIONS_DIR = OUTPUT_DIR / "predictions"


def compute_wilson_ci(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Computes Wilson score confidence interval for a proportion."""
    if n == 0:
        return 0.0, 0.0
    z = 1.95996  # 95%
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return lower, upper


def compute_bootstrap_ci(
    y_true: list[int],
    y_pred: list[int],
    n_resamples: int = 1000,
    seed: int = 42,
) -> dict[str, tuple[float, float]]:
    """Empirical bootstrap confidence intervals for accuracy and macro F1."""
    rng = np.random.RandomState(seed)
    n = len(y_true)
    acc_samples = []
    f1_samples = []
    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)

    for _ in range(n_resamples):
        idxs = rng.randint(0, n, size=n)
        acc_samples.append(accuracy_score(y_true_arr[idxs], y_pred_arr[idxs]))
        f1_samples.append(f1_score(y_true_arr[idxs], y_pred_arr[idxs], average="macro", zero_division=0))

    return {
        "accuracy_ci_95": (float(np.percentile(acc_samples, 2.5)), float(np.percentile(acc_samples, 97.5))),
        "macro_f1_ci_95": (float(np.percentile(f1_samples, 2.5)), float(np.percentile(f1_samples, 97.5))),
    }


def compute_expected_calibration_error(
    y_true: list[int],
    p_pred: list[float],
    n_bins: int = 10,
) -> float:
    """Computes Expected Calibration Error (ECE) with equal-width bins."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total = len(y_true)
    y_true_arr = np.array(y_true)
    p_pred_arr = np.array(p_pred)

    for i in range(n_bins):
        low, high = bin_boundaries[i], bin_boundaries[i + 1]
        mask = (p_pred_arr >= low) & (p_pred_arr < high if i < n_bins - 1 else p_pred_arr <= high)
        n_in_bin = np.sum(mask)
        if n_in_bin > 0:
            bin_acc = np.mean(y_true_arr[mask])
            bin_conf = np.mean(p_pred_arr[mask])
            ece += (n_in_bin / total) * abs(bin_acc - bin_conf)
    return float(ece)


def calculate_comprehensive_metrics(
    y_true: list[int],
    y_pred: list[int],
    p_hallucinated: list[float],
) -> dict[str, Any]:
    """Calculates all mandatory evaluation metrics."""
    total = len(y_true)
    if total == 0:
        return {}

    acc = float(accuracy_score(y_true, y_pred))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    p_per_class = precision_score(y_true, y_pred, average=None, zero_division=0)
    r_per_class = recall_score(y_true, y_pred, average=None, zero_division=0)
    f1_per_class = f1_score(y_true, y_pred, average=None, zero_division=0)

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    # ROC-AUC & PR-AUC
    try:
        roc_auc = float(roc_auc_score(y_true, p_hallucinated))
    except Exception:
        roc_auc = 0.0

    try:
        prec_curve, rec_curve, _ = precision_recall_curve(y_true, p_hallucinated)
        pr_auc = float(auc(rec_curve, prec_curve))
    except Exception:
        pr_auc = 0.0

    # Calibration
    brier = float(brier_score_loss(y_true, p_hallucinated))
    ece = compute_expected_calibration_error(y_true, p_hallucinated, n_bins=10)

    # Confidence distribution
    confs = [max(1.0 - p, p) for p in p_hallucinated]
    correct_confs = [confs[i] for i in range(total) if y_true[i] == y_pred[i]]
    incorrect_confs = [confs[i] for i in range(total) if y_true[i] != y_pred[i]]

    # Confidence intervals
    wilson_acc = compute_wilson_ci(int(sum(yt == yp for yt, yp in zip(y_true, y_pred))), total)
    boot_ci = compute_bootstrap_ci(y_true, y_pred, n_resamples=1000)

    return {
        "sample_count": total,
        "accuracy": acc,
        "accuracy_wilson_ci_95": wilson_acc,
        "accuracy_bootstrap_ci_95": boot_ci["accuracy_ci_95"],
        "balanced_accuracy": bal_acc,
        "macro_f1": macro_f1,
        "macro_f1_bootstrap_ci_95": boot_ci["macro_f1_ci_95"],
        "per_class": {
            "FACTUAL": {
                "precision": float(p_per_class[0]),
                "recall": float(r_per_class[0]),
                "f1": float(f1_per_class[0]),
                "support": tn + fp,
            },
            "HALLUCINATED": {
                "precision": float(p_per_class[1]),
                "recall": float(r_per_class[1]),
                "f1": float(f1_per_class[1]),
                "support": fn + tp,
            },
        },
        "confusion_matrix": {
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp,
        },
        "rates": {
            "false_positive_rate": fpr,
            "false_negative_rate": fnr,
            "hallucination_precision": float(p_per_class[1]),
            "hallucination_recall": float(r_per_class[1]),
        },
        "discrimination": {
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
        },
        "calibration": {
            "brier_score": brier,
            "ece_10bins": ece,
        },
        "confidence": {
            "all": {
                "mean": float(np.mean(confs)),
                "std": float(np.std(confs)),
                "min": float(np.min(confs)),
                "median": float(np.median(confs)),
                "p95": float(np.percentile(confs, 95)),
                "max": float(np.max(confs)),
            },
            "correct": {
                "count": len(correct_confs),
                "mean": float(np.mean(correct_confs)) if correct_confs else 0.0,
                "median": float(np.median(correct_confs)) if correct_confs else 0.0,
            },
            "incorrect": {
                "count": len(incorrect_confs),
                "mean": float(np.mean(incorrect_confs)) if incorrect_confs else 0.0,
                "median": float(np.median(incorrect_confs)) if incorrect_confs else 0.0,
            },
        },
    }


def run_evaluation() -> None:
    print("=" * 80)
    print("TrustRAG Track 2, Step 3.5: Independent Binary Generalization & Robustness Evaluation")
    print("=" * 80)

    # 1. Verification of Checkpoint Integrity
    assert CHECKPOINT_PATH.exists(), f"Checkpoint path not found: {CHECKPOINT_PATH}"
    config_file = CHECKPOINT_PATH / "config.json"
    weights_file = CHECKPOINT_PATH / "model.safetensors"
    tok_file = CHECKPOINT_PATH / "tokenizer.json"
    meta_file = CHECKPOINT_PATH / "training_meta.json"

    file_hashes = {}
    for f in [config_file, weights_file, tok_file, meta_file]:
        with open(f, "rb") as fp:
            file_hashes[f.name] = hashlib.sha256(fp.read()).hexdigest()
        print(f"Verified {f.name}: {file_hashes[f.name]}")

    expected_weights_sha = "472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b"
    assert file_hashes["model.safetensors"] == expected_weights_sha, "Checkpoint weights sha256 mismatch!"

    # 2. Offline Model & Tokenizer Loading
    print("\n[Loading Model & Tokenizer in Offline Mode]")
    t_load_0 = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(str(CHECKPOINT_PATH), local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(str(CHECKPOINT_PATH), local_files_only=True)
    model.eval()
    for param in model.parameters():
        param.requires_grad = False
    t_load = time.perf_counter() - t_load_0
    print(f"Model loaded successfully in {t_load:.2f}s (eval mode, requires_grad=False).")

    # 3. Load Upstream Training & Pilot Validation ID Sets to Guarantee Zero Overlap
    print("\n[Establishing Independent Evaluation Partition]")
    train_records = load_binary_dataset(
        BINARY_DATASET_DIR / "train.jsonl",
        1000,
        strategy="stratified_source_balanced",
    )
    val_records_step342 = load_binary_dataset(
        BINARY_DATASET_DIR / "validation.jsonl",
        200,
        strategy="stratified_source_balanced",
    )
    train_ids = {r["example_id"] for r in train_records}
    val_342_ids = {r["example_id"] for r in val_records_step342}
    print(f"Indexed {len(train_ids)} Step 3.4.2 train IDs and {len(val_342_ids)} Step 3.4.2 validation IDs.")

    # 4. Extract 1,000 Untouched Records from validation.jsonl
    target_per_dataset = 500
    target_per_class = 250
    counts = {"halueval": {"FACTUAL": 0, "HALLUCINATED": 0}, "ragtruth": {"FACTUAL": 0, "HALLUCINATED": 0}}
    eval_records = []
    val_file = BINARY_DATASET_DIR / "validation.jsonl"

    with open(val_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            eid = r["example_id"]
            if eid in train_ids or eid in val_342_ids:
                continue
            src = r["source_dataset"]
            lbl = r["binary_label"]
            if src in counts and counts[src][lbl] < target_per_class:
                eval_records.append(r)
                counts[src][lbl] += 1
            if len(eval_records) >= 1000:
                break

    assert len(eval_records) == 1000, f"Expected 1000 eval records, got {len(eval_records)}"
    eval_ids = {r["example_id"] for r in eval_records}
    assert len(eval_ids.intersection(train_ids)) == 0, "FATAL: Eval records overlap with train records!"
    assert len(eval_ids.intersection(val_342_ids)) == 0, "FATAL: Eval records overlap with Step 3.4.2 validation!"
    print(f"Extracted 1,000 independent evaluation records:")
    print(f"  HaluEval: {counts['halueval']['FACTUAL']} FACTUAL, {counts['halueval']['HALLUCINATED']} HALLUCINATED")
    print(f"  RAGTruth: {counts['ragtruth']['FACTUAL']} FACTUAL, {counts['ragtruth']['HALLUCINATED']} HALLUCINATED")
    print("  Overlap with Train (1,000): 0 (Verified)")
    print("  Overlap with Step 3.4.2 Val (200): 0 (Verified)")

    # 5. Index Rich Upstream Metadata for RAGTruth (Domain, Model, Task, Span Types)
    print("\n[Indexing Upstream Metadata for Fine-Grained Analysis]")
    rt_meta_map = {}
    rt_meta_file = PROJECT_ROOT / "data/processed/ragtruth/train.jsonl"
    with open(rt_meta_file, "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            rt_meta_map[r["record_id"]] = r.get("metadata", {})
    print(f"Indexed {len(rt_meta_map)} RAGTruth metadata entries.")

    # 6. Run Deterministic Inference Pass
    print("\n[Executing Inference Pass on Independent Evaluation Partition]")
    latencies: list[float] = []
    predictions: list[dict[str, Any]] = []

    proc = psutil.Process()
    rss_start = proc.memory_info().rss / (1024 * 1024)
    t_infer_start = time.perf_counter()

    for idx, rec in enumerate(eval_records):
        text_a, text_b = serialize_binary_input(rec)
        t_sample_0 = time.perf_counter()

        with torch.no_grad():
            inputs = tokenizer(
                text_a,
                text_b,
                max_length=128,
                padding="max_length",
                truncation=True,
                return_tensors="pt",
            )
            outputs = model(**inputs)
            logits = outputs.logits[0].cpu()
            probs = torch.softmax(logits, dim=-1).numpy()

        dt = (time.perf_counter() - t_sample_0) * 1000.0  # ms
        latencies.append(dt)

        p_factual = float(probs[0])
        p_hallucinated = float(probs[1])
        pred_label_idx = int(np.argmax(probs))
        pred_label = "HALLUCINATED" if pred_label_idx == 1 else "FACTUAL"
        true_label = rec["binary_label"]
        true_label_idx = LABEL_MAP[true_label]

        # Extract RAGTruth fine-grained metadata
        rt_meta = {}
        halluc_subtype = "N/A"
        if rec["source_dataset"] == "ragtruth":
            rec_id = rec["example_id"].replace("binary_ragtruth_validation_", "")
            rt_meta = rt_meta_map.get(rec_id, {})
            spans = rt_meta.get("hallucination_spans", [])
            span_types = {s.get("label_type") for s in spans}
            if true_label == "HALLUCINATED":
                if any("Conflict" in st for st in span_types):
                    halluc_subtype = "Contradicted"
                elif any("Baseless" in st for st in span_types):
                    halluc_subtype = "Unsupported"
                else:
                    halluc_subtype = "Unspecified_Hallucination"
            else:
                halluc_subtype = "Factual_Grounding"

        pred_record = {
            "example_id": rec["example_id"],
            "source_dataset": rec["source_dataset"],
            "true_label": true_label,
            "true_label_idx": true_label_idx,
            "pred_label": pred_label,
            "pred_label_idx": pred_label_idx,
            "is_correct": bool(pred_label_idx == true_label_idx),
            "p_factual": p_factual,
            "p_hallucinated": p_hallucinated,
            "confidence": float(max(p_factual, p_hallucinated)),
            "latency_ms": dt,
            "task_type": rt_meta.get("task_type", "QA" if rec["source_dataset"] == "halueval" else "Unknown"),
            "generator_model": rt_meta.get("model", "Unknown"),
            "corpus_source": rt_meta.get("source", rec["source_dataset"]),
            "hallucination_subtype": halluc_subtype,
            "question_or_claim_snippet": rec["question_or_claim"][:120],
            "candidate_response_snippet": rec["candidate_response"][:120],
        }
        predictions.append(pred_record)

        if (idx + 1) % 200 == 0 or (idx + 1) == 1000:
            print(f"  Processed {idx + 1}/1000 samples ({((idx + 1) / (time.perf_counter() - t_infer_start)):.1f} samples/s)...")

    total_infer_wall_s = time.perf_counter() - t_infer_start
    rss_end = proc.memory_info().rss / (1024 * 1024)
    vm = psutil.virtual_memory()
    sw = psutil.swap_memory()

    print(f"\nInference completed in {total_infer_wall_s:.2f}s ({len(predictions) / total_infer_wall_s:.2f} samples/sec).")
    print(f"Latency: Median={np.median(latencies):.2f}ms, P95={np.percentile(latencies, 95):.2f}ms, Mean={np.mean(latencies):.2f}ms")
    print(f"Peak RSS: {rss_end:.2f} MB (Delta: +{rss_end - rss_start:.2f} MB), Available RAM: {vm.available / (1024 * 1024):.2f} MB")

    # 7. Partition Predictions and Compute Metrics
    preds_halueval = [p for p in predictions if p["source_dataset"] == "halueval"]
    preds_ragtruth = [p for p in predictions if p["source_dataset"] == "ragtruth"]

    metrics_combined = calculate_comprehensive_metrics(
        [p["true_label_idx"] for p in predictions],
        [p["pred_label_idx"] for p in predictions],
        [p["p_hallucinated"] for p in predictions],
    )
    metrics_halueval = calculate_comprehensive_metrics(
        [p["true_label_idx"] for p in preds_halueval],
        [p["pred_label_idx"] for p in preds_halueval],
        [p["p_hallucinated"] for p in preds_halueval],
    )
    metrics_ragtruth = calculate_comprehensive_metrics(
        [p["true_label_idx"] for p in preds_ragtruth],
        [p["pred_label_idx"] for p in preds_ragtruth],
        [p["p_hallucinated"] for p in preds_ragtruth],
    )

    # 8. Fine-Grained Subgroup Analysis (RAGTruth tasks, generator models, hallucination subtypes)
    # RAGTruth Hallucination Subtypes (Contradicted vs Unsupported)
    halluc_subtypes: dict[str, Any] = {}
    for subtype in ["Contradicted", "Unsupported"]:
        sub_preds = [p for p in preds_ragtruth if p["hallucination_subtype"] == subtype]
        if sub_preds:
            correct = sum(p["is_correct"] for p in sub_preds)
            total_sub = len(sub_preds)
            halluc_subtypes[subtype] = {
                "support": total_sub,
                "correct": correct,
                "recall": float(correct / total_sub),
                "mean_p_hallucinated": float(np.mean([p["p_hallucinated"] for p in sub_preds])),
            }

    # RAGTruth by Task Type
    task_types: dict[str, Any] = {}
    for task in sorted(list({p["task_type"] for p in preds_ragtruth})):
        sub_preds = [p for p in preds_ragtruth if p["task_type"] == task]
        if sub_preds:
            y_t = [p["true_label_idx"] for p in sub_preds]
            y_p = [p["pred_label_idx"] for p in sub_preds]
            task_types[task] = {
                "support": len(sub_preds),
                "accuracy": float(accuracy_score(y_t, y_p)),
                "macro_f1": float(f1_score(y_t, y_p, average="macro", zero_division=0)),
                "factual_count": sum(yt == 0 for yt in y_t),
                "hallucinated_count": sum(yt == 1 for yt in y_t),
            }

    # RAGTruth by Generator Model
    model_types: dict[str, Any] = {}
    for gm in sorted(list({p["generator_model"] for p in preds_ragtruth})):
        sub_preds = [p for p in preds_ragtruth if p["generator_model"] == gm]
        if sub_preds:
            y_t = [p["true_label_idx"] for p in sub_preds]
            y_p = [p["pred_label_idx"] for p in sub_preds]
            model_types[gm] = {
                "support": len(sub_preds),
                "accuracy": float(accuracy_score(y_t, y_p)),
                "macro_f1": float(f1_score(y_t, y_p, average="macro", zero_division=0)),
            }

    # 9. Structure Final Results
    evaluation_results = {
        "status": "COMPLETED",
        "eval_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checkpoint_evaluated": str(CHECKPOINT_PATH),
        "checkpoint_hashes": file_hashes,
        "inference_configuration": {
            "batch_size": 1,
            "max_length": 128,
            "device": "cpu",
            "threads": torch.get_num_threads(),
            "offline_mode": True,
            "decision_threshold": 0.5,
        },
        "performance_telemetry": {
            "total_samples": 1000,
            "wall_clock_seconds": total_infer_wall_s,
            "throughput_samples_per_sec": float(1000 / total_infer_wall_s),
            "latency_ms": {
                "median": float(np.median(latencies)),
                "p95": float(np.percentile(latencies, 95)),
                "mean": float(np.mean(latencies)),
                "min": float(np.min(latencies)),
                "max": float(np.max(latencies)),
            },
            "resources": {
                "peak_rss_mb": float(rss_end),
                "rss_delta_mb": float(rss_end - rss_start),
                "available_ram_mb": float(vm.available / (1024 * 1024)),
                "swap_total_mb": float(sw.total / (1024 * 1024)),
                "swap_used_mb": float(sw.used / (1024 * 1024)),
                "swap_free_mb": float(sw.free / (1024 * 1024)),
            },
        },
        "dataset_provenance": {
            "source_file": str(val_file),
            "total_eval_samples": 1000,
            "halueval_samples": 500,
            "ragtruth_samples": 500,
            "train_set_overlap": 0,
            "step342_val_overlap": 0,
            "test_set_overlap": 0,
            "isolation_verified": True,
        },
        "metrics": {
            "combined": metrics_combined,
            "halueval": metrics_halueval,
            "ragtruth": metrics_ragtruth,
        },
        "subgroup_analysis": {
            "ragtruth_hallucination_subtypes": halluc_subtypes,
            "ragtruth_by_task": task_types,
            "ragtruth_by_generator_model": model_types,
        },
    }

    # 10. Persist Artifacts
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

    # Save predictions
    pred_combined_file = PREDICTIONS_DIR / "predictions_combined.jsonl"
    with open(pred_combined_file, "w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")

    pred_he_file = PREDICTIONS_DIR / "predictions_halueval.jsonl"
    with open(pred_he_file, "w", encoding="utf-8") as f:
        for p in preds_halueval:
            f.write(json.dumps(p) + "\n")

    pred_rt_file = PREDICTIONS_DIR / "predictions_ragtruth.jsonl"
    with open(pred_rt_file, "w", encoding="utf-8") as f:
        for p in preds_ragtruth:
            f.write(json.dumps(p) + "\n")

    results_file = OUTPUT_DIR / "evaluation_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(evaluation_results, f, indent=2)

    print("\n[Evaluation Complete]")
    print(f"Results saved to: {results_file}")
    print(f"Combined Metrics: Acc={metrics_combined['accuracy']*100:.2f}%, BalAcc={metrics_combined['balanced_accuracy']*100:.2f}%, MacroF1={metrics_combined['macro_f1']:.4f}")
    print(f"  HaluEval:       Acc={metrics_halueval['accuracy']*100:.2f}%, BalAcc={metrics_halueval['balanced_accuracy']*100:.2f}%, MacroF1={metrics_halueval['macro_f1']:.4f}")
    print(f"  RAGTruth:       Acc={metrics_ragtruth['accuracy']*100:.2f}%, BalAcc={metrics_ragtruth['balanced_accuracy']*100:.2f}%, MacroF1={metrics_ragtruth['macro_f1']:.4f}")


if __name__ == "__main__":
    run_evaluation()
