"""HalluGuard-inspired Small Reasoning Model (SRM) backends and deterministic fallback.

Supports:
- Local Ollama HTTP backend (`local_ollama`)
- OpenAI-compatible HTTP API backend (`openai_compatible`)
- Optional pluggable model-backed backends via SRMBackendRegistry (e.g., `hf_local` in Step 03)
- Deterministic evidence-synthesis fallback (`DeterministicFallbackBackend`) when explicitly
  configured (`disabled`) or permitted via explicit `fallback_on_error=True`.
"""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence

import httpx

from trustrag.config.engine_config import SRMConfig
from trustrag.config.settings import LLMProviderConfig
from trustrag.engine.schemas import (
    EvidenceOutcome,
    HallucinationCategory,
    SRMBackendHealth,
    SRMClaimJudgment,
    SRMExecutionStatus,
    SRMRequest,
    SRMResponse,
)
from trustrag.exceptions import ModelError, ProviderError

_THINK_BLOCK_RE = re.compile(r"<think>([\s\S]*?)</think>", re.IGNORECASE)


def _normalize_for_span_match(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).lower().split())


def _extract_balanced_json(text: str) -> str:
    """Extract the last/outermost balanced JSON object from raw model text."""
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    in_string = False
    escaped = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if escaped:
            escaped = False
            continue
        if ch == "\\" and in_string:
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]
    return text


def _map_hallucination_category(raw_cat: Any, outcome: EvidenceOutcome) -> HallucinationCategory:
    """Map model classification labels into the canonical 5-class HalluGuard taxonomy."""
    if isinstance(raw_cat, str) and raw_cat.strip():
        norm = raw_cat.strip().upper().replace("-", "_").replace(" ", "_")
        alias_map = {
            "GROUNDED": HallucinationCategory.GROUNDED,
            "SUPPORTED": HallucinationCategory.GROUNDED,
            "SUPPORTS": HallucinationCategory.GROUNDED,
            "INTRINSIC": HallucinationCategory.INTRINSIC_HALLUCINATION,
            "INTRINSIC_HALLUCINATION": HallucinationCategory.INTRINSIC_HALLUCINATION,
            "EXTRINSIC": HallucinationCategory.EXTRINSIC_HALLUCINATION,
            "EXTRINSIC_HALLUCINATION": HallucinationCategory.EXTRINSIC_HALLUCINATION,
            "INSUFFICIENT": HallucinationCategory.INSUFFICIENT_EVIDENCE,
            "INSUFFICIENT_EVIDENCE": HallucinationCategory.INSUFFICIENT_EVIDENCE,
            "NOT_ENOUGH_EVIDENCE": HallucinationCategory.INSUFFICIENT_EVIDENCE,
            "UNVERIFIED": HallucinationCategory.INSUFFICIENT_EVIDENCE,
            "CONTRADICTED": HallucinationCategory.CONTRADICTED,
            "CONTRADICTS": HallucinationCategory.CONTRADICTED,
        }
        if norm in alias_map:
            return alias_map[norm]
    if outcome == EvidenceOutcome.SUPPORTS:
        return HallucinationCategory.GROUNDED
    if outcome == EvidenceOutcome.CONTRADICTS:
        return HallucinationCategory.CONTRADICTED
    return HallucinationCategory.INSUFFICIENT_EVIDENCE


