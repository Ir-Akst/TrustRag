#!/usr/bin/env python3
"""Dedicated 3-Way NLI Training Runner & Verification Module.

Track 2, Step 3.6 / Step 3.7: NLI Training Preparation, Verification & Controlled Pilot Engine.
Architecture: DeBERTa-v3-small with 3-class sequence classification head.
Labels:
  - ENTAILMENT = 0
  - CONTRADICTION = 1
  - NEUTRAL = 2
"""

from __future__ import annotations

import os
import sys
import time
import json
import math
import random
import shutil
import hashlib
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional
from collections import defaultdict, Counter

# Protected Paths - Immutability Enforcement
PROTECTED_PATHS = {
    Path("/home/aditya/rags/models/pretrained/deberta-v3-small").resolve(),
    Path("/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000").resolve(),
    Path("/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000").resolve(),
    Path("/home/aditya/rags/models/trained/deberta-v3-small-nli-remediated").resolve(),
    Path("/home/aditya/rags/TrustRag").resolve(),
}

MANDATORY_NLI_FIELDS = {
    "example_id",
    "source_dataset",
    "source_id",
    "split",
    "premise",
    "hypothesis",
    "nli_label",
    "conflict_types",
    "span_count",
    "source_provenance",
}

NLI_LABEL_MAP = {
    "ENTAILMENT": 0,
    "CONTRADICTION": 1,
    "NEUTRAL": 2,
}

ID_TO_NLI_LABEL = {v: k for k, v in NLI_LABEL_MAP.items()}


class SecurityViolationError(Exception):
    """Raised when an operation attempts to access test data or overwrite protected paths."""
    pass


class ResourceAbortError(Exception):
    """Raised when host resources cross safe execution thresholds."""
    pass


class TimeoutAbortError(Exception):
    """Raised when wall-clock execution exceeds safety cutoff."""
    pass


class TrainingNotAuthorizedError(Exception):
    """Raised when training execution is attempted without explicit authorization."""
    pass


class ClassStarvationError(Exception):
    """Raised when an active training batch/sequence has prolonged class absence."""
    pass


class CheckpointIntegrityError(Exception):
    """Raised when a checkpoint directory fails cryptographic or structural verification."""
    pass


@dataclass
class NLITrainingConfig:
    """Rigorous configuration for 3-way NLI classification training."""
    model_dir: str = "/home/aditya/rags/models/pretrained/deberta-v3-small"
    train_file: str = "/home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/train.jsonl"
    val_file: str = "/home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/validation.jsonl"
    output_dir: str = "/home/aditya/rags/models/trained/deberta-v3-small-nli-remediated"
    num_classes: int = 3
    max_train_samples: int = 1000
    max_val_samples: int = 2662  # Full original imbalanced validation set
    epochs: int = 1
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    warmup_steps: int = 100
    max_grad_norm: float = 1.0
    max_seq_len: int = 384
    min_premise_tokens: int = 64
    batch_size: int = 1
    seed: int = 42
    shuffle: bool = True
    sampler_strategy: str = "stratified_class_balanced"
    class_weights: Optional[list[float]] = None
    save_predictions: bool = True
    max_starvation_threshold: int = 25
    serialization_strategy: str = "evidence_preserving"
    dynamic_padding: bool = True
    evaluate_every_steps: int = 1000
    log_every_steps: int = 50
    num_threads: int = 10
    interop_threads: int = 1
    checkpoint_every_steps: int = 500
    keep_last_n_checkpoints: int = 2
    resume_from_checkpoint: Optional[str] = None
    auto_resume: bool = True
    ram_abort_threshold_mb: float = 700.0
    swap_free_min_mb: float = 1000.0
    max_process_rss_mb: float = 4500.0
    watchdog_consecutive_violations: int = 3
    swap_growth_abort_mb: Optional[float] = None
    max_duration_seconds: float = 3600.0
    authorized: bool = False


class WatchdogMonitor:
    """Active real-time safety watchdog monitoring host resources during execution."""

    def __init__(
        self,
        ram_abort_threshold_mb: float = 700.0,
        swap_free_min_mb: float = 1000.0,
        max_process_rss_mb: float = 4500.0,
        max_duration_seconds: float = 3600.0,
        consecutive_violations_threshold: int = 1,
        swap_growth_abort_mb: Optional[float] = None,
        emergency_save_fn: Optional[Callable[[int, str], None]] = None,
        telemetry_fn: Optional[Callable[[], dict[str, float]]] = None,
    ) -> None:
        self.ram_threshold = ram_abort_threshold_mb
        self.swap_free_min = swap_free_min_mb
        self.max_process_rss = max_process_rss_mb
        self.max_duration = max_duration_seconds
        self.consecutive_violations_threshold = consecutive_violations_threshold
        self.swap_growth_threshold = swap_growth_abort_mb
        self.emergency_save_fn = emergency_save_fn
        self.telemetry_fn = telemetry_fn or self._default_telemetry
        self.t_start: float = time.perf_counter()
        self.baseline_telemetry: dict[str, float] = dict(self.telemetry_fn())
        self.peak_rss_mb: float = self.baseline_telemetry.get("rss_mb", 0.0)
        self.consecutive_violations: int = 0

    def reset_baseline(self) -> None:
        """Resets the baseline telemetry (e.g. before training loop starts after Step 0 eval)."""
        self.baseline_telemetry = dict(self.telemetry_fn())
        self.consecutive_violations = 0

    @staticmethod
    def _default_telemetry() -> dict[str, float]:
        telemetry = {
            "rss_mb": 0.0,
            "available_ram_mb": 0.0,
            "swap_total_mb": 0.0,
            "swap_used_mb": 0.0,
            "swap_free_mb": 0.0,
        }
        try:
            import psutil
            proc = psutil.Process()
            telemetry["rss_mb"] = proc.memory_info().rss / (1024 * 1024)
            vm = psutil.virtual_memory()
            telemetry["available_ram_mb"] = vm.available / (1024 * 1024)
            sw = psutil.swap_memory()
            telemetry["swap_total_mb"] = sw.total / (1024 * 1024)
            telemetry["swap_used_mb"] = sw.used / (1024 * 1024)
            telemetry["swap_free_mb"] = sw.free / (1024 * 1024)
        except Exception:
            pass
        return telemetry

    def check(self, step: int) -> dict[str, Any]:
        current = dict(self.telemetry_fn())
        elapsed = time.perf_counter() - self.t_start
        current["elapsed_seconds"] = elapsed

        if current["rss_mb"] > self.peak_rss_mb:
            self.peak_rss_mb = current["rss_mb"]
        current["peak_rss_mb"] = self.peak_rss_mb

        # 1. Hard Timeout Cutoff
        if elapsed > self.max_duration:
            if self.emergency_save_fn:
                try:
                    self.emergency_save_fn(step, f"TIMEOUT_{elapsed:.1f}s")
                except Exception as exc:
                    print(f"[Watchdog Emergency Save Failed] {exc}")
            raise TimeoutAbortError(
                f"[WATCHDOG ABORT] Step {step}: Execution time {elapsed:.1f}s exceeded hard cutoff of {self.max_duration:.1f}s!"
            )

        # 2. Process RSS Ceiling Check (True Memory Leak)
        if current["rss_mb"] > self.max_process_rss:
            if self.emergency_save_fn:
                try:
                    self.emergency_save_fn(step, f"PROCESS_RSS_CEILING_{current['rss_mb']:.1f}MB")
                except Exception as exc:
                    print(f"[Watchdog Emergency Save Failed] {exc}")
            raise ResourceAbortError(
                f"[WATCHDOG ABORT] Step {step}: Process RSS {current['rss_mb']:.1f} MB exceeded ceiling of {self.max_process_rss:.1f} MB!"
            )

        # 3. Host Absolute Capacity Check (Floor Protection with Sustained Filter)
        ram_breached = current["available_ram_mb"] < self.ram_threshold
        swap_breached = current["swap_free_mb"] < self.swap_free_min

        swap_growth = current["swap_used_mb"] - self.baseline_telemetry.get("swap_used_mb", 0.0)
        current["swap_growth_mb"] = swap_growth
        swap_growth_breached = False
        if self.swap_growth_threshold is not None:
            if swap_growth > self.swap_growth_threshold:
                swap_growth_breached = True

        if ram_breached or swap_breached or swap_growth_breached:
            self.consecutive_violations += 1
            current["consecutive_violations"] = self.consecutive_violations
            if self.consecutive_violations >= self.consecutive_violations_threshold:
                if self.emergency_save_fn:
                    try:
                        self.emergency_save_fn(step, "SUSTAINED_MEMORY_PRESSURE")
                    except Exception as exc:
                        print(f"[Watchdog Emergency Save Failed] {exc}")
                if ram_breached:
                    raise ResourceAbortError(
                        f"[WATCHDOG ABORT] Step {step}: Available host RAM dropped to {current['available_ram_mb']:.1f} MB "
                        f"(Threshold: {self.ram_threshold:.1f} MB)!"
                    )
                elif swap_growth_breached:
                    raise ResourceAbortError(
                        f"[WATCHDOG ABORT] Step {step}: Swap usage grew by {swap_growth:.1f} MB from baseline "
                        f"(Threshold: {self.swap_growth_threshold:.1f} MB)!"
                    )
                elif swap_breached:
                    raise ResourceAbortError(
                        f"[WATCHDOG ABORT] Step {step}: Free swap dropped to {current['swap_free_mb']:.1f} MB "
                        f"(Minimum requirement: {self.swap_free_min:.1f} MB)!"
                    )
        else:
            self.consecutive_violations = 0
            current["consecutive_violations"] = 0

        return current


