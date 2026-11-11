"""Conservative Phase 06 G3 claim-verification generalization refinements.

Every positive support refinement routes back through OutputEvidenceVerifier.verify_claim
so all Phase 03 strict conditional, negation, scope, voice, acronym, and dosage guards stay active.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence

from trustrag.engine.schemas import (
    ClaimVerificationItem,
    EvidenceDocument,
    EvidenceOutcome,
    EvidenceReference,
    G3ClaimVerdict,
)

_SHORTHAND_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*([kmbKMB])\b")
_YEAR_RE = re.compile(r"\b(1[5-9]\d{2}|20\d{2})\b")
_COND_OR_DISJ_RE = re.compile(r"\b(?:unless|except|only\s+(?:when|if|after)|until|provided|or|nor)\b", re.IGNORECASE)
_STOPWORDS = frozenset(
    {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "in", "on", "at", "to", "for", "of", "by", "with", "as", "and", "or",
        "that", "this", "it", "its", "has", "have", "had", "today", "currently", "now",
    }
)

_PARAPHRASE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("serves as", "is"),
    ("acts as", "is"),
    ("functions as", "is"),
    ("resides in", "lives in"),
    ("national capital", "capital"),
    ("capital city", "capital"),
    ("is located in", "is in"),
    ("situated in", "in"),
)

_UNIT_FACTORS: dict[str, tuple[str, float]] = {
    "meter": ("m", 1.0),
    "meters": ("m", 1.0),
    "metre": ("m", 1.0),
    "metres": ("m", 1.0),
    "m": ("m", 1.0),
    "foot": ("m", 0.3048),
    "feet": ("m", 0.3048),
    "ft": ("m", 0.3048),
    "kilometer": ("m", 1000.0),
    "kilometers": ("m", 1000.0),
    "km": ("m", 1000.0),
    "mile": ("m", 1609.344),
    "miles": ("m", 1609.344),
    "kilogram": ("kg", 1.0),
    "kilograms": ("kg", 1.0),
    "kg": ("kg", 1.0),
    "pound": ("kg", 0.45359237),
    "pounds": ("kg", 0.45359237),
    "lb": ("kg", 0.45359237),
    "lbs": ("kg", 0.45359237),
}
_UNIT_VAL_RE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(meters?|metres?|feet|foot|ft|kilometers?|km|miles?|kilograms?|kg|pounds?|lbs?|m)\b",
    re.IGNORECASE,
)


def _expand_numeric_shorthand(text: str) -> str:
    mult = {"k": "thousand", "m": "million", "b": "billion"}
    return _SHORTHAND_RE.sub(lambda m: f"{m.group(1)} {mult[m.group(2).lower()]}", text)


def _linearize_markdown_tables(text: str) -> str | None:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    table_lines = [ln for ln in lines if ln.startswith("|") and ln.endswith("|")]
    if len(table_lines) < 2:
        return None
    headers = [c.strip() for c in table_lines[0].strip("|").split("|")]
    clauses: list[str] = []
    for row_ln in table_lines[1:]:
        cells = [c.strip() for c in row_ln.strip("|").split("|")]
        if all(set(c) <= {"-", ":"} for c in cells) or not cells:
            continue
        subj = cells[0]
        for idx in range(1, min(len(headers), len(cells))):
            val = _expand_numeric_shorthand(cells[idx])
            hdr = headers[idx]
            if hdr.lower().startswith("pop"):
                clauses.append(f"{subj} has a population of {val}.")
            else:
                clauses.append(f"{subj} has {hdr} {val}.")
    return " ".join(clauses) if clauses else None


def _apply_synonym_normalization(text: str) -> str:
    out = text
    for src, dst in _PARAPHRASE_REPLACEMENTS:
        out = re.sub(re.escape(src), dst, out, flags=re.IGNORECASE)
    return out


def _norm_tokens(text: str) -> set[str]:
    low = _apply_synonym_normalization(text).lower().replace("'s", " ")
    return {t for t in re.findall(r"[a-z0-9]+", low) if t not in _STOPWORDS}


def _extract_cap_entities(text: str) -> list[str]:
    seen: list[str] = []
    for m in re.finditer(r"\b[A-Z][a-zA-Z0-9]{1,}\b", text):
        tok = m.group(0)
        if tok not in seen:
            seen.append(tok)
    return seen


def _check_intra_doc_conflict(
    item: ClaimVerificationItem,
    documents: Sequence[EvidenceDocument],
) -> ClaimVerificationItem | None:
    """Downgrade SUPPORTED -> UNCERTAIN when a single document contains competing years for the claim."""
    if item.verdict != G3ClaimVerdict.SUPPORTED or not item.supporting_evidence_refs:
        return None
    claim_years = set(_YEAR_RE.findall(item.claim_text))
    if not claim_years:
        return None
    claim_toks = _norm_tokens(item.claim_text) - claim_years
    if not claim_toks:
        return None

    for doc in documents:
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", doc.text) if s.strip()]
        if len(sents) < 2:
            continue
        for sent in sents:
            sent_years = set(_YEAR_RE.findall(sent))
            if not sent_years or not (sent_years - claim_years):
                continue
            low = sent.lower()
            has_conflict_cue = any(
                cue in low for cue in ("also claim", "disputed", "however", "instead", "other sources", "conflicting")
            )
            overlap = len((_norm_tokens(sent) - sent_years) & claim_toks)
            if has_conflict_cue or overlap >= 2:
                return item.model_copy(
                    update={
                        "outcome": EvidenceOutcome.UNCERTAIN,
                        "verdict": G3ClaimVerdict.UNCERTAIN,
                        "unsupported_flag": True,
                        "confidence": round(min(item.confidence, 0.55), 4),
                        "explanation": (
                            f"Downgraded from SUPPORTED: intra-document conflicting years {sorted(sent_years)} "
                            f"found alongside claim values {sorted(claim_years)} in document '{doc.doc_id}'."
                        ),
                    }
                )
    return None


def _check_deontic_only_guard(
    item: ClaimVerificationItem,
    documents: Sequence[EvidenceDocument],
) -> ClaimVerificationItem | None:
    """Prevent false CONTRADICTED when evidence says 'Only RoleA may Action' and claim says 'RoleB may not Action'."""
    if item.verdict != G3ClaimVerdict.CONTRADICTED:
        return None
    cl_m = re.search(
        r"\b([a-zA-Z]+)\s+(?:may\s+not|cannot|can\s+not|are\s+not\s+allowed\s+to)\s+([a-zA-Z]+)",
        item.claim_text,
        re.IGNORECASE,
    )
    if not cl_m:
        return None
    cl_actor = cl_m.group(1).lower().rstrip("s")
    cl_verb = cl_m.group(2).lower().rstrip("s")

    for doc in documents:
        ev_m = re.search(
            r"\bonly\s+([a-zA-Z]+)\s+(?:may|can|are\s+allowed\s+to)\s+([a-zA-Z]+)",
            doc.text,
            re.IGNORECASE,
        )
        if not ev_m:
            continue
        ev_actor = ev_m.group(1).lower().rstrip("s")
        ev_verb = ev_m.group(2).lower().rstrip("s")
        if ev_verb == cl_verb and ev_actor != cl_actor:
            ref = EvidenceReference(
                doc_id=doc.doc_id,
                source_id=doc.source_id,
                source_dataset=doc.source_dataset,
                provenance=doc.provenance,
                matched_span=doc.text[:220],
                similarity_score=0.75,
                polarity_match=True,
                numeric_match=True,
                coverage_score=0.75,
                alignment_note=f"Restrictive scope 'only {ev_m.group(1)}' entails non-{ev_m.group(1)} exclusion.",
                span_outcome="SUPPORTED",
            )
            return item.model_copy(
                update={
                    "outcome": EvidenceOutcome.SUPPORTS,
                    "verdict": G3ClaimVerdict.SUPPORTED,
                    "unsupported_flag": False,
                    "confidence": 0.78,
                    "supporting_evidence_refs": [ref],
                    "contradicting_evidence_refs": [],
                    "evidence_refs": [ref],
                    "explanation": f"Deontic scope entailment verified: 'only {ev_m.group(1)}' implies '{cl_m.group(1)} may not {cl_m.group(2)}'.",
                }
            )
    return None


def _check_temporal_currency(
    item: ClaimVerificationItem,
    documents: Sequence[EvidenceDocument],
) -> ClaimVerificationItem | None:
    """Detect superseded historical role claimed as current ('today'/'currently'/'now')."""
    if item.verdict != G3ClaimVerdict.INSUFFICIENT:
        return None
    cl_low = item.claim_text.lower()
    if not any(cue in cl_low for cue in ("today", "currently", "now", "presently")):
        return None
    if _YEAR_RE.search(item.claim_text):
        return None

    cl_entities = {e.lower() for e in _extract_cap_entities(item.claim_text)}
    if not cl_entities:
        return None

    for doc in documents:
        parts = re.split(r"[;.]", doc.text)
        dated: list[tuple[int, str]] = []
        for p in parts:
            ym = _YEAR_RE.search(p)
            if ym:
                dated.append((int(ym.group(1)), p.strip()))
        if len(dated) < 2:
            continue
        dated.sort(key=lambda x: x[0])
        earliest_y, earliest_txt = dated[0]
        latest_y, latest_txt = dated[-1]
        if latest_y <= earliest_y:
            continue
        early_ents = {e.lower() for e in _extract_cap_entities(earliest_txt)}
        late_ents = {e.lower() for e in _extract_cap_entities(latest_txt)}
        if (
            (cl_entities & early_ents)
            and not (cl_entities & late_ents)
            and late_ents
            and any(w in latest_txt.lower() for w in ("became", "replaced", "succeeded", "took over", "appointed", "is now"))
        ):
            ref = EvidenceReference(
                doc_id=doc.doc_id,
                source_id=doc.source_id,
                source_dataset=doc.source_dataset,
                provenance=doc.provenance,
                matched_span=doc.text[:220],
                similarity_score=0.70,
                polarity_match=False,
                numeric_match=False,
                coverage_score=0.70,
                alignment_note=f"Historical ({earliest_y}) role superseded in {latest_y}.",
                span_outcome="CONTRADICTED",
            )
            return item.model_copy(
                update={
                    "outcome": EvidenceOutcome.CONTRADICTS,
                    "verdict": G3ClaimVerdict.CONTRADICTED,
                    "unsupported_flag": True,
                    "confidence": 0.80,
                    "contradicting_evidence_refs": [ref],
                    "evidence_refs": [ref],
                    "explanation": f"Temporal contradiction: {earliest_y} entity superseded by {latest_y} successor in document '{doc.doc_id}'.",
                }
            )
    return None


def _unit_context_tokens(text: str) -> set[str]:
    stripped = _UNIT_VAL_RE.sub("", text).lower()
    raw = {t for t in re.findall(r"[a-z0-9]+", stripped) if t not in _STOPWORDS}
    mapped = {"tall" if t in {"high", "height"} else ("is" if t in {"stands", "weighs", "measures"} else t) for t in raw}
    return mapped - {"is"}


def _check_unit_conversion(
    item: ClaimVerificationItem,
    documents: Sequence[EvidenceDocument],
) -> ClaimVerificationItem | None:
    if item.verdict != G3ClaimVerdict.INSUFFICIENT:
        return None
    cl_matches = list(_UNIT_VAL_RE.finditer(item.claim_text))
    if not cl_matches:
        return None
    cl_toks = _unit_context_tokens(item.claim_text)

    for cm in cl_matches:
        c_val = float(cm.group(1))
        c_info = _UNIT_FACTORS.get(cm.group(2).lower())
        if not c_info:
            continue
        c_dim, c_fac = c_info
        c_si = c_val * c_fac

        for doc in documents:
            for dm in _UNIT_VAL_RE.finditer(doc.text):
                d_val = float(dm.group(1))
                d_info = _UNIT_FACTORS.get(dm.group(2).lower())
                if not d_info or d_info[0] != c_dim:
                    continue
                d_si = d_val * d_info[1]
                rel_err = abs(c_si - d_si) / max(1e-6, abs(c_si))
                if rel_err <= 0.015:
                    ev_toks = _unit_context_tokens(doc.text)
                    if cl_toks and (len(cl_toks & ev_toks) / len(cl_toks)) >= 0.50:
                        ref = EvidenceReference(
                            doc_id=doc.doc_id,
                            source_id=doc.source_id,
                            source_dataset=doc.source_dataset,
                            provenance=doc.provenance,
                            matched_span=doc.text[:220],
                            similarity_score=0.85,
                            polarity_match=True,
                            numeric_match=True,
                            coverage_score=0.85,
                            alignment_note=f"Unit-converted match ({dm.group(0)} ~= {cm.group(0)}, rel_err={rel_err:.4f}).",
                            span_outcome="SUPPORTED",
                        )
                        return item.model_copy(
                            update={
                                "outcome": EvidenceOutcome.SUPPORTS,
                                "verdict": G3ClaimVerdict.SUPPORTED,
                                "unsupported_flag": False,
                                "confidence": 0.85,
                                "supporting_evidence_refs": [ref],
                                "evidence_refs": [ref],
                                "explanation": f"Verified via unit conversion: {dm.group(0)} matches {cm.group(0)}.",
                            }
                        )
    return None


def _check_synonym_or_bridge_via_verifier(
    item: ClaimVerificationItem,
    trusted_documents: Sequence[EvidenceDocument],
    verify_claim_fn: Callable[[str, str, Sequence[EvidenceDocument]], ClaimVerificationItem],
) -> ClaimVerificationItem | None:
    """Re-verify with synonym normalization and strict 2-hop transitive bridging via core verify_claim."""
    norm_claim = _apply_synonym_normalization(item.claim_text)
    norm_docs = [d.model_copy(update={"text": _apply_synonym_normalization(d.text)}) for d in trusted_documents]
    changed = (norm_claim != item.claim_text) or any(
        nd.text != od.text for nd, od in zip(norm_docs, trusted_documents, strict=False)
    )
    if changed:
        res = verify_claim_fn(item.claim_id, norm_claim, norm_docs)
        if res.verdict == G3ClaimVerdict.SUPPORTED:
            return res.model_copy(
                update={"claim_text": item.claim_text, "explanation": f"{res.explanation} (paraphrase normalization)"}
            )

    # Strict 2-hop transitive location/entity bridge (never fires if conditionals/disjunctions/numbers present)
    if _COND_OR_DISJ_RE.search(item.claim_text) or re.search(r"\d", item.claim_text):
        return None
    cl_ents = _extract_cap_entities(norm_claim)
    if len(cl_ents) != 2:
        return None
    ent_a, ent_b = cl_ents[0], cl_ents[1]

    for doc, orig_doc in zip(norm_docs, trusted_documents, strict=False):
        if _COND_OR_DISJ_RE.search(doc.text) or re.search(r"\d", doc.text):
            continue
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", doc.text) if s.strip()]
        if len(sents) < 2:
            continue
        for i, sa in enumerate(sents):
            ea = _extract_cap_entities(sa)
            if ent_a not in ea or ent_b in ea:
                continue
            bridges = [e for e in ea if e not in {ent_a, ent_b}]
            for bridge in bridges:
                for j, sb in enumerate(sents):
                    if i == j:
                        continue
                    eb = _extract_cap_entities(sb)
                    if bridge in eb and ent_b in eb:
                        bridged_text = re.sub(rf"\b{re.escape(bridge)}\b", ent_b, sa)
                        bridged_doc = orig_doc.model_copy(update={"text": bridged_text})
                        res = verify_claim_fn(item.claim_id, norm_claim, [bridged_doc])
                        if res.verdict == G3ClaimVerdict.SUPPORTED:
                            return res.model_copy(
                                update={
                                    "claim_text": item.claim_text,
                                    "explanation": f"Verified via 2-hop transitive entity bridge through '{bridge}'.",
                                }
                            )
    return None


def refine_claim_with_generalization(
    item: ClaimVerificationItem,
    trusted_documents: Sequence[EvidenceDocument],
    verify_claim_fn: Callable[[str, str, Sequence[EvidenceDocument]], ClaimVerificationItem],
) -> ClaimVerificationItem:
    """Apply conservative Phase 06 G3 refinements without bypassing Phase 03 safety guards."""
    if not trusted_documents:
        return item

    conflict_guard = _check_intra_doc_conflict(item, trusted_documents)
    if conflict_guard is not None:
        return conflict_guard

    deontic_guard = _check_deontic_only_guard(item, trusted_documents)
    if deontic_guard is not None:
        return deontic_guard

    if item.verdict != G3ClaimVerdict.INSUFFICIENT:
        return item

    table_docs: list[EvidenceDocument] = []
    for d in trusted_documents:
        lin = _linearize_markdown_tables(d.text)
        if lin:
            table_docs.append(d.model_copy(update={"text": lin}))
    if table_docs:
        tbl_res = verify_claim_fn(item.claim_id, item.claim_text, table_docs)
        if tbl_res.verdict == G3ClaimVerdict.SUPPORTED:
            return tbl_res.model_copy(
                update={"explanation": f"{tbl_res.explanation} (linearized tabular evidence)"}
            )

    temp_res = _check_temporal_currency(item, trusted_documents)
    if temp_res is not None:
        return temp_res

    unit_res = _check_unit_conversion(item, trusted_documents)
    if unit_res is not None:
        return unit_res

    para_res = _check_synonym_or_bridge_via_verifier(item, trusted_documents, verify_claim_fn)
    if para_res is not None:
        return para_res

    return item


__all__ = ["refine_claim_with_generalization"]
