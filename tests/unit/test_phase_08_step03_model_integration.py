"""Phase 08 Step 03 tests: Local HF/PEFT SRM adapter, 5-class categories, timeout, OOM, and offline BLOCKED guard."""

from __future__ import annotations

import json
import time

import pytest

from trustrag.config.engine_config import SRMConfig
from trustrag.engine.schemas import HallucinationCategory, SRMRequest
from trustrag.exceptions import ModelError, ProviderError
from trustrag.srm import HuggingFaceLocalSRMBackend, SRMBackendRegistry, SRMClient


class _FakeTokenizer:
    eos_token_id = 2
    pad_token_id = None

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):  # type: ignore[no-untyped-def]
        return messages[0]["content"]

    def __call__(self, text: str, return_tensors: str = "pt") -> dict[str, list[list[int]]]:
        return {"input_ids": [[10, 11, 12]]}

    def decode(self, token_ids, skip_special_tokens=True) -> str:  # type: ignore[no-untyped-def]
        payload = {
            "verdict": "UNTRUSTWORTHY",
            "reasoning_trace": "Evaluated five-class HalluGuard categories.",
            "confidence": 0.86,
            "claim_judgments": [
                {
                    "claim_id": "c1",
                    "claim_text": "Grounded claim",
                    "outcome": "SUPPORTS",
                    "hallucination_category": "GROUNDED",
                    "evidence_ids": ["d1"],
                    "cited_spans": ["AES-256 uses a 256-bit key"],
                    "confidence": 0.91,
                    "rationale": "Exact support in d1.",
                },
                {
                    "claim_id": "c2",
                    "claim_text": "Intrinsic error",
                    "outcome": "CONTRADICTS",
                    "hallucination_category": "INTRINSIC_HALLUCINATION",
                    "evidence_ids": ["d1"],
                    "cited_spans": [],
                    "confidence": 0.93,
                    "rationale": "Distorts fact inside evidence.",
                },
                {
                    "claim_id": "c3",
                    "claim_text": "Extrinsic claim",
                    "outcome": "NOT_ENOUGH_EVIDENCE",
                    "hallucination_category": "EXTRINSIC_HALLUCINATION",
                    "evidence_ids": [],
                    "cited_spans": [],
                    "confidence": 0.80,
                    "rationale": "External fabricated claim.",
                },
                {
                    "claim_id": "c4",
                    "claim_text": "Missing proof",
                    "outcome": "NOT_ENOUGH_EVIDENCE",
                    "hallucination_category": "INSUFFICIENT_EVIDENCE",
                    "evidence_ids": [],
                    "cited_spans": [],
                    "confidence": 0.72,
                    "rationale": "Insufficient evidence.",
                },
                {
                    "claim_id": "c5",
                    "claim_text": "Direct contradiction",
                    "outcome": "CONTRADICTS",
                    "hallucination_category": "CONTRADICTED",
                    "evidence_ids": ["d2"],
                    "cited_spans": [],
                    "confidence": 0.95,
                    "rationale": "Contradicted by d2.",
                },
            ],
        }
        return "<think>Inspecting passages carefully.</think>\n" + json.dumps(payload)


class _FakeModel:
    def generate(self, **kwargs):  # type: ignore[no-untyped-def]
        return [[10, 11, 12, 99, 100]]


def test_hf_local_offline_missing_checkpoint_and_runtime_guard() -> None:
    cfg = SRMConfig(backend="hf_local", model_name="local/missing-qwen-4b", local_files_only=True, fallback_on_error=False)
    backend = SRMBackendRegistry.create(cfg)
    assert isinstance(backend, HuggingFaceLocalSRMBackend)
    assert backend.health_check().available is False
    with pytest.raises(ProviderError):
        backend.initialize()


def test_hf_local_all_five_categories_and_uncalibrated_flag() -> None:
    cfg = SRMConfig(backend="hf_local", model_name="fake-halluguard-4b", inference_mode="think", batch_size=2, fallback_on_error=False)
    backend = HuggingFaceLocalSRMBackend(cfg, loader_override=lambda _c: (_FakeModel(), _FakeTokenizer(), "cpu"))
    client = SRMClient(config=cfg, backend=backend)
    health = client.initialize()
    assert health.initialized is True
    assert health.is_real_model is True

    req = SRMRequest(
        query="Test claims",
        candidate_answer="Mixed answer",
        evidence_passages=[{"doc_id": "d1", "text": "AES-256 uses a 256-bit key."}, {"doc_id": "d2", "text": "DES is insecure."}],
    )
    resp = client.reason(req)
    assert resp.raw_think_trace == "Inspecting passages carefully."
    assert resp.model_config_snapshot["confidence_calibrated"] is False
    cats = [j.hallucination_category for j in resp.claim_judgments]
    assert cats == [
        HallucinationCategory.GROUNDED,
        HallucinationCategory.INTRINSIC_HALLUCINATION,
        HallucinationCategory.EXTRINSIC_HALLUCINATION,
        HallucinationCategory.INSUFFICIENT_EVIDENCE,
        HallucinationCategory.CONTRADICTED,
    ]
    assert resp.claim_judgments[0].verified_citations is True

    batch = backend.invoke_batch([req, req, req])
    assert len(batch) == 3
    client.shutdown()
    assert backend.health_check().initialized is False


def test_hf_local_oom_timeout_and_tokenizer_validation() -> None:
    class _SlowModel:
        def generate(self, **kwargs):  # type: ignore[no-untyped-def]
            time.sleep(0.2)
            return [[10, 11, 12, 99]]

    class _OOMModel:
        def generate(self, **kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("CUDA out of memory while allocating tensor")

    cfg_to = SRMConfig(backend="hf_local", model_name="slow", timeout_seconds=0.05, fallback_on_error=False)
    slow_b = HuggingFaceLocalSRMBackend(cfg_to, loader_override=lambda _c: (_SlowModel(), _FakeTokenizer(), "cuda"))
    with pytest.raises(TimeoutError):
        slow_b.invoke(SRMRequest(query="q", candidate_answer="a"))

    cfg_oom = SRMConfig(backend="hf_local", model_name="oom", fallback_on_error=False)
    oom_b = HuggingFaceLocalSRMBackend(cfg_oom, loader_override=lambda _c: (_OOMModel(), _FakeTokenizer(), "cuda"))
    with pytest.raises(ModelError, match="OOM"):
        oom_b.invoke(SRMRequest(query="q", candidate_answer="a"))
    assert oom_b.health_check().initialized is False

    bad_tok_b = HuggingFaceLocalSRMBackend(cfg_oom, loader_override=lambda _c: (_FakeModel(), object(), "cpu"))
    with pytest.raises(ModelError, match="Incompatible SRM tokenizer"):
        bad_tok_b.initialize()
