"""Offline Loading and Inference Verification for Staged DeBERTa-v3-small.

Strictly verifies local-only loading (HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1),
parameter counts, tokenizer encoding/decoding, and a single inference forward pass.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def get_mem_telemetry() -> dict[str, float]:
    telemetry = {"rss_mb": 0.0, "available_ram_mb": 0.0, "swap_free_mb": 0.0}
    try:
        import psutil
        proc = psutil.Process()
        telemetry["rss_mb"] = proc.memory_info().rss / (1024 * 1024)
        vm = psutil.virtual_memory()
        telemetry["available_ram_mb"] = vm.available / (1024 * 1024)
        sw = psutil.swap_memory()
        telemetry["swap_free_mb"] = sw.free / (1024 * 1024)
    except Exception:
        pass
    return telemetry


def main() -> int:
    # 1. Enforce strict offline isolation
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    staged_dir = Path("/home/aditya/rags/models/pretrained/deberta-v3-small")
    out_dir = Path("/home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_step03_2_model_staging")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== OFFLINE DEBERTA-V3-SMALL LOADING & VERIFICATION ===")
    print(f"Staged model directory: {staged_dir}")
    print(f"Offline environment flags: HF_HUB_OFFLINE={os.environ.get('HF_HUB_OFFLINE')}, TRANSFORMERS_OFFLINE={os.environ.get('TRANSFORMERS_OFFLINE')}")

    t_start = time.perf_counter()
    init_mem = get_mem_telemetry()
    print(f"Initial State: Available RAM = {init_mem['available_ram_mb']:.2f} MB | RSS = {init_mem['rss_mb']:.2f} MB | Swap Free = {init_mem['swap_free_mb']:.2f} MB")

    results: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_dir": str(staged_dir),
        "offline_enforced": True,
        "checks": {},
        "summary": "UNKNOWN",
    }

    # 2. Verify mandatory staged files exist
    required_files = ["config.json", "spm.model"]
    # Check weight file
    has_weights = (staged_dir / "pytorch_model.bin").exists() or (staged_dir / "model.safetensors").exists()
    assert has_weights, f"Missing weight file in {staged_dir}"
    for rf in required_files:
        assert (staged_dir / rf).exists(), f"Missing required file: {rf}"
    print(f"[PASS] Mandatory local files exist (weights, config, spm.model)")

    import torch
    from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer

    # 3. Load Tokenizer offline
    t0_tok = time.perf_counter()
    try:
        tokenizer = AutoTokenizer.from_pretrained(str(staged_dir), local_files_only=True)
        tok_latency = (time.perf_counter() - t0_tok) * 1000.0

        sample_text = "TrustRAG verifies evidence grounding in retrieved passages."
        tokens = tokenizer.tokenize(sample_text)
        encoded = tokenizer(sample_text, return_tensors="pt")
        decoded = tokenizer.decode(encoded["input_ids"][0], skip_special_tokens=True)

        results["checks"]["tokenizer"] = {
            "status": "PASSED",
            "class": tokenizer.__class__.__name__,
            "vocab_size": len(tokenizer),
            "load_latency_ms": tok_latency,
            "sample_token_count": len(tokens),
            "roundtrip_exact_match": (decoded.strip() == sample_text.strip()),
        }
        print(f"[PASS] Tokenizer loaded: {tokenizer.__class__.__name__} (Vocab: {len(tokenizer):,}, Latency: {tok_latency:.1f}ms)")
        print(f"       Sample tokens: {tokens[:8]}...")
        print(f"       Roundtrip decode match: {decoded.strip() == sample_text.strip()}")
    except Exception as exc:
        results["checks"]["tokenizer"] = {"status": "FAILED", "error": str(exc)}
        print(f"[FAIL] Tokenizer loading failed: {exc}")
        return 1

    # 4. Load Pretrained Model offline
    t0_model = time.perf_counter()
    try:
        config = AutoConfig.from_pretrained(str(staged_dir), local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(
            str(staged_dir),
            num_labels=2,
            local_files_only=True,
        )
        model.eval()
        model_latency = (time.perf_counter() - t0_model) * 1000.0

        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

        results["checks"]["model_architecture"] = {
            "status": "PASSED",
            "model_class": model.__class__.__name__,
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "hidden_size": getattr(config, "hidden_size", None),
            "num_hidden_layers": getattr(config, "num_hidden_layers", None),
            "num_attention_heads": getattr(config, "num_attention_heads", None),
            "load_latency_ms": model_latency,
        }
        print(f"[PASS] Model loaded: {model.__class__.__name__} ({total_params:,} total parameters)")
        print(f"       Layers: {config.num_hidden_layers}, Hidden: {config.hidden_size}, Heads: {config.num_attention_heads}")
        print(f"       Load latency: {model_latency:.1f}ms")
    except Exception as exc:
        results["checks"]["model_architecture"] = {"status": "FAILED", "error": str(exc)}
        print(f"[FAIL] Pretrained model loading failed: {exc}")
        return 1

    post_load_mem = get_mem_telemetry()
    print(f"Post-Load State: Available RAM = {post_load_mem['available_ram_mb']:.2f} MB | RSS = {post_load_mem['rss_mb']:.2f} MB")

    # 5. Execute Single Inference Forward Pass (No backward/optimizer)
    t0_infer = time.perf_counter()
    try:
        prompt_pair = (
            "Question: Is AES-256 secure? Context: AES-256 uses 256-bit symmetric keys and is resistant to brute force.",
            "Candidate Answer: AES-256 is secure.",
        )
        inputs = tokenizer(prompt_pair[0], prompt_pair[1], return_tensors="pt", max_length=128, truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)
        infer_latency = (time.perf_counter() - t0_infer) * 1000.0

        logits = outputs.logits[0].tolist()
        probs = torch.softmax(outputs.logits[0], dim=-1).tolist()

        results["checks"]["inference_forward_pass"] = {
            "status": "PASSED",
            "latency_ms": infer_latency,
            "logits": logits,
            "probabilities": probs,
            "input_token_length": int(inputs["input_ids"].shape[1]),
        }
        print(f"[PASS] Inference forward pass: Latency = {infer_latency:.1f}ms | Tokens = {inputs['input_ids'].shape[1]}")
        print(f"       Logits: {logits} | Softmax Probs: {probs}")
    except Exception as exc:
        results["checks"]["inference_forward_pass"] = {"status": "FAILED", "error": str(exc)}
        print(f"[FAIL] Inference forward pass failed: {exc}")
        return 1

    total_time = time.perf_counter() - t_start
    final_mem = get_mem_telemetry()
    peak_rss = max(init_mem["rss_mb"], post_load_mem["rss_mb"], final_mem["rss_mb"])

    results["resource_telemetry"] = {
        "initial_rss_mb": init_mem["rss_mb"],
        "post_load_rss_mb": post_load_mem["rss_mb"],
        "final_rss_mb": final_mem["rss_mb"],
        "peak_rss_mb": peak_rss,
        "initial_available_ram_mb": init_mem["available_ram_mb"],
        "final_available_ram_mb": final_mem["available_ram_mb"],
        "swap_free_before_mb": init_mem["swap_free_mb"],
        "swap_free_after_mb": final_mem["swap_free_mb"],
        "total_elapsed_seconds": total_time,
    }
    results["summary"] = "OFFLINE_VERIFICATION_SUCCESSFUL"

    out_file = out_dir / "offline_verification_results.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n=== VERIFICATION COMPLETE ===")
    print(f"Peak RSS: {peak_rss:.1f} MB | Available RAM Remaining: {final_mem['available_ram_mb']:.1f} MB | Total Time: {total_time:.2f}s")
    print(f"Results written to: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
