"""Multi-Signal Detection (G2) for TrustRAG."""

from .msd import MultiSignalDetector
from .signals import (
    evaluate_consensus_deviation_signals,
    evaluate_embedding_norm_signal,
    evaluate_freq_density_heuristic,
    evaluate_instruction_content_signal,
    evaluate_perplexity_signal,
    evaluate_provenance_signal,
    evaluate_query_match_signal,
)

__all__ = [
    "MultiSignalDetector",
    "evaluate_perplexity_signal",
    "evaluate_embedding_norm_signal",
    "evaluate_query_match_signal",
    "evaluate_instruction_content_signal",
    "evaluate_consensus_deviation_signals",
    "evaluate_provenance_signal",
    "evaluate_freq_density_heuristic",
]
