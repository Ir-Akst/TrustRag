"""Trust-aware document retrieval integrating TF-IDF ranking, G2 MSD, and floor(K/2) removal cap."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple, Union

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from trustrag.config.engine_config import MSDConfig, RetrievalConfig
from trustrag.data.storage import DatasetStorage
from trustrag.data.taxonomy import DocumentSecurityLabel
from trustrag.detection.msd import MultiSignalDetector
from trustrag.engine.schemas import (
    EvidenceDocument,
    G2DocumentAssessment,
    RetrievalResult,
)
from trustrag.engine.text_utils import compute_lexical_overlap
from trustrag.exceptions import RetrievalError
from trustrag.utils.logging import get_logger

LOGGER = get_logger(__name__)


class TrustAwareRetriever:
    """TF-IDF + lexical hybrid retriever tightly integrated with 6-signal G2 MSD."""

    def __init__(
        self,
        documents: Optional[Sequence[Any]] = None,
        *,
        retrieval_config: Optional[RetrievalConfig] = None,
        msd_config: Optional[MSDConfig] = None,
        detector: Optional[MultiSignalDetector] = None,
    ) -> None:
        self.config = retrieval_config or RetrievalConfig()
        self.detector = detector or MultiSignalDetector(config=msd_config)
        self._documents: List[EvidenceDocument] = []
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._raw_vectorizer: Optional[TfidfVectorizer] = None
        self._doc_matrix: Any = None
        self._raw_doc_matrix: Any = None

        if documents:
            self.index_documents(documents)

    @classmethod
    def from_jsonl(
        cls,
        file_path: Union[str, Path],
        *,
        limit: Optional[int] = None,
        retrieval_config: Optional[RetrievalConfig] = None,
        msd_config: Optional[MSDConfig] = None,
    ) -> "TrustAwareRetriever":
        """Build an indexed TrustAwareRetriever directly from a local TrustRAG JSONL file."""
        path = Path(file_path)
        if not path.is_file():
            raise RetrievalError(f"Corpus JSONL file does not exist: {path}")
        raw_records = list(DatasetStorage.load_jsonl(path, limit=limit))
        return cls(
            raw_records,
            retrieval_config=retrieval_config,
            msd_config=msd_config,
        )

    @property
    def document_count(self) -> int:
        return len(self._documents)

    def save(self, path: Union[str, Path]) -> None:
        """Persist indexed retriever state to disk."""
        import pickle
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "documents": [d.model_dump() for d in self._documents],
            "vectorizer": self._vectorizer,
            "raw_vectorizer": self._raw_vectorizer,
            "doc_matrix": self._doc_matrix,
            "raw_doc_matrix": self._raw_doc_matrix,
        }
        with open(p, "wb") as f:
            pickle.dump(state, f)

    @classmethod
    def load(
        cls,
        path: Union[str, Path],
        *,
        retrieval_config: Optional[RetrievalConfig] = None,
        msd_config: Optional[MSDConfig] = None,
        detector: Optional[MultiSignalDetector] = None,
    ) -> "TrustAwareRetriever":
        """Load a persisted retriever index from disk."""
        import pickle
        p = Path(path)
        if not p.is_file():
            raise RetrievalError(f"Persisted index file not found: {p}")
        with open(p, "rb") as f:
            state = pickle.load(f)
        retriever = cls(
            retrieval_config=retrieval_config,
            msd_config=msd_config,
            detector=detector,
        )
        retriever._documents = [EvidenceDocument.model_validate(d) for d in state["documents"]]
        retriever._vectorizer = state.get("vectorizer")
        retriever._raw_vectorizer = state.get("raw_vectorizer")
        retriever._doc_matrix = state.get("doc_matrix")
        retriever._raw_doc_matrix = state.get("raw_doc_matrix")
        return retriever

    def index_documents(self, records: Sequence[Any], deduplicate_by_id: bool = False) -> int:
        """Adapt and index records while keeping original metadata intact."""
        adapted: List[EvidenceDocument] = []
        seen_ids: set[str] = set()
        for idx, rec in enumerate(records):
            doc = EvidenceDocument.from_record(rec, idx=idx)
            if doc is None or not doc.text.strip():
                continue
            if doc.doc_id in seen_ids:
                if deduplicate_by_id:
                    continue
                doc.doc_id = f"{doc.doc_id}#{idx}"
            seen_ids.add(doc.doc_id)
            adapted.append(doc)

        self._documents = adapted
        self._vectorizer = None
        self._raw_vectorizer = None
        self._doc_matrix = None
        self._raw_doc_matrix = None

        if not self._documents:
            return 0

        texts = [d.text for d in self._documents]
        try:
            self._vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                ngram_range=(1, 2),
                token_pattern=r"(?u)\b[a-zA-Z0-9][a-zA-Z0-9\-]*\b",
            )
            self._doc_matrix = self._vectorizer.fit_transform(texts)

            # Unnormalized TF-IDF matrix preserves real vector L2 norms for F2 anomaly analysis
            self._raw_vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                ngram_range=(1, 2),
                norm=None,
                token_pattern=r"(?u)\b[a-zA-Z0-9][a-zA-Z0-9\-]*\b",
            )
            self._raw_doc_matrix = self._raw_vectorizer.fit_transform(texts)
        except ValueError:
            self._vectorizer = None
            self._raw_vectorizer = None
            self._doc_matrix = None
            self._raw_doc_matrix = None

        LOGGER.info(
            "Indexed documents for trust-aware retrieval",
            extra={"indexed_count": len(self._documents)},
        )
        return len(self._documents)

    def retrieve_candidates(
        self,
        query: str,
        top_n: Optional[int] = None,
    ) -> List[Tuple[EvidenceDocument, float]]:
        """Retrieve top-N raw candidate documents sorted deterministically by relevance."""
        return [(doc, score) for _, doc, score in self._retrieve_indexed_candidates(query, top_n=top_n)]

    def _retrieve_indexed_candidates(
        self,
        query: str,
        top_n: Optional[int] = None,
    ) -> List[Tuple[int, EvidenceDocument, float]]:
        if not self._documents or not query.strip():
            return []

        n_limit = top_n or (self.config.top_k * self.config.candidate_multiplier)

        if self._vectorizer is not None and self._doc_matrix is not None:
            q_vec = self._vectorizer.transform([query])
            sims = cosine_similarity(q_vec, self._doc_matrix).flatten()
        else:
            sims = np.zeros(len(self._documents), dtype=float)

        scored: List[Tuple[int, EvidenceDocument, float]] = []
        for idx, doc in enumerate(self._documents):
            tfidf_sim = float(np.clip(sims[idx], 0.0, 1.0))
            lex_sim = compute_lexical_overlap(query, doc.text)
            rel = round(0.75 * tfidf_sim + 0.25 * lex_sim, 4)
            if rel >= self.config.min_relevance_score:
                scored.append((idx, doc, rel))

        scored.sort(key=lambda item: (-item[2], item[0], item[1].doc_id))
        return scored[:n_limit]

    def retrieve_trusted(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> RetrievalResult:
        """Retrieve candidates, run G2 MSD, enforce floor(K/2) removal cap, and return ranked evidence."""
        k = top_k or self.config.top_k
        candidate_n = k * self.config.candidate_multiplier
        indexed_candidates = self._retrieve_indexed_candidates(query, top_n=candidate_n)

        if not indexed_candidates:
            return RetrievalResult(
                query=query,
                total_indexed=len(self._documents),
                requested_top_k=k,
                candidate_count=0,
                removal_cap_k=0,
                removal_cap_limit=0,
                removal_cap_applied=False,
                filtering_mode=self.config.filtering_mode,
                trusted_documents=[],
                removed_documents=[],
                filtered_documents=[],
                assessments=[],
            )

        candidate_indices = [idx for idx, _, _ in indexed_candidates]
        candidate_docs = [doc for _, doc, _ in indexed_candidates]
        rel_scores = [rel for _, _, rel in indexed_candidates]
        orig_ranks = list(range(1, len(candidate_docs) + 1))

        # Supply real vector representations from existing index when configured
        doc_vecs: Optional[List[Optional[np.ndarray]]] = None
        if self.detector.config.embedding_backend == "tfidf_raw" and self._raw_doc_matrix is not None:
            doc_vecs = [self._raw_doc_matrix[corpus_idx].toarray().ravel() for corpus_idx in candidate_indices]

        assessments = self.detector.assess_candidates(
            query=query,
            candidates=candidate_docs,
            relevance_scores=rel_scores,
            doc_embeddings=doc_vecs,
            original_ranks=orig_ranks,
            trust_weight=self.config.trust_weight,
        )

        assessment_by_id = {a.document_id: a for a in assessments}
        doc_by_id = {d.doc_id: d for d in candidate_docs}

        candidate_count = len(candidate_docs)
        # Explicit K policy: removal budget is bounded by requested final top_k
        # (and available retrieved candidates when fewer than top_k match), never silently
        # multiplied by candidate_multiplier.
        removal_cap_k = min(k, candidate_count)
        mode = self.config.filtering_mode
        if not self.config.filter_low_trust and mode == "remove_with_cap":
            mode = "downrank_only"

        if mode == "remove_with_cap":
            removal_cap = (
                math.floor(removal_cap_k * self.config.removal_cap_ratio)
                if self.config.enforce_removal_cap
                else candidate_count
            )
        else:
            removal_cap = 0
        removed_ids: set[str] = set()
        removal_cap_applied = False

        if mode == "remove_with_cap":
            poisoned_assessments = [
                a for a in assessments if a.decision == DocumentSecurityLabel.POISONED
            ]
            # Remove highest-risk / lowest-trust POISONED documents up to floor(K / 2)
            poisoned_assessments.sort(
                key=lambda a: (a.trust_score, -a.instruction_risk_score, a.original_rank or 0)
            )
            if len(poisoned_assessments) > removal_cap:
                removal_cap_applied = True
            for a in poisoned_assessments[:removal_cap]:
                a.removed_by_cap = True
                removed_ids.add(a.document_id)

        surviving_pairs: List[Tuple[EvidenceDocument, G2DocumentAssessment]] = []
        removed_docs: List[EvidenceDocument] = []

        for a in assessments:
            doc = doc_by_id[a.document_id]
            if a.document_id in removed_ids:
                removed_docs.append(doc)
            else:
                if mode == "disabled":
                    a.adjusted_retrieval_score = a.original_retrieval_score
                surviving_pairs.append((doc, a))

        # Sort surviving documents deterministically, preserving original_rank on ties
        if mode == "disabled":
            surviving_pairs.sort(key=lambda pair: (pair[1].original_rank or 0))
        else:
            surviving_pairs.sort(
                key=lambda pair: (
                    -(pair[1].adjusted_retrieval_score or 0.0),
                    pair[1].original_rank or 0,
                    pair[0].doc_id,
                )
            )

        for rank_idx, (_, a) in enumerate(surviving_pairs, start=1):
            a.adjusted_rank = rank_idx

        selected_docs = [pair[0] for pair in surviving_pairs[:k]]
        ordered_assessments = [pair[1] for pair in surviving_pairs] + [
            assessment_by_id[d.doc_id] for d in removed_docs
        ]

        return RetrievalResult(
            query=query,
            total_indexed=len(self._documents),
            requested_top_k=k,
            candidate_count=candidate_count,
            removal_cap_k=removal_cap_k,
            removal_cap_limit=removal_cap,
            removal_cap_applied=removal_cap_applied,
            filtering_mode=mode,
            trusted_documents=selected_docs,
            removed_documents=removed_docs,
            filtered_documents=removed_docs,
            assessments=ordered_assessments,
        )


__all__ = ["TrustAwareRetriever"]
