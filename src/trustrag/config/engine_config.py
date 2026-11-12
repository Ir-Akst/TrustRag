"""Pydantic configuration models for TrustRAG Phase 03 defense engine components.

Defines configurable thresholds, weights, missing-signal policy, reference distributions,
provenance priors, and optional FilterRAG / backend settings for:
- G1: GuardrailsConfig
- Retrieval & G2: RetrievalConfig, MSDConfig
- Generation: GenerationConfig
- G3: VerificationConfig
- SRM: SRMConfig
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, ValidationError as PydanticValidationError, model_validator

from trustrag.exceptions import ConfigurationError


class _ValidatedConfigModel(BaseModel):
    """Base config model surfacing validation failures as project ConfigurationError."""

    def __init__(self, **data: Any) -> None:
        try:
            super().__init__(**data)
        except PydanticValidationError as exc:
            raise ConfigurationError(str(exc)) from exc


class GuardrailsConfig(_ValidatedConfigModel):
    """Configuration for G1 Input Guardrail."""

    enabled: bool = Field(default=True, description="Whether G1 input guardrail is active")
    max_input_length: int = Field(default=4096, ge=1, description="Maximum allowed input characters")
    flag_threshold: float = Field(default=0.35, ge=0.0, le=1.0, description="Risk score threshold to FLAG query")
    block_threshold: float = Field(default=0.70, ge=0.0, le=1.0, description="Risk score threshold to BLOCK query")
    block_on_empty: bool = Field(default=True, description="Block empty or whitespace-only queries")
    strip_zero_width_for_analysis: bool = Field(
        default=True,
        description="Analyze obfuscated zero-width characters while keeping original input intact",
    )
    enable_paraphrasing: bool = Field(
        default=False,
        description="Enable controlled G1 query paraphrasing with strict semantic constraint verification",
    )
    paraphrase_backend: Literal["disabled", "deterministic", "callable"] = Field(
        default="disabled",
        description="Paraphrasing provider mode for G1 query expansion",
    )
    min_paraphrase_similarity: float = Field(
        default=0.30,
        ge=0.0,
        le=1.0,
        description="Minimum lexical/TF-IDF similarity required to accept a G1 paraphrase",
    )

    @model_validator(mode="after")
    def validate_thresholds(self) -> "GuardrailsConfig":
        if self.flag_threshold > self.block_threshold:
            raise ConfigurationError(
                f"flag_threshold ({self.flag_threshold}) cannot exceed block_threshold ({self.block_threshold})"
            )
        return self


class RetrievalConfig(_ValidatedConfigModel):
    """Configuration for trust-aware retrieval and floor(K/2) removal-cap enforcement.

    Note: ``candidate_multiplier`` expands the scored candidate pool (``top_k * candidate_multiplier``)
    so clean backup documents can be promoted above down-ranked/removed items, while the removal-cap
    budget ``K = min(top_k, len(candidates))`` remains strictly bounded by the requested ``top_k``.
    """

    top_k: int = Field(default=5, ge=1, description="Number of final documents returned")
    candidate_multiplier: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Multiplier for oversampling candidates before G2 ranking (does not inflate floor(K/2) cap)",
    )
    min_relevance_score: float = Field(
        default=0.01,
        ge=0.0,
        le=1.0,
        description="Minimum lexical/TF-IDF relevance score to include a candidate",
    )
    filtering_mode: Literal["remove_with_cap", "downrank_only", "disabled"] = Field(
        default="remove_with_cap",
        description="How G2-flagged poisoned documents are handled in retrieval",
    )
    filter_low_trust: bool = Field(
        default=True,
        description="Backwards-compatible boolean toggle; False forces downrank_only behavior",
    )
    enforce_removal_cap: bool = Field(
        default=True,
        description="Enforce TrustRAG floor(K * removal_cap_ratio) <= floor(K/2) removal cap",
    )
    removal_cap_ratio: float = Field(
        default=0.5,
        gt=0.0,
        le=0.5,
        description="Maximum fraction of candidate set of size K removable (default 0.5 -> floor(K/2))",
    )
    trust_weight: float = Field(
        default=0.45,
        ge=0.0,
        le=1.0,
        description="Weight applied to G2 trust score during trust-aware ranking",
    )

    @model_validator(mode="after")
    def validate_retrieval(self) -> "RetrievalConfig":
        if not self.filter_low_trust and self.filtering_mode == "remove_with_cap":
            object.__setattr__(self, "filtering_mode", "downrank_only")
        if self.removal_cap_ratio > 0.5:
            raise ConfigurationError(
                f"removal_cap_ratio ({self.removal_cap_ratio}) cannot exceed TrustRAG limit 0.5 (floor(K/2))"
            )
        return self


class MSDConfig(_ValidatedConfigModel):
    """Configuration for G2 Multi-Signal Detector (MSD)."""

    enabled: bool = Field(default=True, description="Whether G2 Multi-Signal Detector is active")

    # Sigmoid scoring weights & bias: trust_score(d) = sigmoid(w · f(d) + b)
    weight_perplexity: float = Field(default=0.8, ge=0.0, description="Weight for F1 perplexity anomaly")
    weight_embedding_norm: float = Field(default=0.8, ge=0.0, description="Weight for F2 embedding-norm anomaly")
    weight_query_match: float = Field(default=1.2, ge=0.0, description="Weight for F3 query semantic relevance")
    weight_instruction_content: float = Field(default=2.0, ge=0.0, description="Weight for F4 suspicious instruction content")
    weight_consensus_deviation: float = Field(default=1.0, ge=0.0, description="Weight for F5 consensus deviation")
    weight_provenance: float = Field(default=0.8, ge=0.0, description="Weight for F6 provenance prior")
    bias: float = Field(default=0.0, description="Bias term b in sigmoid(w · f(d) + b)")

    # Document classification thresholds (CLEAN / POISONED / UNCERTAIN)
    trust_threshold: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Minimum trust score required for CLEAN classification",
    )
    poison_threshold: float = Field(
        default=0.38,
        ge=0.0,
        le=1.0,
        description="Trust score below which document is classified POISONED",
    )
    instruction_poison_threshold: float = Field(
        default=0.55,
        ge=0.0,
        le=1.0,
        description="F4 adversarial instruction risk threshold triggering POISONED decision",
    )
    instruction_flag_threshold: float = Field(
        default=0.30,
        ge=0.0,
        le=1.0,
        description="F4 medium instruction risk threshold triggering UNCERTAIN review",
    )

    # Missing-signal policy (mathematically justified non-amplifying policies)
    missing_signal_policy: Literal["coverage_attenuated", "zero_log_odds", "strict_uncertain_on_missing"] = Field(
        default="coverage_attenuated",
        description=(
            "Policy when one or more signals are unavailable: 'coverage_attenuated' scales observed log-odds "
            "by available weight ratio r_A <= 1.0 (shrinking toward prior instead of amplifying); "
            "'zero_log_odds' contributes 0 log-odds for missing signals without scaling weights; "
            "'strict_uncertain_on_missing' attenuates confidence and forces UNCERTAIN if any signal is missing."
        ),
    )
    min_available_signals: int = Field(
        default=2,
        ge=1,
        le=6,
        description="Minimum number of valid signals required before avoiding automatic UNCERTAIN",
    )
    min_available_weight_ratio: float = Field(
        default=0.25,
        gt=0.0,
        le=1.0,
        description="Minimum fraction of total configured signal weight required to avoid UNCERTAIN",
    )

    # Optional backends & reference distributions (no invented measurements)
    perplexity_backend: Literal["disabled", "callable"] = Field(
        default="disabled",
        description="Perplexity scorer backend; 'disabled' marks F1 unavailable without fabricating scores",
    )
    perplexity_reference_mean: float = Field(default=25.0, gt=0.0)
    perplexity_reference_std: float = Field(default=15.0, gt=0.0)
    perplexity_z_threshold: float = Field(default=2.0, gt=0.0)

    embedding_backend: Literal["tfidf_raw", "callable", "disabled"] = Field(
        default="tfidf_raw",
        description="Embedding backend used for F2 norm and F3/F5 cosine representations",
    )
    embedding_norm_reference_policy: Literal["require_configured", "allow_empirical_fallback"] = Field(
        default="require_configured",
        description=(
            "Reference baseline policy for F2 embedding_norm: 'require_configured' keeps F2 UNAVAILABLE "
            "unless clean-reference mean/std are explicitly configured (never treating batch-local statistics as clean reference); "
            "'allow_empirical_fallback' permits opt-in batch statistics with symmetric/duplicate ambiguity guards."
        ),
    )
    embedding_norm_reference_mean: Optional[float] = Field(default=None, gt=0.0)
    embedding_norm_reference_std: Optional[float] = Field(default=None, gt=0.0)
    embedding_norm_z_threshold: float = Field(default=2.0, gt=0.0)

    # Configurable source reliability priors (basis must come from explicit user/corpus policy)
    provenance_priors: Dict[str, float] = Field(
        default_factory=dict,
        description="Explicit configurable priors mapped by source_dataset/provenance string (values in [0,1])",
    )

    # Optional FilterRAG supplementary heuristic (excluded from core w · f(d) + b)
    enable_freq_density: bool = Field(
        default=False,
        description="Enable FilterRAG-inspired Freq-Density supplementary heuristic when answer interface is present",
    )

    @model_validator(mode="before")
    @classmethod
    def _handle_legacy_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "clean_threshold" in d and "trust_threshold" not in d:
                d["trust_threshold"] = d.pop("clean_threshold")
            if "filter_threshold" in d and "poison_threshold" not in d:
                d["poison_threshold"] = d.pop("filter_threshold")
            if "instruction_block_threshold" in d and "instruction_poison_threshold" not in d:
                d["instruction_poison_threshold"] = d.pop("instruction_block_threshold")
            return d
        return data

    @model_validator(mode="after")
    def validate_msd_config(self) -> "MSDConfig":
        if self.poison_threshold > self.trust_threshold:
            raise ConfigurationError(
                f"poison_threshold ({self.poison_threshold}) cannot exceed trust_threshold ({self.trust_threshold})"
            )
        if self.instruction_flag_threshold > self.instruction_poison_threshold:
            raise ConfigurationError(
                f"instruction_flag_threshold ({self.instruction_flag_threshold}) cannot exceed "
                f"instruction_poison_threshold ({self.instruction_poison_threshold})"
            )
        total_w = (
            self.weight_perplexity
            + self.weight_embedding_norm
            + self.weight_query_match
            + self.weight_instruction_content
            + self.weight_consensus_deviation
            + self.weight_provenance
        )
        if total_w <= 0.0:
            raise ConfigurationError("At least one MSD signal weight must be strictly positive.")
        if (self.embedding_norm_reference_mean is None) != (self.embedding_norm_reference_std is None):
            raise ConfigurationError(
                "embedding_norm_reference_mean and embedding_norm_reference_std must be provided together."
            )
        for src, prior in self.provenance_priors.items():
            if not (0.0 <= float(prior) <= 1.0):
                raise ConfigurationError(
                    f"Provenance prior for '{src}' must be in [0.0, 1.0], got {prior}."
                )
        return self

    @property
    def clean_threshold(self) -> float:
        return self.trust_threshold

    @property
    def filter_threshold(self) -> float:
        return self.poison_threshold


class GenerationConfig(_ValidatedConfigModel):
    """Configuration for RAG answer generation."""

    mode: Literal["extractive", "llm_with_fallback"] = Field(
        default="extractive",
        description="Generation mode; extractive uses deterministic evidence synthesis",
    )
    max_context_docs: int = Field(default=3, ge=1, description="Maximum trusted docs used to construct answer")
    max_sentences_per_doc: int = Field(default=2, ge=1, description="Max evidence sentences extracted per doc")
    abstain_on_empty_context: bool = Field(
        default=True,
        description="Return explicit abstention answer when no trusted evidence survives G2",
    )


class VerificationConfig(_ValidatedConfigModel):
    """Configuration for G3 Output Evidence Verification."""

    enabled: bool = Field(default=True, description="Whether G3 output evidence verification is active")
    min_support_coverage: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum factual predicate coverage required for SUPPORTS",
    )
    min_relevance_for_check: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Minimum similarity required before an evidence span is evaluated for support/conflict",
    )
    strict_numeric_matching: bool = Field(
        default=True,
        description="Require numbers/units in a claim to be verified in the supporting span",
    )
    strict_negation_check: bool = Field(
        default=True,
        description="Mark opposite polarity assertions on matched topics as CONTRADICTS",
    )


class SRMConfig(_ValidatedConfigModel):
    """Configuration for HalluGuard-inspired Small Reasoning Model (SRM) integration."""

    enabled: bool = Field(default=True, description="Whether SRM verification stage is invoked")
    backend: Literal["disabled", "local_ollama", "openai_compatible", "hf_local", "custom"] = Field(
        default="disabled",
        description="SRM backend type; 'disabled' activates deterministic fallback directly",
    )
    model_name: str = Field(
        default="halluguard-srm-fallback",
        description="Configured model identifier (e.g., qwen2.5:1.5b, local HF path, or API model ID)",
    )
    model_adapter_path: Optional[str] = Field(
        default=None,
        description="Optional local LoRA/PEFT adapter directory for hf_local backend",
    )
    endpoint_url: Optional[str] = Field(
        default=None,
        description="Optional HTTP endpoint URL overriding provider defaults",
    )
    inference_mode: Literal["think", "non_think"] = Field(
        default="non_think",
        description="Reasoning output mode ('think' enables <think> trace extraction prior to JSON)",
    )
    device: Literal["auto", "cpu", "cuda"] = Field(
        default="auto",
        description="Execution device preference for optional local model backends",
    )
    max_new_tokens: int = Field(
        default=512,
        ge=32,
        le=4096,
        description="Maximum tokens generated per SRM reasoning request",
    )
    batch_size: int = Field(
        default=4,
        ge=1,
        le=64,
        description="Maximum controlled batch size for batch SRM inference",
    )
    local_files_only: bool = Field(
        default=True,
        description="Disallow automatic remote weight downloads; require locally staged checkpoints",
    )
    trust_remote_code: bool = Field(
        default=False,
        description="Explicit opt-in required before executing custom tokenizer/model code",
    )
    enforce_citation_grounding: bool = Field(
        default=True,
        description="Validate SRM cited evidence spans against candidate passage text",
    )
    timeout_seconds: float = Field(default=5.0, gt=0.0, description="Request timeout in seconds")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Sampling temperature")
    fallback_on_error: bool = Field(
        default=True,
        description="Use deterministic evidence-based fallback when SRM backend is unavailable or times out",
    )


__all__ = [
    "GuardrailsConfig",
    "RetrievalConfig",
    "MSDConfig",
    "GenerationConfig",
    "VerificationConfig",
    "SRMConfig",
]
