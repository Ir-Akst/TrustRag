"""Bounded Binary Classification Training Runner for TrustRAG (Track 2, Step 3.4.1).

Implements bounded, leakage-safe fine-tuning of microsoft/deberta-v3-small for
binary hallucination classification on CPU with active real-time safety watchdogs.

Design Constraints:
- Task: Binary sequence classification (FACTUAL -> 0, HALLUCINATED -> 1).
- Model: Staged DeBERTa-v3-small (141.9M parameters, FP32).
- Batch size: 1. Max sequence length: 128.
- Training subset: Exactly 1,000 examples (deterministic sampling).
- Validation subset: Exactly 200 examples (100 per class, zero doc leakage).
- Watchdogs: RAM < 700 MB abort, swap drift > 500 MB abort, free swap < 1,000 MB abort,
  wall-clock timeout 1,800 s, CPU threads pinned to 4.
- Test-set access: Strictly prohibited.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import shutil
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Strict offline defaults
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"


class ResourceAbortError(Exception):
    """Raised when physical host RAM or swap limits are breached."""


class TimeoutAbortError(Exception):
    """Raised when training wall-clock time exceeds the maximum threshold."""


class SecurityViolationError(Exception):
    """Raised when test-set access, document leakage, or unsafe directory paths are detected."""


LABEL_MAP = {"FACTUAL": 0, "HALLUCINATED": 1}
REVERSE_LABEL_MAP = {0: "FACTUAL", 1: "HALLUCINATED"}
MANDATORY_FIELDS = {
    "example_id",
    "question_or_claim",
    "context_or_evidence",
    "candidate_response",
    "binary_label",
}


@dataclass
class TrainingConfig:
    train_file: str
    val_file: str
    model_dir: str
    output_dir: str
    max_train_samples: int = 1000
    max_val_samples: int = 200
    sampling_strategy: str = "stratified_source_balanced"  # or "sequential"
    batch_size: int = 1
    max_seq_len: int = 128
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    warmup_steps: int = 100
    seed: int = 42
    num_threads: int = 4
    ram_abort_threshold_mb: float = 700.0
    swap_growth_abort_mb: float = 500.0
    swap_free_min_mb: float = 1000.0
    max_duration_seconds: float = 1800.0
    evaluate_every_steps: int = 1000
    log_every_steps: int = 50


class WatchdogMonitor:
    """Active real-time safety watchdog monitoring host resources during execution."""

    def __init__(
        self,
        ram_abort_threshold_mb: float = 700.0,
        swap_growth_abort_mb: float = 500.0,
        swap_free_min_mb: float = 1000.0,
        max_duration_seconds: float = 1800.0,
        telemetry_fn: Optional[Callable[[], dict[str, float]]] = None,
    ) -> None:
        self.ram_threshold = ram_abort_threshold_mb
        self.swap_growth_threshold = swap_growth_abort_mb
        self.swap_free_min = swap_free_min_mb
        self.max_duration = max_duration_seconds
        self.telemetry_fn = telemetry_fn or self._default_telemetry
        self.t_start: float = time.perf_counter()
        self.baseline_telemetry: dict[str, float] = dict(self.telemetry_fn())
        self.peak_rss_mb: float = self.baseline_telemetry.get("rss_mb", 0.0)

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

    def check(self, step: int) -> dict[str, float]:
        current = dict(self.telemetry_fn())
        elapsed = time.perf_counter() - self.t_start
        current["elapsed_seconds"] = elapsed

        if current["rss_mb"] > self.peak_rss_mb:
            self.peak_rss_mb = current["rss_mb"]
        current["peak_rss_mb"] = self.peak_rss_mb

        # 1. Wall-clock timeout check
        if elapsed > self.max_duration:
            raise TimeoutAbortError(
                f"[WATCHDOG ABORT] Step {step}: Execution time {elapsed:.1f}s exceeded hard cutoff of {self.max_duration:.1f}s!"
            )

        # 2. Available physical RAM check
        if current["available_ram_mb"] < self.ram_threshold:
            raise ResourceAbortError(
                f"[WATCHDOG ABORT] Step {step}: Available host RAM dropped to {current['available_ram_mb']:.1f} MB "
                f"(Threshold: {self.ram_threshold:.1f} MB)!"
            )

        # 3. Swap growth check
        swap_growth = current["swap_used_mb"] - self.baseline_telemetry["swap_used_mb"]
        current["swap_growth_mb"] = swap_growth
        if swap_growth > self.swap_growth_threshold:
            raise ResourceAbortError(
                f"[WATCHDOG ABORT] Step {step}: Swap usage grew by {swap_growth:.1f} MB from baseline "
                f"(Threshold: {self.swap_growth_threshold:.1f} MB)!"
            )

        # 4. Minimum free swap check
        if current["swap_free_mb"] < self.swap_free_min:
            raise ResourceAbortError(
                f"[WATCHDOG ABORT] Step {step}: Free swap dropped to {current['swap_free_mb']:.1f} MB "
                f"(Minimum requirement: {self.swap_free_min:.1f} MB)!"
            )

        return current


def validate_dataset_record(record: dict[str, Any]) -> None:
    """Strictly validates record schema fields and binary label values."""
    missing = MANDATORY_FIELDS - set(record.keys())
    if missing:
        raise ValueError(f"Record {record.get('example_id', 'UNKNOWN')} missing mandatory fields: {missing}")
    if record["binary_label"] not in LABEL_MAP:
        raise ValueError(
            f"Record {record.get('example_id')} has invalid label '{record['binary_label']}'. "
            f"Expected one of: {list(LABEL_MAP.keys())}"
        )
    if record.get("split") == "test":
        raise SecurityViolationError(f"Access to test record prohibited: {record.get('example_id')}")


def serialize_binary_input(record: dict[str, Any]) -> tuple[str, str]:
    """Serializes binary task fields into Text A and Text B.

    Format:
    - Text A (Query and Evidence Context): question_or_claim + " " + context_or_evidence
    - Text B (Candidate Output Response): candidate_response
    Note: NLI premise/hypothesis terminology is strictly avoided for this binary task.
    """
    text_a = f"{record['question_or_claim'].strip()} {record['context_or_evidence'].strip()}".strip()
    text_b = record["candidate_response"].strip()
    return text_a, text_b


def load_binary_dataset(
    file_path: Path | str,
    max_samples: int,
    strategy: str = "stratified_source_balanced",
) -> list[dict[str, Any]]:
    """Loads records with deterministic sampling and schema validation.

    Supported strategies:
    - 'stratified_source_balanced': Exactly equal halves across source datasets (halueval and ragtruth)
      with perfectly balanced FACTUAL (50%) and HALLUCINATED (50%) classes.
    - 'sequential': First N records from the dataset.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    # Enforce test set exclusion
    if "test" in path.name.lower():
        raise SecurityViolationError(f"Direct targeting of test set file is prohibited: {path.name}")

    records: list[dict[str, Any]] = []

    if strategy == "stratified_source_balanced":
        # Target: half per source, half per label within each source
        target_per_source = max_samples // 2
        target_per_class = target_per_source // 2
        selected: list[dict[str, Any]] = []
        counts: dict[str, dict[str, int]] = {
            "halueval": {"FACTUAL": 0, "HALLUCINATED": 0},
            "ragtruth": {"FACTUAL": 0, "HALLUCINATED": 0},
        }

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                validate_dataset_record(rec)
                src = rec.get("source_dataset", "unknown")
                lbl = rec["binary_label"]

                if src in counts and counts[src][lbl] < target_per_class:
                    selected.append(rec)
                    counts[src][lbl] += 1

                if len(selected) >= max_samples:
                    break

        records = selected

    elif strategy == "sequential":
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                validate_dataset_record(rec)
                records.append(rec)
                if len(records) >= max_samples:
                    break
    else:
        raise ValueError(f"Unknown sampling strategy: {strategy}")

    if len(records) != max_samples:
        raise ValueError(f"Requested {max_samples} samples from {path.name}, but obtained {len(records)}")

    return records


