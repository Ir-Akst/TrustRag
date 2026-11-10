"""HalluGuard-inspired Small Reasoning Model (SRM) backends and deterministic fallback.

Supports:
- Local Ollama HTTP backend (`local_ollama`)
- OpenAI-compatible HTTP API backend (`openai_compatible`)
- Deterministic evidence-synthesis fallback (`DeterministicFallbackBackend`) when no
  live SRM model checkpoint/server is configured, available, or responsive within timeout.

Note: No pre-trained large model checkpoint is downloaded or bundled in Phase 03.
"""

from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx

from trustrag.config.engine_config import SRMConfig
from trustrag.config.settings import LLMProviderConfig
from trustrag.engine.schemas import (
    EvidenceOutcome,
    SRMClaimJudgment,
    SRMExecutionStatus,
    SRMRequest,
    SRMResponse,
)
from trustrag.exceptions import ModelError, ProviderError


class BaseSRMBackend(ABC):
    """Abstract interface for HalluGuard-inspired SRM backends."""

    backend_name: str = "base"

    @abstractmethod
    def invoke(self, request: SRMRequest) -> SRMResponse:
        """Execute structured reasoning over query, evidence, answer, and G2/G3 signals."""


def _build_srm_prompt(request: SRMRequest) -> str:
    """Build deterministic verification prompt compatible with small reasoning models."""
    passages_block = "\n".join(
        f"[{p.get('doc_id', 'doc')}]: {p.get('text', '')}"
        for p in request.evidence_passages
    )
    claims_block = json.dumps(request.g3_claim_outcomes, ensure_ascii=False)
    return (
        "You are a concise HalluGuard verification reasoner. Assess whether the candidate answer "
        "is strictly supported by the evidence passages and consistent with G2/G3 signals. "
        "Reply ONLY with valid JSON containing keys: "
        "'verdict' (TRUSTWORTHY|CAUTION|UNTRUSTWORTHY|REFUSE), "
        "'reasoning_trace' (string), 'confidence' (float 0..1), and "
        "'claim_judgments' (list of {claim_text, outcome: SUPPORTS|CONTRADICTS|NOT_ENOUGH_EVIDENCE, rationale}).\n\n"
        f"Query: {request.query}\n"
        f"Candidate Answer: {request.candidate_answer}\n"
        f"Evidence Passages:\n{passages_block}\n"
        f"G2 Trust Scores: {json.dumps(request.g2_trust_scores)}\n"
        f"G3 Preliminary Claims: {claims_block}\n"
    )


