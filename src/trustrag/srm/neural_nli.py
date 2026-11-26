"""Neural NLI Small Reasoning Model (SRM) backend using frozen DeBERTa-v3-small.

Provides real neural inference verification for SRM reasoning:
- Loads the frozen DeBERTa-v3-small NLI checkpoint with cryptographic hash verification
- Executes genuine PyTorch forward passes producing valid softmax probabilities
- Enforces strict contradiction precedence (p_con >= 0.20) and entailment thresholding (p_ent >= 0.50)
- Exposes comprehensive inference health checks (device, dtype, latency, probability normalization)
- Fails safely to explicit degraded status on checkpoint corruption or load failure
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

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
from trustrag.srm.backends import (
    BaseSRMBackend,
    DeterministicFallbackBackend,
    _map_hallucination_category,
)
from trustrag.utils.logging import get_logger

LOGGER = get_logger(__name__)

DEFAULT_FROZEN_CHECKPOINT = "/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch"

# Label indices from fine-tuning: 0: ENTAILMENT, 1: CONTRADICTION, 2: NEUTRAL
LABEL_ENTAILMENT = 0
LABEL_CONTRADICTION = 1
LABEL_NEUTRAL = 2


class NeuralNLISRMBackend(BaseSRMBackend):
    """Real neural SRM backend powered by frozen DeBERTa-v3-small NLI sequence classification."""

    backend_name = "neural_nli"
    is_real_model = True

    def __init__(
        self,
        srm_config: SRMConfig,
        llm_config: LLMProviderConfig | None = None,
    ) -> None:
        self.srm_config = srm_config
        self.llm_config = llm_config
        raw_path = srm_config.model_name
        if not raw_path or raw_path in ("halluguard-srm-fallback", "disabled", "default"):
            self.model_path = Path(DEFAULT_FROZEN_CHECKPOINT)
        else:
            self.model_path = Path(raw_path)

        self._model: Any = None
        self._tokenizer: Any = None
        self._device: str = "cpu"
        self._dtype: str = "torch.float32"
        self._initialized: bool = False
        self._available: bool = False
        self._checkpoint_verified: bool = False
        self._last_error: str | None = None
        self._last_inference_timestamp: str | None = None
        self._last_inference_latency_ms: float | None = None
        self._last_probe_result: dict[str, Any] | None = None
        self._fallback_backend = DeterministicFallbackBackend(model_name="srm-fallback-degraded")

    def initialize(self) -> None:
        """Verify checkpoint integrity, load tokenizer/model, and execute verification probe."""
        if self._initialized and self._model is not None:
            return

        t0 = time.perf_counter()
        if not self.model_path.exists():
            msg = f"Neural SRM checkpoint directory does not exist: {self.model_path}"
            self._last_error = msg
            self._available = False
            self._initialized = False
            LOGGER.error(msg)
            raise ProviderError(msg)

        # 1. Verify required files exist
        required_files = ("config.json", "model.safetensors", "tokenizer_config.json")
        missing = [f for f in required_files if not (self.model_path / f).is_file()]
        if missing:
            msg = f"Neural SRM checkpoint is incomplete. Missing files: {missing} in {self.model_path}"
            self._last_error = msg
            self._available = False
            self._initialized = False
            LOGGER.error(msg)
            raise ModelError(msg)

        # 2. Cryptographic checksum validation
        chk_file = self.model_path / "checksums.sha256"
        if chk_file.is_file():
            try:
                self._verify_checksums(chk_file)
                self._checkpoint_verified = True
            except Exception as e:
                msg = f"Neural SRM checkpoint hash verification failed: {e}"
                self._last_error = msg
                self._available = False
                self._initialized = False
                LOGGER.error(msg)
                raise ModelError(msg) from e
        else:
            self._checkpoint_verified = False

        # 3. Load model and tokenizer
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            req_device = getattr(self.srm_config, "device", "cpu")
            if req_device == "auto":
                req_device = "cuda" if torch.cuda.is_available() else "cpu"
            if req_device == "cuda" and not torch.cuda.is_available():
                req_device = "cpu"

            tokenizer = AutoTokenizer.from_pretrained(str(self.model_path), local_files_only=True)
            model = AutoModelForSequenceClassification.from_pretrained(
                str(self.model_path),
                local_files_only=True,
            )
            model.to(req_device)
            model.eval()
            for p in model.parameters():
                p.requires_grad = False

            self._tokenizer = tokenizer
            self._model = model
            self._device = req_device
            self._dtype = str(next(model.parameters()).dtype)
            self._initialized = True
            self._available = True
            self._last_error = None
            LOGGER.info(
                "Neural SRM DeBERTa model loaded successfully in %.2f ms (device=%s, dtype=%s)",
                (time.perf_counter() - t0) * 1000.0,
                self._device,
                self._dtype,
            )

            # 4. Run real forward pass verification probe
            self.run_inference_probe()

        except (ModelError, ProviderError):
            raise
        except Exception as exc:
            msg = f"Failed to load Neural SRM from {self.model_path}: {exc}"
            self._last_error = msg
            self._available = False
            self._initialized = False
            LOGGER.error(msg)
            raise ModelError(msg) from exc

    def _verify_checksums(self, chk_path: Path) -> None:
        """Verify SHA-256 hashes of all checkpoint files listed in checksums.sha256."""
        with open(chk_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(maxsplit=1)
                if len(parts) != 2:
                    continue
                expected_hash, fname = parts
                fname = fname.strip("*").strip()
                fpath = self.model_path / fname
                if not fpath.is_file():
                    raise FileNotFoundError(f"Missing checkpoint file: {fname}")
                h = hashlib.sha256()
                with open(fpath, "rb") as bf:
                    while chunk := bf.read(65536):
                        h.update(chunk)
                if h.hexdigest().lower() != expected_hash.lower():
                    raise ValueError(f"Checksum mismatch for {fname}: got {h.hexdigest()}, expected {expected_hash}")

    def shutdown(self) -> None:
        """Release model/tokenizer references cleanly."""
        self._model = None
        self._tokenizer = None
        self._initialized = False
        self._available = False

    def run_inference_probe(
        self,
        premise: str = "At standard atmospheric pressure, water boils at 100 degrees Celsius.",
        hypothesis: str = "Water boils at 100 degrees Celsius at sea level.",
    ) -> dict[str, Any]:
        """Perform an actual forward pass with the neural model and return full telemetry."""
        if not self._initialized or self._model is None or self._tokenizer is None:
            return {
                "model_identifier": str(self.model_path),
                "model_loaded": False,
                "device": self._device,
                "dtype": self._dtype,
                "checkpoint_verified": self._checkpoint_verified,
                "last_successful_inference": None,
                "inference_success": False,
                "inference_latency_ms": None,
                "probabilities": None,
                "probabilities_valid": False,
                "error": self._last_error or "Model is not loaded or initialized.",
            }

        t0 = time.perf_counter()
        try:
            import torch

            inputs = self._tokenizer(
                premise,
                hypothesis,
                truncation=True,
                max_length=256,
                padding=True,
                return_tensors="pt",
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            with torch.no_grad():
                out = self._model(**inputs)
                probs = torch.softmax(out.logits[0], dim=-1).cpu().numpy().tolist()

            lat_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            p_ent = round(float(probs[LABEL_ENTAILMENT]), 4)
            p_neu = round(float(probs[LABEL_NEUTRAL]), 4)
            p_con = round(float(probs[LABEL_CONTRADICTION]), 4)
            prob_sum = p_ent + p_neu + p_con
            probs_valid = (
                0.0 <= p_ent <= 1.0
                and 0.0 <= p_neu <= 1.0
                and 0.0 <= p_con <= 1.0
                and 0.98 <= prob_sum <= 1.02
            )

            now_iso = datetime.now(timezone.utc).isoformat()
            self._last_inference_timestamp = now_iso
            self._last_inference_latency_ms = lat_ms
            res = {
                "model_identifier": str(self.model_path),
                "model_loaded": True,
                "device": self._device,
                "dtype": self._dtype,
                "checkpoint_verified": self._checkpoint_verified,
                "last_successful_inference": now_iso,
                "inference_success": True,
                "inference_latency_ms": lat_ms,
                "probabilities": {
                    "p_entailment": p_ent,
                    "p_neutral": p_neu,
                    "p_contradiction": p_con,
                    "sum": round(prob_sum, 4),
                },
                "probabilities_valid": probs_valid,
                "error": None,
            }
            self._last_probe_result = res
            return res
        except Exception as exc:
            lat_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            err_msg = f"Inference probe failed: {exc}"
            self._last_error = err_msg
            return {
                "model_identifier": str(self.model_path),
                "model_loaded": True,
                "device": self._device,
                "dtype": self._dtype,
                "checkpoint_verified": self._checkpoint_verified,
                "last_successful_inference": self._last_inference_timestamp,
                "inference_success": False,
                "inference_latency_ms": lat_ms,
                "probabilities": None,
                "probabilities_valid": False,
                "error": err_msg,
            }

    def health_check(self) -> SRMBackendHealth:
        """Report runtime health reflecting real model load status and actual forward pass capability."""
        if not self._initialized:
            try:
                self.initialize()
            except Exception as e:
                return SRMBackendHealth(
                    backend_name=self.backend_name,
                    model_name=str(self.model_path),
                    initialized=False,
                    available=False,
                    is_real_model=True,
                    device=self._device,
                    inference_mode="neural_nli",
                    detail=f"Neural SRM initialization failed: {e}",
                    last_error=str(e),
                    model_loaded=False,
                    model_dtype=self._dtype,
                    checkpoint_verified=False,
                    state="DEGRADED",
                )

        probe = self._last_probe_result or self.run_inference_probe()
        is_ok = bool(probe.get("inference_success", False))
        detail_msg = (
            f"Neural NLI DeBERTa loaded (device={self._device}, verified={self._checkpoint_verified}, "
            f"latency={probe.get('inference_latency_ms')}ms)"
            if is_ok
            else f"Neural SRM probe failed: {probe.get('error')}"
        )

        state_val = "READY" if is_ok else "DEGRADED"

        return SRMBackendHealth(
            backend_name=self.backend_name,
            model_name=str(self.model_path),
            initialized=self._initialized,
            available=is_ok,
            is_real_model=True,
            device=self._device,
            inference_mode="neural_nli",
            detail=detail_msg,
            last_error=probe.get("error"),
            model_loaded=bool(self._model is not None),
            model_dtype=self._dtype,
            checkpoint_verified=self._checkpoint_verified,
            last_inference_timestamp=probe.get("last_successful_inference"),
            last_inference_latency_ms=probe.get("inference_latency_ms"),
            probabilities=probe.get("probabilities"),
            state=state_val,
        )

    def invoke(
        self,
        request: SRMRequest,
        *,
        status: SRMExecutionStatus = SRMExecutionStatus.SUCCESS,
        error_detail: Optional[str] = None,
    ) -> SRMResponse:
        """Execute real neural DeBERTa-v3-small cross-examination for all claims against evidence."""
        t0 = time.perf_counter()

        if not self._initialized or not self._available:
            try:
                self.initialize()
            except Exception as exc:
                if self.srm_config.fallback_on_error:
                    LOGGER.warning("Neural SRM failed to initialize; falling back to deterministic: %s", exc)
                    return self._fallback_backend.invoke(
                        request,
                        status=SRMExecutionStatus.FALLBACK,
                        error_detail=f"Neural SRM unavailable ({exc}); deterministic fallback engaged.",
                    )
                raise

        if not request.evidence_passages:
            # Explicit empty evidence handling
            judgments: List[SRMClaimJudgment] = []
            for idx, item in enumerate(request.g3_claim_outcomes, start=1):
                judgments.append(
                    SRMClaimJudgment(
                        claim_id=str(item.get("claim_id") or f"claim_{idx}"),
                        claim_text=str(item.get("claim_text") or ""),
                        outcome=EvidenceOutcome.NOT_ENOUGH_EVIDENCE,
                        hallucination_category=HallucinationCategory.INSUFFICIENT_EVIDENCE,
                        evidence_ids=[],
                        confidence=0.90,
                        rationale="No candidate evidence passages supplied or retrieved.",
                    )
                )
            return SRMResponse(
                verdict="REFUSE",
                overall_confidence=0.95,
                backend_used=self.backend_name,
                model_name=str(self.model_path),
                claim_judgments=judgments,
                reasoning_trace="No evidence supplied to verify answer claims. Refusing safely.",
                latency_ms=round((time.perf_counter() - t0) * 1000.0, 3),
                execution_status=SRMExecutionStatus.SUCCESS,
                is_fallback=False,
            )

        import torch

        judgments = []
        has_contradiction = False
        all_supported = True
        claim_items = request.g3_claim_outcomes or [
            {"claim_id": "c1", "claim_text": request.query, "outcome": "SUPPORTS"}
        ]

        total_pairs = 0
        for idx, item in enumerate(claim_items, start=1):
            claim_text = str(item.get("claim_text") or "").strip()
            claim_id = str(item.get("claim_id") or f"claim_{idx}")
            if not claim_text:
                continue

            best_p_con = 0.0
            best_p_ent = 0.0
            best_p_neu = 0.0
            best_ev_id: Optional[str] = None

            for ev_id, ev_text in request.evidence_passages.items():
                if not ev_text.strip():
                    continue
                total_pairs += 1
                inputs = self._tokenizer(
                    ev_text,
                    claim_text,
                    truncation=True,
                    max_length=384,
                    padding=True,
                    return_tensors="pt",
                )
                inputs = {k: v.to(self._device) for k, v in inputs.items()}
                with torch.no_grad():
                    out = self._model(**inputs)
                    probs = torch.softmax(out.logits[0], dim=-1).cpu().numpy().tolist()

                p_ent = float(probs[LABEL_ENTAILMENT])
                p_neu = float(probs[LABEL_NEUTRAL])
                p_con = float(probs[LABEL_CONTRADICTION])

                if p_con > best_p_con:
                    best_p_con = p_con
                if p_ent > best_p_ent:
                    best_p_ent = p_ent
                    best_ev_id = ev_id

            # Enforce 0.20 contradiction threshold and 0.50 entailment threshold
            con_thresh = getattr(self.srm_config, "nli_contradiction_threshold", 0.20)
            ent_thresh = getattr(self.srm_config, "nli_entailment_threshold", 0.50)

            if best_p_con >= con_thresh:
                outcome = EvidenceOutcome.CONTRADICTS
                cat = HallucinationCategory.CONTRADICTED
                conf = round(best_p_con, 4)
                rat = f"Neural NLI identified contradiction (p_con={best_p_con:.4f} >= {con_thresh})."
                has_contradiction = True
                all_supported = False
            elif best_p_ent >= ent_thresh:
                outcome = EvidenceOutcome.SUPPORTS
                cat = HallucinationCategory.GROUNDED
                conf = round(best_p_ent, 4)
                rat = f"Neural NLI identified entailment (p_ent={best_p_ent:.4f} >= {ent_thresh})."
            else:
                outcome = EvidenceOutcome.NOT_ENOUGH_EVIDENCE
                cat = HallucinationCategory.INSUFFICIENT_EVIDENCE
                conf = round(1.0 - best_p_ent, 4)
                rat = f"Neural NLI found insufficient grounding (p_ent={best_p_ent:.4f} < {ent_thresh})."
                all_supported = False

            judgments.append(
                SRMClaimJudgment(
                    claim_id=claim_id,
                    claim_text=claim_text,
                    outcome=outcome,
                    hallucination_category=cat,
                    evidence_ids=[best_ev_id] if best_ev_id else [],
                    confidence=conf,
                    rationale=rat,
                )
            )

        if has_contradiction:
            overall_verdict = "UNTRUSTWORTHY"
            overall_conf = 0.90
        elif all_supported and judgments:
            overall_verdict = "TRUSTWORTHY"
            overall_conf = 0.88
        else:
            overall_verdict = "CAUTION"
            overall_conf = 0.70

        lat_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        now_iso = datetime.now(timezone.utc).isoformat()
        self._last_inference_timestamp = now_iso
        self._last_inference_latency_ms = lat_ms

        return SRMResponse(
            verdict=overall_verdict,
            overall_confidence=overall_conf,
            backend_used=self.backend_name,
            model_name=str(self.model_path),
            claim_judgments=judgments,
            reasoning_trace=(
                f"Neural DeBERTa-v3-small evaluated {len(judgments)} claims against {len(request.evidence_passages)} "
                f"passages ({total_pairs} forward passes) in {lat_ms}ms on {self._device} ({self._dtype})."
            ),
            latency_ms=lat_ms,
            execution_status=SRMExecutionStatus.SUCCESS,
            is_fallback=False,
            metadata={
                "device": self._device,
                "dtype": self._dtype,
                "checkpoint_verified": self._checkpoint_verified,
                "forward_pass_count": total_pairs,
                "model_identifier": str(self.model_path),
            },
        )
