"""Controlled G1 Query Paraphrasing & Semantic Constraint Preservation (Phase 08 Step 04).

Guarantees the original query stays authoritative while verifying any generated
paraphrase preserves numeric values, negation, temporal markers, named entities,
conditional clauses, semantic similarity, Unicode safety, and threat screening.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field

from trustrag.data.preprocessing.cleaning import clean_text, is_empty_text
from trustrag.engine.text_utils import (
    compute_lexical_overlap,
    compute_tfidf_similarities,
    count_fullwidth_ascii_confusables,
    detect_obfuscation,
    extract_numbers_and_units,
    fold_mixed_script_confusables,
    has_strict_negation,
    match_threat_patterns,
)

_YEAR_OR_DATE_RE = re.compile(
    r"\b(?:1[5-9]\d{2}|20\d{2}|jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|before|after|since|until|during|currently|today)\b",
    re.IGNORECASE,
)
_CONDITIONAL_MARKER_RE = re.compile(
    r"\b(?:if|unless|only\s+(?:if|when|after)|except|without|provided|assuming)\b",
    re.IGNORECASE,
)
_ENTITY_RE = re.compile(r"\b(?:[A-Z][a-zA-Z0-9\-]{1,}|[A-Z0-9]{2,}(?:-\d+)?)\b")
_LEADING_NON_ENTITY = frozenset({"what", "which", "when", "where", "who", "whom", "why", "how", "is", "are", "was", "were", "can", "could", "did", "do", "does", "should", "would", "may", "will", "the", "a", "an", "explain", "compare", "list", "describe", "tell"})

_SAFE_SYNONYM_PHRASES: tuple[tuple[str, str], ...] = (
    ("what is the maximum safe daily dose of", "what daily dose limit applies for"),
    ("what is the time complexity of", "what is the big-o complexity of"),
    ("is it safe to", "can a person safely"),
    ("how do i", "what steps allow me to"),
    ("how do agents", "how should agents"),
    ("who is the president of", "who serves as president of"),
    ("what is the capital of", "which city serves as the capital of"),
    ("vulnerable to", "susceptible to"),
)


@dataclass
class ParaphraseValidationResult:
    """Structured outcome of generating and validating a query paraphrase."""

    accepted: bool
    original_query: str
    candidate_paraphrase: str | None
    validated_paraphrase: str | None
    rejection_reasons: list[str] = field(default_factory=list)
    semantic_similarity: float = 0.0


def deterministic_safe_paraphrase(query: str) -> str:
    """Rule-based deterministic paraphraser preserving numbers, entities, and conditionals."""
    q = clean_text(query)
    lower = q.lower()
    for src, dst in _SAFE_SYNONYM_PHRASES:
        idx = lower.find(src)
        if idx != -1:
            replaced = q[:idx] + dst + q[idx + len(src) :]
            return replaced.strip()
    if q.endswith("?"):
        return f"Regarding the question: {q[:-1].strip()}?"
    return f"Clarify information regarding: {q}"


def _extract_entities(text: str) -> set[str]:
    found: set[str] = set()
    for tok in _ENTITY_RE.findall(text):
        low = tok.lower()
        if low in _LEADING_NON_ENTITY:
            continue
        found.add(low)
    return found


def validate_paraphrase(
    original_query: str,
    candidate_paraphrase: str,
    *,
    min_similarity: float = 0.30,
) -> ParaphraseValidationResult:
    """Enforce strict constraint preservation and injection/Unicode hygiene on paraphrases."""
    reasons: list[str] = []
    if is_empty_text(candidate_paraphrase) or len(candidate_paraphrase.strip()) < 3:
        return ParaphraseValidationResult(
            accepted=False,
            original_query=original_query,
            candidate_paraphrase=candidate_paraphrase,
            validated_paraphrase=None,
            rejection_reasons=["PARAPHRASE_EMPTY_OR_TOO_SHORT"],
        )

    if len(candidate_paraphrase) > max(512, len(original_query) * 3):
        reasons.append("PARAPHRASE_EXCESSIVE_LENGTH")

    if "\n" in candidate_paraphrase.strip() or "{" in candidate_paraphrase or "<think>" in candidate_paraphrase.lower():
        reasons.append("PARAPHRASE_MALFORMED_STRUCTURE")

    has_obf, deobf, obf_cnt = detect_obfuscation(candidate_paraphrase)
    folded, mixed_cnt = fold_mixed_script_confusables(deobf)
    fw_cnt = count_fullwidth_ascii_confusables(candidate_paraphrase)
    if has_obf or obf_cnt > 0 or mixed_cnt > 0 or fw_cnt > 0:
        reasons.append("PARAPHRASE_UNICODE_OBFUSCATION")

    cleaned_cand = clean_text(folded)
    if match_threat_patterns(cleaned_cand, target="query"):
        reasons.append("PARAPHRASE_PROMPT_INJECTION_DETECTED")

    orig_clean = clean_text(original_query)
    if has_strict_negation(orig_clean) != has_strict_negation(cleaned_cand):
        reasons.append("PARAPHRASE_NEGATION_MISMATCH")

    orig_nums = set(extract_numbers_and_units(orig_clean))
    cand_nums = set(extract_numbers_and_units(cleaned_cand))
    if orig_nums != cand_nums:
        reasons.append("PARAPHRASE_NUMERIC_CONSTRAINT_CHANGED")

    orig_dates = {m.lower() for m in _YEAR_OR_DATE_RE.findall(orig_clean)}
    cand_dates = {m.lower() for m in _YEAR_OR_DATE_RE.findall(cleaned_cand)}
    if orig_dates != cand_dates:
        reasons.append("PARAPHRASE_TEMPORAL_CONSTRAINT_CHANGED")

    orig_conds = {re.sub(r"\s+", " ", m.lower()) for m in _CONDITIONAL_MARKER_RE.findall(orig_clean)}
    cand_conds = {re.sub(r"\s+", " ", m.lower()) for m in _CONDITIONAL_MARKER_RE.findall(cleaned_cand)}
    if orig_conds != cand_conds:
        reasons.append("PARAPHRASE_CONDITIONAL_CONSTRAINT_CHANGED")

    orig_ents = _extract_entities(orig_clean)
    cand_ents = _extract_entities(cleaned_cand)
    if orig_ents and not orig_ents.issubset(cand_ents):
        reasons.append("PARAPHRASE_NAMED_ENTITY_MISSING_OR_SUBSTITUTED")

    lex_sim = compute_lexical_overlap(orig_clean, cleaned_cand)
    tfidf_sim = compute_tfidf_similarities(orig_clean, [cleaned_cand])[0]
    sem_sim = round(0.5 * lex_sim + 0.5 * tfidf_sim, 4)
    if sem_sim < min_similarity:
        reasons.append(f"PARAPHRASE_SEMANTIC_DRIFT(sim={sem_sim:.4f}<{min_similarity:.2f})")

    accepted = len(reasons) == 0
    return ParaphraseValidationResult(
        accepted=accepted,
        original_query=original_query,
        candidate_paraphrase=candidate_paraphrase,
        validated_paraphrase=cleaned_cand if accepted else None,
        rejection_reasons=reasons,
        semantic_similarity=sem_sim,
    )


class ControlledQueryParaphraser:
    """Orchestrates deterministic or external query paraphrasing behind strict validation."""

    def __init__(
        self,
        *,
        backend: str = "deterministic",
        paraphrase_callable: Callable[[str], str] | None = None,
        min_similarity: float = 0.30,
    ) -> None:
        self.backend = backend
        self.paraphrase_callable = paraphrase_callable
        self.min_similarity = min_similarity

    def generate(self, query: str) -> ParaphraseValidationResult:
        if self.backend == "disabled":
            return ParaphraseValidationResult(
                accepted=False,
                original_query=query,
                candidate_paraphrase=None,
                validated_paraphrase=None,
                rejection_reasons=["PARAPHRASE_DISABLED"],
            )
        if self.backend == "callable" and self.paraphrase_callable is not None:
            try:
                raw_cand = str(self.paraphrase_callable(query))
            except Exception as exc:
                return ParaphraseValidationResult(
                    accepted=False,
                    original_query=query,
                    candidate_paraphrase=None,
                    validated_paraphrase=None,
                    rejection_reasons=[f"PARAPHRASE_BACKEND_ERROR:{type(exc).__name__}"],
                )
        elif self.backend == "deterministic":
            raw_cand = deterministic_safe_paraphrase(query)
        else:
            return ParaphraseValidationResult(
                accepted=False,
                original_query=query,
                candidate_paraphrase=None,
                validated_paraphrase=None,
                rejection_reasons=["PARAPHRASE_BACKEND_UNAVAILABLE"],
            )
        return validate_paraphrase(query, raw_cand, min_similarity=self.min_similarity)


__all__ = [
    "ControlledQueryParaphraser",
    "ParaphraseValidationResult",
    "deterministic_safe_paraphrase",
    "validate_paraphrase",
]