class BaseSRMBackend(ABC):
    """Abstract lifecycle-aware interface for HalluGuard-inspired SRM backends."""

    backend_name: str = "base"
    is_real_model: bool = False

    def initialize(self) -> None:
        """Initialize or validate backend resources prior to inference."""

    def shutdown(self) -> None:
        """Release loaded models, handles, or HTTP pools safely."""

    def health_check(self) -> SRMBackendHealth:
        """Return explicit backend readiness without triggering remote downloads."""
        return SRMBackendHealth(
            backend_name=self.backend_name,
            model_name=getattr(self, "model_name", "unknown"),
            initialized=True,
            available=True,
            is_real_model=self.is_real_model,
            detail="Base backend ready.",
        )

    @abstractmethod
    def invoke(self, request: SRMRequest) -> SRMResponse:
        """Execute structured reasoning over query, evidence, answer, and signals."""

    def invoke_batch(self, requests: Sequence[SRMRequest], *, max_batch_size: int = 4) -> List[SRMResponse]:
        """Execute bounded batch inference cleanly, isolating individual sample sizes."""
        if max_batch_size < 1:
            raise ValueError("max_batch_size must be >= 1")
        responses: List[SRMResponse] = []
        for idx in range(0, len(requests), max_batch_size):
            for req in requests[idx : idx + max_batch_size]:
                responses.append(self.invoke(req))
        return responses

    def verify_claims(self, request: SRMRequest) -> List[SRMClaimJudgment]:
        """Convenience interface returning claim-level judgments from invoke()."""
        return self.invoke(request).claim_judgments

    def classify_evidence(
        self,
        query: str,
        evidence_passages: Sequence[Dict[str, str]],
        candidate_answer: str,
    ) -> SRMResponse:
        """Direct evidence classification wrapper blind to G3 rule outcomes."""
        return self.invoke(
            SRMRequest(
                query=query,
                candidate_answer=candidate_answer,
                evidence_passages=list(evidence_passages),
                blind_to_g3_heuristics=True,
            )
        )


def _build_srm_prompt(
    request: SRMRequest,
    *,
    inference_mode: str = "non_think",
) -> str:
    """Build structured verification prompt aligned with HalluGuard evidence classification."""
    passages_block = "\n".join(
        f"[{p.get('doc_id', 'doc')}]: {p.get('text', '')}"
        for p in request.evidence_passages
    )
    mode_instruction = (
        "You may first emit reasoning inside <think>...</think> tags, then output valid JSON. "
        if inference_mode == "think"
        else "Reply ONLY with valid JSON (no <think> block or markdown prose). "
    )
    heuristic_block = (
        ""
        if request.blind_to_g3_heuristics
        else (
            f"G2 Trust Scores: {json.dumps(request.g2_trust_scores)}\n"
            f"G3 Preliminary Claims: {json.dumps(request.g3_claim_outcomes, ensure_ascii=False)}\n"
        )
    )
    return (
        "You are an evidence-grounded HalluGuard verification model. Classify whether the candidate answer "
        "is strictly grounded in the retrieved evidence passages.\n"
        f"{mode_instruction}"
        "JSON keys required: "
        "'verdict' (TRUSTWORTHY|CAUTION|UNTRUSTWORTHY|REFUSE), "
        "'reasoning_trace' (string), 'confidence' (float 0..1), and 'claim_judgments' (list of "
        "{claim_id, claim_text, outcome: SUPPORTS|CONTRADICTS|NOT_ENOUGH_EVIDENCE, "
        "hallucination_category: GROUNDED|INTRINSIC_HALLUCINATION|EXTRINSIC_HALLUCINATION|INSUFFICIENT_EVIDENCE|CONTRADICTED, "
        "evidence_ids: [str], cited_spans: [str], confidence: float, rationale: str}).\n\n"
        f"Query: {request.query}\n"
        f"Candidate Answer: {request.candidate_answer}\n"
        f"Evidence Passages:\n{passages_block}\n"
        f"{heuristic_block}"
    )


