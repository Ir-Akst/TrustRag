"""Dataset loaders for TrustRAG Phase 01.

Provides adapters for:
- RAG QA: Natural Questions, HotpotQA, MS MARCO, SQuAD, BoolQ
- Hallucination / Claim Verification: HaluEval, RAGTruth, LLM-AggreFact, WiCE, ExpertQA
- Security / Poisoning: RSB, Custom Security
- Training Corpus: FineWeb
"""

from .boolq import BoolQAdapter
from .custom_security import CustomSecurityAdapter
from .expertqa import ExpertQAAdapter
from .fineweb import FineWebAdapter
from .halueval import HaluEvalAdapter
from .hotpotqa import HotpotQAAdapter
from .llm_aggrefact import LLMAggreFactAdapter
from .ms_marco import MSMarcoAdapter
from .natural_questions import NaturalQuestionsAdapter
from .ragtruth import RAGTruthAdapter
from .rsb import RSBAdapter
from .squad import SQuADAdapter
from .wice import WiCEAdapter

__all__ = [
    "NaturalQuestionsAdapter",
    "HotpotQAAdapter",
    "MSMarcoAdapter",
    "SQuADAdapter",
    "BoolQAdapter",
    "HaluEvalAdapter",
    "RAGTruthAdapter",
    "LLMAggreFactAdapter",
    "WiCEAdapter",
    "ExpertQAAdapter",
    "RSBAdapter",
    "CustomSecurityAdapter",
    "FineWebAdapter",
]

