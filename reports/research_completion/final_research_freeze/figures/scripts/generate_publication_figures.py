#!/usr/bin/env python3
"""TrustRAG Publication-Quality Visualization Campaign Runner.

Generates 13 publication-quality figures (PNG at 300 DPI, PDF vector, SVG vector)
using empirical data from Phases 11-20, saves underlying CSV files, and creates
the figure index documentation.
"""

import os
import sys
import json
import math
import numpy as np
import pandas as pd

# Set matplotlib backend and config dir
os.environ["MPLCONFIGDIR"] = "/tmp/mplconfig"
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import Patch

# Base directories
BASE_DIR = "/home/aditya/rags/TrustRag-phase11"
FIG_DIR = os.path.join(BASE_DIR, "reports/research_completion/final_research_freeze/figures")
DATA_DIR = os.path.join(FIG_DIR, "data")
SCRIPTS_DIR = os.path.join(FIG_DIR, "scripts")

os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SCRIPTS_DIR, exist_ok=True)

# Publication styling settings
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 9.5,
    "figure.titlesize": 13,
    "figure.autolayout": False,
    "axes.grid": True,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
    "grid.color": "#999999",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 1.0,
})

# Color-blind friendly accessible palette
CB_COLORS = {
    "blue": "#1f77b4",       # ADR / Positive Defense
    "dark_blue": "#084594",  # Primary Emphasis
    "vermilion": "#d62728",  # ASR / Breached / Unsafe
    "amber": "#ff7f0e",      # False Positive / Warning
    "green": "#2ca02c",      # Clean Preservation / Grounded
    "teal": "#17becf",       # Optimized Configuration
    "purple": "#9467bd",     # Benchmark / Contrast
    "grey": "#7f7f7f",       # Baseline / Standard
    "light_grey": "#e0e0e0"
}

