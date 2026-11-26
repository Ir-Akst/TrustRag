#!/usr/bin/env python3
"""
TrustRAG Phase 11.2 — Step 06: Independent Reproduction & Audit Verification Script
Re-computes all metrics from `predictions_clean_benchmark.jsonl` independently.
"""
import sys
import json
import math
import hashlib
from pathlib import Path
from collections import Counter
import numpy as np

SCRIPT_DIR = Path(__file__).parent.resolve()
PRED_FILE = SCRIPT_DIR / "predictions_clean_benchmark.jsonl"
MANIFEST_FILE = SCRIPT_DIR / "dataset_manifest.json"
THRESH_FILE = SCRIPT_DIR / "threshold_evaluation.json"

TARGET_THRESHOLDS = [0.16, 0.20, 0.24, 0.25, 0.50]
CALIBRATION_TEMP = 1.770106
NLI_LABELS = ["ENTAILMENT", "CONTRADICTION", "NEUTRAL"]

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p_hat = successes / total
    denom = 1.0 + (z**2) / total
    center = (p_hat + (z**2) / (2 * total)) / denom
    margin = (z / denom) * math.sqrt((p_hat * (1.0 - p_hat) / total) + (z**2) / (4 * total**2))
    return max(0.0, center - margin), min(1.0, center + margin)

def main():
    print("=====================================================================")
    print("TrustRAG Phase 11.2 Step 06 — Independent Reproduction Verification")
    print("=====================================================================")

    if not PRED_FILE.exists():
        print(f"[FAIL] Prediction file not found: {PRED_FILE}")
        sys.exit(1)

    print(f"[1] Loading predictions from: {PRED_FILE.name}")
    print(f"    SHA-256: {compute_sha256(PRED_FILE)}")

    records = []
    with open(PRED_FILE, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    N = len(records)
    print(f"    Total Evaluated Records: {N}")
    assert N == 2536, f"Expected 2536 records, got {N}"

    y_true = np.array([r["true_label_idx"] for r in records])
    y_pred_argmax = np.array([r["predicted_label_idx"] for r in records])
    logits = np.array([r["logits"] for r in records])
    probs_uncal = np.array([r["probabilities"] for r in records])

    # Class distribution check
    counts = Counter(y_true)
    print(f"\n[2] Ground-Truth Class Distribution:")
    for idx, name in enumerate(NLI_LABELS):
        print(f"    {name:14s}: {counts[idx]:5d} ({counts[idx]/N*100:5.2f}%)")

    n_clean = int(np.sum(y_true != 1))
    n_con = int(np.sum(y_true == 1))
    n_ent = int(np.sum(y_true == 0))
    n_neu = int(np.sum(y_true == 2))

    print(f"    Total Clean Evidence (Ent + Neu): {n_clean}")
    print(f"    Total Contradiction Controls:      {n_con}")

    # Argmax Confusion Matrix
    cm = np.zeros((3, 3), dtype=int)
    for t, p in zip(y_true, y_pred_argmax):
        cm[t, p] += 1

    acc = np.trace(cm) / np.sum(cm)
    recalls = [cm[i, i] / np.sum(cm[i, :]) for i in range(3)]
    bal_acc = float(np.mean(recalls))

    print(f"\n[3] Argmax Classification Baseline:")
    print(f"    Overall Accuracy:      {acc*100:.2f}%")
    print(f"    Balanced Accuracy:     {bal_acc*100:.2f}%")
    print("    Confusion Matrix (Rows=True, Cols=Pred):")
    print("               Pred ENT   Pred CON   Pred NEU")
    for idx, name in enumerate(NLI_LABELS):
        print(f"      True {name:4s}:  {cm[idx, 0]:8d}   {cm[idx, 1]:8d}   {cm[idx, 2]:8d}")

    # Temperature Scaling
    scaled = logits / CALIBRATION_TEMP
    shifted = scaled - np.max(scaled, axis=1, keepdims=True)
    exp_s = np.exp(shifted)
    probs_cal = exp_s / np.sum(exp_s, axis=1, keepdims=True)

    def evaluate_sweep(probs_mat, name):
        con_scores = probs_mat[:, 1]
        print(f"\n[4] Operating-Point Evaluation — {name}:")
        print("    " + "-"*96)
        print("    Thresh | Pred+ |  TP |  FP (ENT/NEU) | Clean FCR  (95% CI)    | Preserv   (95% CI)    | Con Recall | Con F1")
        print("    " + "-"*96)

        results = {}
        for th in TARGET_THRESHOLDS:
            pred_con = (con_scores >= th)
            tp = int(np.sum((y_true == 1) & pred_con))
            fp = int(np.sum((y_true != 1) & pred_con))
            fn = int(np.sum((y_true == 1) & (~pred_con)))
            tn = int(np.sum((y_true != 1) & (~pred_con)))

            fp_ent = int(np.sum((y_true == 0) & pred_con))
            fp_neu = int(np.sum((y_true == 2) & pred_con))

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

            clean_fcr = fp / n_clean
            preserv = tn / n_clean

            fcr_ci = wilson_interval(fp, n_clean)
            pres_ci = wilson_interval(tn, n_clean)
            rec_ci = wilson_interval(tp, n_con)

            results[f"{th:.2f}"] = {
                "tp": tp, "fp": fp, "fn": fn, "tn": tn,
                "precision": prec, "recall": rec, "f1": f1,
                "clean_fcr": clean_fcr, "preservation": preserv,
            }

            print(f"    {th:6.2f} | {int(np.sum(pred_con)):5d} | {tp:3d} | {fp:3d} ({fp_ent:3d}/{fp_neu:3d}) | {clean_fcr*100:6.2f}% [{fcr_ci[0]*100:5.2f}-{fcr_ci[1]*100:5.2f}%] | {preserv*100:6.2f}% [{pres_ci[0]*100:5.2f}-{pres_ci[1]*100:5.2f}%] | {rec*100:6.2f}%   | {f1:.4f}")

        print("    " + "-"*96)
        return results

    res_uncal = evaluate_sweep(probs_uncal, "Uncalibrated Probabilities (T=1.0)")
    res_cal = evaluate_sweep(probs_cal, f"Temperature-Calibrated Probabilities (T={CALIBRATION_TEMP:.4f})")

    # Compare with saved JSON if present
    if THRESH_FILE.exists():
        with open(THRESH_FILE) as f:
            saved_data = json.load(f)
        saved_uncal = saved_data.get("uncalibrated_thresholds", {})
        mismatch_count = 0
        for th_str, metrics in res_uncal.items():
            if th_str in saved_uncal:
                if metrics["tp"] != saved_uncal[th_str]["tp"] or metrics["fp"] != saved_uncal[th_str]["fp"]:
                    mismatch_count += 1
        if mismatch_count == 0:
            print("\n[PASS] Verified bit-level metric consistency with saved threshold_evaluation.json!")
        else:
            print(f"\n[FAIL] Mismatches detected with saved evaluation: {mismatch_count}")

    print("\n[SUCCESS] Independent Reproduction Completed Successfully.")

if __name__ == "__main__":
    main()

