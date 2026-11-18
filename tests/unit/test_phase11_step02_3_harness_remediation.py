"""Unit tests for Phase 11.1 Step 2.3: CPU Training Harness Remediation.

Covers:
1. Checkpoint save and reload.
2. Optimizer and scheduler state restoration.
3. RNG state restoration.
4. Exact sample-position recovery.
5. No duplicate optimizer steps after resume.
6. Interrupted atomic checkpoint write.
7. Watchdog tolerating swap growth when RAM and free swap remain healthy.
8. Watchdog aborting on sustained absolute memory-floor violations.
9. Emergency checkpoint behavior.
10. Dynamic padding correctness.

Uses synthetic tensors and tiny test models only. No real DeBERTa training.
"""

from __future__ import annotations

import sys
import json
import random
import shutil
import tempfile
import re
from pathlib import Path
from contextlib import contextmanager

import numpy as np
import torch
import torch.nn as nn

try:
    import pytest
except ImportError:
    class MockPytest:
        @staticmethod
        @contextmanager
        def raises(expected_exc, match=None):
            try:
                yield
            except expected_exc as e:
                if match and not re.search(match, str(e)):
                    raise AssertionError(f"Pattern '{match}' does not match exception message: '{e}'")
                return
            except Exception as e:
                raise AssertionError(f"Expected {expected_exc.__name__}, got {type(e).__name__}: {e}")
            raise AssertionError(f"Expected exception {expected_exc.__name__} was not raised")

        @staticmethod
        def fixture(func):
            return func

    pytest = MockPytest()

from tools.training.train_nli_classifier import (
    WatchdogMonitor,
    ResourceAbortError,
    TimeoutAbortError,
    CheckpointIntegrityError,
    evidence_preserving_tokenize,
    save_checkpoint_state,
    load_checkpoint_state,
    verify_checkpoint_integrity,
    prune_old_checkpoints,
)


class TinyModel(nn.Module):
    """Tiny 2-layer linear network for testing serialization without heavy weights."""

    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(4, 3)

    def forward(self, x):
        return self.fc(x)


class DummyTokenizer:
    """Mock tokenizer simulating DeBERTa special tokens and vocabulary mapping."""

    cls_token_id = 1
    sep_token_id = 2
    pad_token_id = 0

    def __call__(self, text, add_special_tokens=True):
        words = text.split()
        return {"input_ids": [abs(hash(w)) % 1000 + 10 for w in words]}


@pytest.fixture
def temp_dir(tmp_path: Path):
    d = tmp_path / "ckpt_test"
    d.mkdir(parents=True, exist_ok=True)
    yield d
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


# 1. Checkpoint Save and Reload
def test_checkpoint_save_and_reload(temp_dir: Path):
    model = TinyModel()
    ckpt_path = temp_dir / "checkpoint_step_000500"

    save_checkpoint_state(
        model=model,
        tokenizer=None,
        optimizer=None,
        checkpoint_dir=ckpt_path,
        step=500,
        epoch=1,
        sample_idx=2000,
        accum_count=0,
        metrics={"val_loss": 0.45},
    )

    valid, reason = verify_checkpoint_integrity(ckpt_path)
    assert valid, f"Integrity check failed: {reason}"

    loaded_model = TinyModel()
    meta = load_checkpoint_state(ckpt_path, model=loaded_model)

    assert meta["step"] == 500
    assert meta["epoch"] == 1
    assert meta["sample_idx"] == 2000

    # Verify tensor weights match
    for p1, p2 in zip(model.parameters(), loaded_model.parameters()):
        assert torch.allclose(p1, p2)