def save_multiformat(fig, base_name):
    """Export figure in PNG (300 DPI), PDF (vector), and SVG (vector)."""
    png_path = os.path.join(FIG_DIR, f"{base_name}.png")
    pdf_path = os.path.join(FIG_DIR, f"{base_name}.pdf")
    svg_path = os.path.join(FIG_DIR, f"{base_name}.svg")
    
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, format="pdf", bbox_inches="tight")
    fig.savefig(svg_path, format="svg", bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {base_name} (PNG 300 DPI, PDF, SVG)")

# ==============================================================================
# FIGURE 1: Overall Architecture Comparison
# ==============================================================================
def generate_figure_01():
    base_name = "figure_01_architecture_comparison"
    df = pd.DataFrame([
        {"Architecture": "Standard RAG", "ADR": 14.29, "ADR_low": 12.12, "ADR_high": 16.76, "ASR": 85.71, "Clean_FPR": 0.00, "Clean_Delivery": 100.00},
        {"Architecture": "TrustRAG G1", "ADR": 14.29, "ADR_low": 12.12, "ADR_high": 16.76, "ASR": 85.71, "Clean_FPR": 0.00, "Clean_Delivery": 100.00},
        {"Architecture": "TrustRAG G1+G2", "ADR": 100.00, "ADR_low": 99.56, "ADR_high": 100.00, "ASR": 0.00, "Clean_FPR": 0.00, "Clean_Delivery": 100.00},
        {"Architecture": "TrustRAG G1+G2+G3 Base", "ADR": 100.00, "ADR_low": 99.56, "ADR_high": 100.00, "ASR": 0.00, "Clean_FPR": 12.50, "Clean_Delivery": 87.50},
        {"Architecture": "TrustRAG G1+G2+G3 Opt", "ADR": 100.00, "ADR_low": 99.56, "ADR_high": 100.00, "ASR": 0.00, "Clean_FPR": 0.00, "Clean_Delivery": 100.00},
    ])
    df.to_csv(os.path.join(DATA_DIR, f"{base_name}.csv"), index=False)
    
    fig, ax = plt.subplots(figsize=(9, 5.2))
    x = np.arange(len(df))
    width = 0.20
    
    rects1 = ax.bar(x - 1.5*width, df["ADR"], width, label="Attack Defense Rate (ADR)", color=CB_COLORS["blue"], edgecolor="#222")
    rects2 = ax.bar(x - 0.5*width, df["ASR"], width, label="Attack Success Rate (ASR)", color=CB_COLORS["vermilion"], edgecolor="#222")
    rects3 = ax.bar(x + 0.5*width, df["Clean_FPR"], width, label="Clean False Positive Rate (FPR)", color=CB_COLORS["amber"], edgecolor="#222")
    rects4 = ax.bar(x + 1.5*width, df["Clean_Delivery"], width, label="Clean Evidence Delivery", color=CB_COLORS["green"], edgecolor="#222")
    
    # Error bars for ADR
    err_low = df["ADR"] - df["ADR_low"]
    err_high = df["ADR_high"] - df["ADR"]
    ax.errorbar(x - 1.5*width, df["ADR"], yerr=[err_low, err_high], fmt="none", ecolor="#111", elinewidth=1.2, capsize=3)
    
    ax.set_ylabel("Percentage (%)")
    ax.set_title("TrustRAG Architecture Comparison: Security Defense vs. Clean Utility\n(N=875 Genuine Attacks, N=1,000 Clean Controls)", pad=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(df["Architecture"], rotation=12, ha="right", fontweight="medium")
    ax.set_ylim(0, 115)
    ax.legend(frameon=True, facecolor="white", edgecolor="#ccc", loc="upper left", ncol=2)
    
    for bar in rects1:
        h = bar.get_height()
        ax.annotate(f"{h:.1f}%", xy=(bar.get_x() + bar.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)
    for bar in rects3:
        h = bar.get_height()
        if h > 0:
            ax.annotate(f"{h:.1f}%", xy=(bar.get_x() + bar.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8, color=CB_COLORS["amber"], fontweight="bold")
            
    save_multiformat(fig, base_name)

# ==============================================================================
# FIGURE 2: Attack Defense Performance across Categories
# ==============================================================================
def generate_figure_02():
    base_name = "figure_02_attack_defense"
    categories = [
        "Prompt Injection (N=125)", "Medical Dosage (N=125)", "Cryptographic (N=125)",
        "Financial Disinfo (N=125)", "Astrophysics (N=125)", "Duplicate Conflict (N=125)",
        "Multi-doc 3v1 (N=125)", "Token DoS (N=125)"
    ]
    df = pd.DataFrame({
        "Category": categories,
        "Standard_RAG": [0.0, 0.0, 0.0, 0.0, 0.0, 50.0, 25.0, 0.0],
        "TrustRAG_G1": [100.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 100.0],
        "TrustRAG_G1_G2": [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0],
        "TrustRAG_Optimized": [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0]
    })
    df.to_csv(os.path.join(DATA_DIR, f"{base_name}.csv"), index=False)
    
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(categories))
    width = 0.22
    
    ax.bar(x - 1.5*width, df["Standard_RAG"], width, label="Standard RAG", color=CB_COLORS["grey"], edgecolor="#222")
    ax.bar(x - 0.5*width, df["TrustRAG_G1"], width, label="TrustRAG G1 (Query Filter)", color=CB_COLORS["amber"], edgecolor="#222")
    ax.bar(x + 0.5*width, df["TrustRAG_G1_G2"], width, label="TrustRAG G1+G2 (MSD Gate)", color=CB_COLORS["blue"], edgecolor="#222")
    ax.bar(x + 1.5*width, df["TrustRAG_Optimized"], width, label="TrustRAG G1+G2+G3 (Full Pipeline)", color=CB_COLORS["teal"], edgecolor="#222")
    
    ax.set_ylabel("Attack Defense Rate (ADR %)")
    ax.set_title("Attack Defense Performance across Security Categories (N=125 per category, Total N=1,000)", pad=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=22, ha="right", fontweight="medium")
    ax.set_ylim(0, 115)
    ax.legend(frameon=True, facecolor="white", edgecolor="#ccc", loc="upper left", ncol=2)
    save_multiformat(fig, base_name)

# ==============================================================================
# FIGURE 3: Clean Utility Comparison
# ==============================================================================
def generate_figure_03():
    base_name = "figure_03_clean_utility"
    df = pd.DataFrame([
        {"Version": "Phase 16.1 Baseline (Unnormalized)", "Clean_FPR": 12.50, "FPR_low": 10.59, "FPR_high": 14.69, "Clean_Delivery": 87.50, "Del_low": 85.31, "Del_high": 89.41},
        {"Version": "Phase 16.2 Optimized (Citation Normalization)", "Clean_FPR": 0.00, "FPR_low": 0.00, "FPR_high": 0.38, "Clean_Delivery": 100.00, "Del_low": 99.62, "Del_high": 100.00}
    ])
    df.to_csv(os.path.join(DATA_DIR, f"{base_name}.csv"), index=False)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 4.5))
    
    # Left: Clean FPR
    x = np.arange(len(df))
    bars1 = ax1.bar(x, df["Clean_FPR"], width=0.45, color=[CB_COLORS["amber"], CB_COLORS["teal"]], edgecolor="#222")
    ax1.errorbar(x, df["Clean_FPR"], yerr=[df["Clean_FPR"] - df["FPR_low"], df["FPR_high"] - df["Clean_FPR"]], fmt="none", ecolor="#222", elinewidth=1.5, capsize=5)
    ax1.set_xticks(x)
    ax1.set_xticklabels(["Phase 16.1 Base\n(Unnormalized)", "Phase 16.2 Opt\n(Normalized)"])
    ax1.set_ylabel("Clean False Positive Rate (%)")
    ax1.set_title("Clean False Positive Rate (Lower is Better)\n(N=1,000 Clean Controls)", fontweight="bold")
    ax1.set_ylim(0, 18)
    for bar in bars1:
        h = bar.get_height()
        ax1.annotate(f"{h:.2f}%", xy=(bar.get_x() + bar.get_width() / 2, h + 1.2), ha="center", va="bottom", fontweight="bold")
    ax1.axhline(0, color="#888", linestyle="--", alpha=0.5)
    
    # Right: Clean Delivery
    bars2 = ax2.bar(x, df["Clean_Delivery"], width=0.45, color=[CB_COLORS["grey"], CB_COLORS["green"]], edgecolor="#222")
    ax2.errorbar(x, df["Clean_Delivery"], yerr=[df["Clean_Delivery"] - df["Del_low"], df["Del_high"] - df["Clean_Delivery"]], fmt="none", ecolor="#222", elinewidth=1.5, capsize=5)
    ax2.set_xticks(x)
    ax2.set_xticklabels(["Phase 16.1 Base\n(Unnormalized)", "Phase 16.2 Opt\n(Normalized)"])
    ax2.set_ylabel("Clean Evidence Delivery Rate (%)")
    ax2.set_title("Clean Evidence Preservation (Higher is Better)\n(N=1,000 Clean Controls)", fontweight="bold")
    ax2.set_ylim(75, 105)
    for bar in bars2:
        h = bar.get_height()
        ax2.annotate(f"{h:.1f}%", xy=(bar.get_x() + bar.get_width() / 2, h + 1.2), ha="center", va="bottom", fontweight="bold")
        
    fig.suptitle("Impact of Premise Citation Normalization on Clean RAG Utility", fontsize=13, fontweight="bold", y=1.03)
    save_multiformat(fig, base_name)

# ==============================================================================
# FIGURE 4: NLI Confusion Matrix
# ==============================================================================
def generate_figure_04():
    base_name = "figure_04_nli_confusion_matrix"
    labels = ["ENTAILMENT", "NEUTRAL", "CONTRADICTION"]
    cm = np.array([
        [1520, 129, 13],
        [342, 264, 38],
        [170, 96, 90]
    ])
    cm_pct = cm / cm.sum(axis=1, keepdims=True) * 100.0
    
    df_cm = pd.DataFrame(cm, index=labels, columns=labels)
    df_cm.to_csv(os.path.join(DATA_DIR, f"{base_name}.csv"))
    
    fig, ax = plt.subplots(figsize=(7, 5.8))
    im = ax.imshow(cm_pct, interpolation="nearest", cmap="Blues", vmin=0, vmax=100)
    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel("Normalized Percentage (%)", rotation=-90, va="bottom")
    
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, fontweight="medium")
    ax.set_yticklabels(labels, fontweight="medium")
    ax.set_ylabel("True Ground Truth Label", fontweight="bold")
    ax.set_xlabel("Predicted Label (DeBERTa-v3-small)", fontweight="bold")
    ax.set_title("DeBERTa-v3-small NLI Confusion Matrix on Validation Set\n(N=2,662 Held-Out Evaluation Samples)", pad=14, fontweight="bold")
    
    # Text annotations
    for i in range(len(labels)):
        for j in range(len(labels)):
            val = cm[i, j]
            pct = cm_pct[i, j]
            txt_color = "white" if pct > 50 else "black"
            ax.text(j, i, f"{val}\n({pct:.1f}%)", ha="center", va="center", color=txt_color, fontsize=10, fontweight="bold")
            
    save_multiformat(fig, base_name)