def validate_nli_record(record: dict[str, Any]) -> None:
    """Validates schema fields and label integrity for 3-way NLI records."""
    missing = MANDATORY_NLI_FIELDS - set(record.keys())
    if missing:
        raise ValueError(f"Record {record.get('example_id', 'UNKNOWN')} missing mandatory fields: {missing}")
    if record["nli_label"] not in NLI_LABEL_MAP:
        raise ValueError(
            f"Record {record.get('example_id')} has invalid label '{record['nli_label']}'. "
            f"Expected one of: {list(NLI_LABEL_MAP.keys())}"
        )
    if record.get("split") == "test":
        raise SecurityViolationError(f"Access to test record prohibited: {record.get('example_id')}")
    if not record.get("premise", "").strip():
        raise ValueError(f"Record {record.get('example_id')} has empty premise.")
    if not record.get("hypothesis", "").strip():
        raise ValueError(f"Record {record.get('example_id')} has empty hypothesis.")


def serialize_nli_input(record: dict[str, Any]) -> tuple[str, str]:
    """Returns premise and hypothesis for cross-encoder tokenization."""
    return record["premise"].strip(), record["hypothesis"].strip()


def check_class_starvation(
    records: list[dict[str, Any]],
    max_starvation_threshold: int = 25,
    classes: tuple[str, ...] = ("ENTAILMENT", "CONTRADICTION", "NEUTRAL"),
    window_size: int = 50,
) -> dict[str, Any]:
    """Monitors class distribution and detects prolonged class starvation runs.

    Args:
        records: List of dataset records containing 'nli_label'.
        max_starvation_threshold: Maximum allowed consecutive steps without a specific class.
        classes: Classes to monitor.
        window_size: Rolling window size for distribution statistics.

    Returns:
        Dictionary with starvation telemetry and rolling window metrics.

    Raises:
        ClassStarvationError: If any class is absent for >= max_starvation_threshold consecutive steps.
    """
    labels = [r["nli_label"] for r in records]
    n = len(labels)
    if n == 0:
        return {"status": "EMPTY", "max_consecutive_absences": {}}

    max_consecutive_absences = {c: 0 for c in classes}
    current_absence = {c: 0 for c in classes}

    for lbl in labels:
        for c in classes:
            if lbl == c:
                current_absence[c] = 0
            else:
                current_absence[c] += 1
                if current_absence[c] > max_consecutive_absences[c]:
                    max_consecutive_absences[c] = current_absence[c]

    # Verify no class experienced prolonged starvation
    for c, max_abs in max_consecutive_absences.items():
        if max_abs >= max_starvation_threshold:
            raise ClassStarvationError(
                f"Class starvation violation: Class '{c}' absent for {max_abs} consecutive steps "
                f"(Hard safety limit: {max_starvation_threshold})!"
            )

    # Rolling window distribution monitoring
    rolling_stats = []
    if n >= window_size:
        for i in range(0, n - window_size + 1, window_size // 2):
            w = labels[i : i + window_size]
            dist = {c: float(w.count(c) / window_size) for c in classes}
            rolling_stats.append({"start_step": i, "end_step": i + window_size, "distribution": dist})

    return {
        "status": "BALANCED_NO_STARVATION",
        "total_records": n,
        "max_consecutive_absences": max_consecutive_absences,
        "rolling_window_stats": rolling_stats,
    }


def evidence_preserving_tokenize(
    tokenizer: Any,
    premise: str,
    hypothesis: str,
    max_seq_len: int = 384,
    min_premise_tokens: int = 64,
    device: str = "cpu",
    dynamic_padding: bool = True,
) -> dict[str, Any]:
    """Tokenizes premise and hypothesis while strictly prioritizing hypothesis claim preservation.

    Strategy:
    - Measures token length of hypothesis.
    - If hypothesis fits within (max_seq_len - min_premise_tokens - 3), hypothesis is 100% PRESERVED
      and remaining token budget is allocated to premise evidence.
    - If hypothesis is excessively long, hypothesis is capped at (max_seq_len - min_premise_tokens - 3),
      guaranteeing premise receives at least min_premise_tokens.
    - Accurately tracks truncation metadata.
    """
    p_ids = tokenizer(premise, add_special_tokens=False)["input_ids"]
    h_ids = tokenizer(hypothesis, add_special_tokens=False)["input_ids"]

    orig_p_len = len(p_ids)
    orig_h_len = len(h_ids)

    special_count = 3  # [CLS] premise [SEP] hypothesis [SEP]
    avail_budget = max_seq_len - special_count

    if orig_h_len + min_premise_tokens <= avail_budget:
        kept_h_len = orig_h_len
        kept_p_len = min(orig_p_len, avail_budget - kept_h_len)
    else:
        kept_p_len = min(orig_p_len, min_premise_tokens)
        kept_h_len = min(orig_h_len, avail_budget - kept_p_len)

    proc_p_ids = p_ids[:kept_p_len]
    proc_h_ids = h_ids[:kept_h_len]

    # Construct input sequence: [CLS] + proc_p_ids + [SEP] + proc_h_ids + [SEP]
    cls_id = getattr(tokenizer, "cls_token_id", 1) or 1
    sep_id = getattr(tokenizer, "sep_token_id", 2) or 2
    pad_id = getattr(tokenizer, "pad_token_id", 0) or 0
    input_ids = [cls_id] + proc_p_ids + [sep_id] + proc_h_ids + [sep_id]
    attention_mask = [1] * len(input_ids)
    token_type_ids = [0] * (len(proc_p_ids) + 2) + [1] * (len(proc_h_ids) + 1)

    if not dynamic_padding and len(input_ids) < max_seq_len:
        pad_len = max_seq_len - len(input_ids)
        input_ids = input_ids + [pad_id] * pad_len
        attention_mask = attention_mask + [0] * pad_len
        token_type_ids = token_type_ids + [0] * pad_len

    metadata = {
        "orig_premise_tokens": orig_p_len,
        "orig_hypothesis_tokens": orig_h_len,
        "total_orig_tokens": orig_p_len + orig_h_len + special_count,
        "processed_premise_tokens": kept_p_len,
        "processed_hypothesis_tokens": kept_h_len,
        "processed_seq_len": len(input_ids),
        "dynamic_padding": dynamic_padding,
        "hypothesis_truncated": kept_h_len < orig_h_len,
        "premise_truncated": kept_p_len < orig_p_len,
        "hypothesis_retention_rate": float(kept_h_len / orig_h_len) if orig_h_len > 0 else 1.0,
        "premise_retention_rate": float(kept_p_len / orig_p_len) if orig_p_len > 0 else 1.0,
    }

    try:
        import torch
        tensors = {
            "input_ids": torch.tensor([input_ids], dtype=torch.long, device=device),
            "attention_mask": torch.tensor([attention_mask], dtype=torch.long, device=device),
            "token_type_ids": torch.tensor([token_type_ids], dtype=torch.long, device=device),
            "metadata": metadata,
        }
    except ImportError:
        tensors = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids,
            "metadata": metadata,
        }
    return tensors