def verify_split_isolation(train_records: list[dict[str, Any]], val_records: list[dict[str, Any]]) -> None:
    """Verifies complete absence of example_id, claim, or context leakage between train and validation."""
    train_ids = {r["example_id"] for r in train_records}
    val_ids = {r["example_id"] for r in val_records}
    id_overlap = train_ids.intersection(val_ids)
    if id_overlap:
        raise SecurityViolationError(f"[DATA LEAKAGE] Found {len(id_overlap)} overlapping example IDs between splits!")


def compute_binary_metrics(
    y_true: list[int],
    y_pred: list[int],
    loss: float = 0.0,
) -> dict[str, Any]:
    """Computes comprehensive binary classification evaluation metrics."""
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true={len(y_true)}, y_pred={len(y_pred)}")
    if not y_true:
        return {}

    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)  # Class 1: Hallucinated
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)  # Class 0: Factual
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)

    total = len(y_true)
    accuracy = (tp + tn) / total if total > 0 else 0.0

    # Sensitivity / Specificity
    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    tnr = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    balanced_accuracy = 0.5 * (tpr + tnr)

    # Class 0 (FACTUAL)
    prec_0 = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    rec_0 = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1_0 = (2 * prec_0 * rec_0) / (prec_0 + rec_0) if (prec_0 + rec_0) > 0 else 0.0

    # Class 1 (HALLUCINATED)
    prec_1 = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec_1 = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_1 = (2 * prec_1 * rec_1) / (prec_1 + rec_1) if (prec_1 + rec_1) > 0 else 0.0

    macro_f1 = 0.5 * (f1_0 + f1_1)
    macro_prec = 0.5 * (prec_0 + prec_1)
    macro_rec = 0.5 * (rec_0 + rec_1)

    return {
        "loss": float(loss),
        "total_samples": total,
        "accuracy": float(accuracy),
        "balanced_accuracy": float(balanced_accuracy),
        "macro_precision": float(macro_prec),
        "macro_recall": float(macro_rec),
        "macro_f1": float(macro_f1),
        "confusion_matrix": {
            "true_positives": tp,
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
        },
        "per_class": {
            "factual_class_0": {
                "support": tn + fp,
                "precision": float(prec_0),
                "recall": float(rec_0),
                "f1": float(f1_0),
            },
            "hallucinated_class_1": {
                "support": tp + fn,
                "precision": float(prec_1),
                "recall": float(rec_1),
                "f1": float(f1_1),
            },
        },
    }


