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


_PARAPHRASE_STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "do",
        "does",
        "did",
        "what",
        "which",
        "who",
        "whom",
        "whose",
        "where",
        "when",
        "how",
        "of",
        "in",
        "on",
        "at",
        "to",
        "for",
        "as",
        "by",
        "with",
        "from",
        "that",
        "this",
        "these",
        "those",
    }
)


_SYNONYM_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"build", "built", "construct", "constructed", "erect", "erected", "create", "created"}),
    frozenset({"when", "year", "date"}),
    frozenset({"capital", "seat"}),
    frozenset({"largest", "biggest", "huge"}),
    frozenset({"oldest", "earliest"}),
    frozenset({"price", "cost"}),
    frozenset({"vulnerable", "susceptible"}),
    frozenset({"begin", "began", "begun", "start", "started"}),
    frozenset({"author", "authors", "wrote", "written", "write", "writes", "writer", "writers"}),
    frozenset({"publisher", "publishers", "published", "publish", "publishes"}),
    frozenset({"reduce", "reduces", "reduced", "reducing", "decrease", "decreases", "decreased", "decreasing", "lower", "lowers", "lowered", "lowering"}),
    frozenset({"increase", "increases", "increased", "increasing", "raise", "raises", "raised", "raising", "boost", "boosts", "boosted", "boosting"}),
    frozenset({"buy", "buys", "bought", "buying", "purchase", "purchases", "purchased", "purchasing"}),
    frozenset({"fix", "fixes", "fixed", "fixing", "repair", "repairs", "repaired", "repairing"}),
    frozenset({"use", "uses", "used", "using", "utilize", "utilizes", "utilized", "utilizing"}),
    frozenset({"require", "requires", "required", "requiring", "need", "needs", "needed", "needing"}),
    frozenset({"help", "helps", "helped", "helping", "aid", "aids", "aided", "aiding", "assist", "assists", "assisted", "assisting"}),
    frozenset({"find", "finds", "found", "finding", "locate", "locates", "located", "locating"}),
    frozenset({"show", "shows", "showed", "shown", "showing", "demonstrate", "demonstrates", "demonstrated", "indicate", "indicates", "indicated"}),
    frozenset({"happen", "happens", "happened", "happening", "occur", "occurs", "occurred", "occurring"}),
    frozenset({"make", "makes", "made", "making", "produce", "produces", "produced", "producing", "manufacture", "manufactures", "manufactured"}),
    frozenset({"teach", "teaches", "taught", "teaching", "instruct", "instructs", "instructed"}),
    frozenset({"prevent", "prevents", "prevented", "preventing", "prevention", "block", "blocks", "blocked", "blocking"}),
    frozenset({"treat", "treats", "treated", "treating", "treatment", "cure", "cures", "cured", "curing"}),
)

_INCOMPATIBLE_ATTRIBUTE_GROUPS: tuple[tuple[frozenset[str], frozenset[str]], ...] = (
    (frozenset({"birth", "born"}), frozenset({"death", "died", "die"})),
    (frozenset({"founded", "found", "established"}), frozenset({"headquartered", "headquarters", "hq"})),
    (frozenset({"founder", "founders", "founded"}), frozenset({"owner", "owners", "owned", "ceo"})),
    (frozenset({"inventor", "inventors", "invent", "invented", "invention"}), frozenset({"discoverer", "discoverers", "discover", "discovered", "discovery"})),
    (frozenset({"author", "authors", "wrote", "written", "writer", "writers"}), frozenset({"publisher", "publishers", "published", "publish", "editor", "editors", "translator", "translators"})),
    (frozenset({"largest", "biggest"}), frozenset({"oldest", "smallest", "newest"})),
    (frozenset({"cause", "causes", "reason"}), frozenset({"consequence", "consequences", "effect", "effects", "outcome"})),
    (frozenset({"capital"}), frozenset({"population", "area", "currency", "language", "gdp", "flag"})),
    (frozenset({"start", "started", "began"}), frozenset({"end", "ended", "finished"})),
    (frozenset({"melting", "melt"}), frozenset({"boiling", "boil", "freezing", "freeze"})),
    (frozenset({"height", "tall"}), frozenset({"weight", "heavy", "mass", "age", "old"})),
    (frozenset({"minimum", "min", "lowest"}), frozenset({"maximum", "max", "highest"})),
    (frozenset({"revenue", "income", "profit"}), frozenset({"cost", "expense", "debt", "loss"})),
    (frozenset({"import", "imports"}), frozenset({"export", "exports"})),
    (frozenset({"inside", "within"}), frozenset({"outside", "beyond"})),
    (frozenset({"above", "over"}), frozenset({"below", "under", "beneath"})),
    (frozenset({"before", "prior"}), frozenset({"after", "following"})),
    (frozenset({"with"}), frozenset({"without"})),
    (frozenset({"treat", "treats", "treated", "treating", "treatment", "therapy", "cure", "cures", "cured", "remedy"}), frozenset({"prevent", "prevents", "prevented", "preventing", "prevention", "prophylaxis"})),
    (frozenset({"treat", "treats", "treated", "treating", "treatment", "cure", "cures", "prevent", "prevents", "prevented", "prevention"}), frozenset({"cause", "causes", "caused", "causing", "trigger", "triggers", "triggered", "induce", "induces"})),
    (frozenset({"treat", "treats", "treated", "treatment"}), frozenset({"diagnose", "diagnoses", "diagnosed", "diagnosing", "diagnosis", "detect", "detects", "detected"})),
)

