"""Step 06: Query-Answer Consistency & DoS Refusal Checker (Paper B Sec 6.3 Step 3)."""

from __future__ import annotations

import re
from collections.abc import Sequence

from pydantic import BaseModel, Field

from trustrag.data.preprocessing.cleaning import is_empty_text
from trustrag.engine.schemas import EvidenceDocument
from trustrag.engine.text_utils import (
    compute_lexical_overlap,
    compute_tfidf_similarities,
    strip_citations,
    tokenize_content_words,
)

_REFUSAL_CUE_RE = re.compile(
    r"\b(?:i\s+cannot\s+answer|unable\s+to\s+answer|cannot\s+comply|i\s+must\s+refuse|as\s+an\s+ai|access\s+denied|request\s+blocked)\b",
    re.IGNORECASE,
)
_YEAR_RE = re.compile(r"\b(1[5-9]\d{2}|20\d{2})\b")
_STOP_CAP = frozenset({"What", "Which", "When", "Where", "Who", "Why", "How", "Is", "Are", "Was", "Were", "Can", "Did", "Does", "Do", "The", "A", "An", "In", "On"})


class QueryConsistencyReport(BaseModel):
    """Structured outcome comparing generated answer against authoritative user query."""

    consistent: bool
    consistency_score: float = Field(ge=0.0, le=1.0)
    spurious_refusal_detected: bool = False
    topic_hijack_detected: bool = False
    missing_query_constraints: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


def evaluate_query_consistency(
    query: str,
    answer_text: str,
    evidence_docs: Sequence[EvidenceDocument],
    *,
    abstained: bool = False,
    min_consistency_score: float = 0.12,
) -> QueryConsistencyReport:
    """Verify answer addresses user query, detects topic-hijacks and spurious refusals."""
    if is_empty_text(query) or abstained or is_empty_text(answer_text):
        return QueryConsistencyReport(
            consistent=True,
            consistency_score=1.0 if abstained else 0.0,
            reasons=["Abstained cleanly; query-consistency override inactive." if abstained else "Empty query/answer."],
        )

    clean_ans = strip_citations(answer_text)
    q_toks = set(tokenize_content_words(query, include_negations=False))
    a_toks = set(tokenize_content_words(clean_ans, include_negations=False))
    lex = compute_lexical_overlap(query, clean_ans)
    tfidf = compute_tfidf_similarities(query, [clean_ans])[0]
    score = round(min(1.0, max(0.0, 0.55 * tfidf + 0.45 * lex)), 4)

    reasons: list[str] = []
    missing_constraints: list[str] = []
    topic_hijack = False
    spurious_refusal = False

    # 1. Spurious DoS refusal when admissible evidence actually matches query
    if _REFUSAL_CUE_RE.search(clean_ans) and evidence_docs:
        ev_sims = compute_tfidf_similarities(query, [d.text for d in evidence_docs])
        if ev_sims and max(ev_sims) >= 0.20:
            spurious_refusal = True
            reasons.append("QUERY_SPURIOUS_REFUSAL_DOS")

    # 2. Topic hijack / off-topic response check
    is_yes_no_short = clean_ans.strip().lower() in {"yes", "no", "true", "false"}
    if not is_yes_no_short and q_toks:
        shared_q = q_toks & a_toks
        q_coverage = len(shared_q) / len(q_toks)
        if score < min_consistency_score and q_coverage < 0.25:
            topic_hijack = True
            reasons.append(f"QUERY_TOPIC_HIJACK_OR_DRIFT(score={score:.4f},coverage={q_coverage:.2f})")

    # 3. Query-specific year/entity anchor check (if zero shared year when answer mentions unrelated text)
    q_years = set(_YEAR_RE.findall(query))
    if q_years and len(clean_ans.split()) >= 5:
        a_years = set(_YEAR_RE.findall(clean_ans))
        if a_years and not (q_years & a_years):
            missing_constraints.extend(sorted(q_years))
            reasons.append(f"QUERY_TEMPORAL_ANCHOR_MISMATCH(expected={sorted(q_years)},got={sorted(a_years)})")

    consistent = not (spurious_refusal or topic_hijack or bool(missing_constraints))
    if consistent and not reasons:
        reasons.append("QUERY_CONSISTENT")

    return QueryConsistencyReport(
        consistent=consistent,
        consistency_score=score,
        spurious_refusal_detected=spurious_refusal,
        topic_hijack_detected=topic_hijack,
        missing_query_constraints=missing_constraints,
        reasons=reasons,
    )


__all__ = ["QueryConsistencyReport", "evaluate_query_consistency"]