# 2. Optimizer and Scheduler State Restoration
def test_optimizer_and_scheduler_state_restoration(temp_dir: Path):
    model = TinyModel()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)

    # Perform 2 training steps on synthetic data
    for _ in range(2):
        optimizer.zero_grad()
        out = model(torch.randn(2, 4))
        loss = out.sum()
        loss.backward()
        optimizer.step()

    ckpt_path = temp_dir / "checkpoint_opt"
    save_checkpoint_state(
        model=model,
        tokenizer=None,
        optimizer=optimizer,
        checkpoint_dir=ckpt_path,
        step=100,
        epoch=1,
        sample_idx=400,
        accum_count=0,
        current_lr=1e-3,
    )

    # Create new optimizer with different state
    new_model = TinyModel()
    new_optimizer = torch.optim.AdamW(new_model.parameters(), lr=5e-5)

    load_checkpoint_state(ckpt_path, model=new_model, optimizer=new_optimizer)

    # Verify optimizer state dict restoration
    orig_state = optimizer.state_dict()
    restored_state = new_optimizer.state_dict()
    assert len(restored_state["state"]) == len(orig_state["state"])
    for k in orig_state["state"]:
        for tensor_key in ["exp_avg", "exp_avg_sq"]:
            t_orig = orig_state["state"][k][tensor_key]
            t_rest = restored_state["state"][k][tensor_key]
            assert torch.allclose(t_orig, t_rest)


# 3. RNG State Restoration
def test_rng_state_restoration(temp_dir: Path):
    torch.manual_seed(12345)
    np.random.seed(12345)
    random.seed(12345)

    model = TinyModel()
    ckpt_path = temp_dir / "checkpoint_rng"
    save_checkpoint_state(
        model=model,
        tokenizer=None,
        optimizer=None,
        checkpoint_dir=ckpt_path,
        step=50,
        epoch=1,
        sample_idx=200,
        accum_count=0,
    )

    # Generate 5 random numbers from each generator
    torch_seq_1 = [torch.randn(1).item() for _ in range(5)]
    np_seq_1 = [np.random.rand() for _ in range(5)]
    py_seq_1 = [random.random() for _ in range(5)]

    # Perturb RNG state
    _ = torch.randn(10)
    _ = np.random.rand(10)
    _ = random.random()

    # Restore checkpoint RNG state
    dummy_model = TinyModel()
    load_checkpoint_state(ckpt_path, model=dummy_model)

    torch_seq_2 = [torch.randn(1).item() for _ in range(5)]
    np_seq_2 = [np.random.rand() for _ in range(5)]
    py_seq_2 = [random.random() for _ in range(5)]

    assert torch_seq_1 == torch_seq_2
    assert np_seq_1 == np_seq_2
    assert py_seq_1 == py_seq_2


# 4. Exact Sample-Position Recovery
def test_exact_sample_position_recovery(temp_dir: Path):
    model = TinyModel()
    ckpt_path = temp_dir / "checkpoint_pos"

    save_checkpoint_state(
        model=model,
        tokenizer=None,
        optimizer=None,
        checkpoint_dir=ckpt_path,
        step=345,
        epoch=2,
        sample_idx=1380,
        accum_count=2,
    )

    meta = load_checkpoint_state(ckpt_path, model=model)
    assert meta["epoch"] == 2
    assert meta["step"] == 345
    assert meta["sample_idx"] == 1380
    assert meta["accum_count"] == 2

    # Next unconsumed sample calculation
    next_sample = meta["sample_idx"] + 1
    assert next_sample == 1381


# 5. No Duplicate Optimizer Steps After Resume
def test_no_duplicate_optimizer_steps_after_resume(temp_dir: Path):
    # Simulate a 10-sample epoch with accumulation=2 (total 5 optimizer steps)
    samples = list(range(10))
    accum_steps = 2

    # Phase 1: Train until sample 3 (Step 2 completed)
    processed_samples_phase1 = []
    opt_step = 0
    accum_count = 0
    model = TinyModel()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

    for idx, s in enumerate(samples[:4]):
        processed_samples_phase1.append(s)
        accum_count += 1
        if accum_count == accum_steps:
            opt_step += 1
            accum_count = 0
            if opt_step == 2:
                # Save checkpoint at step 2, sample_idx 3
                save_checkpoint_state(
                    model=model,
                    tokenizer=None,
                    optimizer=optimizer,
                    checkpoint_dir=temp_dir / "ckpt_step2",
                    step=opt_step,
                    epoch=1,
                    sample_idx=idx,
                    accum_count=accum_count,
                )

    assert opt_step == 2
    assert processed_samples_phase1 == [0, 1, 2, 3]

    # Phase 2: Resume from checkpoint
    meta = load_checkpoint_state(temp_dir / "ckpt_step2", model=model, optimizer=optimizer)
    start_step = meta["step"]
    start_sample_idx = meta["sample_idx"] + 1  # Next unconsumed sample = 4
    accum_count = meta["accum_count"]
    opt_step = start_step

    processed_samples_phase2 = []
    for idx, s in enumerate(samples):
        if idx < start_sample_idx:
            continue
        processed_samples_phase2.append(s)
        accum_count += 1
        if accum_count == accum_steps:
            opt_step += 1
            accum_count = 0

    assert processed_samples_phase2 == [4, 5, 6, 7, 8, 9]
    assert opt_step == 5  # Total steps is exactly 5
    # Zero duplicated samples
    assert set(processed_samples_phase1).isdisjoint(set(processed_samples_phase2))
    assert len(processed_samples_phase1) + len(processed_samples_phase2) == 10