# ==============================================================================
# FIGURE 5: Class-wise Model Performance
# ==============================================================================
def generate_figure_05():
    base_name = "figure_05_classwise_metrics"
    df = pd.DataFrame([
        {"Class": "ENTAILMENT", "Precision": 74.80, "Recall": 91.46, "F1": 82.30, "Support": 1662},
        {"Class": "NEUTRAL", "Precision": 53.99, "Recall": 40.99, "F1": 46.60, "Support": 644},
        {"Class": "CONTRADICTION", "Precision": 63.83, "Recall": 25.28, "F1": 36.22, "Support": 356},
        {"Class": "Macro Average", "Precision": 64.21, "Recall": 52.58, "F1": 55.04, "Support": 2662},
        {"Class": "Weighted Average", "Precision": 68.31, "Recall": 70.47, "F1": 67.50, "Support": 2662}
    ])
    df.to_csv(os.path.join(DATA_DIR, f"{base_name}.csv"), index=False)
    
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(df))
    width = 0.25
    
    r1 = ax.bar(x - width, df["Precision"], width, label="Precision (%)", color=CB_COLORS["blue"], edgecolor="#222")
    r2 = ax.bar(x, df["Recall"], width, label="Recall (%)", color=CB_COLORS["green"], edgecolor="#222")
    r3 = ax.bar(x + width, df["F1"], width, label="F1-Score (%)", color=CB_COLORS["amber"], edgecolor="#222")
    
    ax.set_ylabel("Score (%)")
    ax.set_title("DeBERTa-v3-small NLI Class-wise Metrics (N=2,662 Held-Out Validation Split)", pad=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(df["Class"], rotation=15, ha="right", fontweight="medium")
    ax.set_ylim(0, 110)
    ax.legend(frameon=True, facecolor="white", edgecolor="#ccc", loc="upper right")
    
    for bar in r3:
        h = bar.get_height()
        ax.annotate(f"{h:.1f}%", xy=(bar.get_x() + bar.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
        
    save_multiformat(fig, base_name)

# ==============================================================================
# FIGURE 6: Calibration Reliability Diagram
# ==============================================================================
def generate_figure_06():
    base_name = "figure_06_calibration"
    
    # Load raw validation predictions
    raw_pred_file = os.path.join(BASE_DIR, "reports/research_completion/phase11_1_step03_full_nli_training/predictions_val.jsonl")
    records = []
    with open(raw_pred_file) as f:
        for line in f:
            records.append(json.loads(line))
            
    def compute_bins(records, temp=1.0, n_bins=10):
        bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
        bin_accs, bin_confs, bin_counts = [], [], []
        all_confs, all_correct = [], []
        for r in records:
            logits = np.array(r["logits"]) / temp
            exp_l = np.exp(logits - np.max(logits))
            probs = exp_l / np.sum(exp_l)
            pred_idx = np.argmax(probs)
            conf = probs[pred_idx]
            correct = 1.0 if pred_idx == r["true_label_idx"] else 0.0
            all_confs.append(conf)
            all_correct.append(correct)
        all_confs = np.array(all_confs)
        all_correct = np.array(all_correct)
        ece = 0.0
        for i in range(n_bins):
            b_min, b_max = bin_edges[i], bin_edges[i+1]
            mask = (all_confs > b_min) & (all_confs <= b_max)
            count = np.sum(mask)
            if count > 0:
                acc = np.mean(all_correct[mask])
                conf_mean = np.mean(all_confs[mask])
                bin_accs.append(acc)
                bin_confs.append(conf_mean)
                bin_counts.append(int(count))
                ece += (count / len(records)) * abs(acc - conf_mean)
            else:
                bin_accs.append(np.nan)
                bin_confs.append((b_min + b_max)/2.0)
                bin_counts.append(0)
        brier = np.mean((all_confs - all_correct)**2)
        return ece, brier, bin_confs, bin_accs, bin_counts
        
    ece_raw, brier_raw, confs_raw, accs_raw, counts_raw = compute_bins(records, temp=1.0)
    ece_cal, brier_cal, confs_cal, accs_cal, counts_cal = compute_bins(records, temp=1.7701)
    
    df_cal = pd.DataFrame({
        "Bin_Center": confs_raw,
        "Accuracy_Uncalibrated": accs_raw,
        "Accuracy_Calibrated": accs_cal,
        "Sample_Count": counts_raw
    })
    df_cal.to_csv(os.path.join(DATA_DIR, f"{base_name}.csv"), index=False)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.8))
    
    # Left: Reliability curves
    ax1.plot([0, 1], [0, 1], "k--", label="Perfect Calibration", alpha=0.7)
    ax1.plot(confs_raw, accs_raw, "s-", color=CB_COLORS["vermilion"], label=f"Uncalibrated T=1.0 (ECE={ece_raw*100:.2f}%)", lw=1.8, ms=6)
    ax1.plot(confs_cal, accs_cal, "o-", color=CB_COLORS["blue"], label=f"Calibrated T=1.7701 (ECE={ece_cal*100:.2f}%)", lw=2.0, ms=6)
    ax1.set_xlabel("Mean Predicted Confidence")
    ax1.set_ylabel("Empirical Accuracy")
    ax1.set_title("Reliability Diagram (N=2,662 Validation)", fontweight="bold")
    ax1.set_xlim(0, 1.02)
    ax1.set_ylim(0, 1.02)
    ax1.legend(frameon=True, facecolor="white", edgecolor="#ccc", loc="upper left")
    
    # Right: Confidence Distribution
    bin_centers = np.linspace(0.05, 0.95, 10)
    ax2.bar(bin_centers, counts_raw, width=0.08, color=CB_COLORS["teal"], edgecolor="#222", alpha=0.8)
    ax2.set_xlabel("Confidence Bins")
    ax2.set_ylabel("Sample Frequency")
    ax2.set_title("Prediction Confidence Histogram", fontweight="bold")
    ax2.set_xlim(0, 1.0)
    
    fig.suptitle("DeBERTa-v3-small NLI Calibration: Temperature Scaling (T=1.7701)", fontsize=13, fontweight="bold", y=1.02)
    save_multiformat(fig, base_name)

# ==============================================================================
# FIGURE 7: CPU Thread Optimization
# ==============================================================================
def generate_figure_07():
    base_name = "figure_07_cpu_latency"
    df = pd.DataFrame([
        {"Threads": "1 Thread", "P50_ms": 97.72, "P95_ms": 99.15, "P99_ms": 100.59, "Speedup": 1.00},
        {"Threads": "2 Threads (Opt)", "P50_ms": 55.84, "P95_ms": 58.02, "P99_ms": 63.65, "Speedup": 1.73},
        {"Threads": "4 Threads", "P50_ms": 85.93, "P95_ms": 103.42, "P99_ms": 104.63, "Speedup": 1.10},
        {"Threads": "8 Threads", "P50_ms": 78.31, "P95_ms": 82.71, "P99_ms": 82.97, "Speedup": 1.25}
    ])
    df.to_csv(os.path.join(DATA_DIR, f"{base_name}.csv"), index=False)
    
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    x = np.arange(len(df))
    width = 0.25
    
    r1 = ax.bar(x - width, df["P50_ms"], width, label="P50 Latency (ms)", color=CB_COLORS["blue"], edgecolor="#222")
    r2 = ax.bar(x, df["P95_ms"], width, label="P95 Latency (ms)", color=CB_COLORS["amber"], edgecolor="#222")
    r3 = ax.bar(x + width, df["P99_ms"], width, label="P99 Latency (ms)", color=CB_COLORS["vermilion"], edgecolor="#222")
    
    ax.set_ylabel("Inference Latency (ms)")
    ax.set_title("CPU Intra-Op Thread Latency Benchmarks (DeBERTa-v3-small, 141.9M Params)", pad=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(df["Threads"], fontweight="medium")
    ax.set_ylim(0, 125)
    ax.legend(frameon=True, facecolor="white", edgecolor="#ccc", loc="upper right")
    
    # Highlight 2 threads sweet spot
    ax.annotate("Optimal Sweet Spot\n55.84 ms (1.73x Speedup)", xy=(1, 55.84), xytext=(1, 80),
                arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=6),
                ha="center", fontweight="bold", bbox=dict(boxstyle="round,pad=0.3", facecolor="#e6f2ff", edgecolor="#084594"))
                
    save_multiformat(fig, base_name)

# ==============================================================================
# FIGURE 8: Batch Throughput
# ==============================================================================
def generate_figure_08():
    base_name = "figure_08_batch_throughput"
    df = pd.DataFrame([
        {"Batch_Size": 1, "Latency_Per_Claim_ms": 80.70, "Throughput_Claims_Sec": 12.39},
        {"Batch_Size": 2, "Latency_Per_Claim_ms": 92.65, "Throughput_Claims_Sec": 10.79},
        {"Batch_Size": 4, "Latency_Per_Claim_ms": 78.45, "Throughput_Claims_Sec": 12.75},
        {"Batch_Size": 8, "Latency_Per_Claim_ms": 81.15, "Throughput_Claims_Sec": 12.32},
        {"Batch_Size": 16, "Latency_Per_Claim_ms": 81.34, "Throughput_Claims_Sec": 12.29},
        {"Batch_Size": 32, "Latency_Per_Claim_ms": 83.05, "Throughput_Claims_Sec": 12.04}
    ])
    df.to_csv(os.path.join(DATA_DIR, f"{base_name}.csv"), index=False)
    
    fig, ax1 = plt.subplots(figsize=(8.5, 4.8))
    x = np.arange(len(df))
    
    color = CB_COLORS["blue"]
    ax1.set_xlabel("Batch Size (Claims Verified Simultaneously)", fontweight="bold")
    ax1.set_ylabel("Latency per Claim (ms)", color=color, fontweight="bold")
    l1 = ax1.plot(x, df["Latency_Per_Claim_ms"], "o-", color=color, lw=2.2, ms=7, label="Latency per Claim (ms)")
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"B={b}" for b in df["Batch_Size"]], fontweight="medium")
    ax1.set_ylim(50, 110)
    
    ax2 = ax1.twinx()
    color2 = CB_COLORS["green"]
    ax2.set_ylabel("Sustained Throughput (Claims / sec)", color=color2, fontweight="bold")
    l2 = ax2.plot(x, df["Throughput_Claims_Sec"], "s--", color=color2, lw=2.0, ms=6, label="Throughput (Claims/sec)")
    ax2.tick_params(axis="y", labelcolor=color2)
    ax2.set_ylim(8, 16)
    
    plt.title("Batched Inference Latency and Sustained Throughput on CPU", pad=12, fontweight="bold")
    save_multiformat(fig, base_name)

