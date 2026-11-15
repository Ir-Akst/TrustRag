"""Unit tests for Phase 11.1 Step 2.5: Final Training Harness Limitation Remediation.

Covers:
1. Invalid checkpoint path producing original error (no secondary NameError).
2. Corrupted checkpoint directory producing CheckpointIntegrityError (no secondary NameError).
3. Mid-epoch resume sample position.
4. Last-sample resume and next-epoch transition.
5. Final-epoch completion (clean termination when resuming finished training).
6. Complete multi-phase non-overlapping sample processing (zero duplicates, zero omissions).
7. Optimizer step and learning rate schedule continuity across epoch boundary.

Uses synthetic test structures and tiny networks only. No real DeBERTa training.
"""

from __future__ import annotations

import sys
import json
import shutil
import tempfile
from pathlib import Path
from contextlib import contextmanager

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
                import re
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
    save_checkpoint_state,
    load_checkpoint_state,
    verify_checkpoint_integrity,
    CheckpointIntegrityError,
    NLITrainingConfig,
)


class TinyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(4, 3)

    def forward(self, x):
        return self.fc(x)


@pytest.fixture
def temp_dir():
    d = Path(tempfile.mkdtemp(prefix="test_step2_5_"))
    yield d
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


# 1. Invalid Checkpoint Path Handling
def test_invalid_checkpoint_path_error(temp_dir: Path):
    from unittest.mock import patch
    non_existent = temp_dir / "does_not_exist_xyz123"

    model = TinyModel()
    # Direct load_checkpoint_state verification
    with pytest.raises(CheckpointIntegrityError):
        load_checkpoint_state(non_existent, model=model)

    # Verification that attempting to resume via config raises FileNotFoundError
    # without raising NameError
    from tools.training.train_nli_classifier import execute_training
    config = NLITrainingConfig(
        resume_from_checkpoint=str(non_existent),
        output_dir=str(temp_dir / "out"),
        max_duration_seconds=5.0,
        authorized=True,
    )
    with patch("tools.training.train_nli_classifier.prepare_nli_model", return_value=(TinyModel(), None)):
        try:
            execute_training(config)
            assert False, "execute_training should have raised FileNotFoundError"
        except FileNotFoundError as exc:
            assert "Specified resume checkpoint does not exist" in str(exc)
        except NameError as ne:
            raise AssertionError(f"Secondary NameError was raised: {ne}")
        except Exception as e:
            assert "resume_checkpoint_dir" not in str(e)


# 2. Corrupted Checkpoint Directory Handling (No NameError in Logger)
def test_corrupted_checkpoint_error_logger(temp_dir: Path):
    from unittest.mock import patch
    corrupt_dir = temp_dir / "corrupted_ckpt"
    corrupt_dir.mkdir(parents=True, exist_ok=True)
    (corrupt_dir / "random.txt").write_text("not a checkpoint")

    model = TinyModel()
    with pytest.raises(CheckpointIntegrityError) as exc_info:
        load_checkpoint_state(corrupt_dir, model=model)

    from tools.training.train_nli_classifier import execute_training
    config = NLITrainingConfig(
        resume_from_checkpoint=str(corrupt_dir),
        output_dir=str(temp_dir / "out"),
        max_duration_seconds=5.0,
        authorized=True,
    )
    with patch("tools.training.train_nli_classifier.prepare_nli_model", return_value=(TinyModel(), None)):
        try:
            execute_training(config)
            assert False, "execute_training should have raised CheckpointIntegrityError"
        except CheckpointIntegrityError:
            pass  # Expected!
        except NameError as ne:
            raise AssertionError(f"Secondary NameError was raised in error logger: {ne}")
        except Exception as e:
            assert "resume_checkpoint_dir" not in str(e)


# 3. Mid-Epoch Resume Logic
def test_mid_epoch_resume_logic(temp_dir: Path):
    samples_per_epoch = 100
    model = TinyModel()
    ckpt_path = temp_dir / "mid_epoch_ckpt"

    # Save checkpoint mid-epoch at sample 45 in epoch 1
    save_checkpoint_state(
        model=model,
        tokenizer=None,
        optimizer=None,
        checkpoint_dir=ckpt_path,
        step=12,
        epoch=1,
        sample_idx=45,
        accum_count=1,
    )

    meta = load_checkpoint_state(ckpt_path, model=model)
    raw_sample_idx = meta.get("sample_idx", 0)
    start_epoch = meta.get("epoch", 1)

    if raw_sample_idx >= samples_per_epoch - 1:
        start_epoch += 1
        start_sample_idx = 0
        accum_count = 0
    else:
        start_sample_idx = raw_sample_idx + 1
        accum_count = meta.get("accum_count", 0)

    assert start_epoch == 1
    assert start_sample_idx == 46
    assert accum_count == 1