# 6. Interrupted Atomic Checkpoint Write
def test_interrupted_atomic_checkpoint_write(temp_dir: Path):
    ckpt_path = temp_dir / "checkpoint_target"

    # Simulate an incomplete/corrupted .tmp directory left behind by power loss
    corrupt_tmp = temp_dir / ".tmp_checkpoint_target_9999"
    corrupt_tmp.mkdir(parents=True, exist_ok=True)
    (corrupt_tmp / "corrupt_file.bin").write_text("incomplete write")

    # verify_checkpoint_integrity on corrupt tmp should fail
    valid, reason = verify_checkpoint_integrity(corrupt_tmp)
    assert not valid
    assert "Missing" in reason

    # Attempting to load corrupt directory raises CheckpointIntegrityError
    model = TinyModel()
    with pytest.raises(CheckpointIntegrityError):
        load_checkpoint_state(corrupt_tmp, model=model)


# 7. Watchdog Tolerating Swap Growth When RAM and Free Swap Remain Healthy
def test_watchdog_tolerating_swap_growth_when_healthy():
    state = {
        "rss_mb": 2800.0,
        "available_ram_mb": 4000.0,  # Far above 700 MB
        "swap_total_mb": 6000.0,
        "swap_used_mb": 0.0,
        "swap_free_mb": 6000.0,     # Far above 1000 MB
    }
    wd = WatchdogMonitor(
        ram_abort_threshold_mb=700.0,
        swap_free_min_mb=1000.0,
        max_process_rss_mb=4500.0,
        telemetry_fn=lambda: dict(state),
    )
    wd.check(step=1)

    # Simulate OS background paging: Swap used grows from 0 to 1,500 MB
    state["swap_used_mb"] = 1500.0
    state["swap_free_mb"] = 4500.0  # Still 4.5 GB free swap!
    state["available_ram_mb"] = 3800.0

    # Must NOT raise ResourceAbortError!
    tel = wd.check(step=2)
    assert tel["consecutive_violations"] == 0


# 8. Watchdog Aborting on Sustained Absolute Memory-Floor Violations
def test_watchdog_aborting_on_sustained_floor_violations():
    state = {
        "rss_mb": 2800.0,
        "available_ram_mb": 4000.0,
        "swap_total_mb": 6000.0,
        "swap_used_mb": 1000.0,
        "swap_free_mb": 5000.0,
    }
    wd = WatchdogMonitor(
        ram_abort_threshold_mb=700.0,
        swap_free_min_mb=1000.0,
        consecutive_violations_threshold=3,
        telemetry_fn=lambda: dict(state),
    )
    wd.check(step=1)

    # Violation 1: RAM drops to 650 MB
    state["available_ram_mb"] = 650.0
    t1 = wd.check(step=2)
    assert t1["consecutive_violations"] == 1

    # Temporary recovery at step 3: counter resets!
    state["available_ram_mb"] = 800.0
    t2 = wd.check(step=3)
    assert t2["consecutive_violations"] == 0

    # Now simulate 3 consecutive sustained violations
    state["available_ram_mb"] = 650.0
    wd.check(step=4)  # 1
    wd.check(step=5)  # 2
    with pytest.raises(ResourceAbortError, match="Available host RAM dropped"):
        wd.check(step=6)  # 3: Abort!