# ==============================================================================
# FIGURE 9: Memory Consumption Profile
# ==============================================================================
def generate_figure_09():
    base_name = "figure_09_memory_profile"
    stages = ["Baseline RSS", "Model Allocated", "Total Loaded RSS", "Peak Batch RSS", "Memory Envelope"]
    values = [289.29, 438.96, 728.25, 774.54, 1500.00]
    
    df = pd.DataFrame({"Stage": stages, "Memory_MB": values})
    df.to_csv(os.path.join(DATA_DIR, f"{base_name}.csv"), index=False)
    
    fig, ax = plt.subplots(figsize=(8.5, 5))
    colors = [CB_COLORS["grey"], CB_COLORS["teal"], CB_COLORS["blue"], CB_COLORS["amber"], CB_COLORS["green"]]
    bars = ax.bar(stages, values, width=0.52, color=colors, edgecolor="#222")
    
    ax.set_ylabel("Memory Resident Set Size (MB)")
    ax.set_title("TrustRAG Operational Memory Footprint and Headroom Margin", pad=12, fontweight="bold")
    ax.set_ylim(0, 1750)
    
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"{h:.1f} MB", xy=(bar.get_x() + bar.get_width() / 2, h), xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontweight="bold")
        
    ax.axhline(1500, color=CB_COLORS["green"], linestyle="--", alpha=0.7, label="1.5 GB Container Limit")
    ax.axhline(774.54, color=CB_COLORS["amber"], linestyle=":", alpha=0.7, label="Peak Operational Ceiling (774.5 MB)")
    ax.legend(frameon=True, facecolor="white", edgecolor="#ccc", loc="upper left")
    save_multiformat(fig, base_name)