def _parse_srm_json(
    raw_content: str,
    *,
    backend_name: str,
    model_name: str,
    latency_ms: float,
    inference_mode: str = "non_think",
    evidence_passages: Optional[Sequence[Dict[str, str]]] = None,
    enforce_citation_grounding: bool = True,
    model_config_snapshot: Optional[Dict[str, Any]] = None,
) -> SRMResponse:
    """Parse structured JSON (and optional <think> traces) into an explicit SRMResponse."""
    text = raw_content.strip()
    think_matches = _THINK_BLOCK_RE.findall(text)
    raw_think = "\n".join(m.strip() for m in think_matches if m.strip()) or None
    if think_matches:
        text = _THINK_BLOCK_RE.sub("", text).strip()

    if text.startswith("```"):
        lines = [ln for ln in text.splitlines() if not ln.strip().startswith("```")]
        text = "\n".join(lines).strip()

    json_candidate = _extract_balanced_json(text)
    try:
        payload = json.loads(json_candidate)
    except json.JSONDecodeError as exc:
        raise ModelError(f"SRM returned non-JSON payload: {exc}") from exc

    if not isinstance(payload, dict):
        raise ModelError("SRM payload root must be a JSON object")

    verdict = str(payload.get("verdict") or "CAUTION").upper()
    if verdict not in {"TRUSTWORTHY", "CAUTION", "UNTRUSTWORTHY", "REFUSE"}:
        verdict = "CAUTION"

    norm_evidence = [
        _normalize_for_span_match(str(p.get("text") or ""))
        for p in (evidence_passages or [])
        if str(p.get("text") or "").strip()
    ]

    judgments: List[SRMClaimJudgment] = []
    for idx, item in enumerate(payload.get("claim_judgments") or [], start=1):
        if not isinstance(item, dict):
            continue
        raw_out = str(item.get("outcome") or "NOT_ENOUGH_EVIDENCE").upper()
        try:
            outcome = EvidenceOutcome(raw_out)
        except ValueError:
            outcome = EvidenceOutcome.NOT_ENOUGH_EVIDENCE
        category = _map_hallucination_category(item.get("hallucination_category"), outcome)
        raw_spans = [str(s) for s in (item.get("cited_spans") or []) if str(s).strip()]
        spans_ok = False
        if raw_spans and norm_evidence:
            spans_ok = all(
                any(_normalize_for_span_match(sp) in ev_txt for ev_txt in norm_evidence)
                for sp in raw_spans
            )
        elif not enforce_citation_grounding and outcome != EvidenceOutcome.SUPPORTS:
            spans_ok = False

        raw_item_conf = item.get("confidence")
        if raw_item_conf is None:
            raw_item_conf = payload.get("confidence", 0.5)
        try:
            item_conf = float(0.5 if raw_item_conf is None else raw_item_conf)
        except (TypeError, ValueError):
            item_conf = 0.5
        item_conf = min(1.0, max(0.0, item_conf))

        ev_ids = [str(eid) for eid in (item.get("evidence_ids") or []) if str(eid).strip()]
        judgments.append(
            SRMClaimJudgment(
                claim_id=str(item.get("claim_id") or f"claim_{idx}"),
                claim_text=str(item.get("claim_text") or ""),
                outcome=outcome,
                hallucination_category=category,
                evidence_ids=ev_ids,
                cited_spans=raw_spans,
                verified_citations=spans_ok,
                confidence=round(item_conf, 4),
                rationale=str(item.get("rationale") or ""),
            )
        )

    try:
        conf = float(payload.get("confidence", 0.5))
    except (TypeError, ValueError):
        conf = 0.5
    conf = min(1.0, max(0.0, conf))

    trace = str(payload.get("reasoning_trace") or "")
    if raw_think and not trace:
        trace = raw_think

    return SRMResponse(
        verdict=verdict,
        reasoning_trace=trace,
        claim_judgments=judgments,
        confidence=round(conf, 4),
        backend_used=backend_name,
        model_name=model_name,
        execution_status=SRMExecutionStatus.SUCCESS,
        latency_ms=round(latency_ms, 2),
        is_fallback=False,
        inference_mode=inference_mode,
        raw_think_trace=raw_think,
        model_config_snapshot=dict(model_config_snapshot or {}),
    )