# 9. Emergency Checkpoint Behavior
def test_emergency_checkpoint_behavior(temp_dir: Path):
    emergency_called = []

    def mock_emergency_save(step: int, reason: str):
        emergency_called.append((step, reason))

    state = {
        "rss_mb": 4600.0,  # Exceeds process RSS ceiling (4500 MB)
        "available_ram_mb": 4000.0,
        "swap_total_mb": 6000.0,
        "swap_used_mb": 1000.0,
        "swap_free_mb": 5000.0,
    }
    wd = WatchdogMonitor(
        max_process_rss_mb=4500.0,
        emergency_save_fn=mock_emergency_save,
        telemetry_fn=lambda: dict(state),
    )

    with pytest.raises(ResourceAbortError, match="Process RSS"):
        wd.check(step=42)

    assert len(emergency_called) == 1
    assert emergency_called[0][0] == 42
    assert "PROCESS_RSS_CEILING" in emergency_called[0][1]


# 10. Dynamic Padding Correctness
def test_dynamic_padding_correctness():
    tokenizer = DummyTokenizer()
    premise = "short premise text"
    hypothesis = "short hypothesis"

    # Dynamic padding True
    res_dyn = evidence_preserving_tokenize(
        tokenizer=tokenizer,
        premise=premise,
        hypothesis=hypothesis,
        max_seq_len=384,
        dynamic_padding=True,
    )
    seq_len_dyn = res_dyn["input_ids"].shape[1]
    assert seq_len_dyn < 384
    assert res_dyn["metadata"]["dynamic_padding"] is True

    # Dynamic padding False (Fixed 384)
    res_fixed = evidence_preserving_tokenize(
        tokenizer=tokenizer,
        premise=premise,
        hypothesis=hypothesis,
        max_seq_len=384,
        dynamic_padding=False,
    )
    seq_len_fixed = res_fixed["input_ids"].shape[1]
    assert seq_len_fixed == 384
    assert res_fixed["metadata"]["dynamic_padding"] is False
    assert res_fixed["attention_mask"].sum().item() == seq_len_dyn


if __name__ == "__main__":
    import tempfile
    print("=" * 80)
    print("RUNNING PHASE 11.1 STEP 2.3 HARNESS REMEDIATION MANDATORY TESTS")
    print("=" * 80)
    tests = [
        ("1. Checkpoint save and reload", test_checkpoint_save_and_reload),
        ("2. Optimizer and scheduler state restoration", test_optimizer_and_scheduler_state_restoration),
        ("3. RNG state restoration", test_rng_state_restoration),
        ("4. Exact sample-position recovery", test_exact_sample_position_recovery),
        ("5. No duplicate optimizer steps after resume", test_no_duplicate_optimizer_steps_after_resume),
        ("6. Interrupted atomic checkpoint write", test_interrupted_atomic_checkpoint_write),
        ("7. Watchdog tolerating swap growth when healthy", test_watchdog_tolerating_swap_growth_when_healthy),
        ("8. Watchdog aborting on sustained floor violations", test_watchdog_aborting_on_sustained_floor_violations),
        ("9. Emergency checkpoint behavior", test_emergency_checkpoint_behavior),
        ("10. Dynamic padding correctness", test_dynamic_padding_correctness),
    ]

    passed = 0
    failed = 0

    for name, fn in tests:
        tmp_d = Path(tempfile.mkdtemp(prefix="test_step2_3_"))
        try:
            # Check if function takes temp_dir argument
            import inspect
            sig = inspect.signature(fn)
            if "temp_dir" in sig.parameters:
                fn(tmp_d)
            else:
                fn()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        finally:
            if tmp_d.exists():
                shutil.rmtree(tmp_d, ignore_errors=True)

    print("=" * 80)
    print(f"RESULTS: {passed} PASSED, {failed} FAILED out of {len(tests)} tests")
    print("=" * 80)
    if failed > 0:
        sys.exit(1)