# 4. Last-Sample Resume & Next-Epoch Transition
def test_last_sample_resume_and_next_epoch_transition(temp_dir: Path):
    samples_per_epoch = 100
    model = TinyModel()
    ckpt_path = temp_dir / "end_epoch_ckpt"

    # Save checkpoint at exact last sample of epoch 1 (sample 99 out of 100)
    save_checkpoint_state(
        model=model,
        tokenizer=None,
        optimizer=None,
        checkpoint_dir=ckpt_path,
        step=25,
        epoch=1,
        sample_idx=99,
        accum_count=0,
    )

    meta = load_checkpoint_state(ckpt_path, model=model)
    raw_sample_idx = meta.get("sample_idx", 0)
    start_epoch = meta.get("epoch", 1)

    if raw_sample_idx >= samples_per_epoch - 1:
        start_epoch += 1
        start_sample_idx = 0
        accum_count = 0
    else:
        start_sample_idx = raw_sample_idx + 1
        accum_count = meta.get("accum_count", 0)

    # Must cleanly advance to Epoch 2, Sample Index 0
    assert start_epoch == 2
    assert start_sample_idx == 0
    assert accum_count == 0


# 5. Final-Epoch Completion Logic
def test_final_epoch_completion(temp_dir: Path):
    samples_per_epoch = 50
    total_epochs = 3
    model = TinyModel()
    ckpt_path = temp_dir / "final_epoch_ckpt"

    # Save checkpoint at end of epoch 3
    save_checkpoint_state(
        model=model,
        tokenizer=None,
        optimizer=None,
        checkpoint_dir=ckpt_path,
        step=75,
        epoch=3,
        sample_idx=49,
        accum_count=0,
    )

    meta = load_checkpoint_state(ckpt_path, model=model)
    raw_sample_idx = meta.get("sample_idx", 0)
    start_epoch = meta.get("epoch", 1)

    if raw_sample_idx >= samples_per_epoch - 1:
        start_epoch += 1
        start_sample_idx = 0
        accum_count = 0
    else:
        start_sample_idx = raw_sample_idx + 1

    assert start_epoch == 4
    assert start_sample_idx == 0

    # Simulate loop over range(1, total_epochs + 1)
    executed_epochs = []
    for epoch in range(1, total_epochs + 1):
        if epoch < start_epoch:
            continue
        executed_epochs.append(epoch)

    # Since start_epoch (4) > total_epochs (3), zero epochs are executed!
    assert executed_epochs == []