_SHARED_BRIDGE_WORDS: frozenset[str] = frozenset(
    {
        "about", "regarding", "concerning", "between", "among", "and", "or",
        "across", "through", "toward", "towards", "against", "upon", "via",
    }
)
_IRREGULAR_VERB_LEMMAS: dict[str, str] = {
    "wrote": "write",
    "written": "write",
    "built": "build",
    "taught": "teach",
    "bought": "buy",
    "made": "make",
    "found": "find",
    "fell": "fall",
    "fallen": "fall",
    "rose": "rise",
    "risen": "rise",
    "began": "begin",
    "begun": "begin",
    "drove": "drive",
    "driven": "drive",
    "broke": "break",
    "broken": "break",
    "gave": "give",
    "given": "give",
    "took": "take",
    "taken": "take",
    "saw": "see",
    "seen": "see",
    "led": "lead",
    "held": "hold",
    "kept": "keep",
    "sent": "send",
    "spent": "spend",
    "grew": "grow",
    "grown": "grow",
    "knew": "know",
    "known": "know",
}

_ATTR_PREP_SUBJ_RE = re.compile(
    r"\b(?:of|for|about|in|regarding|concerning|via|against|toward|towards)\s+(?:the\s+|an?\s+)?([a-z0-9][a-z0-9\-]*(?:\s+[a-z0-9][a-z0-9\-]*){0,2})(?=\s*(?:[?.,!;:]|$|\b(?:in|on|at|during|under|with|by|unless|if|when|before|after)\b))",
    re.IGNORECASE,
)
_BETWEEN_SUBJ_RE = re.compile(
    r"\bbetween\s+(?:the\s+|an?\s+)?([a-z0-9][a-z0-9\-]*(?:\s+[a-z0-9][a-z0-9\-]*){0,2})\s+and\s+(?:the\s+|an?\s+)?([a-z0-9][a-z0-9\-]*(?:\s+[a-z0-9][a-z0-9\-]*){0,2})(?=\s*(?:[?.,!;:]|$|\b(?:in|on|at|during|under|with|by|unless|if|when|before|after)\b))",
    re.IGNORECASE,
)
_POSSESSIVE_SUBJ_RE = re.compile(r"\b([a-z0-9][a-z0-9\-]*)['\u2019]s\b", re.IGNORECASE)
_WH_POST_VERB_TARGET_RE = re.compile(
    r"^(?:what|who|which|when|where|why|how)\s+(?:[a-z]+\s+){1,2}?(?:the\s+|an?\s+)?([a-z0-9][a-z0-9\-]*(?:\s+[a-z0-9][a-z0-9\-]*)?)\s*[?.!]*$",
    re.IGNORECASE,
)
_WH_AUX_SUBJ_RE = re.compile(
    r"^(?:what|who|which|when|where|why|how)\s+(?:do|does|did|is|are|was|were|can|could|will|would|should)\s+(?:the\s+|an?\s+)?([a-z0-9][a-z0-9\-]*(?:\s+[a-z0-9][a-z0-9\-]*)?)\s+[a-z]+",
    re.IGNORECASE,
)


def _extract_attribute_subject_tokens(text: str) -> set[str]:
    """Extract candidate subject-anchor tokens from prepositional ('of/for/about/in/between <subj>') and possessive phrases."""
    subjects: set[str] = set()
    for pat in (_ATTR_PREP_SUBJ_RE, _BETWEEN_SUBJ_RE, _POSSESSIVE_SUBJ_RE):
        for m in pat.finditer(text):
            for grp in m.groups():
                if not grp:
                    continue
                for tok in re.findall(r"[a-z0-9]+", grp.lower()):
                    if tok not in _PARAPHRASE_STOPWORDS and not tok.isdigit():
                        subjects.add(tok)
    return subjects