def load_nli_dataset(
    file_path: Path | str,
    max_samples: int,
    strategy: str = "stratified_class_balanced",
    seed: int = 42,
    shuffle: bool = True,
    max_starvation_threshold: int = 25,
) -> list[dict[str, Any]]:
    """Loads NLI records with deterministic sampling, schema validation, and starvation monitoring.

    Supported strategies:
    - 'stratified_class_balanced': Equal samples per class (ENTAILMENT, CONTRADICTION, NEUTRAL)
      with seed-controlled post-selection shuffling and starvation prevention.
    - 'sequential': First N valid records (preserving original split distribution).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    if "test" in path.name.lower():
        raise SecurityViolationError(f"Direct targeting of test set file is prohibited: {path.name}")

    if strategy == "stratified_class_balanced":
        target_per_class = max_samples // 3
        remainder = max_samples % 3
        targets = {
            "ENTAILMENT": target_per_class + (1 if remainder > 0 else 0),
            "CONTRADICTION": target_per_class + (1 if remainder > 1 else 0),
            "NEUTRAL": target_per_class,
        }
        counts = {"ENTAILMENT": 0, "CONTRADICTION": 0, "NEUTRAL": 0}
        selected: list[dict[str, Any]] = []

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                validate_nli_record(rec)
                lbl = rec["nli_label"]
                if counts[lbl] < targets[lbl]:
                    selected.append(rec)
                    counts[lbl] += 1
                if len(selected) >= max_samples:
                    break

        if len(selected) != max_samples:
            raise ValueError(f"Requested {max_samples} samples from {path.name}, but obtained {len(selected)}")

        # Exact quota verification
        for c in ["ENTAILMENT", "CONTRADICTION", "NEUTRAL"]:
            if counts[c] != targets[c]:
                raise ValueError(f"Class {c} quota mismatch: expected {targets[c]}, got {counts[c]}")

        # Seed-controlled shuffling to eliminate recency bias / tail collapse
        if shuffle:
            import random
            rng = random.Random(seed)
            rng.shuffle(selected)
            # Verify no class starvation exists in shuffled sequence
            check_class_starvation(selected, max_starvation_threshold=max_starvation_threshold)

        return selected

    elif strategy == "sequential":
        selected = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                validate_nli_record(rec)
                selected.append(rec)
                if len(selected) >= max_samples:
                    break
        if len(selected) != max_samples:
            raise ValueError(f"Requested {max_samples} samples from {path.name}, but obtained {len(selected)}")
        return selected

    else:
        raise ValueError(f"Unknown sampling strategy: {strategy}")


def verify_split_isolation(train_records: list[dict[str, Any]], val_records: list[dict[str, Any]]) -> None:
    """Verifies complete absence of example_id and premise text leakage between train and validation."""
    train_ids = {r["example_id"] for r in train_records}
    val_ids = {r["example_id"] for r in val_records}
    id_overlap = train_ids.intersection(val_ids)
    if id_overlap:
        raise SecurityViolationError(f"Example ID leakage detected: {len(id_overlap)} overlapping IDs!")

    train_hashes = {hashlib.sha256(r["premise"].strip().encode("utf-8")).hexdigest() for r in train_records}
    val_hashes = {hashlib.sha256(r["premise"].strip().encode("utf-8")).hexdigest() for r in val_records}
    premise_overlap = train_hashes.intersection(val_hashes)
    if premise_overlap:
        raise SecurityViolationError(f"Document/premise leakage detected: {len(premise_overlap)} overlapping documents!")


def compute_nli_metrics(
    y_true: list[int],
    y_pred: list[int],
    y_probs: Optional[list[list[float]]] = None,
    loss: Optional[float] = None,
) -> dict[str, Any]:
    """Computes comprehensive 3-way NLI evaluation metrics."""
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true={len(y_true)}, y_pred={len(y_pred)}")
    total = len(y_true)
    if total == 0:
        return {}

    correct = sum(yt == yp for yt, yp in zip(y_true, y_pred))
    acc = float(correct / total)

    cm = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    for yt, yp in zip(y_true, y_pred):
        cm[yt][yp] += 1

    per_class_metrics = {}
    f1_list = []
    recalls = []
    weighted_f1_sum = 0.0

    for c in range(3):
        name = ID_TO_NLI_LABEL[c]
        tp = cm[c][c]
        fp = sum(cm[r][c] for r in range(3) if r != c)
        fn = sum(cm[c][p] for p in range(3) if p != c)
        support = sum(cm[c])

        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        per_class_metrics[name] = {
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "support": support,
        }
        f1_list.append(f1)
        recalls.append(rec)
        weighted_f1_sum += f1 * support

    bal_acc = float(sum(recalls) / 3.0)
    macro_f1 = float(sum(f1_list) / 3.0)
    weighted_f1 = float(weighted_f1_sum / total)

    metrics: dict[str, Any] = {
        "total_samples": total,
        "loss": loss if loss is not None else 0.0,
        "accuracy": acc,
        "balanced_accuracy": bal_acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "per_class": per_class_metrics,
        "confusion_matrix": cm,
    }

    if y_probs is not None and len(y_probs) == total:
        brier_sum = 0.0
        for yt, probs in zip(y_true, y_probs):
            one_hot = [1.0 if i == yt else 0.0 for i in range(3)]
            brier_sum += sum((p - oh) ** 2 for p, oh in zip(probs, one_hot))
        metrics["brier_score"] = float(brier_sum / total)

        n_bins = 10
        bin_counts = [0] * n_bins
        bin_correct = [0] * n_bins
        bin_conf_sum = [0.0] * n_bins
        for yt, yp, probs in zip(y_true, y_pred, y_probs):
            conf = max(probs)
            bin_idx = min(int(conf * n_bins), n_bins - 1)
            bin_counts[bin_idx] += 1
            bin_conf_sum[bin_idx] += conf
            if yt == yp:
                bin_correct[bin_idx] += 1

        ece = 0.0
        for i in range(n_bins):
            if bin_counts[i] > 0:
                bin_acc = bin_correct[i] / bin_counts[i]
                bin_conf = bin_conf_sum[i] / bin_counts[i]
                ece += (bin_counts[i] / total) * abs(bin_acc - bin_conf)
        metrics["ece_10bins"] = float(ece)

    return metrics


def save_checkpoint_atomic(
    model: Any,
    tokenizer: Any,
    output_dir: Path | str,
    step: int = 1000,
    metrics: Optional[dict[str, Any]] = None,
    pretrained_model_dir: str = "",
    meta: Optional[dict[str, Any]] = None,
) -> Path:
    """Atomically serializes model, tokenizer, and metadata with protected path guard."""
    out_path = Path(output_dir).resolve()
    for protected in PROTECTED_PATHS:
        if out_path == protected or protected in out_path.parents:
            raise SecurityViolationError(f"Attempted overwrite of protected path: {out_path}")

    tmp_dir = out_path.parent / f".tmp_{out_path.name}_{int(time.time())}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    metadata = meta if meta is not None else {
        "step": step,
        "task": "evidence_grounded_3way_nli",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pretrained_base": pretrained_model_dir,
        "metrics": metrics or {},
    }

    try:
        model.save_pretrained(tmp_dir)
        tokenizer.save_pretrained(tmp_dir)
        with open(tmp_dir / "training_meta.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        if out_path.exists():
            shutil.rmtree(out_path)
        tmp_dir.rename(out_path)
        return out_path
    except Exception as e:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        raise e


def compute_directory_checksums(directory: Path | str) -> dict[str, str]:
    """Computes SHA-256 for all regular files in directory and writes checksums.sha256."""
    dir_path = Path(directory).resolve()
    checksums = {}
    for p in sorted(dir_path.rglob("*")):
        if p.is_file() and p.name != "checksums.sha256" and not p.name.startswith(".tmp_"):
            rel = p.relative_to(dir_path).as_posix()
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            checksums[rel] = h

    ck_file = dir_path / "checksums.sha256"
    lines = [f"{h}  {name}\n" for name, h in sorted(checksums.items())]
    ck_file.write_text("".join(lines), encoding="utf-8")
    return checksums


def verify_checkpoint_integrity(checkpoint_dir: Path | str) -> tuple[bool, str]:
    """Verifies cryptographic and structural integrity of a serialized checkpoint directory."""
    dir_path = Path(checkpoint_dir).resolve()
    if not dir_path.is_dir():
        return False, f"Directory does not exist: {dir_path}"

    meta_file = dir_path / "checkpoint_meta.json"
    if not meta_file.is_file():
        meta_file = dir_path / "training_meta.json"
        if not meta_file.is_file():
            return False, "Missing checkpoint_meta.json or training_meta.json"

    ck_file = dir_path / "checksums.sha256"
    if not ck_file.is_file():
        has_weights = (
            (dir_path / "model.safetensors").is_file()
            or (dir_path / "pytorch_model.bin").is_file()
            or (dir_path / "model.pt").is_file()
        )
        if not has_weights:
            return False, "Missing weight file and checksums.sha256"
        return True, "Valid (no checksums.sha256 manifest present)"

    manifest_lines = ck_file.read_text(encoding="utf-8").strip().splitlines()
    for line in manifest_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        expected_hash, rel_path = parts[0], parts[1].strip()
        target_file = dir_path / rel_path
        if not target_file.is_file():
            return False, f"Missing manifest target file: {rel_path}"
        actual_hash = hashlib.sha256(target_file.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            return False, f"Checksum mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"

    return True, "OK"


def prune_old_checkpoints(base_dir: Path | str, keep_last_n: int = 2) -> list[str]:
    """Prunes step checkpoints in base_dir, retaining the latest keep_last_n step checkpoints."""
    b_path = Path(base_dir).resolve()
    if not b_path.exists():
        return []
    step_dirs = []
    for d in b_path.iterdir():
        if d.is_dir() and d.name.startswith("checkpoint_step_"):
            try:
                step_num = int(d.name.split("_")[-1])
                step_dirs.append((step_num, d))
            except ValueError:
                pass
    step_dirs.sort(key=lambda x: x[0])
    pruned = []
    if len(step_dirs) > keep_last_n:
        to_delete = step_dirs[:-keep_last_n]
        for _, d in to_delete:
            shutil.rmtree(d, ignore_errors=True)
            pruned.append(d.name)
    return pruned


def save_checkpoint_state(
    model: Any,
    tokenizer: Any,
    optimizer: Any,
    checkpoint_dir: Path | str,
    step: int,
    epoch: int,
    sample_idx: int,
    accum_count: int,
    metrics: Optional[dict[str, Any]] = None,
    scheduler: Optional[Any] = None,
    current_lr: Optional[float] = None,
    best_epoch: int = 0,
    best_step: int = 0,
    best_macro_f1: float = -1.0,
    best_val_loss: float = float("inf"),
    epoch_history: Optional[list[dict[str, Any]]] = None,
    pretrained_model_dir: str = "",
    is_best: bool = False,
    is_emergency: bool = False,
    emergency_reason: str = "",
) -> Path:
    """Atomically serializes model, optimizer, scheduler, RNG, and metadata state."""
    import torch
    import numpy as np
    out_path = Path(checkpoint_dir).resolve()
    for protected in PROTECTED_PATHS:
        if out_path == protected or protected in out_path.parents:
            raise SecurityViolationError(f"Attempted overwrite of protected path: {out_path}")

    tmp_dir = out_path.parent / f".tmp_{out_path.name}_{int(time.time() * 1000)}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Model & Tokenizer
        if hasattr(model, "save_pretrained"):
            model.save_pretrained(tmp_dir)
        else:
            torch.save(model.state_dict(), tmp_dir / "model.pt")

        if tokenizer is not None and hasattr(tokenizer, "save_pretrained"):
            tokenizer.save_pretrained(tmp_dir)

        # 2. Optimizer State
        if optimizer is not None:
            torch.save(optimizer.state_dict(), tmp_dir / "optimizer.pt")

        # 3. Scheduler & LR State
        sched_payload = {
            "scheduler_state": scheduler.state_dict() if scheduler is not None and hasattr(scheduler, "state_dict") else None,
            "current_lr": current_lr,
        }
        torch.save(sched_payload, tmp_dir / "scheduler.pt")

        # 4. RNG State
        rng_payload = {
            "torch": torch.get_rng_state(),
            "numpy": np.random.get_state(),
            "python": random.getstate(),
        }
        torch.save(rng_payload, tmp_dir / "rng_state.pt")

        # 5. Metadata
        meta_payload = {
            "version": "2.3",
            "step": step,
            "epoch": epoch,
            "sample_idx": sample_idx,
            "accum_count": accum_count,
            "current_lr": current_lr,
            "best_epoch": best_epoch,
            "best_step": best_step,
            "best_macro_f1": best_macro_f1,
            "best_val_loss": best_val_loss,
            "epoch_history": epoch_history or [],
            "metrics": metrics or {},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "pretrained_base": pretrained_model_dir,
            "is_best": is_best,
            "is_emergency": is_emergency,
            "emergency_reason": emergency_reason,
        }
        with open(tmp_dir / "checkpoint_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta_payload, f, indent=2)

        # 6. Cryptographic Checksums
        compute_directory_checksums(tmp_dir)

        # 7. Atomic Commit
        if out_path.exists():
            shutil.rmtree(out_path)
        tmp_dir.rename(out_path)

        # 8. Record latest pointer
        latest_pointer = out_path.parent / "latest_checkpoint.json"
        try:
            with open(latest_pointer, "w", encoding="utf-8") as f:
                json.dump({
                    "latest_checkpoint_dir": str(out_path),
                    "step": step,
                    "epoch": epoch,
                    "timestamp": meta_payload["timestamp"],
                }, f, indent=2)
        except Exception:
            pass

        return out_path
    except Exception as e:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)
        raise e


def _safe_torch_load(path: Path | str, map_location: Any = None) -> Any:
    """Helper to safely load torch checkpoint files across PyTorch versions."""
    import torch
    try:
        return torch.load(path, map_location=map_location, weights_only=False)
    except TypeError:
        return torch.load(path, map_location=map_location)


def load_checkpoint_state(
    checkpoint_dir: Path | str,
    model: Any,
    optimizer: Optional[Any] = None,
    scheduler: Optional[Any] = None,
    device: str = "cpu",
) -> dict[str, Any]:
    """Restores model, optimizer, scheduler, and RNG state from verified checkpoint directory."""
    import torch
    import numpy as np

    ckpt_path = Path(checkpoint_dir).resolve()
    valid, reason = verify_checkpoint_integrity(ckpt_path)
    if not valid:
        raise CheckpointIntegrityError(f"Checkpoint integrity verification failed for {ckpt_path}: {reason}")

    # 1. Model Weights
    if (ckpt_path / "model.safetensors").exists():
        try:
            from safetensors.torch import load_file
            state_dict = load_file(str(ckpt_path / "model.safetensors"), device=device)
        except Exception:
            state_dict = _safe_torch_load(ckpt_path / "model.safetensors", map_location=device)
        model.load_state_dict(state_dict)
    elif (ckpt_path / "pytorch_model.bin").exists():
        state_dict = _safe_torch_load(ckpt_path / "pytorch_model.bin", map_location=device)
        model.load_state_dict(state_dict)
    elif (ckpt_path / "model.pt").exists():
        state_dict = _safe_torch_load(ckpt_path / "model.pt", map_location=device)
        model.load_state_dict(state_dict)
    else:
        raise CheckpointIntegrityError(f"No model weight file found in {ckpt_path}")

    # 2. Optimizer State
    if optimizer is not None and (ckpt_path / "optimizer.pt").exists():
        opt_state = _safe_torch_load(ckpt_path / "optimizer.pt", map_location=device)
        optimizer.load_state_dict(opt_state)

    # 3. Scheduler State
    if (ckpt_path / "scheduler.pt").exists():
        sched_state = _safe_torch_load(ckpt_path / "scheduler.pt", map_location=device)
        if scheduler is not None and sched_state.get("scheduler_state") is not None:
            scheduler.load_state_dict(sched_state["scheduler_state"])

    # 4. RNG State
    if (ckpt_path / "rng_state.pt").exists():
        rng_payload = _safe_torch_load(ckpt_path / "rng_state.pt", map_location="cpu")
        if "torch" in rng_payload:
            torch.set_rng_state(rng_payload["torch"])
        if "numpy" in rng_payload:
            np.random.set_state(rng_payload["numpy"])
        if "python" in rng_payload:
            random.setstate(rng_payload["python"])

    # 5. Metadata
    meta_file = ckpt_path / "checkpoint_meta.json"
    if not meta_file.exists():
        meta_file = ckpt_path / "training_meta.json"
    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    return meta


def prepare_nli_model(
    model_dir: str,
    device: str = "cpu",
) -> tuple[Any, Any]:
    """Loads and initializes DeBERTa-v3-small for 3-class NLI in offline FP32 mode."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import torch
    from transformers import AutoConfig, AutoTokenizer, AutoModelForSequenceClassification

    config = AutoConfig.from_pretrained(
        model_dir,
        num_labels=3,
        id2label=ID_TO_NLI_LABEL,
        label2id=NLI_LABEL_MAP,
        local_files_only=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_dir,
        config=config,
        local_files_only=True,
    )
    model = model.float().to(device)
    return model, tokenizer


