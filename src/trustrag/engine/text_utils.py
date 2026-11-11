"""Shared lexical, statistical, polarity, and pattern-matching utilities for TrustRAG Phase 03.

Avoids duplicated text-processing logic across G1 (guardrail), Retrieval,
G2 (multi-signal detector), Generation, and G3 (evidence verifier).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import List, Optional, Sequence, Set, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

STOPWORDS: Set[str] = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "by", "can",
    "could", "did", "do", "does", "for", "from", "had", "has", "have", "he",
    "her", "here", "his", "how", "i", "if", "in", "into", "is", "it", "its",
    "may", "might", "must", "of", "on", "or", "our", "she", "should", "so",
    "such", "than", "that", "the", "their", "them", "then", "there", "these",
    "they", "this", "those", "to", "was", "were", "what", "when", "where",
    "which", "while", "who", "whom", "why", "will", "with", "would", "you",
    "your",
}

NEGATION_WORDS: Set[str] = {
    "no", "not", "never", "none", "neither", "nor", "nothing", "nowhere",
    "without", "cannot", "cant", "dont", "doesnt", "didnt", "isnt", "arent",
    "wasnt", "werent", "wont", "wouldnt", "shouldnt", "couldnt", "refuted",
    "refute", "refutes", "false", "disproved", "disprove", "dissolved",
    "denied", "deny", "denies", "contradicts", "contradict", "impossible",
    "infeasible", "unable", "lack", "lacks", "lacking", "absent", "absence",
    "fail", "failed", "fails", "unlikely", "unrelated", "invalid", "broken",
}

# Strict clause-level negators excluding domain adjectives like "infeasible" or "broken"
STRICT_CONTRADICTION_NEGATIONS: Set[str] = {
    "no", "not", "never", "none", "neither", "nor", "nothing", "cannot",
    "cant", "dont", "doesnt", "didnt", "isnt", "arent", "wasnt", "werent",
    "wont", "wouldnt", "shouldnt", "couldnt", "refuted", "refute", "refutes",
    "disproved", "disprove", "dissolved", "denied", "deny", "denies",
    "contradicts", "contradict", "false", "lack", "lacks", "lacking", "absent",
}

ZERO_WIDTH_OR_CONTROL_RE = re.compile(
    r"[\u00ad\u034f\u061c\u115f\u1160\u180e\u200b-\u200f\u202a-\u202e\u2060-\u206f\u3164\ufe00-\ufe0f\ufeff\uffa0\ufff9-\ufffb\U000e0001-\U000e007f\U000e0100-\U000e01ef\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
)
TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)?")
NUMBER_UNIT_RE = re.compile(
    r"(?<!\w)(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?:[\s-]*(%|(?:percent|mcg|ug|mg|g|kg|ml|l|iu|tablets?|capsules?|pills?|doses?|drops?|puffs?|injections?|teaspoons?|tablespoons?|bits?|bytes|kb|mb|gb|tb|hours?|hrs?|minutes?|mins?|seconds?|secs?|days?|weeks?|months?|years?|c|f|bp|bps)))?(?=$|[^\w])",
    re.IGNORECASE,
)
_WORD_DOSAGE_UNIT_RE = re.compile(
    r"(?<!\w)(one|two|three|four|five|six|seven|eight|nine|ten)[\s-]+(tablets?|capsules?|pills?|doses?|drops?|puffs?|injections?|teaspoons?|tablespoons?|mcg|ug|mg|g|kg|ml|l|iu)(?=$|[^\w])",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ThreatPatternSpec:
    """Parameterized specification for instruction/injection/payload rules."""

    rule_name: str
    category: str
    pattern: re.Pattern[str]
    severity: float
    apply_to_query: bool = True
    apply_to_document: bool = True


SHARED_THREAT_PATTERNS: Tuple[ThreatPatternSpec, ...] = (
    ThreatPatternSpec(
        rule_name="ignore_previous_instructions",
        category="PROMPT_INJECTION",
        pattern=re.compile(
            r"\b(?:ignore|disregard|forget|override|bypass)\s+(?:all\s+)?(?:previous|prior|above|system|safety|initial)\s+(?:instructions?|directives?|rules?|prompts?|constraints?|guards?)",
            re.IGNORECASE,
        ),
        severity=0.90,
    ),
    ThreatPatternSpec(
        rule_name="system_override_tag",
        category="PROMPT_INJECTION",
        pattern=re.compile(
            r"(?:SYSTEM\s+OVERRIDE|(?i:system\s+override\s*:|\[/?SYSTEM\]|\[/?INST\]|<\|im_start\|>|<\|system\|>|###\s*SYSTEM\s*:))"
        ),
        severity=0.90,
    ),
    ThreatPatternSpec(
        rule_name="role_jailbreak_directive",
        category="ROLE_HIJACK",
        pattern=re.compile(
            r"\b(?:you\s+are\s+now\s+(?:in\s+)?(?:DAN|developer\s+mode|unfiltered|jailbroken)|act\s+as\s+(?:an?\s+)?unrestricted|pretend\s+there\s+are\s+no\s+rules)\b",
            re.IGNORECASE,
        ),
        severity=0.85,
    ),
    ThreatPatternSpec(
        rule_name="prompt_leak_extraction",
        category="PROMPT_INJECTION",
        pattern=re.compile(
            r"\b(?:reveal|print|dump|output|leak|expose|display)\s+(?:all\s+)?(?:system\s+prompt|hidden\s+instructions?|secret\s+keys?|user\s+passwords?|api\s+keys?|credentials?)\b",
            re.IGNORECASE,
        ),
        severity=0.85,
    ),
    ThreatPatternSpec(
        rule_name="shell_exfiltration_chain",
        category="MALICIOUS_COMMAND",
        pattern=re.compile(
            r"(?:&&|\|\||;)\s*(?:curl|wget|nc|netcat|bash|sh|powershell|pwsh|python)\b.*?(?:https?://|~/.ssh|/etc/passwd|id_rsa|-d\s+@|\|\s*sh)",
            re.IGNORECASE,
        ),
        severity=0.95,
    ),
    ThreatPatternSpec(
        rule_name="sensitive_path_or_destructive_cmd",
        category="MALICIOUS_COMMAND",
        pattern=re.compile(
            r"(?:~/\.ssh/id_rsa|/etc/shadow|\brm\s+-rf\s+/|\bInvoke-Expression\b|\bIEX\s*\(|;\s*DROP\s+TABLE\b|<script[^>]*>)",
            re.IGNORECASE,
        ),
        severity=0.85,
    ),
    ThreatPatternSpec(
        rule_name="recursive_dos_trigger",
        category="DOS_TRIGGER",
        pattern=re.compile(
            r"(?:\[START_RECURSIVE_EXPANSION|\brepeat\s+(?:the\s+word\s+)?['\"]?\w+['\"]?\s+\d{3,}\s+times\b|\binfinite\s+loop\b)",
            re.IGNORECASE,
        ),
        severity=0.80,
    ),
    ThreatPatternSpec(
        rule_name="disable_safety_restrictions",
        category="PROMPT_INJECTION",
        pattern=re.compile(
            r"\b(?:disable|turn\s+off|remove|bypass|suspend)\s+(?:all\s+)?(?:safety|content|moderation|ethical|security)\s+(?:restrictions?|filters?|guardrails?|checks?|rules?|guidelines?)\b",
            re.IGNORECASE,
        ),
        severity=0.88,
        apply_to_query=True,
        apply_to_document=True,
    ),
    ThreatPatternSpec(
        rule_name="direct_ai_instruction",
        category="PROMPT_INJECTION",
        pattern=re.compile(
            r"\b(?:note\s+to\s+(?:the\s+)?(?:ai|assistant|model|language\s+model|llm)|attention\s+(?:ai|assistant|model|llm)|instructions?\s+for\s+(?:the\s+)?(?:ai|assistant|language\s+model|llm)|dear\s+(?:ai|assistant)|as\s+an?\s+(?:ai|language)\s+model,?\s+you\s+must)\b",
            re.IGNORECASE,
        ),
        severity=0.75,
        apply_to_query=False,
        apply_to_document=True,
    ),
    ThreatPatternSpec(
        rule_name="answer_manipulation_directive",
        category="PROMPT_INJECTION",
        pattern=re.compile(
            r"\b(?:when\s+answering\s+(?:this|the)\s+(?:query|question|user),?\s+(?:always|never|only|you\s+must)|you\s+must\s+(?:always\s+)?(?:reply|respond|answer|state|output)\s+(?:only\s+)?that|ignore\s+other\s+(?:sources|passages|documents)\s+and\s+(?:state|output|say))\b",
            re.IGNORECASE,
        ),
        severity=0.75,
        apply_to_query=False,
        apply_to_document=True,
    ),
)


_MIXED_SCRIPT_CONFUSABLE_MAP: dict[str, str] = {
    # Cyrillic lowercase & uppercase lookalikes
    "\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "p", "\u0441": "c",
    "\u0443": "y", "\u0445": "x", "\u0456": "i", "\u0457": "i", "\u0458": "j",
    "\u0455": "s", "\u0501": "d", "\u051b": "q", "\u051d": "w", "\u04cf": "l",
    "\u0410": "A", "\u0412": "B", "\u0415": "E", "\u041a": "K", "\u041c": "M",
    "\u041d": "H", "\u041e": "O", "\u0420": "P", "\u0421": "C", "\u0422": "T",
    "\u0425": "X", "\u0406": "I",
    # Greek lowercase & uppercase lookalikes
    "\u03b1": "a", "\u03b5": "e", "\u03b9": "i", "\u03bf": "o", "\u03c1": "p",
    "\u03c2": "s", "\u03c4": "t", "\u03c5": "y", "\u03c7": "x",
    "\u0391": "A", "\u0392": "B", "\u0395": "E", "\u0396": "Z", "\u0397": "H",
    "\u0399": "I", "\u039a": "K", "\u039c": "M", "\u039d": "N", "\u039f": "O",
    "\u03a1": "P", "\u03a4": "T", "\u03a5": "Y", "\u03a7": "X",
}
_MIXED_SCRIPT_TOKEN_RE = re.compile(r"[A-Za-z\u0370-\u03ff\u0400-\u052f]+")


def _is_emoji_base_char(ch: str) -> bool:
    """Return True if char can legitimately carry a BMP presentation variation selector (U+FE0E/U+FE0F)."""
    cp = ord(ch)
    if cp >= 0x1F000 or (0x2100 <= cp <= 0x2BFF):
        return True
    return unicodedata.category(ch) in {"So", "Sk"}


def _is_complex_script_char(ch: str) -> bool:
    """Return True if char belongs to Arabic/Persian, Indic/Brahmic, or SE Asian complex scripts using ZWNJ/ZWJ."""
    cp = ord(ch)
    return (
        (0x0600 <= cp <= 0x06FF)      # Arabic / Persian
        or (0x0750 <= cp <= 0x077F)   # Arabic Supplement
        or (0x08A0 <= cp <= 0x08FF)   # Arabic Extended-A
        or (0xFB50 <= cp <= 0xFDFF)   # Arabic Presentation Forms-A
        or (0xFE70 <= cp <= 0xFEFF)   # Arabic Presentation Forms-B (excluding FEFF handled earlier)
        or (0x0900 <= cp <= 0x0DFF)   # Devanagari, Bengali, Gurmukhi, Gujarati, Oriya, Tamil, Telugu, Kannada, Malayalam, Sinhala
        or (0x0E00 <= cp <= 0x109F)   # Thai, Lao, Tibetan, Myanmar
        or (0x1780 <= cp <= 0x17FF)   # Khmer
    ) and cp != 0xFEFF


def _is_valid_script_joiner(text: str, idx: int) -> bool:
    """Validate whether U+200C (ZWNJ) or U+200D (ZWJ) sits within an authentic script or emoji sequence."""
    if idx <= 0 or idx + 1 >= len(text):
        return False
    prev_ch = text[idx - 1]
    next_ch = text[idx + 1]
    ch = text[idx]
    if ch == "\u200c":
        return _is_complex_script_char(prev_ch) and _is_complex_script_char(next_ch)
    if ch == "\u200d":
        if _is_complex_script_char(prev_ch) and _is_complex_script_char(next_ch):
            return True
        prev_emoji = _is_emoji_base_char(prev_ch) or prev_ch in {"\ufe0e", "\ufe0f", "\U0001f3fb", "\U0001f3fc", "\U0001f3fd", "\U0001f3fe", "\U0001f3ff"}
        next_emoji = _is_emoji_base_char(next_ch)
        return prev_emoji and next_emoji
    return False


def _is_suspicious_invisible_char(text: str, idx: int) -> bool:
    """Distinguish malicious invisible/format obfuscation from legitimate emoji and complex-script joiners."""
    ch = text[idx]
    if ch in {"\ufe0e", "\ufe0f"} and idx > 0:
        prev_ch = text[idx - 1]
        if _is_emoji_base_char(prev_ch):
            return False
        if prev_ch in "0123456789#*" and idx + 1 < len(text) and text[idx + 1] == "\u20e3":
            return False
        return True
    if ch in {"\u200c", "\u200d"}:
        return not _is_valid_script_joiner(text, idx)
    if ZERO_WIDTH_OR_CONTROL_RE.match(ch):
        return True
    if unicodedata.category(ch) == "Cf":
        return True
    return False


def count_fullwidth_ascii_confusables(text: str) -> int:
    """Count fullwidth ASCII Latin compatibility characters (U+FF21..U+FF3A, U+FF41..U+FF5A)."""
    return sum(1 for ch in text if (0xFF21 <= ord(ch) <= 0xFF3A) or (0xFF41 <= ord(ch) <= 0xFF5A))


def detect_obfuscation(text: str) -> Tuple[bool, str, int]:
    """Detect zero-width, invisible, or malicious format chars while sparing emoji selectors."""
    cleaned_chars: List[str] = []
    suspicious_count = 0
    for idx, ch in enumerate(text):
        if _is_suspicious_invisible_char(text, idx):
            suspicious_count += 1
        else:
            cleaned_chars.append(ch)
    cleaned = unicodedata.normalize("NFKC", "".join(cleaned_chars))
    return suspicious_count > 0, cleaned, suspicious_count


def fold_mixed_script_confusables(text: str) -> Tuple[str, int]:
    """Fold Cyrillic/Greek homoglyphs mixed with Latin text; return (folded_text, intra_word_mixed_count)."""
    if not text:
        return text, 0
    has_latin_context = bool(re.search(r"[A-Za-z]", text))
    mixed_count = 0

    def _replace_tok(match: re.Match[str]) -> str:
        nonlocal mixed_count
        tok = match.group(0)
        has_ascii_alpha = any("a" <= ch.lower() <= "z" for ch in tok)
        has_confusable = any(ch in _MIXED_SCRIPT_CONFUSABLE_MAP for ch in tok)
        if not has_confusable:
            return tok
        if has_ascii_alpha:
            confusable_hits = sum(1 for ch in tok if ch in _MIXED_SCRIPT_CONFUSABLE_MAP)
            mixed_count += confusable_hits
            return "".join(_MIXED_SCRIPT_CONFUSABLE_MAP.get(ch, ch) for ch in tok)
        if has_latin_context and all(ch in _MIXED_SCRIPT_CONFUSABLE_MAP for ch in tok):
            return "".join(_MIXED_SCRIPT_CONFUSABLE_MAP[ch] for ch in tok)
        return tok

    folded = _MIXED_SCRIPT_TOKEN_RE.sub(_replace_tok, text)
    return folded, mixed_count


def tokenize_content_words(text: str, include_negations: bool = True) -> List[str]:
    """Extract lowercase content words excluding standard stopwords."""
    normalized = text.lower().replace("'", "")
    tokens = TOKEN_RE.findall(normalized)
    result: List[str] = []
    for tok in tokens:
        if tok in STOPWORDS:
            if include_negations and tok in NEGATION_WORDS:
                result.append(tok)
            continue
        if len(tok) == 1 and not tok.isdigit():
            continue
        result.append(tok)
    return result


_WORD_NUMBERS: dict[str, int] = {
    "once": 1,
    "twice": 2,
    "thrice": 3,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

_PERIOD_SCALES: dict[str, Tuple[str, float]] = {
    "hourly": ("day", 24.0),
    "hour": ("day", 24.0),
    "hours": ("day", 24.0),
    "daily": ("day", 1.0),
    "day": ("day", 1.0),
    "days": ("day", 1.0),
    "weekly": ("week", 1.0),
    "week": ("week", 1.0),
    "weeks": ("week", 1.0),
    "monthly": ("month", 1.0),
    "month": ("month", 1.0),
    "months": ("month", 1.0),
}

_FREQ_MULTIPLIER_RE = re.compile(
    r"\b(?:(once|twice|thrice)|(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+times?)\s+"
    r"(?:(?:a|per|an)\s+)?(day|daily|week|weekly|month|monthly|hour|hourly)\b",
    re.IGNORECASE,
)

_FREQ_EVERY_INTERVAL_RE = re.compile(
    r"\bevery\s+(?:(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+)?(hours?|hrs?|days?|weeks?|months?)\b",
    re.IGNORECASE,
)

_FREQ_ON_BASIS_RE = re.compile(
    r"\bon\s+an?\s+(daily|weekly|monthly|hourly)\s+basis\b",
    re.IGNORECASE,
)

_FREQ_BARE_ADVERB_RE = re.compile(
    r"\b(daily|weekly|monthly|hourly)\b",
    re.IGNORECASE,
)

# Pre-modifiers / determiners before daily/weekly/... indicating a nominal phrase rather than predicate frequency
_FREQ_NOMINAL_PRE_MODS: Set[str] = {
    "a", "an", "the", "this", "that", "these", "those", "my", "your", "our", "his", "her", "its", "their",
    "each", "every", "some", "any", "no", "maximum", "minimum", "max", "min", "recommended", "standard",
    "typical", "total", "average", "current", "usual", "normal", "regular", "new", "initial", "final",
    "target", "safe", "toxic", "optimal", "allowable", "baseline",
}

# Nominal head nouns modified by pre-nominal daily/weekly/monthly/hourly adjectives
_FREQ_NOMINAL_HEADS: Set[str] = {
    "limit", "limits", "plan", "plans", "report", "reports", "testing", "monitoring", "screening",
    "dosing", "dose", "doses", "dosage", "dosages", "intake", "allowance", "cap", "caps",
    "threshold", "thresholds", "schedule", "schedules", "routine", "regimen", "regimens",
    "summary", "summaries", "review", "reviews", "check", "checks", "visit", "visits",
    "assessment", "assessments", "measurement", "measurements", "session", "sessions",
    "audit", "audits", "round", "rounds", "update", "updates", "note", "notes", "log", "logs",
    "record", "records", "rate", "rates", "goal", "goals", "target", "targets", "total",
    "average", "quota", "level", "levels", "protocol", "protocols", "reading", "readings",
    "follow-up", "vitals", "charting", "reporting",
}

_CLAUSE_CONNECTOR_WORDS: Set[str] = {
    "in", "on", "at", "by", "for", "with", "without", "after", "before", "until", "till", "during",
    "under", "over", "since", "unless", "when", "while", "whereas", "although", "though", "if", "as",
    "because", "that", "than", "and", "or", "but", "nor", "to", "from", "into", "across", "throughout",
    "per", "via", "using", "following", "through", "between", "among", "upon", "around", "within",
    "cleanly", "safely", "reliably", "consistently", "independently", "strictly", "only", "instead",
}

_AUX_SPLIT_MARKERS: Set[str] = {
    "is", "are", "was", "were", "be", "been", "being", "has", "have", "had",
    "does", "do", "did", "can", "could", "may", "might", "must", "will", "would", "shall", "should",
}

_PLURAL_COLLECTIVE_SUBJ: Set[str] = {
    "people", "children", "women", "men", "staff", "personnel", "police", "faculty", "data",
}

_PLURAL_NON_VERB_OBJECTS: Set[str] = {
    "vitals", "labs", "levels", "panels", "tablets", "capsules", "pills", "doses", "drops",
    "drugs", "medications", "medicines", "patients", "subjects", "tests", "scans", "charts",
    "logs", "sites", "pumps", "infusions", "foods", "fluids", "symptoms", "records", "results",
    "measurements", "procedures", "sessions", "samples", "checks", "metrics", "orders",
    "relapses", "vessels", "sugars", "days", "weeks", "months", "hours", "times",
    "nurses", "doctors", "physicians", "clinicians", "pharmacists", "surgeons", "adults",
    "therapists", "caregivers", "providers",
}

_DUAL_NOUN_VERB_3SG: Set[str] = {
    "checks", "tests", "scans", "doses", "drops", "orders", "records", "logs", "charts",
    "monitors", "reviews", "reports", "visits", "controls", "triggers", "stops",
}

_STRICT_PLURAL_NON_VERBS: Set[str] = _PLURAL_NON_VERB_OBJECTS - _DUAL_NOUN_VERB_3SG

_SUBJ_PP_PREPS: Set[str] = {
    "on", "in", "at", "with", "of", "for", "from", "by", "under", "during", "after", "before", "without",
}

_NON_BARE_VERB_MODIFIERS: Set[str] = {
    "mild", "severe", "moderate", "chronic", "acute", "daily", "weekly", "monthly", "hourly",
    "high", "low", "higher", "lower", "normal", "abnormal", "empty", "full", "safe", "toxic",
    "good", "bad", "old", "new", "young", "elderly", "adult", "adults", "renal", "hepatic",
    "cardiac", "hospital", "oral", "intravenous", "topical", "primary", "secondary", "standard",
    "blood", "clinical", "medical", "inpatient", "outpatient", "baseline", "total", "average",
    "routine", "regular",
}

_IRREGULAR_PAST_SCHED_VERBS: Set[str] = {
    "took", "gave", "made", "kept", "sent", "held", "led", "fed", "got", "left", "paid",
    "said", "went", "came", "began", "broke", "chose", "drove", "fell", "felt", "found",
    "fled", "grew", "knew", "met", "ran", "saw", "sold", "slept", "spoke", "spent",
    "stood", "struck", "taught", "thought", "told", "wore", "wrote", "won",
    "arose", "ate", "bled", "drank", "drew", "fought", "froze", "lent", "lit", "lost",
    "meant", "overcame", "rose", "shot", "shrank", "shut", "sank", "sat", "slid", "sprang",
    "stole", "stuck", "swam", "swept", "swore", "threw", "tore", "understood", "withdrew", "woke",
}


@dataclass(frozen=True)
class ScheduleAssertion:
    """Structured schedule assertion preserving subject, predicate/action, frequency, period, and local context."""

    rate_per_period: float
    period: str
    raw_phrase: str
    subject_tokens: Set[str]
    action_tokens: Set[str]
    local_context_tokens: Set[str]


def extract_numbers_and_units(text: str) -> List[Tuple[str, str]]:
    """Extract normalized numeric and word-written dosage quantities with optional units."""
    matches_with_pos: List[Tuple[int, str, str]] = []
    for m in NUMBER_UNIT_RE.finditer(text):
        num_str, unit = m.group(1), m.group(2)
        clean_num = num_str.replace(",", "")
        try:
            # Canonical numeric string (e.g., 20.0 -> 20, 4.5 -> 4.5)
            val = float(clean_num)
            norm_num = str(int(val)) if val.is_integer() else f"{val:g}"
        except ValueError:
            norm_num = clean_num
        matches_with_pos.append((m.start(), norm_num, (unit or "").lower()))

    for m in _WORD_DOSAGE_UNIT_RE.finditer(text):
        word_num = m.group(1).lower()
        unit = m.group(2).lower()
        norm_num = str(_WORD_NUMBERS[word_num])
        matches_with_pos.append((m.start(), norm_num, unit))

    matches_with_pos.sort(key=lambda item: item[0])
    return [(num, unit) for _, num, unit in matches_with_pos]


def _is_adverbial_schedule_adverb(text: str, start: int, end: int) -> bool:
    """Return True if bare `daily/weekly/monthly/hourly` modifies a predicate rather than acting as a nominal modifier."""
    prev_words = re.findall(r"[A-Za-z0-9']+", text[:start].lower())
    if prev_words and prev_words[-1] in _FREQ_NOMINAL_PRE_MODS:
        return False

    tail = text[end:]
    if not tail or re.match(r"^\s*(?:$|[,.;:!?)\]])", tail):
        return True

    next_tokens = re.findall(r"^\s*([A-Za-z][A-Za-z0-9\-]*)(?:\s+([A-Za-z][A-Za-z0-9\-]*))?", tail)
    if not next_tokens:
        return True
    w1 = next_tokens[0][0].lower()
    w2 = next_tokens[0][1].lower() if next_tokens[0][1] else ""
    if w1 in _FREQ_NOMINAL_HEADS:
        return False
    if w1 not in _CLAUSE_CONNECTOR_WORDS and w2 in _FREQ_NOMINAL_HEADS:
        return False
    return True


def _is_plural_subject_head(tok_lower: str) -> bool:
    """Return True if token is a plural or collective subject noun or plural pronoun."""
    if tok_lower in _PLURAL_COLLECTIVE_SUBJ or tok_lower in {"they", "we", "you"}:
        return True
    if tok_lower in STOPWORDS:
        return False
    return (
        len(tok_lower) >= 3
        and tok_lower.endswith("s")
        and not tok_lower.endswith(("ss", "us", "is", "as", "os", "ous", "ics"))
    )


_PURE_NOMINAL_FREQ_HEADS: Set[str] = {
    "intake", "regimen", "quota", "protocol", "threshold", "routine",
    "summary", "dosage", "allowance", "follow-up",
}


_NON_BARE_VERB_SUFFIXES: Tuple[str, ...] = (
    "s", "ly", "tion", "sion", "ment", "ness", "ity", "ous", "ful", "less",
    "ing", "al", "ic", "ive", "ary", "ory", "ery", "able", "ible", "ent",
    "ant", "ism", "ist", "dom", "age", "ure", "ship", "hood", "ern", "est",
)


def _looks_like_bare_verb(w: str) -> bool:
    """Return True if token morphology fits an uninflected active verb (not noun/modifier/prep)."""
    wl = w.lower()
    return (
        bool(w)
        and w[0].islower()
        and w.isalpha()
        and len(wl) >= 3
        and wl not in STOPWORDS
        and wl not in _CLAUSE_CONNECTOR_WORDS
        and wl not in _PURE_NOMINAL_FREQ_HEADS
        and wl not in _NON_BARE_VERB_MODIFIERS
        and wl not in _PLURAL_NON_VERB_OBJECTS
        and not wl.endswith(_NON_BARE_VERB_SUFFIXES)
    )


def _split_clause_subject_predicate(clause_prefix: str) -> Tuple[Optional[Set[str]], Set[str]]:
    """Split a clause prefix before a schedule expression into optional clause subject and predicate action tokens."""
    words = re.findall(r"[A-Za-z0-9\-']+", clause_prefix)
    if not words:
        return None, set()

    split_idx: Optional[int] = None
    # Pass 1: Explicit auxiliary/modal verbs
    for idx, w in enumerate(words):
        if idx > 0 and w.lower() in _AUX_SPLIT_MARKERS:
            split_idx = idx
            break

    # Pass 2: Bare active plural verbs following a plural/collective subject (even across PP modifiers like 'on duty')
    if split_idx is None:
        subj_plural_seen = _is_plural_subject_head(words[0].lower())
        pp_start: Optional[int] = None
        pp_expect_obj = False
        for idx in range(1, len(words)):
            w = words[idx]
            wl = w.lower()
            prev_w = words[idx - 1].lower()
            if subj_plural_seen and wl in _SUBJ_PP_PREPS:
                if pp_start is None:
                    pp_start = idx
                pp_expect_obj = True
                continue
            if pp_expect_obj:
                if wl in _NON_BARE_VERB_MODIFIERS or wl in {"the", "a", "an", "this", "these", "their", "its"}:
                    continue
                pp_expect_obj = False
                continue

            if _is_plural_subject_head(prev_w) and _looks_like_bare_verb(w):
                split_idx = idx
                break
            if subj_plural_seen and pp_start is not None and _looks_like_bare_verb(w):
                split_idx = idx
                break
            if _is_plural_subject_head(wl) and not pp_start:
                subj_plural_seen = True

    # Pass 3: Inflected (-ed, valid 3sg -s), productive verb derivations, and core irregular past verbs
    if split_idx is None:
        for idx, w in enumerate(words):
            if idx == 0:
                continue
            wl = w.lower()
            prev_w = words[idx - 1].lower()
            if wl in STOPWORDS or prev_w in {"the", "a", "an", "of", "in", "for", "with", "severe", "mild", "chronic", "acute"}:
                continue
            if not w[0].islower() or not w.isalpha():
                continue

            is_dual_3sg = (
                wl in _DUAL_NOUN_VERB_3SG
                and prev_w not in _NON_BARE_VERB_MODIFIERS
                and prev_w not in {"the", "a", "an", "of", "in", "for", "with", "lab", "blood", "clinical", "medical"}
                and idx + 1 < len(words)
                and words[idx + 1].lower() not in _CLAUSE_CONNECTOR_WORDS
            )
            is_inflected_verb = (
                (len(wl) >= 4 and wl.endswith("ed"))
                or is_dual_3sg
                or (
                    len(wl) >= 4
                    and wl.endswith("s")
                    and wl not in _PLURAL_NON_VERB_OBJECTS
                    and wl not in _STRICT_PLURAL_NON_VERBS
                    and not (idx + 1 < len(words) and words[idx + 1].lower() in _SUBJ_PP_PREPS)
                    and not wl.endswith(("ss", "us", "is", "as", "os", "ous", "ics", "ness", "ions", "ments", "ings", "ties", "als", "els", "ols", "ils"))
                )
                or (len(wl) >= 5 and wl.endswith(("ize", "ise", "ify")))
                or (wl in _IRREGULAR_PAST_SCHED_VERBS)
            )
            if is_inflected_verb:
                split_idx = idx
                break

    # Pass 4: Structural SVO fallback for determiner + singular actor + unseen irregular/bare verb + object
    if split_idx is None and len(words) >= 4 and words[0].lower() in {"the", "a", "an", "this", "each", "every"}:
        for idx in range(2, len(words) - 1):
            w = words[idx]
            prev_w = words[idx - 1].lower()
            nxt_w = words[idx + 1].lower()
            if (
                prev_w not in _NON_BARE_VERB_MODIFIERS
                and prev_w not in STOPWORDS
                and _looks_like_bare_verb(w)
                and nxt_w not in _CLAUSE_CONNECTOR_WORDS
                and nxt_w not in _AUX_SPLIT_MARKERS
            ):
                split_idx = idx
                break

    if split_idx is not None:
        # Exclude trailing post-nominal prepositional modifiers (e.g., "on duty") from core subject_tokens
        # when pre-PP content exists so unrelated subjects ("Doctors on duty" vs "Nurses on duty") stay disjoint.
        core_end = split_idx
        for j in range(1, split_idx):
            if words[j].lower() in {"on", "in", "at", "with", "under", "during", "after", "before", "for"}:
                pre_pp_toks = tokenize_content_words(" ".join(words[:j]), include_negations=False)
                if pre_pp_toks:
                    core_end = j
                    break
        subj_txt = " ".join(words[:core_end])
        act_txt = " ".join(words[split_idx:])
        subj_toks = {t for t in tokenize_content_words(subj_txt, include_negations=False) if not t.isdigit()}
        act_toks = {t for t in tokenize_content_words(act_txt, include_negations=False) if not t.isdigit()}
        if subj_toks:
            return subj_toks, act_toks

    all_toks = {t for t in tokenize_content_words(clause_prefix, include_negations=False) if not t.isdigit()}
    return None, all_toks


def _extract_schedule_components(
    text: str,
    start: int,
    end: int,
    prior_subject: Optional[Set[str]] = None,
) -> Tuple[Set[str], Set[str], Set[str]]:
    """Extract (subject_tokens, action_tokens, local_context_tokens) for a schedule span at [start:end]."""
    clause_breaks = [
        m.end()
        for m in re.finditer(r"[,.;]|\b(?:and|or|but|while|whereas|although|though)\b", text[:start], re.IGNORECASE)
    ]
    left_bound = clause_breaks[-1] if clause_breaks else 0

    right_match = re.search(r"[,.;]|\b(?:and|or|but|while|whereas|although|though)\b", text[end:], re.IGNORECASE)
    right_bound = end + right_match.start() if right_match else len(text)

    pre_txt = text[left_bound:start]
    post_txt = text[end:right_bound]

    clause_subj, pre_act = _split_clause_subject_predicate(pre_txt)
    crossed_semicolon = left_bound > 0 and ";" in text[max(0, left_bound - 2) : left_bound]
    if clause_subj is not None:
        subj_toks = clause_subj
    elif left_bound > 0 and prior_subject and not crossed_semicolon:
        subj_toks = set(prior_subject)
    else:
        # Derive sentence-level subject up to the earliest clause delimiter if clause itself omitted a clear marker
        first_pre = text[: clause_breaks[0]] if clause_breaks else text[:start]
        sent_subj, _ = _split_clause_subject_predicate(first_pre)
        subj_toks = sent_subj or set()

    post_toks = {t for t in tokenize_content_words(post_txt, include_negations=False) if not t.isdigit()}
    action_toks = pre_act if pre_act else post_toks
    local_ctx = subj_toks | pre_act | post_toks
    return subj_toks, action_toks, local_ctx


def _extract_local_schedule_context(text: str, start: int, end: int) -> Set[str]:
    """Extract content words from the immediate sub-clause containing a frequency match."""
    _, _, local_ctx = _extract_schedule_components(text, start, end)
    return local_ctx


def extract_schedule_assertions(text: str) -> List[ScheduleAssertion]:
    """Extract canonical schedule assertions preserving subject, predicate/action, rate, period, and local context."""
    if not text or not text.strip():
        return []

    found: List[Tuple[int, int, float, str, str]] = []

    def _overlaps(s: int, e: int) -> bool:
        return any(not (e <= fs or s >= fe) for fs, fe, _, _, _ in found)

    for m in _FREQ_MULTIPLIER_RE.finditer(text):
        word_mult, num_mult, raw_period = m.group(1), m.group(2), m.group(3).lower()
        key = (word_mult or num_mult).lower()
        count = float(_WORD_NUMBERS[key]) if key in _WORD_NUMBERS else float(key)
        base_period, scale = _PERIOD_SCALES[raw_period]
        found.append((m.start(), m.end(), round(count * scale, 4), base_period, m.group(0)))

    for m in _FREQ_EVERY_INTERVAL_RE.finditer(text):
        if _overlaps(m.start(), m.end()):
            continue
        raw_interval, raw_unit = m.group(1), m.group(2).lower()
        unit_norm = "hour" if raw_unit.startswith("hr") or raw_unit.startswith("hour") else raw_unit.rstrip("s")
        interval = 1.0
        if raw_interval:
            k = raw_interval.lower()
            interval = float(_WORD_NUMBERS[k]) if k in _WORD_NUMBERS else float(k)
        if interval <= 0.0:
            continue
        if unit_norm == "hour":
            found.append((m.start(), m.end(), round(24.0 / interval, 4), "day", m.group(0)))
        else:
            found.append((m.start(), m.end(), round(1.0 / interval, 4), unit_norm, m.group(0)))

    for m in _FREQ_ON_BASIS_RE.finditer(text):
        if _overlaps(m.start(), m.end()):
            continue
        adv = m.group(1).lower()
        base_period, rate = _PERIOD_SCALES[adv]
        found.append((m.start(), m.end(), round(rate, 4), base_period, m.group(0)))

    for m in _FREQ_BARE_ADVERB_RE.finditer(text):
        s, e = m.start(1), m.end(1)
        if _overlaps(s, e):
            continue
        if not _is_adverbial_schedule_adverb(text, s, e):
            continue
        adv = m.group(1).lower()
        base_period, rate = _PERIOD_SCALES[adv]
        # Preserve strictly the adverb span so preceding units/verbs remain intact for numeric extraction
        found.append((s, e, round(rate, 4), base_period, m.group(1)))

    found.sort(key=lambda item: item[0])
    assertions: List[ScheduleAssertion] = []
    last_subj: Optional[Set[str]] = None
    for s, e, rate, period, phrase in found:
        subj_toks, act_toks, local_ctx = _extract_schedule_components(text, s, e, prior_subject=last_subj)
        if subj_toks:
            last_subj = subj_toks
        assertions.append(
            ScheduleAssertion(
                rate_per_period=rate,
                period=period,
                raw_phrase=phrase,
                subject_tokens=subj_toks,
                action_tokens=act_toks,
                local_context_tokens=local_ctx,
            )
        )
    return assertions


def extract_frequency_expressions_with_context(text: str) -> List[Tuple[float, str, str, Set[str]]]:
    """Extract canonical schedule frequencies with local action/subject context tokens.

    Returns `(rate_per_period, period, raw_phrase, local_context_tokens)`.
    """
    return [
        (sa.rate_per_period, sa.period, sa.raw_phrase, sa.local_context_tokens)
        for sa in extract_schedule_assertions(text)
    ]


def extract_frequency_expressions(text: str) -> List[Tuple[float, str, str]]:
    """Extract canonical dosage/schedule frequency expressions as (rate_per_period, period, raw_phrase).

    Normalizes day/hour intervals onto 'day' while preserving week/month periods, generalizing
    schedule adverbs across clinical predicates while rejecting nominal modifiers such as
    'maximum daily limit' or 'daily monitoring plan'.
    """
    return [
        (sa.rate_per_period, sa.period, sa.raw_phrase)
        for sa in extract_schedule_assertions(text)
    ]


def split_sentences(text: str) -> List[str]:
    """Split text into clean, non-empty sentences/clauses for verification and extraction."""
    if not text or not text.strip():
        return []
    # Remove bracketed citation tags like [doc_1] before splitting claims if isolated
    segments: List[str] = []
    for raw_line in text.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        # Split on sentence-ending punctuation followed by whitespace or end
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\[\(\"'])", line)
        for p in parts:
            cleaned = p.strip()
            if cleaned:
                segments.append(cleaned)
    return segments


def strip_citations(text: str) -> str:
    """Remove trailing inline bracket citations such as `[doc_001]`."""
    return re.sub(r"\s*\[[^\]]+\]", "", text).strip()


def has_negation_cue(text: str) -> bool:
    """Return True if text contains explicit negation or refutation markers."""
    tokens = set(TOKEN_RE.findall(text.lower().replace("'", "")))
    return bool(tokens & NEGATION_WORDS)


def has_strict_negation(text: str) -> bool:
    """Return True if text contains strict clause-level negation markers."""
    tokens = set(TOKEN_RE.findall(text.lower().replace("'", "")))
    return bool(tokens & STRICT_CONTRADICTION_NEGATIONS)


def compute_lexical_overlap(text_a: str, text_b: str) -> float:
    """Compute asymmetric or symmetric content-word overlap ratio in [0.0, 1.0]."""
    toks_a = set(tokenize_content_words(text_a, include_negations=False))
    toks_b = set(tokenize_content_words(text_b, include_negations=False))
    if not toks_a or not toks_b:
        return 0.0
    union = toks_a | toks_b
    return len(toks_a & toks_b) / len(union)


def compute_tfidf_similarities(query: str, documents: Sequence[str]) -> List[float]:
    """Compute TF-IDF cosine similarity between query and each document in [0.0, 1.0].

    Falls back gracefully to content-token overlap when TF-IDF vocabulary is empty.
    """
    if not documents:
        return []
    if not query.strip():
        return [0.0] * len(documents)

    corpus = [query] + [doc if doc.strip() else "empty_placeholder" for doc in documents]
    try:
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b[a-zA-Z0-9][a-zA-Z0-9\-]*\b",
        )
        matrix = vectorizer.fit_transform(corpus)
        q_vec = matrix[0:1]
        d_vecs = matrix[1:]
        sims = cosine_similarity(q_vec, d_vecs).flatten()
        scores = [float(np.clip(s, 0.0, 1.0)) for s in sims]
        # If TF-IDF yielded all zeros due to stopword-only tokens, supplement with Jaccard overlap
        if all(s == 0.0 for s in scores):
            return [compute_lexical_overlap(query, doc) for doc in documents]
        return scores
    except ValueError:
        return [compute_lexical_overlap(query, doc) for doc in documents]


def match_threat_patterns(
    text: str,
    *,
    target: str = "query",
) -> List[Tuple[ThreatPatternSpec, str]]:
    """Run shared parameterized threat rules against query or document text."""
    findings: List[Tuple[ThreatPatternSpec, str]] = []
    for spec in SHARED_THREAT_PATTERNS:
        if target == "query" and not spec.apply_to_query:
            continue
        if target == "document" and not spec.apply_to_document:
            continue
        m = spec.pattern.search(text)
        if m:
            findings.append((spec, m.group(0)[:120]))
    return findings


def check_repetitive_flood(text: str, min_repeats: int = 8) -> Tuple[bool, str]:
    """Detect token-flooding DoS repetition patterns (e.g., repeating a word many times)."""
    words = re.findall(r"\b\w+\b", text.lower())
    if len(words) < min_repeats:
        return False, ""
    streak = 1
    for i in range(1, len(words)):
        if words[i] == words[i - 1]:
            streak += 1
            if streak >= min_repeats:
                return True, f"token '{words[i]}' repeated {streak}+ consecutive times"
        else:
            streak = 1
    return False, ""


__all__ = [
    "STOPWORDS",
    "NEGATION_WORDS",
    "STRICT_CONTRADICTION_NEGATIONS",
    "ThreatPatternSpec",
    "SHARED_THREAT_PATTERNS",
    "detect_obfuscation",
    "fold_mixed_script_confusables",
    "count_fullwidth_ascii_confusables",
    "tokenize_content_words",
    "extract_numbers_and_units",
    "ScheduleAssertion",
    "extract_schedule_assertions",
    "extract_frequency_expressions",
    "extract_frequency_expressions_with_context",
    "split_sentences",
    "strip_citations",
    "has_negation_cue",
    "has_strict_negation",
    "compute_lexical_overlap",
    "compute_tfidf_similarities",
    "match_threat_patterns",
    "check_repetitive_flood",
]