def _extract_wh_target_tokens(text: str) -> set[str]:
    """Fallback extraction of grammatical clause target/subject tokens in anchorless WH-questions."""
    targets: set[str] = set()
    stripped = text.strip()
    for pat in (_WH_AUX_SUBJ_RE, _WH_POST_VERB_TARGET_RE):
        m = pat.match(stripped)
        if m:
            for tok in re.findall(r"[a-z0-9]+", m.group(1).lower()):
                if tok not in _PARAPHRASE_STOPWORDS and not tok.isdigit():
                    targets.add(tok)
    return targets


def _stem_token(tok: str) -> str:
    t = _IRREGULAR_VERB_LEMMAS.get(tok.lower(), tok.lower())
    for suf in ("ation", "ment", "ing", "ed", "es", "ly", "s"):
        if len(t) > len(suf) + 2 and t.endswith(suf):
            return t[: -len(suf)]
    return t


def _expand_with_synonyms(stems: set[str], raw_tokens: set[str]) -> set[str]:
    expanded = set(stems)
    for grp in _SYNONYM_GROUPS:
        if grp & raw_tokens:
            expanded.update(_stem_token(w) for w in grp)
    return expanded


def _has_attribute_head_drift(
    orig_clean: str,
    cand_clean: str,
    orig_ents: set[str],
    cand_ents: set[str],
) -> bool:
    """Detect central attribute/relation substitutions when surface entity/structure is preserved."""
    orig_raw = set(re.findall(r"[a-z0-9]+", re.sub(r"['\u2019]s\b", "", orig_clean.lower())))
    cand_raw = set(re.findall(r"[a-z0-9]+", re.sub(r"['\u2019]s\b", "", cand_clean.lower())))

    for grp_a, grp_b in _INCOMPATIBLE_ATTRIBUTE_GROUPS:
        if ((grp_a & orig_raw) and (grp_b & cand_raw) and not (grp_a & cand_raw)) or (
            (grp_b & orig_raw) and (grp_a & cand_raw) and not (grp_b & cand_raw)
        ):
            return True

    ent_lower = {e.lower() for e in (orig_ents | cand_ents)}
    orig_subj_toks = _extract_attribute_subject_tokens(orig_clean)
    cand_subj_toks = _extract_attribute_subject_tokens(cand_clean)
    shared_subj_toks = (orig_subj_toks & cand_raw) | (cand_subj_toks & orig_raw)
    anchor_tokens = (orig_ents & cand_ents) | shared_subj_toks
    if not anchor_tokens:
        orig_wh_toks = _extract_wh_target_tokens(orig_clean)
        cand_wh_toks = _extract_wh_target_tokens(cand_clean)
        shared_wh_toks = (orig_wh_toks & cand_raw) | (cand_wh_toks & orig_raw)
        shared_subj_toks = shared_subj_toks | shared_wh_toks
        anchor_tokens = shared_wh_toks

    removed_anchors = ent_lower | shared_subj_toks
    orig_ct = _content_tokens(orig_clean) - removed_anchors
    cand_ct = _content_tokens(cand_clean) - removed_anchors
    shared_bridges = (orig_ct & cand_ct) & _SHARED_BRIDGE_WORDS
    orig_ct_core = orig_ct - shared_bridges
    cand_ct_core = cand_ct - shared_bridges
    if anchor_tokens and orig_ct_core and cand_ct_core:
        orig_stems = _expand_with_synonyms({_stem_token(t) for t in orig_ct_core}, orig_raw)
        cand_stems = _expand_with_synonyms({_stem_token(t) for t in cand_ct_core}, cand_raw)
        if not (orig_stems & cand_stems):
            return True
    return False


def _content_tokens(text: str) -> set[str]:
    """Normalize possessives and extract content-bearing tokens for paraphrase similarity."""
    cleaned = re.sub(r"['\u2019]s\b", "", text.lower())
    tokens = re.findall(r"[a-z0-9]+", cleaned)
    return {t for t in tokens if t not in _PARAPHRASE_STOPWORDS}


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

    if _has_attribute_head_drift(orig_clean, cleaned_cand, orig_ents, cand_ents):
        reasons.append("PARAPHRASE_ATTRIBUTE_DRIFT")

    lex_sim = compute_lexical_overlap(orig_clean, cleaned_cand)
    tfidf_sim = compute_tfidf_similarities(orig_clean, [cleaned_cand])[0]
    base_sim = 0.5 * lex_sim + 0.5 * tfidf_sim
    orig_ct = _content_tokens(orig_clean)
    cand_ct = _content_tokens(cleaned_cand)
    if orig_ct and cand_ct:
        ct_jaccard = len(orig_ct & cand_ct) / len(orig_ct | cand_ct)
        sem_sim = round(max(base_sim, 0.5 * ct_jaccard + 0.5 * max(lex_sim, tfidf_sim)), 4)
    else:
        sem_sim = round(base_sim, 4)
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