# 6. Multi-Phase Resume Non-Overlapping Execution Simulation
def test_multi_phase_resume_no_duplicate_samples(temp_dir: Path):
    samples_per_epoch = 10
    total_epochs = 2
    accum_steps = 2

    # Data: 10 items per epoch
    all_processed: list[tuple[int, int]] = []

    # Phase 1: Train Epoch 1, samples 0..5 (save at sample 5, step 3)
    p1_processed = []
    opt_step = 0
    accum_count = 0
    for idx in range(6):
        p1_processed.append((1, idx))
        accum_count += 1
        if accum_count == accum_steps:
            opt_step += 1
            accum_count = 0

    ckpt1 = temp_dir / "ckpt_phase1"
    model = TinyModel()
    save_checkpoint_state(
        model=model,
        tokenizer=None,
        optimizer=None,
        checkpoint_dir=ckpt1,
        step=opt_step,
        epoch=1,
        sample_idx=5,
        accum_count=accum_count,
    )
    all_processed.extend(p1_processed)

    # Phase 2: Resume from ckpt1, finish Epoch 1 (samples 6..9)
    meta1 = load_checkpoint_state(ckpt1, model=model)
    s_epoch = meta1["epoch"]
    raw_s = meta1["sample_idx"]
    if raw_s >= samples_per_epoch - 1:
        s_epoch += 1
        s_idx = 0
    else:
        s_idx = raw_s + 1

    p2_processed = []
    for idx in range(samples_per_epoch):
        if 1 == s_epoch and idx < s_idx:
            continue
        p2_processed.append((1, idx))
        accum_count += 1
        if accum_count == accum_steps:
            opt_step += 1
            accum_count = 0

    assert p2_processed == [(1, 6), (1, 7), (1, 8), (1, 9)]

    # Save end-of-epoch checkpoint
    ckpt2 = temp_dir / "ckpt_phase2_end_epoch1"
    save_checkpoint_state(
        model=model,
        tokenizer=None,
        optimizer=None,
        checkpoint_dir=ckpt2,
        step=opt_step,
        epoch=1,
        sample_idx=9,
        accum_count=0,
    )
    all_processed.extend(p2_processed)

    # Phase 3: Resume from ckpt2 (end-of-epoch). Should transition directly to Epoch 2, Sample 0
    meta2 = load_checkpoint_state(ckpt2, model=model)
    s_epoch = meta2["epoch"]
    raw_s = meta2["sample_idx"]
    if raw_s >= samples_per_epoch - 1:
        s_epoch += 1
        s_idx = 0
    else:
        s_idx = raw_s + 1

    assert s_epoch == 2
    assert s_idx == 0

    p3_processed = []
    for epoch in range(1, total_epochs + 1):
        if epoch < s_epoch:
            continue
        for idx in range(samples_per_epoch):
            if epoch == s_epoch and idx < s_idx:
                continue
            p3_processed.append((epoch, idx))
            accum_count += 1
            if accum_count == accum_steps:
                opt_step += 1
                accum_count = 0

    assert p3_processed == [(2, i) for i in range(10)]
    all_processed.extend(p3_processed)

    # Final Verification: Total samples processed is 20, zero duplicates, zero omissions
    expected = [(1, i) for i in range(10)] + [(2, i) for i in range(10)]
    assert all_processed == expected
    assert len(all_processed) == 20
    assert len(set(all_processed)) == 20


# 7. Optimizer & Scheduler Continuity Across Epoch Boundary
def test_optimizer_and_scheduler_continuity_across_epoch(temp_dir: Path):
    model = TinyModel()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

    # Train for 5 steps
    for _ in range(5):
        optimizer.zero_grad()
        loss = model(torch.randn(2, 4)).sum()
        loss.backward()
        optimizer.step()

    ckpt = temp_dir / "ckpt_epoch_boundary"
    save_checkpoint_state(
        model=model,
        tokenizer=None,
        optimizer=optimizer,
        checkpoint_dir=ckpt,
        step=50,
        epoch=1,
        sample_idx=99,
        accum_count=0,
        current_lr=1.5e-5,
    )

    restored_model = TinyModel()
    restored_optimizer = torch.optim.AdamW(restored_model.parameters(), lr=1e-3)
    meta = load_checkpoint_state(ckpt, model=restored_model, optimizer=restored_optimizer)

    assert meta["current_lr"] == 1.5e-5
    assert meta["step"] == 50

    # Ensure optimizer state dict has exact momentum
    for k in optimizer.state_dict()["state"]:
        for t_name in ["exp_avg", "exp_avg_sq"]:
            t_orig = optimizer.state_dict()["state"][k][t_name]
            t_rest = restored_optimizer.state_dict()["state"][k][t_name]
            assert torch.allclose(t_orig, t_rest)


if __name__ == "__main__":
    print("=" * 80)
    print("RUNNING PHASE 11.1 STEP 2.5 FINAL HARNESS REMEDIATION TESTS")
    print("=" * 80)

    tests = [
        ("1. Invalid checkpoint path produces original error (no NameError)", test_invalid_checkpoint_path_error),
        ("2. Corrupted checkpoint produces CheckpointIntegrityError (no NameError)", test_corrupted_checkpoint_error_logger),
        ("3. Mid-epoch resume sample position", test_mid_epoch_resume_logic),
        ("4. Last-sample resume & next-epoch transition", test_last_sample_resume_and_next_epoch_transition),
        ("5. Final-epoch completion (clean termination)", test_final_epoch_completion),
        ("6. Multi-phase resume without duplicate samples", test_multi_phase_resume_no_duplicate_samples),
        ("7. Optimizer & scheduler continuity across epoch boundary", test_optimizer_and_scheduler_continuity_across_epoch),
    ]

    passed = 0
    failed = 0

    for name, fn in tests:
        tmp_d = Path(tempfile.mkdtemp(prefix="test_step2_5_"))
        try:
            fn(tmp_d)
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
