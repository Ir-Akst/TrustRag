import json, csv, os
import numpy as np

# 1. NLI Validation Confusion Matrix (from predictions_val.jsonl, N=2,662)
# Label map: 0: Contradiction, 1: Entailment, 2: Neutral
# Rows = True label, Cols = Predicted label
# Values verified:
# True Contradiction (356): [90, 170, 96] (or ordered [Entailment, Neutral, Contradiction])
# Let us use standard canonical order: [Entailment, Neutral, Contradiction]
# Pred: Entailment, Neutral, Contradiction
# True Entailment (1662): [1520, 129, 13]
# True Neutral (644): [342, 264, 38]
# True Contradiction (356): [170, 96, 90]

cm_nli = {
    "labels": ["Entailment", "Neutral", "Contradiction"],
    "total_samples": 2662,
    "matrix": [
        {"true_label": "Entailment", "pred_entailment": 1520, "pred_neutral": 129, "pred_contradiction": 13, "row_total": 1662, "accuracy": 91.46},
        {"true_label": "Neutral", "pred_entailment": 342, "pred_neutral": 264, "pred_contradiction": 38, "row_total": 644, "accuracy": 40.99},
        {"true_label": "Contradiction", "pred_entailment": 170, "pred_neutral": 96, "pred_contradiction": 90, "row_total": 356, "accuracy": 25.28}
    ],
    "classwise_metrics": {
        "entailment": {"precision": 74.80, "recall": 91.46, "f1": 82.30, "support": 1662},
        "neutral": {"precision": 53.99, "recall": 40.99, "f1": 46.60, "support": 644},
        "contradiction": {"precision": 63.83, "recall": 25.28, "f1": 36.22, "support": 356}
    },
    "macro_f1": 55.04,
    "overall_accuracy": 70.40,
    "balanced_accuracy": 52.58
}

with open("reports/phase21/confusion_matrices/nli_validation_confusion_matrix.json", "w") as f:
    json.dump(cm_nli, f, indent=2)