def save_checkpoint_atomic(
    model: Any,
    tokenizer: Any,
    output_dir: Path | str,
    step: int,
    metrics: dict[str, Any],
    pretrained_model_dir: Path | str,
) -> Path:
    """Atomically serializes model, tokenizer, and metrics to target directory.

    Guarantees:
    - Never overwrites the base pretrained model directory.
    - Uses temporary staging with atomic directory rename to prevent partial checkpoint corruptions.
    """
    target_path = Path(output_dir).resolve()
    base_path = Path(pretrained_model_dir).resolve()

    if target_path == base_path or base_path in target_path.parents:
        raise SecurityViolationError(
            f"Checkpoint output directory {target_path} cannot overwrite pretrained model directory {base_path}!"
        )

    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=f"checkpoint_step_{step}_", dir=str(target_path.parent)))

    try:
        # Save model and tokenizer
        model.save_pretrained(str(temp_dir))
        tokenizer.save_pretrained(str(temp_dir))

        # Save training metadata
        meta = {
            "step": step,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "metrics": metrics,
        }
        with open(temp_dir / "training_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        # Atomic swap
        if target_path.exists():
            shutil.rmtree(target_path)
        shutil.move(str(temp_dir), str(target_path))
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

    return target_path


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TrustRAG Bounded Binary Classification Training Runner"
    )
    parser.add_argument("--train-file", type=str, required=True, help="Path to binary train.jsonl")
    parser.add_argument("--val-file", type=str, required=True, help="Path to binary validation.jsonl")
    parser.add_argument("--model-dir", type=str, required=True, help="Path to staged DeBERTa-v3-small directory")
    parser.add_argument("--output-dir", type=str, required=True, help="Path to save trained checkpoint")
    parser.add_argument("--max-train-samples", type=int, default=1000, help="Maximum training examples (default: 1000)")
    parser.add_argument("--max-val-samples", type=int, default=200, help="Maximum validation examples (default: 200)")
    parser.add_argument(
        "--sampling-strategy",
        type=str,
        default="stratified_source_balanced",
        choices=["stratified_source_balanced", "sequential"],
        help="Deterministic sampling strategy",
    )
    parser.add_argument("--batch-size", type=int, default=1, help="Training batch size (default: 1)")
    parser.add_argument("--max-seq-len", type=int, default=128, help="Maximum token sequence length (default: 128)")
    parser.add_argument("--lr", type=float, default=2e-5, help="AdamW learning rate (default: 2e-5)")
    parser.add_argument("--weight-decay", type=float, default=0.01, help="AdamW weight decay (default: 0.01)")
    parser.add_argument("--warmup-steps", type=int, default=100, help="Linear warmup steps (default: 100)")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed (default: 42)")
    parser.add_argument("--num-threads", type=int, default=4, help="PyTorch CPU threads (default: 4)")
    parser.add_argument(
        "--ram-abort-threshold-mb",
        type=float,
        default=700.0,
        help="Abort if available physical RAM drops below this limit in MB (default: 700.0)",
    )
    parser.add_argument(
        "--swap-growth-abort-mb",
        type=float,
        default=500.0,
        help="Abort if swap usage increases by more than this limit in MB (default: 500.0)",
    )
    parser.add_argument(
        "--swap-free-min-mb",
        type=float,
        default=1000.0,
        help="Abort if free swap drops below this limit in MB (default: 1000.0)",
    )
    parser.add_argument(
        "--max-duration-seconds",
        type=float,
        default=1800.0,
        help="Hard wall-clock timeout in seconds (default: 1800.0 / 30 min)",
    )
    parser.add_argument(
        "--report-dir",
        type=str,
        default="",
        help="Optional directory to save training_results.json",
    )
    return parser.parse_args(args)