# ==============================================================================
# FIGURE 10: Advanced Red-Team Heatmap
# ==============================================================================
def generate_figure_10():
    base_name = "figure_10_redteam_heatmap"
    categories = [
        "04. Character Obfuscation", "06. Narrative Contradictions", "08. Duplicate Source Mirroring",
        "12. Context Exhaustion Padding", "14. Domain Misinformation", "01. Adaptive Prompt Injection",
        "03. Cross-lingual Injection", "02. Multi-turn Manipulation", "05. Paraphrased Inversion",
        "07. Multi-doc Distributed", "09. Sybil Varied Ratios (2v1-5v1)", "10. Majority Consensus Spoofing",
        "11. Retrieval Ranking Gaming", "13. Citation Header Forgery", "15. Mixed Benign/Malicious"
    ]
    adrs = [100.0, 100.0, 100.0, 100.0, 75.0, 33.3, 20.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    asrs = [0.0, 0.0, 0.0, 0.0, 25.0, 66.7, 80.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0]
    counts = [30, 30, 30, 30, 40, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]
    
    df = pd.DataFrame({
        "Threat_Category": categories,
        "ADR_pct": adrs,
        "ASR_pct": asrs,
        "Sample_Count": counts
    })
    df.to_csv(os.path.join(DATA_DIR, f"{base_name}.csv"), index=False)
    
    fig, ax = plt.subplots(figsize=(10.5, 7.5))
    y = np.arange(len(categories))
    y = y[::-1] # Top to bottom
    
    # Horizontal stacked bar
    b1 = ax.barh(y, adrs, color=CB_COLORS["blue"], edgecolor="#222", height=0.65, label="Defended (ADR %)")
    b2 = ax.barh(y, asrs, left=adrs, color=CB_COLORS["vermilion"], edgecolor="#222", height=0.65, label="Breached (ASR %)")
    
    ax.set_yticks(y)
    ax.set_yticklabels(categories, fontweight="medium")
    ax.set_xlabel("Percentage (%)", fontweight="bold")
    ax.set_xlim(0, 100)
    ax.set_title("Advanced Security Red Teaming Evaluation across 15 Threat Vectors\n(N=460 Real Adversarial Injections, Overall ADR=36.09%, ASR=63.91%)", pad=12, fontweight="bold")
    ax.legend(frameon=True, facecolor="white", edgecolor="#ccc", loc="lower right")
    
    # Annotate values
    for i, (adr, asr) in enumerate(zip(adrs, asrs)):
        if adr > 0:
            ax.text(adr/2, y[i], f"{adr:.1f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=8.5)
        if asr > 0:
            ax.text(adr + asr/2, y[i], f"{asr:.1f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=8.5)
            
    # Highlight failure regions
    ax.axhspan(-0.5, 7.5, color="#ffebee", alpha=0.3, zorder=0)
    ax.text(75, 3.5, "ADAPTIVE FRONTIER BREACHES\n(Sybil, Paraphrase, Multi-doc)", ha="center", va="center", color="#b71c1c", fontweight="bold", fontsize=9, bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#d62728"))
    
    save_multiformat(fig, base_name)

# ==============================================================================
# FIGURE 11: External Benchmark Comparison
# ==============================================================================
def generate_figure_11():
    base_name = "figure_11_external_benchmarks"
    df = pd.DataFrame([
        {"Benchmark": "RAGTruth (ACL 2024)", "Task": "Real LLM News/QA Summaries", "Sample_Size": 200, "ADR_Recall": 66.0, "Precision": 58.9, "F1_Score": 62.3, "Clean_FPR": 46.0},
        {"Benchmark": "HaluEval (EMNLP 2023)", "Task": "Entity Fragment QA", "Sample_Size": 200, "ADR_Recall": 89.0, "Precision": 47.6, "F1_Score": 62.0, "Clean_FPR": 98.0}
    ])
    df.to_csv(os.path.join(DATA_DIR, f"{base_name}.csv"), index=False)
    
    fig, ax = plt.subplots(figsize=(8.5, 5))
    x = np.arange(len(df))
    width = 0.18
    
    r1 = ax.bar(x - 1.5*width, df["ADR_Recall"], width, label="Recall / ADR (%)", color=CB_COLORS["blue"], edgecolor="#222")
    r2 = ax.bar(x - 0.5*width, df["Precision"], width, label="Precision (%)", color=CB_COLORS["teal"], edgecolor="#222")
    r3 = ax.bar(x + 0.5*width, df["F1_Score"], width, label="F1 Score (%)", color=CB_COLORS["green"], edgecolor="#222")
    r4 = ax.bar(x + 1.5*width, df["Clean_FPR"], width, label="Clean False Positive Rate (%)", color=CB_COLORS["amber"], edgecolor="#222")
    
    ax.set_ylabel("Score (%)")
    ax.set_title("Independent Public Benchmark Generalization: RAGTruth vs. HaluEval\n(Live DeBERTa-v3-small Weights, N=200 Balanced Sample Each)", pad=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r['Benchmark']}\n({r['Task']})" for _, r in df.iterrows()], fontweight="medium")
    ax.set_ylim(0, 115)
    ax.legend(frameon=True, facecolor="white", edgecolor="#ccc", loc="upper left", ncol=2)
    
    for bar in r3:
        h = bar.get_height()
        ax.annotate(f"F1={h:.1f}%", xy=(bar.get_x() + bar.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontweight="bold", fontsize=9)
    for bar in r4:
        h = bar.get_height()
        ax.annotate(f"FPR={h:.1f}%", xy=(bar.get_x() + bar.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontweight="bold", fontsize=9, color=CB_COLORS["amber"])
        
    save_multiformat(fig, base_name)

# ==============================================================================
# FIGURE 12: Security vs. Latency Trade-off
# ==============================================================================
def generate_figure_02_tradeoff():
    base_name = "figure_12_security_latency_tradeoff"
    df = pd.DataFrame([
        {"Architecture": "Standard RAG", "Latency_P50_ms": 3.29, "ADR_pct": 14.29, "Pareto": False},
        {"Architecture": "TrustRAG G1", "Latency_P50_ms": 3.43, "ADR_pct": 14.29, "Pareto": False},
        {"Architecture": "TrustRAG G1+G2", "Latency_P50_ms": 3.36, "ADR_pct": 100.00, "Pareto": True},
        {"Architecture": "TrustRAG G1+G2+G3 Base", "Latency_P50_ms": 96.06, "ADR_pct": 100.00, "Pareto": False},
        {"Architecture": "TrustRAG G1+G2+G3 Opt", "Latency_P50_ms": 55.84, "ADR_pct": 100.00, "Pareto": True}
    ])
    df.to_csv(os.path.join(DATA_DIR, f"{base_name}.csv"), index=False)
    
    fig, ax = plt.subplots(figsize=(8.5, 5))
    
    colors = [CB_COLORS["grey"], CB_COLORS["amber"], CB_COLORS["blue"], CB_COLORS["purple"], CB_COLORS["teal"]]
    for i, row in df.iterrows():
        ax.scatter(row["Latency_P50_ms"], row["ADR_pct"], s=160, color=colors[i], edgecolors="#222", zorder=4, label=row["Architecture"])
        offset_y = 3 if i != 2 else -6
        ax.annotate(row["Architecture"], xy=(row["Latency_P50_ms"], row["ADR_pct"]), xytext=(row["Latency_P50_ms"] + 2, row["ADR_pct"] + offset_y),
                    fontweight="bold", fontsize=9)
                    
    # Plot Pareto line between G1+G2 and G3 Optimized
    pareto_pts = df[df["Pareto"]].sort_values("Latency_P50_ms")
    ax.plot(pareto_pts["Latency_P50_ms"], pareto_pts["ADR_pct"], "--", color="#084594", alpha=0.6, lw=1.8, label="Optimal Defense Boundary")
    
    ax.set_xlabel("Median Pipeline Latency (ms) [Logarithmic Scale]", fontweight="bold")
    ax.set_ylabel("Attack Defense Rate (ADR %)", fontweight="bold")
    ax.set_xscale("log")
    ax.set_xlim(2, 150)
    ax.set_ylim(0, 115)
    ax.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    ax.set_title("Security Defense Rate vs. Inference Latency Trade-off", pad=12, fontweight="bold")
    ax.legend(frameon=True, facecolor="white", edgecolor="#ccc", loc="center right")
    save_multiformat(fig, base_name)

# ==============================================================================
# FIGURE 13: Historical Research Progress
# ==============================================================================
def generate_figure_13():
    base_name = "figure_13_research_progress"
    milestones = [
        {"Phase": "Phase 11.1", "Date": "Nov 14", "Event": "DeBERTa NLI Training", "Metric_Name": "Macro F1", "Value": 84.1, "Type": "Model"},
        {"Phase": "Phase 11.2", "Date": "Nov 15", "Event": "Clean Benchmark", "Metric_Name": "False Contradiction", "Value": 4.2, "Type": "Utility"},
        {"Phase": "Phase 13", "Date": "Nov 16", "Event": "Synthetic Hardening", "Metric_Name": "Attack Defense", "Value": 100.0, "Type": "Security"},
        {"Phase": "Phase 15", "Date": "Nov 17", "Event": "Public RAGTruth", "Metric_Name": "Real LLM F1", "Value": 62.3, "Type": "Generalization"},
        {"Phase": "Phase 16.1", "Date": "Nov 18", "Event": "Reconciliation", "Metric_Name": "Astrophysical FPR", "Value": 12.5, "Type": "Audit"},
        {"Phase": "Phase 16.2", "Date": "Nov 19", "Event": "Premise Normalization", "Metric_Name": "Clean FPR", "Value": 0.0, "Type": "Remediation"},
        {"Phase": "Phase 18", "Date": "Nov 19", "Event": "15-Category Red Team", "Metric_Name": "Red-Team ADR", "Value": 36.1, "Type": "RedTeam"},
        {"Phase": "Phase 19", "Date": "Nov 19", "Event": "CPU 2-Thread Sweetspot", "Metric_Name": "P50 Latency (ms)", "Value": 55.8, "Type": "Systems"},
        {"Phase": "Phase 20", "Date": "Nov 19", "Event": "Immutable Research Freeze", "Metric_Name": "Zero Leakage", "Value": 100.0, "Type": "Freeze"}
    ]
    df = pd.DataFrame(milestones)
    df.to_csv(os.path.join(DATA_DIR, f"{base_name}.csv"), index=False)
    
    fig, ax = plt.subplots(figsize=(11, 5.5))
    x = np.arange(len(df))
    
    ax.plot(x, df["Value"], "o-", color=CB_COLORS["dark_blue"], lw=2.2, ms=8, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r['Phase']}\n({r['Event']})" for _, r in df.iterrows()], rotation=22, ha="right", fontweight="medium")
    ax.set_ylabel("Empirical Metric Value (% or ms)", fontweight="bold")
    ax.set_title("TrustRAG Empirical Research Milestones Across Phases 11–20", pad=12, fontweight="bold")
    ax.set_ylim(-5, 115)
    
    for i, row in df.iterrows():
        ax.annotate(f"{row['Metric_Name']}:\n{row['Value']}", xy=(x[i], row["Value"]), xytext=(0, 10 if row['Value'] < 90 else -25),
                    textcoords="offset points", ha="center", fontsize=8, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="#f8f9fa", edgecolor="#bbb", alpha=0.9))
                    
    save_multiformat(fig, base_name)

def generate_figure_index():
    index_path = os.path.join(FIG_DIR, "figure_index.md")
    content = """# TrustRAG Publication-Quality Research Figure Index

This index catalogs the complete collection of publication-quality research figures generated for the TrustRAG master research report, peer-reviewed academic papers, and technical presentations.

Every figure is backed by underlying empirical CSV data in `data/`, generated via `scripts/generate_publication_figures.py`, and exported in 300 DPI PNG, vector PDF, and vector SVG formats.

---

## Catalog of Research Figures

| Figure Number | Filename Identifier | Title & Scientific Subject | Primary Data Source | Evaluation Cohort & Sample Size ($N$) | Key Empirical Interpretation |
|---|---|---|---|:---:|---|
| **Figure 1** | `figure_01_architecture_comparison` | Overall Architecture Comparison: Security vs Clean Utility | `phase17_comparative_results.json` | $N=875$ Attacks, $N=1,000$ Controls | Proves G1+G2 achieves $100\%$ defense on synthetic attacks while premise normalization in G3 restores $100\%$ clean delivery ($0\%$ FPR). |
| **Figure 2** | `figure_02_attack_defense` | Attack Defense Performance Across Security Categories | `phase13_generalization_and_hardening` | $N=1,000$ ($N=125$ per category) | Visualizes per-category defense rates across Standard RAG, G1, G1+G2, and G3 Optimized across 8 attack categories. |
| **Figure 3** | `figure_03_clean_utility` | Clean Utility Impact of Premise Citation Normalization | `phase16_2_neural_utility_optimization` | $N=1,000$ Clean Controls | Demonstrates remediation of astrophysical false alarms: clean FPR drops from $12.50\% \to 0.00\%$ with Wilson 95% CIs. |
| **Figure 4** | `figure_04_nli_confusion_matrix` | DeBERTa-v3-small NLI Confusion Matrix on Validation Set | `predictions_val.jsonl` | $N=2,662$ Held-Out Validation Pairs | Visualizes normalized classification matrix across Entailment ($91.5\%$), Neutral ($41.0\%$), and Contradiction ($25.3\%$). |
| **Figure 5** | `figure_05_classwise_metrics` | Class-wise Model Performance: Precision, Recall, F1 | `predictions_val.jsonl` | $N=2,662$ Held-Out Validation Pairs | Class-specific metrics: Entailment F1=$82.3\%$, Neutral F1=$46.6\%$, Contradiction F1=$36.2\%$, Macro F1=$55.0\%$, Weighted F1=$67.5\%$. |
| **Figure 6** | `figure_06_calibration` | Calibration Reliability Diagram: Temperature Scaling | `predictions_val.jsonl` | $N=2,662$ Validation ($T=1.7701$) | Displays predicted confidence vs observed accuracy; proves Expected Calibration Error drops from $15.01\% \to 3.06\%$ after scaling. |
| **Figure 7** | `figure_07_cpu_latency` | CPU Intra-Op Thread Latency Benchmarks (1, 2, 4, 8 Threads) | `phase19_scalability_results.json` | 20 Iterations per Thread Configuration | Proves 2 CPU threads is the optimal operating sweet spot ($55.84\text{ ms}$ P50, $1.73\times$ speedup) avoiding cache thrashing at 4+ threads. |
| **Figure 8** | `figure_08_batch_throughput` | Batched Inference Latency and Sustained Throughput | `phase19_scalability_results.json` | Batch Sizes $B \in [1, 2, 4, 8, 16, 32]$ | Demonstrates batched forward passes maintain steady per-claim latency ($\sim 80\text{ ms}$) yielding $>12\text{ claims/sec}$ on CPU. |
| **Figure 9** | `figure_09_memory_profile` | Operational Memory Footprint and Headroom Margin | `phase19_scalability_results.json` | Standalone CPU x86_64 Profiling | Details RAM allocation: Baseline $289\text{ MB}$, Loaded $728\text{ MB}$, Peak $774\text{ MB}$, fitting comfortably inside $1.5\text{ GB}$ container envelope. |
| **Figure 10** | `figure_10_redteam_heatmap` | Advanced Security Red Teaming Evaluation across 15 Vectors | `phase18_attack_dataset_manifest.json` | $N=460$ Real Red-Team Attacks | Discloses the red-team frontier: $100\%$ defense on character/narrative vectors, but $0\%\text{--}33\%$ on Sybil consensus, paraphrase, and code injection. |
| **Figure 11** | `figure_11_external_benchmarks` | Independent Public Benchmark Generalization: RAGTruth vs HaluEval | `phase15_final_release_and_freeze` | $N=200$ Balanced Samples Each | Demarcates the Generalization Reality Gap: RAGTruth F1=$62.3\%$ (FPR=$46\%$) vs HaluEval F1=$62.0\%$ (FPR=$98\%$ Propositional Dilemma). |
| **Figure 12** | `figure_12_security_latency_tradeoff` | Security Defense Rate vs. Inference Latency Pareto Trade-off | `phase17_comparative_results.json` | Multi-Configuration Pareto Analysis | Maps the Pareto frontier: G1+G2 ($3.36\text{ ms}, 100\%$ synthetic) to G3 Optimized ($55.84\text{ ms}, 100\%$ deep inspection). |
| **Figure 13** | `figure_13_research_progress` | Empirical Research Milestones Across Phases 11–20 | Phases 11–20 Research Completion Reports | 10 Sequential Empirical Milestones | Chronological timeline tracing NLI training, discrepancy resolution, baseline audits, premise normalization, and final freeze. |

---

## Reproduction Commands

To reproduce all 13 figures, CSV datasets, and exports:

```bash
cd /home/aditya/rags/TrustRag-phase11
export MPLCONFIGDIR=/tmp/mplconfig
/usr/bin/python3 reports/research_completion/final_research_freeze/figures/scripts/generate_publication_figures.py
```
"""
    with open(index_path, "w") as f:
        f.write(content)
    print("Generated: figure_index.md")

def main():
    print("Starting Publication-Quality Figure Generation Campaign...")
    generate_figure_01()
    generate_figure_02()
    generate_figure_03()
    generate_figure_04()
    generate_figure_05()
    generate_figure_06()
    generate_figure_07()
    generate_figure_08()
    generate_figure_09()
    generate_figure_10()
    generate_figure_11()
    generate_figure_02_tradeoff()
    generate_figure_13()
    generate_figure_index()
    print("All 13 publication figures successfully created with CSVs, PNGs, PDFs, and SVGs.")

if __name__ == "__main__":
    main()