class LocalOllamaBackend(BaseSRMBackend):
    """HTTP backend for local Ollama-served Small Reasoning Models."""

    backend_name = "local_ollama"
    is_real_model = True

    def __init__(
        self,
        srm_config: SRMConfig,
        llm_config: Optional[LLMProviderConfig] = None,
    ) -> None:
        self.srm_config = srm_config
        self.model_name = srm_config.model_name
        self.llm_config = llm_config or LLMProviderConfig()
        base = (srm_config.endpoint_url or self.llm_config.local_base_url).rstrip("/")
        self.base_url = base.removesuffix("/api/chat").removesuffix("/api/generate")
        self.endpoint = base if base.endswith("/api/chat") or base.endswith("/api/generate") else f"{base}/api/chat"
        self._initialized = False
        self._last_error: Optional[str] = None

    def initialize(self) -> None:
        """Probe Ollama /api/tags without downloading models."""
        try:
            with httpx.Client(timeout=min(2.0, self.srm_config.timeout_seconds)) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
            self._initialized = True
            self._last_error = None
        except (httpx.HTTPError, ValueError) as exc:
            self._initialized = False
            self._last_error = str(exc)
            raise ProviderError(f"Local Ollama daemon unreachable at '{self.base_url}': {exc}") from exc

    def shutdown(self) -> None:
        self._initialized = False

    def health_check(self) -> SRMBackendHealth:
        available = False
        detail = "Not checked"
        try:
            with httpx.Client(timeout=min(2.0, self.srm_config.timeout_seconds)) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                models = [m.get("name", "") for m in (resp.json().get("models") or [])]
                available = self.srm_config.model_name in models or any(
                    m.startswith(f"{self.srm_config.model_name}:") for m in models
                )
                detail = (
                    f"Ollama live at {self.base_url}; model_present={available}"
                    if models
                    else f"Ollama live at {self.base_url}; zero local models pulled"
                )
        except (httpx.HTTPError, ValueError) as exc:
            self._last_error = str(exc)
            detail = f"Ollama unavailable: {exc}"
        return SRMBackendHealth(
            backend_name=self.backend_name,
            model_name=self.srm_config.model_name,
            initialized=self._initialized,
            available=available,
            is_real_model=True,
            device=self.srm_config.device,
            inference_mode=self.srm_config.inference_mode,
            detail=detail,
            last_error=self._last_error,
        )

    def invoke(self, request: SRMRequest) -> SRMResponse:
        prompt = _build_srm_prompt(request, inference_mode=self.srm_config.inference_mode)
        body: Dict[str, Any] = {
            "model": self.srm_config.model_name,
            "stream": False,
            "options": {
                "temperature": self.srm_config.temperature,
                "num_predict": self.srm_config.max_new_tokens,
            },
            "messages": [{"role": "user", "content": prompt}],
        }
        if self.srm_config.inference_mode == "non_think":
            body["format"] = "json"
        t0 = time.perf_counter()
        try:
            with httpx.Client(timeout=self.srm_config.timeout_seconds) as client:
                resp = client.post(self.endpoint, json=body)
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as exc:
            self._last_error = str(exc)
            raise TimeoutError(
                f"Local Ollama SRM timed out after {self.srm_config.timeout_seconds}s"
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            self._last_error = str(exc)
            raise ProviderError(f"Local Ollama SRM unavailable at '{self.endpoint}': {exc}") from exc

        latency_ms = (time.perf_counter() - t0) * 1000.0
        content = ""
        if isinstance(data, dict):
            msg = data.get("message")
            if isinstance(msg, dict):
                content = str(msg.get("content") or "")
            else:
                content = str(data.get("response") or "")

        self._initialized = True
        self._last_error = None
        return _parse_srm_json(
            content,
            backend_name=self.backend_name,
            model_name=self.srm_config.model_name,
            latency_ms=latency_ms,
            inference_mode=self.srm_config.inference_mode,
            evidence_passages=request.evidence_passages,
            enforce_citation_grounding=self.srm_config.enforce_citation_grounding,
            model_config_snapshot={
                "backend": self.backend_name,
                "model_name": self.srm_config.model_name,
                "inference_mode": self.srm_config.inference_mode,
                "temperature": self.srm_config.temperature,
                "max_new_tokens": self.srm_config.max_new_tokens,
            },
        )


class OpenAICompatibleAPIBackend(BaseSRMBackend):
    """HTTP backend for OpenAI-compatible reasoning model APIs."""

    backend_name = "openai_compatible"
    is_real_model = True

    def __init__(
        self,
        srm_config: SRMConfig,
        llm_config: Optional[LLMProviderConfig] = None,
    ) -> None:
        self.srm_config = srm_config
        self.model_name = srm_config.model_name
        self.llm_config = llm_config or LLMProviderConfig()
        base = (srm_config.endpoint_url or "https://api.openai.com/v1/chat/completions").rstrip("/")
        self.endpoint = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
        self._last_error: Optional[str] = None

    def _resolve_credential(self) -> Optional[str]:
        return self.llm_config.openai_api_key or os.getenv("OPENAI_API_KEY")

    def initialize(self) -> None:
        if not self._resolve_credential():
            self._last_error = "Missing OPENAI_API_KEY credential"
            raise ProviderError("No API credential configured for openai_compatible SRM backend.")

    def health_check(self) -> SRMBackendHealth:
        has_key = bool(self._resolve_credential())
        return SRMBackendHealth(
            backend_name=self.backend_name,
            model_name=self.srm_config.model_name,
            initialized=has_key,
            available=has_key,
            is_real_model=True,
            device="remote_api",
            inference_mode=self.srm_config.inference_mode,
            detail="Credential configured" if has_key else "Missing API credential",
            last_error=self._last_error,
        )

    def invoke(self, request: SRMRequest) -> SRMResponse:
        credential = self._resolve_credential()
        if not credential:
            raise ProviderError("No API credential configured for openai_compatible SRM backend.")

        prompt = _build_srm_prompt(request, inference_mode=self.srm_config.inference_mode)
        headers = {
            "Authorization": f"Bearer {credential}",
            "Content-Type": "application/json",
        }
        body: Dict[str, Any] = {
            "model": self.srm_config.model_name,
            "temperature": self.srm_config.temperature,
            "max_tokens": self.srm_config.max_new_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        t0 = time.perf_counter()
        try:
            with httpx.Client(timeout=self.srm_config.timeout_seconds) as client:
                resp = client.post(self.endpoint, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as exc:
            self._last_error = str(exc)
            raise TimeoutError(
                f"OpenAI-compatible SRM timed out after {self.srm_config.timeout_seconds}s"
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            self._last_error = str(exc)
            raise ProviderError(f"OpenAI-compatible SRM API error: {exc}") from exc

        latency_ms = (time.perf_counter() - t0) * 1000.0
        try:
            content = str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelError(f"Unexpected OpenAI-compatible SRM response shape: {exc}") from exc

        self._last_error = None
        return _parse_srm_json(
            content,
            backend_name=self.backend_name,
            model_name=self.srm_config.model_name,
            latency_ms=latency_ms,
            inference_mode=self.srm_config.inference_mode,
            evidence_passages=request.evidence_passages,
            enforce_citation_grounding=self.srm_config.enforce_citation_grounding,
            model_config_snapshot={
                "backend": self.backend_name,
                "model_name": self.srm_config.model_name,
                "inference_mode": self.srm_config.inference_mode,
                "temperature": self.srm_config.temperature,
                "max_new_tokens": self.srm_config.max_new_tokens,
            },
        )


class DeterministicFallbackBackend(BaseSRMBackend):
    """HalluGuard-inspired deterministic fallback reasoner synthesizing G2 & G3 evidence signals."""

    backend_name = "deterministic_fallback"
    is_real_model = False

    def __init__(self, model_name: str = "halluguard-srm-fallback") -> None:
        self.model_name = model_name

    def health_check(self) -> SRMBackendHealth:
        return SRMBackendHealth(
            backend_name=self.backend_name,
            model_name=self.model_name,
            initialized=True,
            available=True,
            is_real_model=False,
            device="cpu",
            inference_mode="deterministic",
            detail="Rule-based fallback active (NOT a trained neural SRM).",
        )

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

        for idx, item in enumerate(request.g3_claim_outcomes, start=1):
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
                    claim_id=str(item.get("claim_id") or f"claim_{idx}"),
                    claim_text=str(item.get("claim_text") or ""),
                    outcome=outcome,
                    hallucination_category=_map_hallucination_category(None, outcome),
                    evidence_ids=[str(eid) for eid in (item.get("evidence_ids") or [])],
                    confidence=0.80 if outcome in {EvidenceOutcome.SUPPORTS, EvidenceOutcome.CONTRADICTS} else 0.50,
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
            inference_mode="deterministic",
            error_detail=error_detail,
        )


__all__ = [
    "BaseSRMBackend",
    "LocalOllamaBackend",
    "OpenAICompatibleAPIBackend",
    "DeterministicFallbackBackend",
    "_build_srm_prompt",
    "_parse_srm_json",
]
