"""Evidence-grounded answer generator for TrustRAG Phase 03."""

from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Tuple

from trustrag.config.engine_config import GenerationConfig
from trustrag.engine.schemas import EvidenceDocument, GeneratedAnswer
from trustrag.engine.text_utils import compute_lexical_overlap, compute_tfidf_similarities, split_sentences
from trustrag.utils.logging import get_logger

LOGGER = get_logger(__name__)


class AnswerGenerator:
    """Deterministic evidence-grounded generator with optional LLM hook support."""

    def __init__(
        self,
        config: Optional[GenerationConfig] = None,
        llm_callable: Optional[Callable[[str, Sequence[EvidenceDocument]], str]] = None,
    ) -> None:
        self.config = config or GenerationConfig()
        self.llm_callable = llm_callable

    def generate(
        self,
        query: str,
        trusted_documents: Sequence[EvidenceDocument],
        *,
        answer_override: Optional[str] = None,
    ) -> GeneratedAnswer:
        """Produce a grounded answer from trusted evidence documents (or abstain if empty)."""
        if answer_override is not None:
            return GeneratedAnswer(
                answer_text=answer_override.strip(),
                abstained=False,
                cited_doc_ids=[d.doc_id for d in trusted_documents[: self.config.max_context_docs]],
                generator_mode="override",
            )

        if not trusted_documents:
            if self.config.abstain_on_empty_context:
                return GeneratedAnswer(
                    answer_text="Insufficient trusted evidence is available to answer this query reliably.",
                    abstained=True,
                    abstention_reason="NO_TRUSTED_EVIDENCE",
                    cited_doc_ids=[],
                    generator_mode=self.config.mode,
                )
            return GeneratedAnswer(
                answer_text="",
                abstained=True,
                abstention_reason="EMPTY_CONTEXT",
                cited_doc_ids=[],
                generator_mode=self.config.mode,
            )

        context_docs = list(trusted_documents[: self.config.max_context_docs])

        if self.config.mode == "llm_with_fallback" and self.llm_callable is not None:
            try:
                raw_out = self.llm_callable(query, context_docs).strip()
                if raw_out:
                    return GeneratedAnswer(
                        answer_text=raw_out,
                        abstained=False,
                        cited_doc_ids=[d.doc_id for d in context_docs],
                        generator_mode="llm",
                    )
            except Exception as exc:
                LOGGER.warning(
                    "LLM generator failed; falling back to extractive synthesis",
                    extra={"error": str(exc)},
                )

        # Deterministic extractive synthesis grounded directly in trusted evidence sentences
        selected_parts: List[str] = []
        cited_ids: List[str] = []
        seen_sentences: set[str] = set()

        for doc in context_docs:
            sents = split_sentences(doc.text)
            if not sents:
                continue
            sims = compute_tfidf_similarities(query, sents)
            scored_sents: List[Tuple[float, int, str]] = []
            for idx, (sent, sim) in enumerate(zip(sents, sims)):
                lex = compute_lexical_overlap(query, sent)
                score = 0.65 * sim + 0.35 * lex
                scored_sents.append((score, idx, sent))

            scored_sents.sort(key=lambda item: (-item[0], item[1]))
            chosen = 0
            for _, _, sent in scored_sents:
                norm_s = sent.lower().strip()
                if norm_s in seen_sentences:
                    continue
                seen_sentences.add(norm_s)
                selected_parts.append(f"{sent} [{doc.doc_id}]")
                if doc.doc_id not in cited_ids:
                    cited_ids.append(doc.doc_id)
                chosen += 1
                if chosen >= self.config.max_sentences_per_doc:
                    break

        if not selected_parts:
            return GeneratedAnswer(
                answer_text="Insufficient verifiable claims found in the trusted evidence.",
                abstained=True,
                abstention_reason="NO_EXTRACTABLE_SENTENCES",
                cited_doc_ids=[],
                generator_mode="extractive",
            )

        return GeneratedAnswer(
            answer_text=" ".join(selected_parts),
            abstained=False,
            cited_doc_ids=cited_ids,
            generator_mode="extractive_fallback" if self.config.mode == "llm_with_fallback" else "extractive",
        )


__all__ = ["AnswerGenerator"]