def _parse_srm_json(
    raw_content: str,
    *,
    backend_name: str,
    model_name: str,
    latency_ms: float,
) -> SRMResponse:
    """Parse structured JSON emitted by an SRM backend into an explicit SRMResponse."""
    text = raw_content.strip()
    if text.startswith("```"):
        # Strip optional markdown JSON fences
        lines = [ln for ln in text.splitlines() if not ln.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ModelError(f"SRM returned non-JSON payload: {exc}") from exc

    if not isinstance(payload, dict):
        raise ModelError("SRM payload root must be a JSON object")

    verdict = str(payload.get("verdict") or "CAUTION").upper()
    if verdict not in {"TRUSTWORTHY", "CAUTION", "UNTRUSTWORTHY", "REFUSE"}:
        verdict = "CAUTION"

    judgments: List[SRMClaimJudgment] = []
    for item in payload.get("claim_judgments") or []:
        if not isinstance(item, dict):
            continue
        raw_out = str(item.get("outcome") or "NOT_ENOUGH_EVIDENCE").upper()
        try:
            outcome = EvidenceOutcome(raw_out)
        except ValueError:
            outcome = EvidenceOutcome.NOT_ENOUGH_EVIDENCE
        judgments.append(
            SRMClaimJudgment(
                claim_text=str(item.get("claim_text") or ""),
                outcome=outcome,
                rationale=str(item.get("rationale") or ""),
            )
        )

    try:
        conf = float(payload.get("confidence", 0.5))
    except (TypeError, ValueError):
        conf = 0.5
    conf = min(1.0, max(0.0, conf))

    return SRMResponse(
        verdict=verdict,
        reasoning_trace=str(payload.get("reasoning_trace") or ""),
        claim_judgments=judgments,
        confidence=round(conf, 4),
        backend_used=backend_name,
        model_name=model_name,
        execution_status=SRMExecutionStatus.SUCCESS,
        latency_ms=round(latency_ms, 2),
        is_fallback=False,
    )


class LocalOllamaBackend(BaseSRMBackend):
    """HTTP backend for local Ollama-served Small Reasoning Models."""

    backend_name = "local_ollama"

    def __init__(
        self,
        srm_config: SRMConfig,
        llm_config: Optional[LLMProviderConfig] = None,
    ) -> None:
        self.srm_config = srm_config
        self.llm_config = llm_config or LLMProviderConfig()
        base = (srm_config.endpoint_url or self.llm_config.local_base_url).rstrip("/")
        self.endpoint = base if base.endswith("/api/chat") or base.endswith("/api/generate") else f"{base}/api/chat"

    def invoke(self, request: SRMRequest) -> SRMResponse:
        prompt = _build_srm_prompt(request)
        body: Dict[str, Any] = {
            "model": self.srm_config.model_name,
            "stream": False,
            "format": "json",
            "options": {"temperature": self.srm_config.temperature},
            "messages": [{"role": "user", "content": prompt}],
        }
        t0 = time.perf_counter()
        try:
            with httpx.Client(timeout=self.srm_config.timeout_seconds) as client:
                resp = client.post(self.endpoint, json=body)
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as exc:
            raise TimeoutError(
                f"Local Ollama SRM timed out after {self.srm_config.timeout_seconds}s"
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(f"Local Ollama SRM unavailable at '{self.endpoint}': {exc}") from exc

        latency_ms = (time.perf_counter() - t0) * 1000.0
        content = ""
        if isinstance(data, dict):
            msg = data.get("message")
            if isinstance(msg, dict):
                content = str(msg.get("content") or "")
            else:
                content = str(data.get("response") or "")

        return _parse_srm_json(
            content,
            backend_name=self.backend_name,
            model_name=self.srm_config.model_name,
            latency_ms=latency_ms,
        )


class OpenAICompatibleAPIBackend(BaseSRMBackend):
    """HTTP backend for OpenAI-compatible reasoning model APIs."""

    backend_name = "openai_compatible"

    def __init__(
        self,
        srm_config: SRMConfig,
        llm_config: Optional[LLMProviderConfig] = None,
    ) -> None:
        self.srm_config = srm_config
        self.llm_config = llm_config or LLMProviderConfig()
        base = (srm_config.endpoint_url or "https://api.openai.com/v1/chat/completions").rstrip("/")
        self.endpoint = base if base.endswith("/chat/completions") else f"{base}/chat/completions"

    def _resolve_credential(self) -> Optional[str]:
        return self.llm_config.openai_api_key or os.getenv("OPENAI_API_KEY")

    def invoke(self, request: SRMRequest) -> SRMResponse:
        credential = self._resolve_credential()
        if not credential:
            raise ProviderError("No API credential configured for openai_compatible SRM backend.")

        prompt = _build_srm_prompt(request)
        headers = {
            "Authorization": f"Bearer {credential}",
            "Content-Type": "application/json",
        }
        body: Dict[str, Any] = {
            "model": self.srm_config.model_name,
            "temperature": self.srm_config.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        t0 = time.perf_counter()
        try:
            with httpx.Client(timeout=self.srm_config.timeout_seconds) as client:
                resp = client.post(self.endpoint, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as exc:
            raise TimeoutError(
                f"OpenAI-compatible SRM timed out after {self.srm_config.timeout_seconds}s"
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(f"OpenAI-compatible SRM API error: {exc}") from exc

        latency_ms = (time.perf_counter() - t0) * 1000.0
        content = ""
        try:
            content = str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelError(f"Unexpected OpenAI-compatible SRM response shape: {exc}") from exc

        return _parse_srm_json(
            content,
            backend_name=self.backend_name,
            model_name=self.srm_config.model_name,
            latency_ms=latency_ms,
        )


class DeterministicFallbackBackend(BaseSRMBackend):
    """HalluGuard-inspired deterministic fallback reasoner synthesizing G2 & G3 evidence signals."""

    backend_name = "deterministic_fallback"

    def __init__(self, model_name: str = "halluguard-srm-fallback") -> None:
        self.model_name = model_name

    def invoke(
        self,
        request: SRMRequest,
        *,
        status: SRMExecutionStatus = SRMExecutionStatus.FALLBACK,
        error_detail: Optional[str] = None,
    ) -> SRMResponse:
        t0 = time.perf_counter()

        trust_values = list(request.g2_trust_scores.values())
        avg_trust = sum(trust_values) / len(trust_values) if trust_values else 0.0

        judgments: List[SRMClaimJudgment] = []
        contradicted = 0
        supported = 0
        nee = 0
        uncertain = 0

        for item in request.g3_claim_outcomes:
            raw_out = str(item.get("outcome") or "NOT_ENOUGH_EVIDENCE")
            try:
                outcome = EvidenceOutcome(raw_out)
            except ValueError:
                outcome = EvidenceOutcome.NOT_ENOUGH_EVIDENCE

            if outcome == EvidenceOutcome.CONTRADICTS:
                contradicted += 1
            elif outcome == EvidenceOutcome.SUPPORTS:
                supported += 1
            elif outcome == EvidenceOutcome.UNCERTAIN:
                uncertain += 1
            else:
                nee += 1

            judgments.append(
                SRMClaimJudgment(
                    claim_text=str(item.get("claim_text") or ""),
                    outcome=outcome,
                    rationale=str(item.get("explanation") or "Synthesized from G3 evidence alignment."),
                )
            )

        if not request.evidence_passages:
            verdict = "REFUSE"
            conf = 0.90
            trace = (
                "Deterministic SRM fallback: zero trusted evidence passages survived G2 assessment; "
                "recommending abstention/refusal."
            )
        elif contradicted > 0:
            verdict = "UNTRUSTWORTHY"
            conf = 0.92
            trace = (
                f"Deterministic SRM fallback: detected {contradicted} contradicted claim(s) against "
                f"{len(request.evidence_passages)} evidence passage(s) (avg_g2_trust={avg_trust:.2f})."
            )
        elif nee > 0 or uncertain > 0:
            verdict = "CAUTION"
            conf = round(max(0.50, 0.70 * (supported / max(1, len(judgments)))), 4)
            trace = (
                f"Deterministic SRM fallback: {nee} insufficient and {uncertain} uncertain/conflicting claim(s) "
                f"(supported={supported}, avg_g2_trust={avg_trust:.2f})."
            )
        elif supported > 0 and avg_trust >= 0.65:
            verdict = "TRUSTWORTHY"
            conf = round(min(0.95, 0.55 + 0.40 * avg_trust), 4)
            trace = (
                f"Deterministic SRM fallback: all {supported} claim(s) verified against "
                f"high-trust evidence (avg_g2_trust={avg_trust:.2f})."
            )
        else:
            verdict = "CAUTION"
            conf = 0.60
            trace = (
                f"Deterministic SRM fallback: moderate evidence confidence "
                f"(supported={supported}, avg_g2_trust={avg_trust:.2f})."
            )

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return SRMResponse(
            verdict=verdict,
            reasoning_trace=trace,
            claim_judgments=judgments,
            confidence=conf,
            backend_used=self.backend_name,
            model_name=self.model_name,
            execution_status=status,
            latency_ms=round(latency_ms, 2),
            is_fallback=True,
            error_detail=error_detail,
        )


__all__ = [
    "BaseSRMBackend",
    "LocalOllamaBackend",
    "OpenAICompatibleAPIBackend",
    "DeterministicFallbackBackend",
]