def execute_training(config: NLITrainingConfig, report_dir: str = "") -> dict[str, Any]:
    """Executes the complete bounded NLI training workflow with real-time watchdog enforcement.

    STRICT SAFETY GUARD: Requires explicit authorization flag (config.authorized=True).
    """
    if not config.authorized:
        raise TrainingNotAuthorizedError(
            "NLI training execution is NOT authorized. "
            "Track 2 Step 3.7 is an audit and verification step only. "
            "Pass authorized=True (or --authorize-nli-training) only after receiving explicit user authorization."
        )

    import numpy as np
    import torch

    print("=" * 80)
    print("TRUSTRAG BOUNDED 3-WAY NLI TRAINING EXPERIMENT")
    print("=" * 80)
    print(f"Pretrained Base:       {config.model_dir}")
    print(f"Output Checkpoint:     {config.output_dir}")
    print(f"Training Samples/Epoch:{config.max_train_samples} ({config.sampler_strategy})")
    print(f"Validation Samples:    {config.max_val_samples} (original imbalanced validation split)")
    print(f"Learning Rate:         {config.learning_rate} (warmup={config.warmup_steps}, decay=linear)")
    print(f"CPU Threads:           {config.num_threads}")
    print(f"Memory Safeguards:     RAM >= {config.ram_abort_threshold_mb}MB | Swap Growth <= {config.swap_growth_abort_mb}MB | Free Swap >= {config.swap_free_min_mb}MB")
    print(f"Wall-Clock Limit:      {config.max_duration_seconds}s ({config.max_duration_seconds / 3600.0:.2f} hours)")

    # 1. Environment & Concurrency Setup
    torch.set_num_threads(config.num_threads)
    try:
        torch.set_num_interop_threads(config.interop_threads)
    except Exception:
        pass
    torch.manual_seed(config.seed)
    np.random.seed(config.seed)
    random.seed(config.seed)

    # 2. Watchdog & Emergency Checkpoint Hook
    curr_epoch_ref = [1]
    curr_sample_ref = [0]
    curr_accum_ref = [0]
    curr_lr_ref = [config.learning_rate]

    def emergency_save(step: int, reason: str) -> None:
        emergency_dir = Path(config.output_dir) / "checkpoint_emergency"
        print(f"\n[EMERGENCY CHECKPOINT] Saving state at step {step} (Reason: {reason}) -> {emergency_dir}")
        try:
            save_checkpoint_state(
                model=model,
                tokenizer=tokenizer,
                optimizer=optimizer,
                checkpoint_dir=emergency_dir,
                step=step,
                epoch=curr_epoch_ref[0],
                sample_idx=curr_sample_ref[0],
                accum_count=curr_accum_ref[0],
                metrics={"step0": step0_metrics},
                current_lr=curr_lr_ref[0],
                best_epoch=best_epoch,
                best_step=best_step,
                best_macro_f1=best_macro_f1,
                best_val_loss=best_val_loss,
                epoch_history=epoch_history,
                pretrained_model_dir=config.model_dir,
                is_emergency=True,
                emergency_reason=reason,
            )
            print(f"[EMERGENCY CHECKPOINT] Successfully serialized to {emergency_dir}")
        except Exception as err:
            print(f"[EMERGENCY CHECKPOINT ERROR] Could not save: {err}")

    watchdog = WatchdogMonitor(
        ram_abort_threshold_mb=config.ram_abort_threshold_mb,
        swap_free_min_mb=config.swap_free_min_mb,
        max_process_rss_mb=config.max_process_rss_mb,
        max_duration_seconds=config.max_duration_seconds,
        consecutive_violations_threshold=config.watchdog_consecutive_violations,
        swap_growth_abort_mb=config.swap_growth_abort_mb,
        emergency_save_fn=emergency_save,
    )
    init_telemetry = watchdog.check(step=0)
    print(f"\n[Preflight Telemetry] Available RAM: {init_telemetry['available_ram_mb']:.1f} MB | RSS: {init_telemetry['rss_mb']:.1f} MB | Free Swap: {init_telemetry['swap_free_mb']:.1f} MB")

    # 3. Dataset Loading & Split Isolation Verification
    t0_data = time.perf_counter()
    train_records = load_nli_dataset(
        config.train_file,
        config.max_train_samples,
        strategy=config.sampler_strategy,
        seed=config.seed,
        shuffle=config.shuffle,
        max_starvation_threshold=config.max_starvation_threshold,
    )
    val_records = load_nli_dataset(config.val_file, config.max_val_samples, strategy="sequential")
    verify_split_isolation(train_records, val_records)
    print(f"[PASS] Loaded {len(train_records)} train records (strategy={config.sampler_strategy}) and {len(val_records)} val records in {time.perf_counter()-t0_data:.2f}s")

    # 4. Offline Model Loading & Head Initialization
    model, tokenizer = prepare_nli_model(config.model_dir, device="cpu")
    model.train()
    print(f"[PASS] Initialized DeBERTa-v3-small 3-class NLI model ({sum(p.numel() for p in model.parameters()):,} params in FP32)")

    # 5. Loss Function Configuration (Class-Weighted Cross-Entropy)
    if config.class_weights is not None:
        if len(config.class_weights) != config.num_classes:
            raise ValueError(f"class_weights must have {config.num_classes} elements, got {len(config.class_weights)}")
        weights_tensor = torch.tensor(config.class_weights, dtype=torch.float, device="cpu")
        loss_fct = torch.nn.CrossEntropyLoss(weight=weights_tensor)
        print(f"[Loss Configuration] Class-Weighted Cross-Entropy: {config.class_weights} (Order: ENTAILMENT=0, CONTRADICTION=1, NEUTRAL=2)")
    else:
        loss_fct = torch.nn.CrossEntropyLoss()
        print("[Loss Configuration] Standard Unweighted Cross-Entropy")

    # 6. Optimizer & Step Arithmetic Calculation
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
        betas=(0.9, 0.999),
        eps=1e-8,
    )

    samples_per_epoch = len(train_records)
    steps_per_epoch = math.ceil(samples_per_epoch / config.gradient_accumulation_steps)
    total_optimizer_steps = steps_per_epoch * config.epochs
    print(f"Epochs:                {config.epochs}")
    print(f"Samples per Epoch:     {samples_per_epoch}")
    print(f"Total Samples:         {samples_per_epoch * config.epochs}")
    print(f"Effective Batch Size:  {config.gradient_accumulation_steps * config.batch_size} (Accumulation Steps={config.gradient_accumulation_steps})")
    print(f"Steps per Epoch:       {steps_per_epoch}")
    print(f"Total Optimizer Steps: {total_optimizer_steps}")

    # 7. Checkpoint Resumption & State Restoration
    start_epoch = 1
    start_sample_idx = 0
    start_opt_step = 0
    accum_count = 0
    best_macro_f1 = -1.0
    best_val_loss = float("inf")
    best_epoch = 0
    best_step = 0
    epoch_history: list[dict[str, Any]] = []
    resume_meta: dict[str, Any] = {}

    resume_dir = None
    if config.resume_from_checkpoint:
        resume_dir = Path(config.resume_from_checkpoint).resolve()
        if not resume_dir.exists():
            raise FileNotFoundError(f"Specified resume checkpoint does not exist: {resume_dir}")
        if not resume_dir.is_dir():
            raise NotADirectoryError(f"Specified resume checkpoint is not a directory: {resume_dir}")
    elif config.auto_resume:
        latest_file = Path(config.output_dir) / "latest_checkpoint.json"
        if latest_file.is_file():
            try:
                latest_data = json.loads(latest_file.read_text(encoding="utf-8"))
                target_dir = Path(latest_data.get("latest_checkpoint_dir", ""))
                if target_dir.is_dir():
                    resume_dir = target_dir
            except Exception:
                pass

    if resume_dir is not None:
        print(f"\n[CHECKPOINT RESUME] Restoring training state from: {resume_dir}")
        try:
            resume_meta = load_checkpoint_state(resume_dir, model=model, optimizer=optimizer)
            start_epoch = resume_meta.get("epoch", 1)
            start_opt_step = resume_meta.get("step", 0)
            raw_sample_idx = resume_meta.get("sample_idx", 0)
            accum_count = resume_meta.get("accum_count", 0)
            best_macro_f1 = resume_meta.get("best_macro_f1", -1.0)
            best_val_loss = resume_meta.get("best_val_loss", float("inf"))
            best_epoch = resume_meta.get("best_epoch", 0)
            best_step = resume_meta.get("best_step", 0)
            epoch_history = resume_meta.get("epoch_history", [])

            # Check if checkpoint was saved at end-of-epoch boundary
            if raw_sample_idx >= samples_per_epoch - 1:
                start_epoch += 1
                start_sample_idx = 0
                accum_count = 0
                print(
                    f"[CHECKPOINT RESUME] Checkpoint was at end of Epoch {start_epoch - 1}. "
                    f"Advancing to Epoch {start_epoch}, Sample Index 0/{samples_per_epoch} (Accum: 0)."
                )
            else:
                start_sample_idx = raw_sample_idx + 1  # Next unconsumed sample
                print(
                    f"[CHECKPOINT RESUME] Restored to Epoch {start_epoch}, Step {start_opt_step}, "
                    f"Sample Index {start_sample_idx}/{samples_per_epoch} (Accum: {accum_count})"
                )
        except Exception as exc:
            print(f"[CHECKPOINT RESUME ERROR] Could not load checkpoint from {resume_dir}: {exc}")
            raise exc

    def get_lr(opt_step: int) -> float:
        if opt_step < config.warmup_steps:
            return config.learning_rate * float(opt_step) / float(max(1, config.warmup_steps))
        progress = float(opt_step - config.warmup_steps) / float(max(1, total_optimizer_steps - config.warmup_steps))
        return max(0.0, config.learning_rate * (1.0 - progress))

    def encode_item(rec: dict[str, Any]) -> dict[str, Any]:
        premise, hypothesis = serialize_nli_input(rec)
        if config.serialization_strategy == "evidence_preserving":
            return evidence_preserving_tokenize(
                tokenizer=tokenizer,
                premise=premise,
                hypothesis=hypothesis,
                max_seq_len=config.max_seq_len,
                min_premise_tokens=config.min_premise_tokens,
                device="cpu",
                dynamic_padding=config.dynamic_padding,
            )
        else:
            enc = tokenizer(
                premise,
                hypothesis,
                max_length=config.max_seq_len,
                truncation=True,
                padding=False if config.dynamic_padding else "max_length",
                return_tensors="pt",
            )
            return enc

    # Validation Evaluation Helper with Prediction Serialization
    def evaluate(
        eval_records: list[dict[str, Any]],
        desc: str = "Validation",
        save_predictions_path: Optional[Path] = None,
    ) -> dict[str, Any]:
        model.eval()
        losses = []
        preds = []
        targets = []
        probs_all = []
        sample_predictions = []
        with torch.no_grad():
            for idx, rec in enumerate(eval_records):
                y = NLI_LABEL_MAP[rec["nli_label"]]
                enc = encode_item(rec)
                kw = {
                    "input_ids": enc["input_ids"],
                    "attention_mask": enc["attention_mask"],
                }
                if "token_type_ids" in enc:
                    kw["token_type_ids"] = enc["token_type_ids"]

                out = model(**kw)
                logits = out.logits[0]
                label_tensor = torch.tensor([y], dtype=torch.long)
                loss_val = float(loss_fct(out.logits, label_tensor).item())
                losses.append(loss_val)
                probs = torch.softmax(logits, dim=-1).tolist()
                pred_cls = int(torch.argmax(logits, dim=-1).item())
                preds.append(pred_cls)
                targets.append(y)
                probs_all.append(probs)

                if save_predictions_path is not None:
                    sample_predictions.append({
                        "sample_id": rec.get("example_id", f"sample_{idx}"),
                        "true_label": rec["nli_label"],
                        "true_label_idx": y,
                        "predicted_label": ID_TO_NLI_LABEL[pred_cls],
                        "predicted_label_idx": pred_cls,
                        "logits": logits.tolist(),
                        "probabilities": probs,
                        "is_correct": bool(pred_cls == y),
                    })

                if (idx + 1) % 500 == 0 or (idx + 1) == len(eval_records):
                    print(f"  [{desc}] Evaluated {idx + 1}/{len(eval_records)} samples...")

        if save_predictions_path is not None:
            save_predictions_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_predictions_path, "w", encoding="utf-8") as f:
                for sp in sample_predictions:
                    f.write(json.dumps(sp) + "\n")
            print(f"[PASS] Persisted {len(sample_predictions)} validation predictions to: {save_predictions_path}")

        model.train()
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        return compute_nli_metrics(targets, preds, y_probs=probs_all, loss=avg_loss)

    # 8. Step 0 Pre-Training Baseline Evaluation
    if resume_dir is not None and "step0" in resume_meta.get("metrics", {}):
        step0_metrics = resume_meta["metrics"]["step0"]
        print(f"[Step 0 Baseline (Restored)] Loss: {step0_metrics.get('loss', 0.0):.4f} | Acc: {step0_metrics.get('accuracy', 0.0):.4f} | Bal Acc: {step0_metrics.get('balanced_accuracy', 0.0):.4f} | Macro F1: {step0_metrics.get('macro_f1', 0.0):.4f}")
    else:
        print("\n--- Running Step 0 Pre-Training Baseline Validation ---")
        step0_metrics = evaluate(val_records, desc="Pre-Training Baseline")
        print(f"[Step 0 Baseline] Loss: {step0_metrics['loss']:.4f} | Acc: {step0_metrics['accuracy']:.4f} | Bal Acc: {step0_metrics['balanced_accuracy']:.4f} | Macro F1: {step0_metrics['macro_f1']:.4f}")

    # 9. Multi-Epoch Training Loop with Gradient Accumulation & Sub-Epoch Checkpoints
    print(f"\n--- Starting Multi-Epoch Training Loop ({config.epochs} epochs, {total_optimizer_steps} optimizer steps) ---")
    watchdog.reset_baseline()
    post_val_telemetry = watchdog.baseline_telemetry
    print(f"[Training Loop Telemetry Baseline] Available RAM: {post_val_telemetry['available_ram_mb']:.1f} MB | RSS: {post_val_telemetry['rss_mb']:.1f} MB | Swap Used: {post_val_telemetry['swap_used_mb']:.1f} MB | Free Swap: {post_val_telemetry['swap_free_mb']:.1f} MB")
    train_losses = []
    step_telemetry_log = []
    best_state_dict: Optional[dict[str, Any]] = None
    opt_step = start_opt_step
    optimizer.zero_grad(set_to_none=True)

    for epoch in range(1, config.epochs + 1):
        if epoch < start_epoch:
            continue
        print(f"\n--- Epoch {epoch}/{config.epochs} Starting ---")
        epoch_losses = []

        for step_idx, rec in enumerate(train_records):
            if epoch == start_epoch and step_idx < start_sample_idx:
                continue

            current_lr = get_lr(opt_step)
            curr_epoch_ref[0] = epoch
            curr_sample_ref[0] = step_idx
            curr_accum_ref[0] = accum_count
            curr_lr_ref[0] = current_lr

            for param_group in optimizer.param_groups:
                param_group["lr"] = current_lr

            target_label = NLI_LABEL_MAP[rec["nli_label"]]
            encoding = encode_item(rec)
            kwargs = {
                "input_ids": encoding["input_ids"],
                "attention_mask": encoding["attention_mask"],
            }
            if "token_type_ids" in encoding:
                kwargs["token_type_ids"] = encoding["token_type_ids"]

            outputs = model(**kwargs)
            labels = torch.tensor([target_label], dtype=torch.long)
            raw_loss = loss_fct(outputs.logits, labels)
            loss = raw_loss / config.gradient_accumulation_steps
            loss_val = float(raw_loss.item())
            epoch_losses.append(loss_val)
            train_losses.append(loss_val)

            loss.backward()
            accum_count += 1
            curr_accum_ref[0] = accum_count

            is_last_sample_of_epoch = (step_idx + 1 == len(train_records))
            if accum_count == config.gradient_accumulation_steps or is_last_sample_of_epoch:
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=config.max_grad_norm)
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                opt_step += 1
                accum_count = 0
                curr_accum_ref[0] = 0

                step_telemetry = watchdog.check(step=opt_step)

                # Periodic sub-epoch checkpoint saving
                if config.checkpoint_every_steps > 0 and opt_step % config.checkpoint_every_steps == 0:
                    step_ckpt_dir = Path(config.output_dir) / f"checkpoint_step_{opt_step:06d}"
                    print(f"\n[Sub-Epoch Checkpoint] Saving periodic checkpoint at Step {opt_step} -> {step_ckpt_dir}")
                    try:
                        save_checkpoint_state(
                            model=model,
                            tokenizer=tokenizer,
                            optimizer=optimizer,
                            checkpoint_dir=step_ckpt_dir,
                            step=opt_step,
                            epoch=epoch,
                            sample_idx=step_idx,
                            accum_count=accum_count,
                            metrics={"step0": step0_metrics},
                            current_lr=current_lr,
                            best_epoch=best_epoch,
                            best_step=best_step,
                            best_macro_f1=best_macro_f1,
                            best_val_loss=best_val_loss,
                            epoch_history=epoch_history,
                            pretrained_model_dir=config.model_dir,
                        )
                        prune_old_checkpoints(config.output_dir, keep_last_n=config.keep_last_n_checkpoints)
                    except Exception as exc:
                        print(f"[Sub-Epoch Checkpoint Warning] Could not save step checkpoint: {exc}")

                if opt_step % config.log_every_steps == 0 or opt_step == total_optimizer_steps:
                    rolling_loss = sum(train_losses[-config.log_every_steps:]) / len(train_losses[-config.log_every_steps:])
                    print(
                        f"Epoch {epoch}/{config.epochs} | "
                        f"Step {opt_step:4d}/{total_optimizer_steps} | "
                        f"Loss: {loss_val:.4f} (Rolling: {rolling_loss:.4f}) | "
                        f"LR: {current_lr:.2e} | "
                        f"RSS: {step_telemetry['rss_mb']:.1f} MB | "
                        f"Avail RAM: {step_telemetry['available_ram_mb']:.1f} MB | "
                        f"Elapsed: {step_telemetry['elapsed_seconds']:.1f}s"
                    )
                    step_telemetry_log.append({
                        "epoch": epoch,
                        "step": opt_step,
                        "loss": loss_val,
                        "rolling_loss": rolling_loss,
                        "lr": current_lr,
                        "telemetry": step_telemetry,
                    })

            del outputs, raw_loss, loss, encoding

        # End of Epoch Validation
        print(f"\n--- Running End-of-Epoch {epoch} Validation ---")
        epoch_val_metrics = evaluate(val_records, desc=f"Epoch {epoch} Validation")
        con_recall = epoch_val_metrics["per_class"]["CONTRADICTION"]["recall"]
        print(
            f"[Epoch {epoch} Validation] Loss: {epoch_val_metrics['loss']:.4f} | "
            f"Acc: {epoch_val_metrics['accuracy']:.4f} | "
            f"Bal Acc: {epoch_val_metrics['balanced_accuracy']:.4f} | "
            f"Macro F1: {epoch_val_metrics['macro_f1']:.4f} | "
            f"Con Recall: {con_recall:.4f}"
        )

        is_best = (epoch_val_metrics["macro_f1"] > best_macro_f1) or (
            epoch_val_metrics["macro_f1"] == best_macro_f1 and epoch_val_metrics["loss"] < best_val_loss
        )
        if is_best:
            best_macro_f1 = epoch_val_metrics["macro_f1"]
            best_val_loss = epoch_val_metrics["loss"]
            best_epoch = epoch
            best_step = opt_step
            best_state_dict = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            print(f"  >>> Best Model Selected at Epoch {epoch} (Macro F1: {best_macro_f1:.4f}, Loss: {best_val_loss:.4f})")
            try:
                save_checkpoint_state(
                    model=model,
                    tokenizer=tokenizer,
                    optimizer=optimizer,
                    checkpoint_dir=config.output_dir,
                    step=opt_step,
                    epoch=epoch,
                    sample_idx=len(train_records) - 1,
                    accum_count=0,
                    metrics={
                        "step0": step0_metrics,
                        "best_epoch": best_epoch,
                        "best_step": best_step,
                        "interim_val": epoch_val_metrics,
                        "epoch_history": epoch_history,
                    },
                    current_lr=current_lr,
                    best_epoch=best_epoch,
                    best_step=best_step,
                    best_macro_f1=best_macro_f1,
                    best_val_loss=best_val_loss,
                    epoch_history=epoch_history,
                    pretrained_model_dir=config.model_dir,
                    is_best=True,
                )
                print(f"  [Interim Checkpoint] Saved best checkpoint to {config.output_dir}")
            except Exception as exc:
                print(f"  [Warning] Could not save interim checkpoint: {exc}")

        epoch_history.append({
            "epoch": epoch,
            "optimizer_step": opt_step,
            "val_metrics": epoch_val_metrics,
            "is_best": is_best,
        })

        if report_dir:
            rep_path = Path(report_dir)
            rep_path.mkdir(parents=True, exist_ok=True)
            interim_results = {
                "status": "RUNNING",
                "current_epoch": epoch,
                "epochs": config.epochs,
                "opt_step": opt_step,
                "total_optimizer_steps": total_optimizer_steps,
                "best_epoch": best_epoch,
                "best_macro_f1": best_macro_f1,
                "best_val_loss": best_val_loss,
                "epoch_history": epoch_history,
                "initial_metrics": step0_metrics,
                "telemetry_log": step_telemetry_log,
            }
            with open(rep_path / "training_results.json", "w", encoding="utf-8") as f:
                json.dump(interim_results, f, indent=2)

    # 10. Model Restoration & Final Validation with Prediction Persistence
    if best_state_dict is not None:
        model.load_state_dict(best_state_dict)
        print(f"\n[Model Selection] Restored best model weights from Epoch {best_epoch} (Macro F1: {best_macro_f1:.4f})")

    rep_path = Path(report_dir) if report_dir else Path(config.output_dir)
    pred_path = rep_path / "predictions_val.jsonl" if config.save_predictions else None
    print(f"\n--- Running Final Validation on Selected Model ---")
    final_metrics = evaluate(val_records, desc="Best Model Final Validation", save_predictions_path=pred_path)
    print(
        f"[Final Validation] Loss: {final_metrics['loss']:.4f} | "
        f"Acc: {final_metrics['accuracy']:.4f} | "
        f"Bal Acc: {final_metrics['balanced_accuracy']:.4f} | "
        f"Macro F1: {final_metrics['macro_f1']:.4f} | "
        f"Con Recall: {final_metrics['per_class']['CONTRADICTION']['recall']:.4f}"
    )

    # 11. Final Atomic Checkpoint Serialization
    print(f"\n--- Serializing Final Atomic Checkpoint to {config.output_dir} ---")
    checkpoint_path = save_checkpoint_state(
        model=model,
        tokenizer=tokenizer,
        optimizer=optimizer,
        checkpoint_dir=config.output_dir,
        step=opt_step,
        epoch=config.epochs,
        sample_idx=len(train_records) - 1,
        accum_count=0,
        metrics={
            "step0": step0_metrics,
            "best_epoch": best_epoch,
            "best_step": best_step,
            "final": final_metrics,
            "epoch_history": epoch_history,
        },
        current_lr=0.0,
        best_epoch=best_epoch,
        best_step=best_step,
        best_macro_f1=best_macro_f1,
        best_val_loss=best_val_loss,
        epoch_history=epoch_history,
        pretrained_model_dir=config.model_dir,
        is_best=True,
    )
    print(f"[PASS] Successfully saved atomic checkpoint to: {checkpoint_path}")

    results = {
        "status": "COMPLETED",
        "total_samples": len(train_records) * config.epochs,
        "samples_per_epoch": len(train_records),
        "epochs": config.epochs,
        "gradient_accumulation_steps": config.gradient_accumulation_steps,
        "steps_per_epoch": steps_per_epoch,
        "total_optimizer_steps": total_optimizer_steps,
        "sampler_strategy": config.sampler_strategy,
        "class_weights": config.class_weights,
        "best_epoch": best_epoch,
        "best_step": best_step,
        "best_macro_f1": best_macro_f1,
        "best_val_loss": best_val_loss,
        "epoch_history": epoch_history,
        "initial_metrics": step0_metrics,
        "final_metrics": final_metrics,
        "checkpoint_path": str(checkpoint_path),
        "initial_train_loss": train_losses[0] if train_losses else None,
        "final_train_loss": train_losses[-1] if train_losses else None,
        "avg_train_loss": sum(train_losses) / len(train_losses) if train_losses else None,
        "peak_rss_mb": watchdog.peak_rss_mb,
        "telemetry_log": step_telemetry_log,
    }

    if report_dir:
        rep_path = Path(report_dir)
        rep_path.mkdir(parents=True, exist_ok=True)
        with open(rep_path / "training_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"[PASS] Successfully wrote training results to {rep_path / 'training_results.json'}")

        meta = {
            "model_dir": config.model_dir,
            "train_file": config.train_file,
            "val_file": config.val_file,
            "output_dir": config.output_dir,
            "epochs": config.epochs,
            "gradient_accumulation_steps": config.gradient_accumulation_steps,
            "sampler_strategy": config.sampler_strategy,
            "class_weights": config.class_weights,
            "learning_rate": config.learning_rate,
            "warmup_steps": config.warmup_steps,
            "weight_decay": config.weight_decay,
            "max_seq_len": config.max_seq_len,
            "min_premise_tokens": config.min_premise_tokens,
            "seed": config.seed,
            "num_threads": config.num_threads,
            "max_duration_seconds": config.max_duration_seconds,
            "best_epoch": best_epoch,
            "best_step": best_step,
            "best_macro_f1": best_macro_f1,
            "best_val_loss": best_val_loss,
        }
        with open(rep_path / "training_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        print(f"[PASS] Successfully wrote training metadata to {rep_path / 'training_meta.json'}")

    return results


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TrustRAG 3-Way NLI Training Runner")
    parser.add_argument("--authorize-nli-training", action="store_true", default=False, help="Explicit authorization flag")
    parser.add_argument("--model-dir", type=str, default="/home/aditya/rags/models/pretrained/deberta-v3-small")
    parser.add_argument("--train-file", type=str, default="/home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/train.jsonl")
    parser.add_argument("--val-file", type=str, default="/home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/validation.jsonl")
    parser.add_argument("--output-dir", type=str, default="/home/aditya/rags/models/trained/deberta-v3-small-nli-remediated")
    parser.add_argument("--report-dir", type=str, default="/home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_step03_10_remediation")
    parser.add_argument("--max-train-samples", type=int, default=1000)
    parser.add_argument("--max-val-samples", type=int, default=2662)
    parser.add_argument("--epochs", type=int, default=1, help="Number of training epochs")
    parser.add_argument("--gradient-accumulation-steps", type=int, default=4, help="Number of steps for gradient accumulation")
    parser.add_argument(
        "--sampler-strategy",
        type=str,
        choices=["stratified_class_balanced", "sequential"],
        default="stratified_class_balanced",
        help="Sampling strategy: stratified_class_balanced or sequential",
    )
    parser.add_argument(
        "--class-weights",
        type=float,
        nargs=3,
        default=None,
        help="Class weights for cross-entropy loss [w_entailment, w_contradiction, w_neutral]",
    )
    parser.add_argument("--save-predictions", action="store_true", default=False, help="Persist validation predictions")
    parser.add_argument("--max-seq-len", type=int, default=384)
    parser.add_argument("--min-premise-tokens", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--warmup-steps", type=int, default=100)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--num-threads", type=int, default=10, help="PyTorch CPU intra-op threads")
    parser.add_argument("--interop-threads", type=int, default=1, help="PyTorch CPU inter-op threads")
    parser.add_argument("--no-dynamic-padding", action="store_true", default=False, help="Disable dynamic sequence padding")
    parser.add_argument("--checkpoint-every-steps", type=int, default=500, help="Periodic sub-epoch checkpoint frequency")
    parser.add_argument("--keep-last-n-checkpoints", type=int, default=2, help="Number of recent step checkpoints to retain")
    parser.add_argument("--resume-from-checkpoint", type=str, default=None, help="Specific checkpoint directory to resume from")
    parser.add_argument("--no-auto-resume", action="store_true", default=False, help="Disable automatic checkpoint resumption")
    parser.add_argument("--ram-abort-threshold-mb", type=float, default=700.0)
    parser.add_argument("--swap-free-min-mb", type=float, default=1000.0)
    parser.add_argument("--max-process-rss-mb", type=float, default=4500.0)
    parser.add_argument("--watchdog-consecutive-violations", type=int, default=3)
    parser.add_argument("--swap-growth-abort-mb", type=float, default=None, help="Optional swap growth abort threshold")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--max-duration-seconds",
        type=float,
        default=3600.0,
        help="Maximum allowed total training pipeline duration in seconds",
    )
    parsed = parser.parse_args(args)
    # Validate --max-duration-seconds: reject zero, negative, NaN, and infinite values
    if not (parsed.max_duration_seconds > 0 and math.isfinite(parsed.max_duration_seconds)):
        parser.error(
            f"--max-duration-seconds must be a positive finite number, got {parsed.max_duration_seconds}"
        )
    return parsed


if __name__ == "__main__":
    args = parse_args()
    cfg = NLITrainingConfig(
        model_dir=args.model_dir,
        train_file=args.train_file,
        val_file=args.val_file,
        output_dir=args.output_dir,
        max_train_samples=args.max_train_samples,
        max_val_samples=args.max_val_samples,
        epochs=args.epochs,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        sampler_strategy=args.sampler_strategy,
        class_weights=args.class_weights,
        save_predictions=args.save_predictions,
        max_seq_len=args.max_seq_len,
        min_premise_tokens=args.min_premise_tokens,
        learning_rate=args.learning_rate,
        warmup_steps=args.warmup_steps,
        weight_decay=args.weight_decay,
        num_threads=args.num_threads,
        interop_threads=args.interop_threads,
        dynamic_padding=not args.no_dynamic_padding,
        checkpoint_every_steps=args.checkpoint_every_steps,
        keep_last_n_checkpoints=args.keep_last_n_checkpoints,
        resume_from_checkpoint=args.resume_from_checkpoint,
        auto_resume=not args.no_auto_resume,
        ram_abort_threshold_mb=args.ram_abort_threshold_mb,
        swap_free_min_mb=args.swap_free_min_mb,
        max_process_rss_mb=args.max_process_rss_mb,
        watchdog_consecutive_violations=args.watchdog_consecutive_violations,
        swap_growth_abort_mb=args.swap_growth_abort_mb,
        seed=args.seed,
        max_duration_seconds=args.max_duration_seconds,
        authorized=args.authorize_nli_training,
    )
    if not cfg.authorized:
        print("[SAFETY ABORT] --authorize-nli-training was NOT provided. Exiting safely.")
        sys.exit(1)
    results = execute_training(cfg, report_dir=args.report_dir)
    print("Execution completed.")