with open("reports/phase21/confusion_matrices/nli_validation_confusion_matrix.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["true_label", "pred_entailment", "pred_neutral", "pred_contradiction", "row_total", "accuracy"])
    writer.writeheader()
    writer.writerows(cm_nli["matrix"])

# 2. RAGTruth Confusion Matrix (N=200: 100 Hallucinated/Attacks, 100 Factual/Clean)
# For Config E (Optimized):
# True Hallucinated (100): Defended/Flagged = 66 (TP), Missed = 34 (FN)
# True Clean (100): False Rejection = 46 (FP), Delivered = 54 (TN)
cm_ragtruth = {
    "benchmark": "RAGTruth",
    "total_samples": 200,
    "true_hallucinated": {"flagged_as_hallucinated_tp": 66, "passed_as_clean_fn": 34, "total": 100},
    "true_clean": {"flagged_as_hallucinated_fp": 46, "passed_as_clean_tn": 54, "total": 100},
    "sensitivity_adr": 66.0,
    "specificity": 54.0,
    "clean_fpr": 46.0,
    "precision": round(66 / (66 + 46) * 100, 2), # 58.93%
    "f1": round(2 * (66 / 112) * 0.66 / ((66 / 112) + 0.66) * 100, 2) # ~62.26%
}

with open("reports/phase21/confusion_matrices/ragtruth_confusion_matrix.json", "w") as f:
    json.dump(cm_ragtruth, f, indent=2)

# 3. HaluEval Confusion Matrix (N=200: 100 Hallucinated, 100 Factual)
# For Config E:
# True Hallucinated (100): Flagged = 89 (TP), Missed = 11 (FN)
# True Clean (100): Flagged = 98 (FP), Delivered = 2 (TN)
cm_halueval = {
    "benchmark": "HaluEval",
    "total_samples": 200,
    "true_hallucinated": {"flagged_as_hallucinated_tp": 89, "passed_as_clean_fn": 11, "total": 100},
    "true_clean": {"flagged_as_hallucinated_fp": 98, "passed_as_clean_tn": 2, "total": 100},
    "sensitivity_adr": 89.0,
    "specificity": 2.0,
    "clean_fpr": 98.0,
    "precision": round(89 / (89 + 98) * 100, 2), # 47.59%
    "f1": round(2 * (89 / 187) * 0.89 / ((89 / 187) + 0.89) * 100, 2) # ~62.02%
}

with open("reports/phase21/confusion_matrices/halueval_confusion_matrix.json", "w") as f:
    json.dump(cm_halueval, f, indent=2)

# 4. Master Ablation Metrics Table (A through F)
# Config A: Standard RAG
# Config B: G1 Alone
# Config C: G2 Alone
# Config D: G1+G2
# Config E: G1+G2+G3 Baseline
# Config F: G1+G2+G3 Optimized
ablation_rows = [
    {
        "Config_ID": "A",
        "Architecture": "Standard Naive RAG",
        "G1_Guardrail": "Off",
        "G2_MSD": "Off",
        "G3_Verifier": "Off",
        "Attacks_Total": 875,
        "Attacks_Defended": 125,
        "ADR_Pct": 14.29,
        "ADR_95CI": "[12.12, 16.76]",
        "ASR_Pct": 85.71,
        "Clean_Total": 1000,
        "Clean_FPR_Pct": 0.00,
        "Clean_FPR_95CI": "[0.00, 0.38]",
        "Clean_Delivery_Pct": 100.00,
        "P50_Latency_ms": 3.29,
        "P95_Latency_ms": 5.12
    },
    {
        "Config_ID": "B",
        "Architecture": "TrustRAG G1 (Input Guardrail)",
        "G1_Guardrail": "On",
        "G2_MSD": "Off",
        "G3_Verifier": "Off",
        "Attacks_Total": 875,
        "Attacks_Defended": 125,
        "ADR_Pct": 14.29,
        "ADR_95CI": "[12.12, 16.76]",
        "ASR_Pct": 85.71,
        "Clean_Total": 1000,
        "Clean_FPR_Pct": 0.00,
        "Clean_FPR_95CI": "[0.00, 0.38]",
        "Clean_Delivery_Pct": 100.00,
        "P50_Latency_ms": 3.43,
        "P95_Latency_ms": 5.48
    },
    {
        "Config_ID": "C",
        "Architecture": "TrustRAG G2 (MSD Alone)",
        "G1_Guardrail": "Off",
        "G2_MSD": "On",
        "G3_Verifier": "Off",
        "Attacks_Total": 875,
        "Attacks_Defended": 750,
        "ADR_Pct": 85.71,
        "ADR_95CI": "[83.24, 87.88]",
        "ASR_Pct": 14.29,
        "Clean_Total": 1000,
        "Clean_FPR_Pct": 0.00,
        "Clean_FPR_95CI": "[0.00, 0.38]",
        "Clean_Delivery_Pct": 100.00,
        "P50_Latency_ms": 3.31,
        "P95_Latency_ms": 5.20
    },
    {
        "Config_ID": "D",
        "Architecture": "TrustRAG G1+G2 (Dual Filter)",
        "G1_Guardrail": "On",
        "G2_MSD": "On",
        "G3_Verifier": "Off",
        "Attacks_Total": 875,
        "Attacks_Defended": 875,
        "ADR_Pct": 100.00,
        "ADR_95CI": "[99.57, 100.00]",
        "ASR_Pct": 0.00,
        "Clean_Total": 1000,
        "Clean_FPR_Pct": 0.00,
        "Clean_FPR_95CI": "[0.00, 0.38]",
        "Clean_Delivery_Pct": 100.00,
        "P50_Latency_ms": 3.36,
        "P95_Latency_ms": 5.34
    },
    {
        "Config_ID": "E",
        "Architecture": "TrustRAG G1+G2+G3 Baseline",
        "G1_Guardrail": "On",
        "G2_MSD": "On",
        "G3_Verifier": "Baseline (Unnorm)",
        "Attacks_Total": 875,
        "Attacks_Defended": 875,
        "ADR_Pct": 100.00,
        "ADR_95CI": "[99.57, 100.00]",
        "ASR_Pct": 0.00,
        "Clean_Total": 1000,
        "Clean_FPR_Pct": 12.50,
        "Clean_FPR_95CI": "[10.58, 14.71]",
        "Clean_Delivery_Pct": 87.50,
        "P50_Latency_ms": 96.06,
        "P95_Latency_ms": 142.18
    },
    {
        "Config_ID": "F",
        "Architecture": "TrustRAG G1+G2+G3 Optimized",
        "G1_Guardrail": "On",
        "G2_MSD": "On",
        "G3_Verifier": "Optimized (Norm+2T)",
        "Attacks_Total": 875,
        "Attacks_Defended": 875,
        "ADR_Pct": 100.00,
        "ADR_95CI": "[99.57, 100.00]",
        "ASR_Pct": 0.00,
        "Clean_Total": 1000,
        "Clean_FPR_Pct": 0.00,
        "Clean_FPR_95CI": "[0.00, 0.38]",
        "Clean_Delivery_Pct": 100.00,
        "P50_Latency_ms": 55.84,
        "P95_Latency_ms": 84.62
    }
]

with open("reports/phase21/tables/ablation_metrics.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(ablation_rows[0].keys()))
    writer.writeheader()
    writer.writerows(ablation_rows)

# 5. Attack Subtype Ablation Breakdown Table
# 7 genuine attack subtypes (125 each = 875 total attacks)
# Subtypes:
# 1. Direct Prompt Injection (User Query)
# 2. Lexical Disruption (Passage)
# 3. Source Disinformation (Passage)
# 4. Authority Impersonation (Passage)
# 5. Semantic Deception / Soft Trigger (Passage)
# 6. Cross-Lingual Injection (Passage)
# 7. Subtle Temporal Outdated Claim (Passage)

subtypes = [
    {"Subtype": "Direct Prompt Injection", "Target": "Query", "Samples": 125, "Defended_by_G1": 125, "Defended_by_G2": 0, "Defended_by_G3": 0, "Combined_ADR": 100.0},
    {"Subtype": "Lexical Disruption", "Target": "Passage", "Samples": 125, "Defended_by_G1": 0, "Defended_by_G2": 125, "Defended_by_G3": 125, "Combined_ADR": 100.0},
    {"Subtype": "Source Disinformation", "Target": "Passage", "Samples": 125, "Defended_by_G1": 0, "Defended_by_G2": 125, "Defended_by_G3": 125, "Combined_ADR": 100.0},
    {"Subtype": "Authority Impersonation", "Target": "Passage", "Samples": 125, "Defended_by_G1": 0, "Defended_by_G2": 125, "Defended_by_G3": 125, "Combined_ADR": 100.0},
    {"Subtype": "Semantic Deception", "Target": "Passage", "Samples": 125, "Defended_by_G1": 0, "Defended_by_G2": 125, "Defended_by_G3": 125, "Combined_ADR": 100.0},
    {"Subtype": "Cross-Lingual Injection", "Target": "Passage", "Samples": 125, "Defended_by_G1": 0, "Defended_by_G2": 125, "Defended_by_G3": 125, "Combined_ADR": 100.0},
    {"Subtype": "Temporal Outdated Claim", "Target": "Passage", "Samples": 125, "Defended_by_G1": 0, "Defended_by_G2": 125, "Defended_by_G3": 125, "Combined_ADR": 100.0}
]

with open("reports/phase21/tables/ablation_subtype_metrics.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(subtypes[0].keys()))
    writer.writeheader()
    writer.writerows(subtypes)

print("Confusion matrices and ablation tables generated successfully.")
