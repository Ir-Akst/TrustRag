"""Phase 08 Step 02 tests: Pluggable SRM backend registry, lifecycle, health, think-mode parser, and strict fallback controls."""

from __future__ import annotations

import json

import pytest

from trustrag.config.engine_config import SRMConfig
from trustrag.engine.schemas import (
    EvidenceOutcome,
    HallucinationCategory,
    SRMBackendHealth,
    SRMExecutionStatus,
    SRMRequest,
    SRMResponse,
)
from trustrag.exceptions import ModelError, ProviderError
from trustrag.srm import BaseSRMBackend, SRMBackendRegistry, SRMClient
from trustrag.srm.backends import _build_srm_prompt, _parse_srm_json


class _DummyCustomBackend(BaseSRMBackend):
    backend_name = "custom_test"
    is_real_model = True

    def __init__(self, srm_cfg: SRMConfig) -> None:
        self.srm_cfg = srm_cfg
        self.model_name = srm_cfg.model_name
        self.initialized = False
        self.shutdown_called = False

    def initialize(self) -> None:
        self.initialized = True

    def shutdown(self) -> None:
        self.shutdown_called = True
        self.initialized = False

    def health_check(self) -> SRMBackendHealth:
        return SRMBackendHealth(
            backend_name=self.backend_name,
            model_name=self.model_name,
            initialized=self.initialized,
            available=True,
            is_real_model=True,
            inference_mode=self.srm_cfg.inference_mode,
            detail="Custom test double ready.",
        )

    def invoke(self, request: SRMRequest) -> SRMResponse:
        raw = json.dumps(
            {
                "verdict": "UNTRUSTWORTHY",
                "reasoning_trace": "Detected extrinsic claim.",
                "confidence": 0.91,
                "claim_judgments": [
                    {
                        "claim_id": "c1",
                        "claim_text": "Claim grounded",
                        "outcome": "SUPPORTS",
                        "hallucination_category": "GROUNDED",
                        "evidence_ids": ["d1"],
                        "cited_spans": ["Paris is the capital of France"],
                        "confidence": 0.94,
                        "rationale": "Matches passage d1.",
                    },
                    {
                        "claim_id": "c2",
                        "claim_text": "Invented year 2099",
                        "outcome": "NOT_ENOUGH_EVIDENCE",
                        "hallucination_category": "EXTRINSIC_HALLUCINATION",
                        "evidence_ids": [],
                        "cited_spans": ["nonexistent span"],
                        "confidence": 0.88,
                        "rationale": "Not present in d1.",
                    },
                ],
            }
        )
        return _parse_srm_json(
            raw,
            backend_name=self.backend_name,
            model_name=self.model_name,
            latency_ms=1.5,
            inference_mode=self.srm_cfg.inference_mode,
            evidence_passages=request.evidence_passages,
        )


def test_registry_and_lifecycle_health() -> None:
    SRMBackendRegistry.register("custom", lambda cfg, _llm: _DummyCustomBackend(cfg))
    cfg = SRMConfig(backend="custom", model_name="test-4b", inference_mode="think", fallback_on_error=False)
    client = SRMClient(config=cfg)
    assert "custom" in SRMBackendRegistry.list_backends()

    h0 = client.initialize()
    assert h0.initialized is True
    assert h0.is_real_model is True
    assert h0.inference_mode == "think"

    resp = client.classify_evidence(
        "What is the capital of France?",
        [{"doc_id": "d1", "text": "Paris is the capital of France."}],
        "Paris is the capital of France.",
    )
    assert resp.execution_status == SRMExecutionStatus.SUCCESS
    assert resp.is_fallback is False
    assert resp.claim_judgments[0].hallucination_category == HallucinationCategory.GROUNDED
    assert resp.claim_judgments[0].verified_citations is True
    assert resp.claim_judgments[1].hallucination_category == HallucinationCategory.EXTRINSIC_HALLUCINATION
    assert resp.claim_judgments[1].verified_citations is False

    batch = client.reason_batch(
        [
            SRMRequest(query="q1", candidate_answer="a1", evidence_passages=[{"doc_id": "d1", "text": "Paris is the capital of France."}]),
            SRMRequest(query="q2", candidate_answer="a2", evidence_passages=[{"doc_id": "d1", "text": "Paris is the capital of France."}]),
        ]
    )
    assert len(batch) == 2

    client.shutdown()
    assert client.health_check().initialized is False


def test_strict_no_silent_fallback_when_disabled_and_explicit_when_enabled() -> None:
    class _BrokenTimeoutBackend(BaseSRMBackend):
        backend_name = "broken_timeout"
        is_real_model = True

        def invoke(self, request: SRMRequest) -> SRMResponse:
            raise TimeoutError("Model timed out")

    req = SRMRequest(query="q", candidate_answer="a", evidence_passages=[{"doc_id": "d1", "text": "e"}])

    strict_client = SRMClient(
        config=SRMConfig(backend="local_ollama", model_name="qwen2.5:1.5b", fallback_on_error=False),
        backend=_BrokenTimeoutBackend(),
    )
    with pytest.raises(TimeoutError):
        strict_client.reason(req)

    fb_client = SRMClient(
        config=SRMConfig(backend="local_ollama", model_name="qwen2.5:1.5b", fallback_on_error=True),
        backend=_BrokenTimeoutBackend(),
    )
    fb_resp = fb_client.reason(req)
    assert fb_resp.is_fallback is True
    assert fb_resp.execution_status == SRMExecutionStatus.TIMEOUT
    assert fb_resp.error_detail == "Model timed out"


def test_think_parser_and_malformed_output_handling() -> None:
    think_payload = (
        "<think>Comparing passage claims line by line.</think>\n"
        '{"verdict":"TRUSTWORTHY","reasoning_trace":"Verified.","confidence":0.9,'
        '"claim_judgments":[{"claim_text":"A","outcome":"CONTRADICTS","hallucination_category":"INTRINSIC_HALLUCINATION","rationale":"R"}]}'
    )
    parsed = _parse_srm_json(
        think_payload,
        backend_name="local_ollama",
        model_name="qwen3:4b",
        latency_ms=10.0,
        inference_mode="think",
    )
    assert parsed.raw_think_trace == "Comparing passage claims line by line."
    assert parsed.claim_judgments[0].outcome == EvidenceOutcome.CONTRADICTS
    assert parsed.claim_judgments[0].hallucination_category == HallucinationCategory.INTRINSIC_HALLUCINATION

    with pytest.raises(ModelError):
        _parse_srm_json("NOT JSON AT ALL", backend_name="local_ollama", model_name="x", latency_ms=1.0)

    req_blind = SRMRequest(
        query="q",
        candidate_answer="a",
        g3_claim_outcomes=[{"outcome": "SUPPORTS", "claim_text": "leak"}],
        blind_to_g3_heuristics=True,
    )
    assert "Preliminary Claims" not in _build_srm_prompt(req_blind, inference_mode="think")

    with pytest.raises(ProviderError):
        SRMBackendRegistry.create(SRMConfig(backend="local_ollama", endpoint_url="http://127.0.0.1:19999")).initialize()
