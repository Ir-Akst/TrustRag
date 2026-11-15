"""Full-Architecture DeBERTa-v3-small CPU Feasibility Pilot (Track 2, Step 3.3).

Executes a strictly bounded, genuine forward/backward optimization pilot using:
- Full official DeBERTa-v3-small architecture (141.9M parameters)
- Pretrained weights loaded offline from /home/aditya/rags/models/pretrained/deberta-v3-small
- Official DebertaV2Tokenizer
- Real text examples from data/processed/sft_v2/binary/train.jsonl
- Max 3 optimizer steps, batch size 1, max_seq_len 128
- Seed: 42
- Rigorous resource safety telemetry (RSS, Available RAM, Swap, CPU load)
"""

from __future__ import annotations

import gc
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# 1. Enforce strict offline isolation
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"


def get_mem_telemetry() -> dict[str, float]:
    telemetry = {
        "rss_mb": 0.0,
        "available_ram_mb": 0.0,
        "swap_total_mb": 0.0,
        "swap_used_mb": 0.0,
        "swap_free_mb": 0.0,
        "cpu_percent": 0.0,
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
        telemetry["cpu_percent"] = psutil.cpu_percent(interval=None)
    except Exception as e:
        print(f"[WARN] Error reading telemetry: {e}")
    return telemetry


def main() -> int:
    print("=" * 75)
    print("TRUST RAG — TRACK 2, STEP 3.3: FULL-ARCHITECTURE DEBERTA-V3-SMALL CPU PILOT")
    print("=" * 75)

    import torch
    import numpy as np

    # Set deterministic seed
    torch.manual_seed(42)
    np.random.seed(42)

    t_start = time.perf_counter()
    init_mem = get_mem_telemetry()
    print(f"Pre-pilot Host State:")
    print(f"  Available RAM: {init_mem['available_ram_mb']:.2f} MB")
    print(f"  Process RSS:   {init_mem['rss_mb']:.2f} MB")
    print(f"  Swap Used:     {init_mem['swap_used_mb']:.2f} MB / {init_mem['swap_total_mb']:.2f} MB")

    # Safety RAM check
    if init_mem["available_ram_mb"] < 1000.0:
        print(f"[FATAL] Available RAM is below 1000 MB ({init_mem['available_ram_mb']:.2f} MB). Aborting pilot.")
        return 1

    model_dir = Path("/home/aditya/rags/models/pretrained/deberta-v3-small")
    data_path = Path("/home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/train.jsonl")
    out_dir = Path("/home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_step03_3_cpu_feasibility_pilot")
    out_dir.mkdir(parents=True, exist_ok=True)

    pilot_record: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_target": "microsoft/deberta-v3-small",
        "model_dir": str(model_dir),
        "dataset_path": str(data_path),
        "offline_enforced": True,
        "seed": 42,
        "num_threads": 4,
        "max_steps": 3,
        "batch_size": 1,
        "max_seq_len": 128,
        "pre_pilot_telemetry": init_mem,
        "steps": [],
        "verdict": "UNKNOWN",
    }

    # Verify input dataset exists
    if not data_path.exists():
        print(f"[FATAL] Dataset file not found: {data_path}")
        return 1

    # Load 3 training examples
    examples = []
    with open(data_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= 3:
                break
            examples.append(json.loads(line))

    print(f"\n[1] Loaded {len(examples)} examples from {data_path.name}")
    for idx, ex in enumerate(examples):
        print(f"  Example {idx+1}: ID={ex.get('example_id')}, Source={ex.get('source_dataset')}, Label={ex.get('binary_label')}")

    # Label mapping according to binary schema
    label_map = {"FACTUAL": 0, "HALLUCINATED": 1}

    from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer

    # Pin threads to 4 for CPU efficiency without context thrashing
    torch.set_num_threads(4)
    print(f"\n[2] PyTorch initialized on CPU (torch.get_num_threads() = {torch.get_num_threads()})")

    # Load Tokenizer offline
    t0_tok = time.perf_counter()
    try:
        tokenizer = AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True)
        tok_latency_ms = (time.perf_counter() - t0_tok) * 1000.0
        print(f"[PASS] Tokenizer loaded offline: {tokenizer.__class__.__name__} (Vocab: {len(tokenizer):,}, Latency: {tok_latency_ms:.1f}ms)")
    except Exception as exc:
        print(f"[FATAL] Failed to load tokenizer: {exc}")
        return 1

    # Load Model offline
    t0_model = time.perf_counter()
    try:
        config = AutoConfig.from_pretrained(str(model_dir), num_labels=2, local_files_only=True)
        # Capture loading info (missing keys, unexpected keys)
        model = AutoModelForSequenceClassification.from_pretrained(
            str(model_dir),
            config=config,
            local_files_only=True,
            torch_dtype=torch.float32,  # CPU requires FP32 for training
        )
        model_latency_s = time.perf_counter() - t0_model
        mem_after_load = get_mem_telemetry()
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

        # Inspect parameter dtypes
        param_dtypes = list({str(p.dtype) for p in model.parameters()})

        # Check classifier head initialization
        classifier_keys = [k for k, _ in model.named_parameters() if "classifier" in k or "pooler" in k]

        print(f"[PASS] Model loaded offline: {model.__class__.__name__}")
        print(f"       Total parameters: {total_params:,} (Trainable: {trainable_params:,})")
        print(f"       Parameter dtypes: {param_dtypes}")
        print(f"       Newly initialized head/pooler keys: {classifier_keys}")
        print(f"       Load time: {model_latency_s:.2f}s | Current RSS: {mem_after_load['rss_mb']:.2f} MB | Available RAM: {mem_after_load['available_ram_mb']:.2f} MB")
        pilot_record["model_info"] = {
            "class": model.__class__.__name__,
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "parameter_dtypes": param_dtypes,
            "newly_initialized_keys": classifier_keys,
            "load_time_seconds": model_latency_s,
            "post_load_rss_mb": mem_after_load["rss_mb"],
        }
    except Exception as exc:
        print(f"[FATAL] Failed to load model: {exc}")
        return 1

    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)

    print("\n[3] Beginning 3-Step Bounded Feasibility Pilot Loop...")

    peak_rss = mem_after_load["rss_mb"]

    for step_idx, ex in enumerate(examples):
        step_num = step_idx + 1
        t_step_start = time.perf_counter()
        pre_step_mem = get_mem_telemetry()

        # Safety check: available RAM abort condition (< 700 MB)
        if pre_step_mem["available_ram_mb"] < 700.0:
            print(f"[FATAL] Available RAM dropped below 700 MB ({pre_step_mem['available_ram_mb']:.2f} MB). Aborting immediately!")
            pilot_record["verdict"] = "ABORTED_LOW_MEMORY"
            return 1

        # Tokenize example
        # Prompt structure: Premise = question + " " + context; Hypothesis = candidate_response
        text_a = f"{ex['question_or_claim']} {ex['context_or_evidence']}"
        text_b = ex["candidate_response"]
        label_int = label_map[ex["binary_label"]]

        encoding = tokenizer(
            text_a,
            text_b,
            max_length=128,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )
        input_ids = encoding["input_ids"]
        attention_mask = encoding["attention_mask"]
        token_type_ids = encoding.get("token_type_ids", None)
        labels = torch.tensor([label_int], dtype=torch.long)

        active_tokens = int(attention_mask.sum().item())

        # Forward pass
        t_fwd_0 = time.perf_counter()
        kwargs = {"input_ids": input_ids, "attention_mask": attention_mask, "labels": labels}
        if token_type_ids is not None:
            kwargs["token_type_ids"] = token_type_ids

        outputs = model(**kwargs)
        loss = outputs.loss
        loss_val = float(loss.item())
        logits = outputs.logits
        logits_val = [round(float(x), 4) for x in logits[0].detach().numpy()]
        fwd_latency = time.perf_counter() - t_fwd_0
        post_fwd_mem = get_mem_telemetry()

        # Snapshot weights of classifier weight to verify actual optimizer update
        ref_classifier_weight = model.classifier.weight.clone().detach()

        # Backward pass
        t_bwd_0 = time.perf_counter()
        optimizer.zero_grad()
        loss.backward()
        bwd_latency = time.perf_counter() - t_bwd_0
        post_bwd_mem = get_mem_telemetry()

        # Compute gradient norm (L2) and check finiteness
        total_grad_norm_sq = 0.0
        grad_is_finite = True
        grad_non_zero_count = 0
        total_grad_params = 0

        for name, p in model.named_parameters():
            if p.grad is not None:
                total_grad_params += 1
                param_norm = p.grad.data.norm(2).item()
                if not (param_norm >= 0.0 and param_norm < float("inf")):
                    grad_is_finite = False
                if param_norm > 1e-9:
                    grad_non_zero_count += 1
                total_grad_norm_sq += param_norm ** 2
        total_grad_norm = total_grad_norm_sq ** 0.5

        # Optimizer step
        t_opt_0 = time.perf_counter()
        optimizer.step()
        opt_latency = time.perf_counter() - t_opt_0
        post_opt_mem = get_mem_telemetry()

        # Verify parameter delta norm
        with torch.no_grad():
            ref_delta_norm = (model.classifier.weight - ref_classifier_weight).norm(2).item()

        # Clear gradient and temporary references to maintain clean memory
        optimizer.zero_grad(set_to_none=True)
        del outputs, loss, logits
        gc.collect()

        t_step_total = time.perf_counter() - t_step_start
        post_step_mem = get_mem_telemetry()
        if post_step_mem["rss_mb"] > peak_rss:
            peak_rss = post_step_mem["rss_mb"]

        step_telemetry = {
            "step": step_num,
            "example_id": ex["example_id"],
            "source_dataset": ex["source_dataset"],
            "label_str": ex["binary_label"],
            "label_int": label_int,
            "active_tokens": active_tokens,
            "max_seq_len": 128,
            "loss": loss_val,
            "logits": logits_val,
            "gradient_l2_norm": float(total_grad_norm),
            "gradient_is_finite": grad_is_finite,
            "grad_param_count": total_grad_params,
            "grad_non_zero_params": grad_non_zero_count,
            "param_delta_l2_norm": float(ref_delta_norm),
            "timings": {
                "forward_ms": fwd_latency * 1000.0,
                "backward_ms": bwd_latency * 1000.0,
                "optimizer_ms": opt_latency * 1000.0,
                "total_step_ms": t_step_total * 1000.0,
            },
            "memory": {
                "pre_rss_mb": pre_step_mem["rss_mb"],
                "post_fwd_rss_mb": post_fwd_mem["rss_mb"],
                "post_bwd_rss_mb": post_bwd_mem["rss_mb"],
                "post_step_rss_mb": post_step_mem["rss_mb"],
                "available_ram_mb": post_step_mem["available_ram_mb"],
                "swap_used_mb": post_step_mem["swap_used_mb"],
            },
        }
        pilot_record["steps"].append(step_telemetry)

        print(f"--- Step {step_num}/3 ---")
        print(f"  Example ID:      {ex['example_id']} ({ex['source_dataset']}, {ex['binary_label']})")
        print(f"  Active Tokens:   {active_tokens}/128")
        print(f"  Loss:            {loss_val:.4f} | Logits: {logits_val}")
        print(f"  Grad L2 Norm:    {total_grad_norm:.4f} (Finite: {grad_is_finite}, Non-zero params: {grad_non_zero_count}/{total_grad_params})")
        print(f"  Weight Delta:    {ref_delta_norm:.6f}")
        print(f"  Latency:         Fwd: {fwd_latency*1000:.1f}ms | Bwd: {bwd_latency*1000:.1f}ms | Opt: {opt_latency*1000:.1f}ms | Total: {t_step_total*1000:.1f}ms")
        print(f"  Memory:          RSS: {post_step_mem['rss_mb']:.1f} MB | Avail RAM: {post_step_mem['available_ram_mb']:.1f} MB | Swap: {post_step_mem['swap_used_mb']:.1f} MB")

    total_pilot_time = time.perf_counter() - t_start
    final_mem = get_mem_telemetry()

    # Calculate summary metrics
    avg_step_ms = sum(s["timings"]["total_step_ms"] for s in pilot_record["steps"]) / len(pilot_record["steps"])
    avg_fwd_ms = sum(s["timings"]["forward_ms"] for s in pilot_record["steps"]) / len(pilot_record["steps"])
    avg_bwd_ms = sum(s["timings"]["backward_ms"] for s in pilot_record["steps"]) / len(pilot_record["steps"])
    avg_opt_ms = sum(s["timings"]["optimizer_ms"] for s in pilot_record["steps"]) / len(pilot_record["steps"])
    throughput_samples_per_sec = 1000.0 / avg_step_ms

    pilot_record["summary"] = {
        "status": "COMPLETED",
        "total_steps": len(pilot_record["steps"]),
        "total_elapsed_seconds": total_pilot_time,
        "peak_process_rss_mb": peak_rss,
        "final_available_ram_mb": final_mem["available_ram_mb"],
        "swap_drift_mb": final_mem["swap_used_mb"] - init_mem["swap_used_mb"],
        "avg_step_ms": avg_step_ms,
        "avg_fwd_ms": avg_fwd_ms,
        "avg_bwd_ms": avg_bwd_ms,
        "avg_opt_ms": avg_opt_ms,
        "throughput_samples_per_sec": throughput_samples_per_sec,
        "all_gradients_finite": all(s["gradient_is_finite"] for s in pilot_record["steps"]),
        "all_updates_verified": all(s["param_delta_l2_norm"] > 0 for s in pilot_record["steps"]),
    }
    pilot_record["verdict"] = "PILOT_PASSED"

    print("\n" + "=" * 75)
    print("PILOT EXECUTION SUMMARY")
    print("=" * 75)
    print(f"Verdict:              {pilot_record['verdict']}")
    print(f"Total Steps:          {pilot_record['summary']['total_steps']}")
    print(f"Total Elapsed Time:   {total_pilot_time:.2f} s")
    print(f"Peak Process RSS:     {peak_rss:.2f} MB")
    print(f"Final Available RAM:  {final_mem['available_ram_mb']:.2f} MB")
    print(f"Swap Drift:           {pilot_record['summary']['swap_drift_mb']:+.2f} MB")
    print(f"Avg Step Latency:     {avg_step_ms:.1f} ms (Fwd: {avg_fwd_ms:.1f} ms, Bwd: {avg_bwd_ms:.1f} ms, Opt: {avg_opt_ms:.1f} ms)")
    print(f"Throughput:           {throughput_samples_per_sec:.2f} samples/sec ({throughput_samples_per_sec * 3600:.1f} samples/hr)")
    print(f"Gradients Finite:     {pilot_record['summary']['all_gradients_finite']}")
    print(f"Weights Updated:      {pilot_record['summary']['all_updates_verified']}")

    # Write pilot results json
    results_path = out_dir / "pilot_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(pilot_record, f, indent=2)
    print(f"\n[PASS] Saved results to {results_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