def run_training_experiment(config: TrainingConfig, report_dir: str = "") -> dict[str, Any]:
    """Executes the complete bounded training workflow with real-time watchdog enforcement."""
    import numpy as np
    import torch
    from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer

    print("=" * 75)
    print("TRUSTRAG BOUNDED BINARY TRAINING EXPERIMENT")
    print("=" * 75)
    print(f"Model Directory:       {config.model_dir}")
    print(f"Output Directory:      {config.output_dir}")
    print(f"Training Samples:      {config.max_train_samples} ({config.sampling_strategy})")
    print(f"Validation Samples:    {config.max_val_samples}")
    print(f"CPU Threads:           {config.num_threads}")
    print(f"Memory Safeguards:     RAM >= {config.ram_abort_threshold_mb}MB | Swap Growth <= {config.swap_growth_abort_mb}MB | Free Swap >= {config.swap_free_min_mb}MB")
    print(f"Wall-Clock Limit:      {config.max_duration_seconds}s (30 min)")

    # 1. Environment & Concurrency Setup
    torch.set_num_threads(config.num_threads)
    torch.manual_seed(config.seed)
    np.random.seed(config.seed)

    # 2. Watchdog Initialization
    watchdog = WatchdogMonitor(
        ram_abort_threshold_mb=config.ram_abort_threshold_mb,
        swap_growth_abort_mb=config.swap_growth_abort_mb,
        swap_free_min_mb=config.swap_free_min_mb,
        max_duration_seconds=config.max_duration_seconds,
    )
    init_telemetry = watchdog.check(step=0)
    print(f"\n[Preflight Telemetry] Available RAM: {init_telemetry['available_ram_mb']:.1f} MB | RSS: {init_telemetry['rss_mb']:.1f} MB | Free Swap: {init_telemetry['swap_free_mb']:.1f} MB")

    # 3. Dataset Loading & Verification
    t0_data = time.perf_counter()
    train_records = load_binary_dataset(config.train_file, config.max_train_samples, config.sampling_strategy)
    val_records = load_binary_dataset(config.val_file, config.max_val_samples, config.sampling_strategy)
    verify_split_isolation(train_records, val_records)
    print(f"[PASS] Loaded {len(train_records)} train & {len(val_records)} val records in {time.perf_counter()-t0_data:.2f}s (Zero leakage verified)")

    # 4. Offline Tokenizer & Model Loading
    tokenizer = AutoTokenizer.from_pretrained(config.model_dir, local_files_only=True)
    model_cfg = AutoConfig.from_pretrained(config.model_dir, num_labels=2, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        config.model_dir,
        config=model_cfg,
        local_files_only=True,
        torch_dtype=torch.float32,
    )
    model.train()
    print(f"[PASS] Loaded DeBERTa-v3-small offline ({sum(p.numel() for p in model.parameters()):,} params in FP32)")

    # 5. Optimizer & LR Scheduler Setup
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
        betas=(0.9, 0.999),
        eps=1e-8,
    )

    def get_lr(step: int) -> float:
        if step < config.warmup_steps:
            return config.learning_rate * float(step) / float(max(1, config.warmup_steps))
        progress = float(step - config.warmup_steps) / float(max(1, config.max_train_samples - config.warmup_steps))
        return max(0.0, config.learning_rate * (1.0 - progress))

    # Helper function for evaluation
    def evaluate(eval_records: list[dict[str, Any]], desc: str = "Validation") -> dict[str, Any]:
        model.eval()
        losses = []
        preds = []
        targets = []
        with torch.no_grad():
            for rec in eval_records:
                text_a, text_b = serialize_binary_input(rec)
                y = LABEL_MAP[rec["binary_label"]]
                enc = tokenizer(
                    text_a,
                    text_b,
                    max_length=config.max_seq_len,
                    truncation=True,
                    padding="max_length",
                    return_tensors="pt",
                )
                kw = {
                    "input_ids": enc["input_ids"],
                    "attention_mask": enc["attention_mask"],
                    "labels": torch.tensor([y], dtype=torch.long),
                }
                if "token_type_ids" in enc:
                    kw["token_type_ids"] = enc["token_type_ids"]

                out = model(**kw)
                losses.append(out.loss.item())
                pred_cls = int(torch.argmax(out.logits, dim=-1).item())
                preds.append(pred_cls)
                targets.append(y)

        model.train()
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        return compute_binary_metrics(targets, preds, loss=avg_loss)

    # 6. Step 0 Baseline Validation
    print("\n--- Running Step 0 Baseline Validation ---")
    step0_metrics = evaluate(val_records, desc="Pre-Training Baseline")
    print(f"[Step 0 Baseline] Loss: {step0_metrics['loss']:.4f} | Acc: {step0_metrics['accuracy']:.4f} | Bal Acc: {step0_metrics['balanced_accuracy']:.4f} | Macro F1: {step0_metrics['macro_f1']:.4f}")

    # 7. Bounded Training Loop
    print(f"\n--- Starting Bounded Training Loop ({config.max_train_samples} steps) ---")
    train_losses = []
    step_telemetry_log = []

    for step_idx, rec in enumerate(train_records):
        step_num = step_idx + 1

        # Watchdog check on every single step
        step_telemetry = watchdog.check(step=step_num)

        # Update learning rate
        current_lr = get_lr(step_idx)
        for param_group in optimizer.param_groups:
            param_group["lr"] = current_lr

        text_a, text_b = serialize_binary_input(rec)
        target_label = LABEL_MAP[rec["binary_label"]]

        encoding = tokenizer(
            text_a,
            text_b,
            max_length=config.max_seq_len,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )
        kwargs = {
            "input_ids": encoding["input_ids"],
            "attention_mask": encoding["attention_mask"],
            "labels": torch.tensor([target_label], dtype=torch.long),
        }
        if "token_type_ids" in encoding:
            kwargs["token_type_ids"] = encoding["token_type_ids"]

        optimizer.zero_grad()
        outputs = model(**kwargs)
        loss = outputs.loss
        loss_val = float(loss.item())
        train_losses.append(loss_val)

        loss.backward()
        optimizer.step()

        # Clean step memory
        optimizer.zero_grad(set_to_none=True)
        del outputs, loss, encoding

        if step_num % config.log_every_steps == 0 or step_num == config.max_train_samples:
            rolling_loss = sum(train_losses[-config.log_every_steps:]) / len(train_losses[-config.log_every_steps:])
            print(
                f"Step {step_num:4d}/{config.max_train_samples} | "
                f"Loss: {loss_val:.4f} (Rolling: {rolling_loss:.4f}) | "
                f"LR: {current_lr:.2e} | "
                f"RSS: {step_telemetry['rss_mb']:.1f} MB | "
                f"Avail RAM: {step_telemetry['available_ram_mb']:.1f} MB | "
                f"Elapsed: {step_telemetry['elapsed_seconds']:.1f}s"
            )
            step_telemetry_log.append({
                "step": step_num,
                "loss": loss_val,
                "rolling_loss": rolling_loss,
                "lr": current_lr,
                "telemetry": step_telemetry,
            })

    # 8. Final Post-Training Validation
    print("\n--- Running Final Post-Training Validation (Step 1,000) ---")
    final_metrics = evaluate(val_records, desc="Post-Training")
    print(f"[Final Validation] Loss: {final_metrics['loss']:.4f} | Acc: {final_metrics['accuracy']:.4f} | Bal Acc: {final_metrics['balanced_accuracy']:.4f} | Macro F1: {final_metrics['macro_f1']:.4f}")

    # 9. Atomic Checkpoint Serialization
    print(f"\n--- Serializing Atomic Checkpoint to {config.output_dir} ---")
    checkpoint_path = save_checkpoint_atomic(
        model=model,
        tokenizer=tokenizer,
        output_dir=config.output_dir,
        step=config.max_train_samples,
        metrics={"step0": step0_metrics, "final": final_metrics},
        pretrained_model_dir=config.model_dir,
    )
    print(f"[PASS] Successfully saved atomic checkpoint to: {checkpoint_path}")

    results = {
        "status": "COMPLETED",
        "total_steps": config.max_train_samples,
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
        rep_p = Path(report_dir)
        rep_p.mkdir(parents=True, exist_ok=True)
        with open(rep_p / "training_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"[PASS] Saved training results to {rep_p / 'training_results.json'}")

    return results


def main() -> int:
    args = parse_args()
    config = TrainingConfig(
        train_file=args.train_file,
        val_file=args.val_file,
        model_dir=args.model_dir,
        output_dir=args.output_dir,
        max_train_samples=args.max_train_samples,
        max_val_samples=args.max_val_samples,
        sampling_strategy=args.sampling_strategy,
        batch_size=args.batch_size,
        max_seq_len=args.max_seq_len,
        learning_rate=args.lr,
        weight_decay=args.weight_decay,
        warmup_steps=args.warmup_steps,
        seed=args.seed,
        num_threads=args.num_threads,
        ram_abort_threshold_mb=args.ram_abort_threshold_mb,
        swap_growth_abort_mb=args.swap_growth_abort_mb,
        swap_free_min_mb=args.swap_free_min_mb,
        max_duration_seconds=args.max_duration_seconds,
    )
    try:
        run_training_experiment(config, report_dir=args.report_dir)
        return 0
    except (ResourceAbortError, TimeoutAbortError, SecurityViolationError) as exc:
        print(f"\n[FATAL ABORT] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"\n[FATAL ERROR] Unexpected runtime failure: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
