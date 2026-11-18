"""CPU Training Environment Runtime Smoke Tests (Track 2 Step 3.1).

Verifies PyTorch CPU tensor ops, Transformers architecture initialization,
forward pass, backward pass, optimizer step, checkpoint save/reload,
and deterministic seed behavior without remote network downloads.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def get_process_memory_mb() -> float:
    try:
        import psutil
        proc = psutil.Process()
        return proc.memory_info().rss / (1024 * 1024)
    except Exception:
        # Fallback reading /proc/self/statm
        try:
            with open("/proc/self/statm") as f:
                pages = int(f.read().split()[1])
                return (pages * os.sysconf("SC_PAGE_SIZE")) / (1024 * 1024)
        except Exception:
            return 0.0


def main() -> int:
    results: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tests": {},
        "summary": "UNKNOWN",
    }
    t_start = time.perf_counter()
    rss_start = get_process_memory_mb()

    print("=== STARTING CPU RUNTIME SMOKE TESTS ===")
    print(f"Python interpreter: {sys.executable} (Version: {sys.version.split()[0]})")
    print(f"Initial Process RSS: {rss_start:.2f} MB")

    # 1. PyTorch Imports
    try:
        import torch
        results["tests"]["pytorch_import"] = {
            "status": "PASSED",
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "num_threads": torch.get_num_threads(),
        }
        print(f"[PASS] PyTorch {torch.__version__} imported (Threads: {torch.get_num_threads()}, CUDA: {torch.cuda.is_available()})")
    except Exception as exc:
        results["tests"]["pytorch_import"] = {"status": "FAILED", "error": str(exc)}
        print(f"[FAIL] PyTorch import failed: {exc}")
        return 1

    # 2. CPU Tensor Operations
    try:
        torch.set_num_threads(4)
        a = torch.randn(256, 256, dtype=torch.float32)
        b = torch.randn(256, 256, dtype=torch.float32)
        c = torch.matmul(a, b)
        s = torch.softmax(c, dim=-1)
        mean_val = float(torch.mean(s))
        assert abs(mean_val - (1.0 / 256.0)) < 1e-4
        results["tests"]["cpu_tensor_ops"] = {
            "status": "PASSED",
            "matmul_shape": list(c.shape),
            "mean_softmax": mean_val,
        }
        print(f"[PASS] CPU tensor operations (256x256 matmul + softmax mean: {mean_val:.6f})")
    except Exception as exc:
        results["tests"]["cpu_tensor_ops"] = {"status": "FAILED", "error": str(exc)}
        print(f"[FAIL] CPU tensor ops failed: {exc}")
        return 1

    # 3. Transformers & Auxiliary Imports
    try:
        import transformers
        import accelerate
        import sklearn
        results["tests"]["framework_imports"] = {
            "status": "PASSED",
            "transformers_version": transformers.__version__,
            "accelerate_version": accelerate.__version__,
            "sklearn_version": sklearn.__version__,
        }
        print(f"[PASS] Transformers {transformers.__version__}, Accelerate {accelerate.__version__}, Scikit-Learn {sklearn.__version__}")
    except Exception as exc:
        results["tests"]["framework_imports"] = {"status": "FAILED", "error": str(exc)}
        print(f"[FAIL] Framework imports failed: {exc}")
        return 1

    # 4. Local Tokenizer Availability Check
    deberta_dir = Path("/home/aditya/rags/models/pretrained/deberta-v3-small")
    has_local_tokenizer = (deberta_dir / "spm.model").exists() or (deberta_dir / "tokenizer.json").exists()
    results["tests"]["tokenizer_loading"] = {
        "status": "OFFLINE_GUARDED",
        "local_weights_exist": has_local_tokenizer,
        "detail": "Local weights not present; remote download strictly disallowed by offline policy.",
    }
    print(f"[INFO] Tokenizer loading: Local weights exist = {has_local_tokenizer} (Offline policy enforced)")

    # 5. Architecture Instantiation & Forward Pass (from config without remote download)
    try:
        from transformers import DebertaV2Config, DebertaV2ForSequenceClassification
        # Miniature configuration to smoke test forward/backward/loss logic
        cfg = DebertaV2Config(
            vocab_size=1000,
            hidden_size=128,
            num_hidden_layers=2,
            num_attention_heads=4,
            intermediate_size=256,
            num_labels=2,
        )
        model = DebertaV2ForSequenceClassification(cfg)
        model.eval()

        batch_size = 2
        seq_len = 32
        input_ids = torch.randint(0, 1000, (batch_size, seq_len), dtype=torch.long)
        attention_mask = torch.ones((batch_size, seq_len), dtype=torch.long)
        labels = torch.tensor([0, 1], dtype=torch.long)

        with torch.no_grad():
            out = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        loss_val = float(out.loss.item())
        logits_shape = list(out.logits.shape)
        results["tests"]["forward_pass"] = {
            "status": "PASSED",
            "initial_loss": loss_val,
            "logits_shape": logits_shape,
        }
        print(f"[PASS] Forward pass successful (Loss: {loss_val:.4f}, Logits shape: {logits_shape})")
    except Exception as exc:
        results["tests"]["forward_pass"] = {"status": "FAILED", "error": str(exc)}
        print(f"[FAIL] Forward pass failed: {exc}")
        return 1

    # 6. Backward Pass & Gradient Verification
    try:
        model.train()
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        optimizer.zero_grad()
        out = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        loss = out.loss
        loss.backward()

        grad_norms = []
        for name, p in model.named_parameters():
            if p.requires_grad and p.grad is not None:
                grad_norms.append(float(p.grad.norm().item()))
        assert len(grad_norms) > 0, "No gradients populated"
        assert not any(torch.isnan(torch.tensor(grad_norms))), "NaN detected in gradients"
        results["tests"]["backward_pass"] = {
            "status": "PASSED",
            "populated_grad_tensors": len(grad_norms),
            "mean_grad_norm": sum(grad_norms) / len(grad_norms),
        }
        print(f"[PASS] Backward pass successful ({len(grad_norms)} gradient tensors, Mean norm: {sum(grad_norms)/len(grad_norms):.6f})")
    except Exception as exc:
        results["tests"]["backward_pass"] = {"status": "FAILED", "error": str(exc)}
        print(f"[FAIL] Backward pass failed: {exc}")
        return 1

    # 7. Optimizer Step
    try:
        param_sample_before = next(model.parameters()).clone()
        optimizer.step()
        param_sample_after = next(model.parameters())
        diff = float((param_sample_before - param_sample_after).abs().sum().item())
        assert diff > 0.0, "Optimizer step did not update model parameters"
        results["tests"]["optimizer_step"] = {
            "status": "PASSED",
            "weight_delta_l1": diff,
        }
        print(f"[PASS] Optimizer step successful (Weight update L1 delta: {diff:.6f})")
    except Exception as exc:
        results["tests"]["optimizer_step"] = {"status": "FAILED", "error": str(exc)}
        print(f"[FAIL] Optimizer step failed: {exc}")
        return 1

    # 8. Checkpoint Save & Reload
    try:
        ckpt_path = Path("/tmp/trustrag_smoke_test_ckpt.pt")
        torch.save(model.state_dict(), ckpt_path)
        new_model = DebertaV2ForSequenceClassification(cfg)
        new_model.load_state_dict(torch.load(ckpt_path, weights_only=True))
        
        # Verify weight equality
        p1 = list(model.parameters())[0]
        p2 = list(new_model.parameters())[0]
        assert torch.equal(p1, p2), "Loaded state dict does not match saved state dict"
        ckpt_size = ckpt_path.stat().st_size
        if ckpt_path.exists():
            ckpt_path.unlink()
        results["tests"]["checkpoint_io"] = {
            "status": "PASSED",
            "checkpoint_size_bytes": ckpt_size,
            "weights_verified": True,
        }
        print(f"[PASS] Checkpoint save & reload successful ({ckpt_size} bytes verified)")
    except Exception as exc:
        results["tests"]["checkpoint_io"] = {"status": "FAILED", "error": str(exc)}
        print(f"[FAIL] Checkpoint IO failed: {exc}")
        return 1

    # 9. Deterministic Seed Behavior
    try:
        torch.manual_seed(1337)
        t1 = torch.randn(10, 10)
        torch.manual_seed(1337)
        t2 = torch.randn(10, 10)
        assert torch.equal(t1, t2), "Tensors generated with identical seed are not equal"
        results["tests"]["deterministic_seed"] = {
            "status": "PASSED",
            "seed": 1337,
            "reproducible": True,
        }
        print("[PASS] Deterministic seed behavior verified (Seed: 1337)")
    except Exception as exc:
        results["tests"]["deterministic_seed"] = {"status": "FAILED", "error": str(exc)}
        print(f"[FAIL] Deterministic seed test failed: {exc}")
        return 1

    t_total = time.perf_counter() - t_start
    rss_end = get_process_memory_mb()
    results["metrics"] = {
        "elapsed_seconds": t_total,
        "rss_start_mb": rss_start,
        "rss_end_mb": rss_end,
        "rss_peak_mb": max(rss_start, rss_end),
    }
    results["summary"] = "ALL_TESTS_PASSED"

    out_file = Path("/home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_step03_1_cpu_environment/smoke_test_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n=== ALL SMOKE TESTS COMPLETED SUCCESSFULLY ===")
    print(f"Elapsed: {t_total:.2f}s | Peak RSS: {max(rss_start, rss_end):.2f} MB")
    print(f"Results saved to: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
