"""Benchmark construction package for TrustRAG.

Phase 02 Benchmark Construction:
- Benchmark A: Clean RAG
- Benchmark B: Knowledge Poisoning
- Benchmark C: Hallucination Detection
- Benchmark D: Adversarial Robustness
"""

from .builder import BENCHMARK_CATEGORIES, BenchmarkBuilder
from .security_generator import PROVENANCE_STRING, generate_security_benchmark_pairs

__all__ = [
    "BENCHMARK_CATEGORIES",
    "BenchmarkBuilder",
    "PROVENANCE_STRING",
    "generate_security_benchmark_pairs",
]

