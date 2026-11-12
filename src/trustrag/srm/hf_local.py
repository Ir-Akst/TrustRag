"""Optional local HuggingFace / LoRA-PEFT Small Reasoning Model backend (Phase 08 Step 03).

Supports local CPU/GPU causal LMs and optional PEFT adapters with lazy imports,
tokenizer validation, bounded inference timeouts, controlled batching, OOM isolation,
and deterministic test-double injection without downloading remote checkpoints.
"""

from __future__ import annotations

import importlib
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from pathlib import Path
from typing import Any

from trustrag.config.engine_config import SRMConfig
from trustrag.config.settings import LLMProviderConfig
from trustrag.engine.schemas import SRMBackendHealth, SRMRequest, SRMResponse
from trustrag.exceptions import ModelError, ProviderError
from trustrag.srm.backends import BaseSRMBackend, _build_srm_prompt, _parse_srm_json


class HuggingFaceLocalSRMBackend(BaseSRMBackend):
    """Resource-aware local Transformers / PEFT SRM backend."""

    backend_name = "hf_local"
    is_real_model = True

    def __init__(
        self,
        srm_config: SRMConfig,
        llm_config: LLMProviderConfig | None = None,
        *,
        loader_override: Callable[[SRMConfig], tuple[Any, Any, str]] | None = None,
    ) -> None:
        self.srm_config = srm_config
        self.model_name = srm_config.model_name
        self.llm_config = llm_config or LLMProviderConfig()
        self._loader_override = loader_override
        self._model: Any = None
        self._tokenizer: Any = None
        self._device_used: str = "cpu"
        self._initialized: bool = False
        self._last_error: str | None = None

    @staticmethod
    def _import_optional_runtime() -> tuple[Any, Any, Any | None]:
        try:
            torch_mod = importlib.import_module("torch")
            transformers_mod = importlib.import_module("transformers")
        except ImportError as exc:
            raise ProviderError(
                "hf_local SRM backend requires optional dependencies 'torch' and 'transformers', "
                f"which are not installed in this environment: {exc}"
            ) from exc
        try:
            peft_mod: Any | None = importlib.import_module("peft")
        except ImportError:
            peft_mod = None
        return torch_mod, transformers_mod, peft_mod

    def _validate_tokenizer(self, tokenizer: Any) -> None:
        if not callable(tokenizer) or not hasattr(tokenizer, "decode"):
            raise ModelError("Incompatible SRM tokenizer: missing callable tokenization or decode().")
        if getattr(tokenizer, "eos_token_id", None) is None and getattr(tokenizer, "pad_token_id", None) is None:
            raise ModelError("Incompatible SRM tokenizer: both eos_token_id and pad_token_id are unset.")
        if getattr(tokenizer, "pad_token_id", None) is None:
            tokenizer.pad_token_id = tokenizer.eos_token_id

    def initialize(self) -> None:
        """Load and validate tokenizer + model (+ optional PEFT LoRA adapter) locally."""
        if self._initialized and self._model is not None and self._tokenizer is not None:
            return

        if self._loader_override is not None:
            try:
                model, tokenizer, device_used = self._loader_override(self.srm_config)
                self._validate_tokenizer(tokenizer)
                if not hasattr(model, "generate"):
                    raise ModelError("Loaded SRM object lacks generate() method.")
                self._model = model
                self._tokenizer = tokenizer
                self._device_used = device_used
                self._initialized = True
                self._last_error = None
                return
            except (ModelError, ProviderError) as exc:
                self._last_error = str(exc)
                raise
            except Exception as exc:
                self._last_error = str(exc)
                raise ModelError(f"SRM loader_override failed: {exc}") from exc

        if self.srm_config.local_files_only:
            model_path = Path(self.srm_config.model_name)
            if not model_path.exists():
                msg = (
                    f"Local checkpoint '{self.srm_config.model_name}' not found and local_files_only=True "
                    "(automatic remote download disabled)."
                )
                self._last_error = msg
                raise ProviderError(msg)
            if self.srm_config.model_adapter_path and not Path(self.srm_config.model_adapter_path).exists():
                msg = f"Local PEFT adapter path '{self.srm_config.model_adapter_path}' does not exist."
                self._last_error = msg
                raise ProviderError(msg)

        torch_mod, transformers_mod, peft_mod = self._import_optional_runtime()
        req_dev = self.srm_config.device
        resolved_dev = "cuda" if (req_dev == "auto" and torch_mod.cuda.is_available()) else ("cpu" if req_dev == "auto" else req_dev)
        if resolved_dev == "cuda" and not torch_mod.cuda.is_available():
            raise ProviderError("CUDA requested for hf_local SRM backend but GPU is unavailable.")

        try:
            tokenizer = transformers_mod.AutoTokenizer.from_pretrained(
                self.srm_config.model_name,
                local_files_only=self.srm_config.local_files_only,
                trust_remote_code=self.srm_config.trust_remote_code,
            )
            self._validate_tokenizer(tokenizer)
            model = transformers_mod.AutoModelForCausalLM.from_pretrained(
                self.srm_config.model_name,
                local_files_only=self.srm_config.local_files_only,
                trust_remote_code=self.srm_config.trust_remote_code,
            )
            if self.srm_config.model_adapter_path:
                if peft_mod is None:
                    raise ProviderError("model_adapter_path specified but optional dependency 'peft' is not installed.")
                model = peft_mod.PeftModel.from_pretrained(
                    model,
                    self.srm_config.model_adapter_path,
                    local_files_only=self.srm_config.local_files_only,
                )
            model.to(resolved_dev)
            if hasattr(model, "eval"):
                model.eval()
            self._model = model
            self._tokenizer = tokenizer
            self._device_used = resolved_dev
            self._initialized = True
            self._last_error = None
        except (ProviderError, ModelError):
            raise
        except Exception as exc:
            self._last_error = str(exc)
            raise ModelError(f"Failed initializing hf_local SRM checkpoint '{self.srm_config.model_name}': {exc}") from exc

    def shutdown(self) -> None:
        """Release model/tokenizer references cleanly and clear CUDA cache if present."""
        self._model = None
        self._tokenizer = None
        self._initialized = False
        try:
            torch_mod = importlib.import_module("torch")
            if torch_mod.cuda.is_available():
                torch_mod.cuda.empty_cache()
        except Exception:
            pass

    def health_check(self) -> SRMBackendHealth:
        detail = "Initialized and ready."
        available = self._initialized and self._model is not None
        if not available:
            if self._loader_override is not None:
                detail = "Test-double loader configured (not yet initialized)."
                available = True
            else:
                try:
                    self._import_optional_runtime()
                    exists = Path(self.srm_config.model_name).exists() if self.srm_config.local_files_only else True
                    available = exists
                    detail = "Dependencies present; checkpoint staged." if exists else f"Checkpoint '{self.srm_config.model_name}' missing locally."
                except ProviderError as exc:
                    self._last_error = str(exc)
                    detail = str(exc)
        return SRMBackendHealth(
            backend_name=self.backend_name,
            model_name=self.srm_config.model_name,
            initialized=self._initialized,
            available=available,
            is_real_model=True,
            device=self._device_used,
            inference_mode=self.srm_config.inference_mode,
            detail=detail,
            last_error=self._last_error,
        )

    def _format_prompt(self, request: SRMRequest) -> str:
        prompt = _build_srm_prompt(request, inference_mode=self.srm_config.inference_mode)
        if hasattr(self._tokenizer, "apply_chat_template"):
            try:
                return str(
                    self._tokenizer.apply_chat_template(
                        [{"role": "user", "content": prompt}],
                        tokenize=False,
                        add_generation_prompt=True,
                    )
                )
            except Exception:
                return prompt
        return prompt

    def _generate_raw(self, prompt_text: str) -> str:
        if self._model is None or self._tokenizer is None:
            raise ModelError("SRM model not initialized.")
        encoded = self._tokenizer(prompt_text, return_tensors="pt")
        input_ids = encoded["input_ids"] if isinstance(encoded, dict) else getattr(encoded, "input_ids", encoded)
        prompt_len = len(input_ids[0]) if hasattr(input_ids, "__len__") else 0

        gen_kwargs: dict[str, Any] = {
            "max_new_tokens": self.srm_config.max_new_tokens,
            "do_sample": self.srm_config.temperature > 0.0,
            "pad_token_id": getattr(self._tokenizer, "pad_token_id", None),
        }
        if self.srm_config.temperature > 0.0:
            gen_kwargs["temperature"] = self.srm_config.temperature

        try:
            outputs = self._model.generate(**(encoded if isinstance(encoded, dict) else {"input_ids": input_ids}), **gen_kwargs)
        except MemoryError as exc:
            self.shutdown()
            raise ModelError(f"SRM OOM during generation: {exc}") from exc
        except RuntimeError as exc:
            if "out of memory" in str(exc).lower():
                self.shutdown()
                raise ModelError(f"SRM GPU/CPU OOM during generation: {exc}") from exc
            raise ModelError(f"SRM generation error: {exc}") from exc

        seq = outputs[0]
        new_tokens = seq[prompt_len:] if prompt_len and hasattr(seq, "__getitem__") else seq
        return str(self._tokenizer.decode(new_tokens, skip_special_tokens=True))

    def invoke(self, request: SRMRequest) -> SRMResponse:
        """Execute bounded-timeout inference and validate HalluGuard 5-class structured schema."""
        if not self._initialized or self._model is None:
            self.initialize()

        prompt_text = self._format_prompt(request)
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(self._generate_raw, prompt_text)
            try:
                raw_text = fut.result(timeout=self.srm_config.timeout_seconds)
            except FuturesTimeoutError as exc:
                self._last_error = f"hf_local SRM timed out after {self.srm_config.timeout_seconds}s"
                raise TimeoutError(self._last_error) from exc

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return _parse_srm_json(
            raw_text,
            backend_name=self.backend_name,
            model_name=self.srm_config.model_name,
            latency_ms=latency_ms,
            inference_mode=self.srm_config.inference_mode,
            evidence_passages=request.evidence_passages,
            enforce_citation_grounding=self.srm_config.enforce_citation_grounding,
            model_config_snapshot={
                "backend": self.backend_name,
                "model_name": self.srm_config.model_name,
                "adapter_path": self.srm_config.model_adapter_path,
                "device": self._device_used,
                "inference_mode": self.srm_config.inference_mode,
                "max_new_tokens": self.srm_config.max_new_tokens,
                "confidence_calibrated": False,
            },
        )

    def invoke_batch(self, requests: Sequence[SRMRequest], *, max_batch_size: int | None = None) -> list[SRMResponse]:
        bs = max_batch_size or self.srm_config.batch_size
        return super().invoke_batch(requests, max_batch_size=bs)


__all__ = ["HuggingFaceLocalSRMBackend"]
