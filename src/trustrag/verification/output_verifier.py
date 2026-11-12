"""G3: Output Evidence Verification for TrustRAG.

Performs atomic claim-level grounding of generated answers against retrieved evidence:
1. Extracts independently verifiable factual claims while filtering conversational greetings,
   questions, meta-refusals, and subjective opinion statements.
2. Precomputes evidence span representations once per verification pass (reusing TF-IDF or an
   optional caller-supplied embedding callable without redundant repeated model calls).
3. Verifies polarity, semantic antonym alignment, unit/dimension-aware numeric & dosage bounds,
   non-initial named entities, and claim-side lexical coverage (never marking SUPPORTED from
   keyword or cosine similarity alone).
4. Emits canonical Step 4 claim verdicts (`SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT`,
   `UNCERTAIN`) and answer verdicts (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTED`,
   `INSUFFICIENT_EVIDENCE`, `UNCERTAIN`) alongside backwards-compatible `EvidenceOutcome` and
   `VerificationStatus` values.

Limitation note: Evidence alignment verifies whether candidate claims are grounded in retrieved
passages; it does not establish external real-world truth if the underlying corpus itself is wrong
or incomplete.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from trustrag.config.engine_config import VerificationConfig
from trustrag.engine.schemas import (
    ClaimVerificationItem,
    EvidenceDocument,
    EvidenceOutcome,
    EvidenceReference,
    G3AnswerVerdict,
    G3ClaimVerdict,
    G3VerificationReport,
    VerificationStatus,
)
from trustrag.engine.text_utils import (
    STOPWORDS,
    ScheduleAssertion,
    compute_lexical_overlap,
    extract_numbers_and_units,
    extract_schedule_assertions,
    has_strict_negation,
    split_sentences,
    strip_citations,
    tokenize_content_words,
)
from trustrag.utils.logging import get_logger

LOGGER = get_logger(__name__)

_ANTONYM_PAIRS: Tuple[Tuple[Set[str], Set[str]], ...] = (
    (
        {"confirmed", "verified", "detected", "present", "true", "raised", "effective", "safe"},
        {"refuted", "disproved", "dissolved", "zero", "false", "denied", "ineffective", "absent", "unsafe"},
    ),
    (
        {"infeasible", "impossible", "secure", "resistant", "allowed", "recommended", "permitted", "allow", "allows", "permit", "permits"},
        {"vulnerable", "broken", "backdoor", "feasible", "lethal", "overdose", "toxic", "prohibited", "prohibit", "prohibits", "forbidden", "forbid", "forbids", "banned", "ban", "bans"},
    ),
    (
        {"approved", "approve", "approves", "authorized", "authorize", "authorizes"},
        {"rejected", "reject", "rejects", "disapproved", "disapprove", "disapproves"},
    ),
    (
        {"accepted", "accept", "accepts"},
        {"denied", "deny", "denies", "rejected", "reject", "rejects"},
    ),
    (
        {"took", "take", "takes", "taken"},
        {"avoided", "avoid", "avoids", "skipped", "skip", "skips"},
    ),
    (
        {"received", "receive", "receives"},
        {"refused", "refuse", "refuses", "declined", "decline", "declines"},
    ),
    (
        {"increased", "increase", "increases"},
        {"decreased", "decrease", "decreases"},
    ),
)

# Physical unit conversion factors to canonical base units within same physical dimension
_UNIT_DIMENSIONS: Dict[str, Tuple[str, float]] = {
    "ug": ("mass", 1e-3),
    "mcg": ("mass", 1e-3),
    "mg": ("mass", 1.0),
    "g": ("mass", 1e3),
    "kg": ("mass", 1e6),
    "ml": ("volume", 1.0),
    "l": ("volume", 1e3),
    "sec": ("time", 1.0),
    "secs": ("time", 1.0),
    "second": ("time", 1.0),
    "seconds": ("time", 1.0),
    "min": ("time", 60.0),
    "mins": ("time", 60.0),
    "minute": ("time", 60.0),
    "minutes": ("time", 60.0),
    "hr": ("time", 3600.0),
    "hrs": ("time", 3600.0),
    "hour": ("time", 3600.0),
    "hours": ("time", 3600.0),
    "day": ("time", 86400.0),
    "days": ("time", 86400.0),
    "week": ("time", 604800.0),
    "weeks": ("time", 604800.0),
    "month": ("time", 2592000.0),
    "months": ("time", 2592000.0),
    "year": ("time", 31536000.0),
    "years": ("time", 31536000.0),
    "bit": ("data", 1.0),
    "bits": ("data", 1.0),
    "byte": ("data", 8.0),
    "bytes": ("data", 8.0),
    "kb": ("data", 8192.0),
    "mb": ("data", 8388608.0),
    "gb": ("data", 8589934592.0),
    "tb": ("data", 8796093022208.0),
    "%": ("ratio", 1.0),
    "percent": ("ratio", 1.0),
    "iu": ("iu", 1.0),
    "tablet": ("dosage_tablet", 1.0),
    "tablets": ("dosage_tablet", 1.0),
    "capsule": ("dosage_capsule", 1.0),
    "capsules": ("dosage_capsule", 1.0),
    "pill": ("dosage_pill", 1.0),
    "pills": ("dosage_pill", 1.0),
    "dose": ("dosage_dose", 1.0),
    "doses": ("dosage_dose", 1.0),
    "drop": ("dosage_drop", 1.0),
    "drops": ("dosage_drop", 1.0),
    "puff": ("dosage_puff", 1.0),
    "puffs": ("dosage_puff", 1.0),
    "injection": ("dosage_injection", 1.0),
    "injections": ("dosage_injection", 1.0),
    "teaspoon": ("dosage_teaspoon", 1.0),
    "teaspoons": ("dosage_teaspoon", 1.0),
    "tablespoon": ("dosage_tablespoon", 1.0),
    "tablespoons": ("dosage_tablespoon", 1.0),
    "c": ("temp_c", 1.0),
    "f": ("temp_f", 1.0),
    "bp": ("pressure", 1.0),
    "bps": ("rate", 1.0),
}

_AUX_MODAL_VERBS_SET: Set[str] = {
    "is", "are", "was", "were", "be", "been", "being", "has", "have", "had",
    "does", "do", "did", "can", "cannot", "can't", "may", "might", "must",
    "will", "would", "shall", "should", "could", "won't", "doesn't", "don't",
    "didn't", "isn't", "aren't", "wasn't", "weren't",
}
_SINGULAR_AUX_VERBS: Set[str] = {"is", "was", "has", "does"}
_PLURAL_AUX_VERBS: Set[str] = {"are", "were", "have", "do"}
_MODALS_OR_PLURAL_BARE_AUX: Set[str] = {
    "are", "were", "have", "do", "does", "did", "can", "cannot", "can't",
    "could", "may", "might", "must", "shall", "should", "will", "would",
    "don't", "doesn't", "didn't", "won't",
}

_NON_VERB_DERIV_SUFFIXES: Tuple[str, ...] = (
    "tion", "sion", "ment", "ness", "ity", "ities", "ance", "ence", "ances", "ences",
    "logy", "sis", "ia", "um", "oma", "itis", "osis", "ism", "ist", "able", "ible",
    "ful", "less", "ous", "ious", "eous", "ish", "ary", "ory", "ery", "ing", "al",
    "ic", "ive", "ent", "ant", "ship", "hood", "ward", "wise", "ly", "age", "ure",
    "dom", "id", "ern", "est", "fold",
)

_LEADING_PREDICATE_ADVERBS: Set[str] = {
    "safely", "cleanly", "effectively", "often", "usually", "also", "always", "never",
    "rarely", "frequently", "sometimes", "generally", "typically", "primarily", "mainly",
    "significantly", "substantially", "dramatically", "directly", "indirectly", "rapidly",
    "quickly", "steadily", "slowly", "gradually", "consistently", "reliably",
    "independently", "temporarily", "permanently", "completely", "partially", "only",
    "merely", "simply", "not", "evenly",
}

_NP_PRECEDING_MARKERS: Set[str] = {
    "the", "a", "an", "this", "these", "those", "every", "each", "some", "any", "no",
    "my", "your", "our", "his", "her", "its", "their", "one", "two", "three", "four",
    "five", "six", "seven", "eight", "nine", "ten", "in", "on", "at", "by", "for",
    "of", "from", "into", "onto", "with", "without", "under", "over", "during", "within",
    "between", "among", "across", "against", "toward", "towards", "per", "via",
    "severe", "mild", "moderate", "chronic", "acute", "urban", "rural", "healthy",
    "pregnant", "elderly", "pediatric", "geriatric", "common", "rare", "high", "low",
    "empty", "full", "dry", "wet", "oral", "intravenous", "topical", "human",
    "primary", "secondary", "daily", "weekly", "monthly", "hourly",
}

_NON_VERB_WORDS: Set[str] = (STOPWORDS - _AUX_MODAL_VERBS_SET) | {
    "not", "no", "never", "even", "odd", "mild", "severe", "moderate", "chronic", "acute",
    "urban", "rural", "healthy", "pregnant", "pediatric", "geriatric", "elderly",
    "adult", "adults", "child", "children", "patient", "patients", "doctor", "doctors",
    "clinician", "clinicians", "nurse", "nurses", "people", "person", "persons",
    "individual", "individuals", "infant", "infants", "adolescent", "adolescents",
    "human", "humans", "male", "female", "high", "low", "higher", "normal", "abnormal",
    "common", "rare", "empty", "full", "true", "false", "able", "unable", "likely", "unlikely",
    "same", "different", "other", "another", "every", "each", "all", "both", "many", "most",
    "some", "several", "few", "more", "less", "very", "quite", "rather", "almost", "nearly",
    "however", "therefore", "moreover", "furthermore", "meanwhile", "otherwise", "unless",
    "except", "although", "though", "because", "since", "until", "till", "whereas", "while",
    "within", "without", "between", "among", "through", "throughout", "across", "against",
    "toward", "towards", "about", "around", "near", "per", "via", "versus", "vs",
    "daily", "weekly", "monthly", "hourly", "annual", "blood", "heart", "chest", "oxygen",
    "muscle", "joint", "skin", "nerve", "liver", "kidney", "fever", "cough", "fatigue",
    "nausea", "headache", "headaches", "fevers", "coughs", "allergies", "strokes", "clots",
    "wounds", "burns", "rashes", "ulcers", "tumors", "symptoms", "effects", "outcomes",
    "results", "findings", "studies", "trials", "cases", "risks", "rates", "levels",
    "values", "cells", "organs", "tissues", "muscles", "joints", "bones", "nerves",
    "vessels", "drugs", "medicines", "medications", "tablets", "capsules", "pills",
    "doses", "drops", "puffs", "years", "months", "weeks", "days", "hours", "minutes",
    "seconds", "substances", "instances", "distances", "differences", "consequences",
    "circumstances", "resistances", "evidences", "events", "agents", "clients", "parents",
    "students", "nutrients", "ingredients", "variants", "participants", "antioxidants",
    "stimulants", "anticoagulants", "consultants", "receptors", "factors", "actors",
    "sectors", "vectors", "sensors", "responders", "researchers", "caregivers",
    "prescribers", "providers", "practitioners", "observers", "reviewers", "survivors",
    "workers", "binders", "markers", "blockers", "inhibitors", "agonists",
    "sore", "dry", "sharp", "dull", "stiff", "weak", "strong", "soft", "loud", "hard",
    "fast", "new", "old", "good", "bad", "poor", "rich", "young", "long", "short",
    "early", "late", "real", "pure", "fresh", "toxic", "fatal", "lethal", "banned",
    "safe", "unsafe", "stable", "unstable", "ill", "sick", "well",
    "extreme", "blurred", "blurry", "persistent", "recurrent", "constant", "occasional",
    "intermittent", "excessive", "abdominal", "sudden", "visual", "dizzy", "minor",
    "major", "total", "entire", "complete", "upper", "lower", "inner", "outer",
    "central", "bilateral",
    "red", "bed", "shed", "hundred", "wicked", "naked", "sacred", "beloved", "wretched",
    "crooked", "jagged", "aged", "etc",
} | _LEADING_PREDICATE_ADVERBS

_NOUN_ONLY_PLURAL_SUFFIXES: Tuple[str, ...] = (
    "ss", "us", "is", "as", "os", "ous", "ics", "ness", "less", "ish", "ism", "ist",
    "ions", "ments", "ings", "ships", "hoods", "wards", "ities", "gies", "pies", "cies",
    "mies", "ables", "ibles", "ologists", "alists", "apists", "icists", "acists", "entists",
)

_ADJ_NOUN_ATE_EXCLUDE: Set[str] = {
    "accurate", "adequate", "appropriate", "approximate", "certificate", "chocolate",
    "climate", "candidate", "delicate", "desperate", "elaborate", "fortunate", "immediate",
    "intimate", "lactate", "legitimate", "mandate", "moderate", "nitrate", "phosphate",
    "private", "rate", "separate", "state", "sulfate", "carbonate", "ultimate", "date",
}

_CORE_BASE_OR_IRREGULAR_VERBS: Set[str] = {
    "act", "add", "affect", "aid", "allow", "alter", "appear", "apply", "approve", "avoid",
    "bake", "become", "became", "begin", "began", "bind", "block", "boost", "break", "broke",
    "bring", "brought", "build", "built", "burn", "calm", "carry", "cause", "check", "choose",
    "chose", "clean", "clear", "combine", "come", "came", "confirm", "contain", "control",
    "convert", "cost", "cover", "cure", "curb", "cut", "damage", "decrease", "deliver", "deny",
    "depend", "develop", "digest", "dissolve", "drain", "draw", "drew", "drink", "drank",
    "drive", "drove", "drop", "eat", "ate", "enable", "enforce", "enhance", "ensure", "enter",
    "exceed", "exist", "extend", "fail", "fall", "fell", "feed", "fed", "feel", "felt",
    "fight", "fought", "filter", "find", "found", "fit", "fix", "flow", "follow", "form",
    "gain", "gave", "give", "go", "went", "got", "get", "grow", "grew", "halt", "harm",
    "heal", "help", "hit", "hold", "held", "host", "hurt", "improve", "include", "increase",
    "inhibit", "injure", "keep", "kept", "kill", "know", "knew", "last", "lead", "led",
    "learn", "leave", "left", "let", "limit", "link", "live", "lose", "lost", "lower",
    "maintain", "make", "made", "manage", "mask", "mean", "meant", "measure", "meet", "met",
    "mix", "monitor", "move", "need", "occur", "open", "pass", "pay", "paid", "perform",
    "persist", "place", "play", "present", "prevent", "produce", "prohibit", "promote",
    "protect", "prove", "provide", "pull", "push", "put", "raise", "ran", "run", "reach",
    "react", "read", "receive", "recover", "reduce", "reflect", "refuse", "reject", "relieve",
    "rely", "remain", "remove", "repair", "replace", "report", "require", "resolve", "respond",
    "rest", "restore", "restrict", "retain", "return", "reveal", "review", "rise", "rose",
    "risk", "save", "say", "said", "scan", "see", "saw", "seek", "seem", "select", "send",
    "sent", "serve", "set", "show", "shrink", "shrank", "shut", "sleep", "slept", "slow",
    "solve", "speak", "spoke", "spend", "spent", "split", "spread", "stand", "stood", "start",
    "stay", "stem", "stop", "store", "strike", "struck", "study", "suffer", "suggest",
    "supply", "support", "suppress", "survive", "sustain", "take", "took", "target", "teach",
    "taught", "tell", "told", "tend", "test", "think", "thought", "throw", "threw", "track",
    "train", "transfer", "transport", "travel", "treat", "trigger", "try", "turn", "use",
    "vary", "verify", "visit", "wait", "walk", "want", "warn", "watch", "wear", "wore",
    "weigh", "win", "won", "work", "worry", "write", "wrote", "yield",
}

_LEADING_PRONOUN_SUBJECT_RE = re.compile(
    r"^\s*(?:it|they|he|she|we|you|there|this|that|these|those)\b",
    re.IGNORECASE,
)

_NON_FACTUAL_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(
        r"^\s*(?:hi|hello|hey|greetings|good\s+(?:morning|afternoon|evening)|thanks?|thank\s+you|"
        r"you(?:'re|\s+are)\s+welcome|hope\s+(?:this|that)\s+helps|let\s+me\s+know|please\s+(?:ask|let\s+me)|"
        r"feel\s+free\s+to|happy\s+to\s+help|glad\s+to\s+help|have\s+a\s+(?:great|nice|good)\s+day)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(?:in\s+my\s+(?:opinion|view)|personally,?|i\s+(?:think|believe|feel|suppose|guess|prefer|love|like|hate)|"
        r"it\s+seems\s+to\s+me|from\s+my\s+perspective)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(?:sure,?\s+here\s+is|here\s+is\s+(?:the|an?)\s+(?:answer|summary|overview)|below\s+is\s+the\s+information)\b[:\s]*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(?:insufficient\s+(?:trusted\s+evidence|verifiable\s+claims)|request\s+blocked\s+by\s+g1)\b",
        re.IGNORECASE,
    ),
)

_COMPOUND_CLAUSE_SPLIT_RE = re.compile(
    r",\s+(?:and|but|or|nor|yet|while|whereas)\s+|\s+(?:while|whereas|nor|yet)\s+",
    re.IGNORECASE,
)
_CAUSAL_COMPARATIVE_SPLIT_RE = re.compile(
    r",?\s+\b(?:because|due\s+to|owing\s+to)\b\s+|,?\s+\b(?:more|less|fewer|greater|higher|lower|faster|slower|better|worse|stronger|weaker|longer|shorter|earlier|later|safer)\s+(?:[A-Za-z\-]+\s+){0,2}?\bthan\b\s+",
    re.IGNORECASE,
)
_CONCESSIVE_SPLIT_RE = re.compile(
    r"^\s*(?:although|even\s+though|though)\s+([^,]+),\s*(.+)$",
    re.IGNORECASE,
)

# Restrictive scope and qualifier verification patterns (HIGH-01)
_UNIVERSAL_QUANTIFIER_RE = re.compile(
    r"\b(everyone|everybody|anyone|anybody|always|all\s+(?:patients|people|individuals|adults|children|users))\b",
    re.IGNORECASE,
)
_RESTRICTIVE_SCOPE_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:unless|except(?:\s+(?:for|when|in|if))?|only\s+(?:if|when|after|before|until|within|during|for|in|by|with)|provided\s+(?:that)?|excluding|contraindicated\s+(?:for|in))\s+[^.;]+",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bunder\s+(?:medical|clinical|doctor(?:'s)?|physician(?:'s)?)\s+supervision\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:aged?\s+\d+[^,;.]*|(?:older|younger)\s+than\s+\d+(?:\s+years?)?|(?:under|over)\s+(?:age\s+)?\d+\s+years?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:in|for)\s+(?:the\s+)?(?:(?:healthy|severe|mild|moderate|pregnant|elderly|pediatric|geriatric|adult|adults|children|child|infants?|neonatal|adolescents?|male|female|smokers?)\s+){0,2}"
        r"(?:adults?|children|patients?|elderly|infants?|pregnant\s+women|adolescents?)(?:\s+(?:aged|with)\s+[^.;,]+)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwith\s+(?:(?:severe|mild|moderate|chronic|acute|type\s+\d+)\s+){0,2}"
        r"(?:(?:renal|hepatic|liver|kidney|cardiac|heart|stomach|gastric|peptic)\s+)?"
        r"(?:impairment|disease|failure|ulcers?|diabetes|hypertension|allergy|allergies|insufficiency|cancer|infection|asthma|pregnancy)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:on\s+an\s+empty\s+stomach|with\s+food|after\s+meals|without\s+food|before\s+bedtime)\b",
        re.IGNORECASE,
    ),
)
_SCOPE_NON_DEFINING_WORDS: Set[str] = {
    "in", "for", "with", "under", "aged", "age", "older", "than", "unless", "except",
    "only", "if", "provided", "that", "patient", "patients", "when", "the", "and", "or", "on", "an",
}

# Coordinated VP split for shared-subject compound predicates (including or, nor, yet, as well as, while)
_VP_CONJUNCTION_RE = re.compile(
    r",\s*as\s+well\s+as\s+|\s+as\s+well\s+as\s+|,\s*(?:and|but|or|nor|yet)\s+|,\s*while\s+|,\s+|\s+(?:and|but|or|nor|yet|while)\s+",
    re.IGNORECASE,
)
_NOMINAL_ING_NOUNS: Set[str] = {
    "bleeding", "swelling", "itching", "morning", "evening", "warning", "feeling",
    "meaning", "finding", "testing", "monitoring", "screening", "dosing", "fasting",
    "imaging", "scarring", "bruising", "vomiting", "coughing", "sneezing", "wheezing",
    "tingling", "numbness", "training", "reading", "writing", "setting", "lighting",
    "thing", "something", "nothing", "anything", "everything",
}

# Identifying copula and role-attribution slot checks (MEDIUM-01)
_SLOT_RELATION_RE = re.compile(
    r"^(.{2,}?)\s+\b(?:is|was|are|were|serves\s+as|acts\s+as|remains|became)\s+(?:the\s+|an?\s+)?(.{2,})$",
    re.IGNORECASE,
)
_ENTITY_SLOT_LIST_CUE_RE = re.compile(
    r"\b(?:and|or|including|such\s+as|examples?|between|several|multiple|many)\b",
    re.IGNORECASE,
)
_PRONOUN_AMBIGUITY_START_RE = re.compile(
    r"^\s*(?:it|they|he|she)\b|^\s*(?:this|that|these|those)\s+"
    r"(?:is|are|was|were|can|may|might|will|has|have|had|improves?|causes?|reduces?|shows?|means?|indicates?)\b",
    re.IGNORECASE,
)
_EXCLUDED_UPPER_ACRONYMS: Set[str] = {
    "THE", "AND", "NOT", "FOR", "ARE", "BUT", "ALL", "YOU", "CAN",
    "IN", "ON", "AT", "BY", "TO", "OF", "OR", "AN", "AS", "IS", "IT",
    "IF", "WE", "HE", "ME", "MY", "NO", "SO", "UP", "DO", "GO", "AM", "BE", "VS",
}
_COMMON_INITIAL_NON_PROPER_WORDS: Set[str] = {
    "the", "a", "an", "this", "that", "these", "those", "it", "they", "he", "she", "we", "you", "there",
    "in", "on", "at", "by", "for", "with", "under", "over", "after", "before", "from", "into",
    "although", "though", "because", "since", "unless", "until", "while", "whereas", "however",
    "therefore", "moreover", "furthermore", "additionally", "meanwhile", "otherwise", "generally",
    "usually", "often", "sometimes", "always", "never", "everyone", "everybody", "anyone", "anybody",
    "someone", "nobody", "each", "every", "both", "many", "most", "some", "several", "few", "all", "no",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "first", "second", "third",
    "adult", "adults", "child", "children", "elderly", "patient", "patients", "person", "people",
    "individual", "individuals", "human", "humans", "clinician", "clinicians", "doctor", "doctors",
    "physician", "physicians", "nurse", "nurses", "scientist", "scientists", "researcher", "researchers",
    "study", "studies", "research", "trial", "trials", "evidence", "data", "results", "findings",
    "water", "air", "blood", "heart", "cells", "cell", "medicine", "medicines", "medication", "medications",
    "drug", "drugs", "treatment", "treatments", "therapy", "therapies", "anticoagulation",
    "vaccine", "vaccines", "antibiotic", "antibiotics", "bacteria", "virus", "viruses",
    "standard", "regular", "daily", "weekly", "monthly", "hourly", "modern", "recent", "early", "late",
    "high", "low", "severe", "mild", "moderate", "chronic", "acute", "healthy", "pregnant", "quantum",
    "photosynthesis", "boiling", "taking", "using", "combining", "mixing", "baking",
}
_PERIOD_TO_DAYS: Dict[str, float] = {"hour": 1.0 / 24.0, "day": 1.0, "week": 7.0, "month": 30.0}
_DIGIT_TO_WORD: Dict[str, str] = {
    "1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
    "6": "six", "7": "seven", "8": "eight", "9": "nine", "10": "ten",
}


def _extract_proper_entities(claim: str, *, context_texts: Optional[Sequence[str]] = None) -> Set[str]:
    """Identify capitalized proper entities, 2+ char acronyms, mixed-case acronyms, and contextual initial proper nouns."""
    words = re.findall(r"\b[A-Za-z0-9\-]+\b", claim)
    # Build lowercase vs non-initial capitalized contextual evidence across claim + evidence spans
    non_initial_caps: Set[str] = set()
    lower_only_seen: Set[str] = set()
    for src_txt in ([claim] + list(context_texts or [])):
        for i, tok in enumerate(re.findall(r"\b[A-Za-z0-9\-]+\b", src_txt)):
            if tok.islower() and len(tok) >= 3:
                lower_only_seen.add(tok)
            elif i > 0 and tok[0].isupper() and len(tok) >= 3 and not tok.isupper():
                non_initial_caps.add(tok.lower())

    entities: Set[str] = set()
    for idx, w in enumerate(words):
        if len(w) >= 2 and w.isupper() and any(ch.isalpha() for ch in w) and w not in _EXCLUDED_UPPER_ACRONYMS:
            entities.add(w.lower())
            continue
        if len(w) >= 2 and not w.isupper() and any(ch.isupper() for ch in w[1:]):
            # Mixed-case scientific/domain acronyms such as mRNA, siRNA, HbA1c, SARS-CoV-2
            entities.add(w.lower())
            continue
        if idx > 0 and w[0].isupper() and len(w) >= 3:
            entities.add(w.lower())
            continue
        if idx == 0 and w[0].isupper() and len(w) >= 3:
            wl = w.lower()
            if wl in non_initial_caps or (wl not in _COMMON_INITIAL_NON_PROPER_WORDS and wl not in lower_only_seen):
                entities.add(wl)
    return entities


def _extract_slot_actor_entities(segment: str) -> Set[str]:
    """Extract proper names and acronyms inside an entity/attribution slot fragment."""
    ents: Set[str] = set()
    for w in re.findall(r"\b[A-Za-z0-9\-]+\b", segment):
        if len(w) >= 2 and w.isupper() and any(ch.isalpha() for ch in w) and w not in _EXCLUDED_UPPER_ACRONYMS:
            ents.add(w.lower())
        elif len(w) >= 2 and not w.isupper() and any(ch.isupper() for ch in w[1:]):
            ents.add(w.lower())
        elif w[0].isupper() and len(w) >= 3 and w.lower() not in _COMMON_INITIAL_NON_PROPER_WORDS:
            ents.add(w.lower())
    return ents


def _evaluate_restrictive_scope(claim: str, span: str) -> Tuple[bool, str]:
    """Detect omitted restrictive qualifiers in evidence or unwarranted universal broadening in claim."""
    # 1. Universal quantifier check in claim not warranted by evidence
    span_lower = span.lower()
    for m in _UNIVERSAL_QUANTIFIER_RE.finditer(claim):
        q_phrase = m.group(1).lower()
        if not re.search(rf"\b{re.escape(q_phrase)}\b", span_lower):
            return (
                False,
                f"Scope broadening error: claim asserts universal '{m.group(1)}' not present in evidence.",
            )

    # 2. Restrictive population, age, comorbidity, conditional, or supervision qualifiers in evidence omitted from claim
    claim_tokens_norm = {tok.rstrip("s") for tok in tokenize_content_words(claim, include_negations=True)}
    claim_raw_words = {w.lower().rstrip("s") for w in re.findall(r"\b[a-z0-9]+\b", claim)}
    claim_vocab = claim_tokens_norm | claim_raw_words

    for pat in _RESTRICTIVE_SCOPE_PATTERNS:
        for m in pat.finditer(span):
            phrase = m.group(0).strip()
            req_tokens = [
                tok.rstrip("s")
                for tok in tokenize_content_words(phrase, include_negations=True)
                if tok not in _SCOPE_NON_DEFINING_WORDS
            ]
            if not req_tokens:
                # Fallback if all matched words were condition keywords (e.g. adult/children)
                req_tokens = [
                    w.lower().rstrip("s")
                    for w in re.findall(r"\b[a-z0-9]+\b", phrase)
                    if w.lower() not in _SCOPE_NON_DEFINING_WORDS
                ]
            if not req_tokens:
                continue
            matched = sum(1 for t in req_tokens if t in claim_vocab)
            if matched / len(req_tokens) < 0.75:
                return (
                    False,
                    f"Restrictive scope omitted: evidence qualifies claim with '{phrase}'.",
                )

    return True, "Scope and qualifiers consistent."


def _evaluate_entity_slot_conflict(claim: str, span: str) -> Tuple[bool, str]:
    """Detect mutually exclusive entity/actor replacements across copula, 'serves as', and organization attribution slots."""
    if has_strict_negation(claim) or has_strict_negation(span):
        return False, ""

    c_clean = claim.strip().rstrip(".!?")
    s_clean = span.strip().rstrip(".!?")

    def _tok_jaccard(a: str, b: str) -> float:
        ta = set(tokenize_content_words(a, include_negations=False))
        tb = set(tokenize_content_words(b, include_negations=False))
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    m_c = _SLOT_RELATION_RE.match(c_clean)
    m_s = _SLOT_RELATION_RE.match(s_clean)
    if m_c and m_s:
        c_left, c_right = m_c.group(1), m_c.group(2)
        s_left, s_right = m_s.group(1), m_s.group(2)
        if not (_ENTITY_SLOT_LIST_CUE_RE.search(c_right) or _ENTITY_SLOT_LIST_CUE_RE.search(s_right)):
            # Direction 1: matching left frame, conflicting right entity ("The capital of France is Paris" vs "Lyon"; "approved by FDA" vs "EMA")
            if _tok_jaccard(c_left, s_left) >= 0.80:
                c_r_ents = _extract_slot_actor_entities(c_right)
                s_r_ents = _extract_slot_actor_entities(s_right)
                if c_r_ents and s_r_ents and (c_r_ents & s_r_ents == set()):
                    return (
                        True,
                        f"Entity slot conflict on '{c_left.strip()}': claim asserts {sorted(c_r_ents)}, evidence states {sorted(s_r_ents)}.",
                    )
            # Direction 2: matching right role/predicate, conflicting left entity ("Toronto serves as..." vs "Ottawa serves as...", "IV fluids were..." vs "PO fluids were...")
            if _tok_jaccard(c_right, s_right) >= 0.80:
                c_l_ents = _extract_slot_actor_entities(c_left)
                s_l_ents = _extract_slot_actor_entities(s_left)
                if c_l_ents and s_l_ents and (c_l_ents & s_l_ents == set()):
                    return (
                        True,
                        f"Entity slot conflict on '{c_right.strip()}': claim asserts {sorted(c_l_ents)}, evidence states {sorted(s_l_ents)}.",
                    )

    return False, ""


def _inside_parentheses_or_number_mask(text: str) -> List[bool]:
    """Return per-character boolean mask where True means inside (...) parentheses or digit comma (e.g. 50,000)."""
    mask = [False] * len(text)
    depth = 0
    for i, ch in enumerate(text):
        if ch == "(":
            depth += 1
            mask[i] = True
        elif ch == ")":
            mask[i] = True
            depth = max(0, depth - 1)
        elif depth > 0:
            mask[i] = True
        elif ch == "," and i > 0 and i + 1 < len(text) and text[i - 1].isdigit() and text[i + 1].isdigit():
            mask[i] = True
    return mask


def _scan_unmasked_word_spans(text: str) -> List[Tuple[int, int, str]]:
    """Return `(start, end, raw_word)` spans excluding tokens inside `(...)` parentheses."""
    paren_mask = [False] * len(text)
    depth = 0
    for i, ch in enumerate(text):
        if ch == "(":
            depth += 1
            paren_mask[i] = True
        elif ch == ")":
            paren_mask[i] = True
            depth = max(0, depth - 1)
        elif depth > 0:
            paren_mask[i] = True
    return [
        (m.start(), m.end(), m.group(0))
        for m in re.finditer(r"[A-Za-z0-9\-']+", text)
        if not any(paren_mask[pos] for pos in range(m.start(), m.end()))
    ]


def _classify_finite_verb_token(
    tok_raw: str,
    *,
    prev_lower: str = "",
    tok_index: int = 0,
    require_lowercase: bool = False,
    allow_open_bare: bool = False,
) -> Optional[str]:
    """Classify a candidate finite verb token as `'aux'`, `'v3s'`, `'ved'`, `'vbase'`, or `None`."""
    if not tok_raw or len(tok_raw) < 2:
        return None
    clean = tok_raw.lower()
    if clean in _AUX_MODAL_VERBS_SET:
        if (require_lowercase or tok_index > 0) and tok_raw[0].isupper():
            return None
        return "aux"
    if not tok_raw.isalpha():
        return None
    if (require_lowercase or tok_index > 0) and tok_raw[0].isupper():
        return None
    if clean in _NON_VERB_WORDS:
        return None
    if prev_lower in _NP_PRECEDING_MARKERS:
        return None

    # Open-class 3rd-person singular present (-s / -es / -ies) filtering plural noun suffixes
    if len(clean) >= 4 and clean.endswith("s") and not clean.endswith(_NOUN_ONLY_PLURAL_SUFFIXES):
        return "v3s"

    # Open-class regular past tense / participle (-ed)
    if len(clean) >= 4 and clean.endswith("ed"):
        return "ved"

    # Productive derivational verb suffixes and core irregular / uninflected base verbs
    if len(clean) >= 5 and clean.endswith(("ize", "ise", "ify", "ate")) and clean not in _ADJ_NOUN_ATE_EXCLUDE:
        return "vbase"
    if clean.endswith(
        (
            "strengthen", "worsen", "lessen", "weaken", "harden", "soften",
            "deepen", "broaden", "widen", "shorten", "tighten", "loosen",
            "quicken", "threaten",
        )
    ):
        return "vbase"
    if clean in _CORE_BASE_OR_IRREGULAR_VERBS:
        return "vbase"

    # Open-class bare verb fallback for plural-subject or modal-shared predicates
    if (
        allow_open_bare
        and len(clean) >= 3
        and not clean.endswith("s")
        and not clean.endswith(_NON_VERB_DERIV_SUFFIXES)
    ):
        return "vbase"

    return None


def _is_attributive_ed_modifier(spans: Sequence[Tuple[int, int, str]], ed_idx: int) -> bool:
    """Return True if an `-ed` token modifies a following plural subject noun preceding the true matrix verb."""
    limit = min(len(spans), ed_idx + 4)
    for j in range(ed_idx + 1, limit):
        tok_l = spans[j][2].lower()
        if tok_l in {"and", "but", "or", "while", "whereas"}:
            return False
        if tok_l.endswith("s") and (tok_l in _NON_VERB_WORDS or tok_l.endswith(_NOUN_ONLY_PLURAL_SUFFIXES)):
            if j + 1 < len(spans):
                nxt_kind = _classify_finite_verb_token(
                    spans[j + 1][2],
                    prev_lower=tok_l,
                    tok_index=j + 1,
                    require_lowercase=True,
                    allow_open_bare=True,
                )
                if nxt_kind is not None:
                    return True
    return False


def _find_first_finite_verb_span(text: str) -> Optional[Tuple[int, int, str, str]]:
    """Return `(start, end, lower_token, kind)` of the earliest finite matrix verb after a non-empty subject."""
    spans = _scan_unmasked_word_spans(text)
    if len(spans) < 2:
        return None

    protected = _inside_parentheses_or_number_mask(text)
    # Partition spans into shallow clause slices at coordinators and unmasked commas so objects/tails cannot shadow matrix verbs
    slice_bounds: List[Tuple[int, int]] = []
    start_idx = 0
    for idx, (s, _, raw) in enumerate(spans):
        has_unmasked_comma = idx > start_idx and any(
            text[p] == "," and not protected[p] for p in range(spans[idx - 1][1], min(len(protected), s))
        )
        if idx > start_idx and (
            raw.lower() in {"and", "but", "or", "nor", "yet", "while", "because", "whereas"}
            or has_unmasked_comma
        ):
            slice_bounds.append((start_idx, idx))
            start_idx = idx + (1 if raw.lower() in {"and", "but", "or", "nor", "yet", "while", "because", "whereas"} else 0)
    slice_bounds.append((start_idx, len(spans)))

    _INTRO_PREPOSITIONS: Set[str] = {
        "in", "on", "at", "by", "for", "with", "without", "from", "into", "under", "over",
        "during", "after", "before", "within", "between", "among", "through", "despite",
    }
    _SUBJ_DETS: Set[str] = {"the", "a", "an", "this", "that", "these", "those", "each", "every", "some", "no", "any", "such"}
    _PURE_ADJ_PRE_HEADS: Set[str] = {
        "severe", "mild", "moderate", "acute", "major", "minor", "new", "old", "high", "low",
        "common", "rare", "standard", "primary", "secondary", "adult", "pediatric", "elderly",
    }
    _PURE_ADJ_SUFFIXES: Tuple[str, ...] = (
        "al", "ic", "ous", "ive", "ful", "less", "ary", "ory", "able", "ible", "ly", "ern",
    )

    for c_start, c_end in slice_bounds:
        if c_end - c_start < 2:
            continue
        for idx in range(c_start + 1, c_end):
            s, e, raw = spans[idx]
            prev_lower = spans[idx - 1][2].lower()
            kind = _classify_finite_verb_token(
                raw,
                prev_lower=prev_lower,
                tok_index=idx,
                require_lowercase=True,
                allow_open_bare=False,
            )
            if kind is not None:
                if kind == "ved" and _is_attributive_ed_modifier(spans, idx):
                    continue
                return s, e, raw.lower(), kind

        # Open-class bare / unseen irregular-past matrix verb after an explicit subject NP within the same clause
        lead_tok = spans[c_start][2].lower()
        if lead_tok in _INTRO_PREPOSITIONS and c_start == 0:
            continue

        subj_end = c_start + 1
        if lead_tok in _SUBJ_DETS:
            j = c_start + 1
            while j < c_end - 1:
                jl = spans[j][2].lower()
                if jl in _PURE_ADJ_PRE_HEADS or jl.endswith(_PURE_ADJ_SUFFIXES):
                    j += 1
                    continue
                break
            # Advance past the single head noun completing `det + adj* + head_noun`
            subj_end = min(c_end - 1, j + 1)
        elif lead_tok in _NON_VERB_WORDS or lead_tok.endswith(_NON_VERB_DERIV_SUFFIXES):
            subj_end = min(c_end - 1, c_start + 2)

        for idx in range(subj_end, c_end):
            s, e, raw = spans[idx]
            prev_lower = spans[idx - 1][2].lower()
            kind = _classify_finite_verb_token(
                raw,
                prev_lower=prev_lower,
                tok_index=idx,
                require_lowercase=True,
                allow_open_bare=True,
            )
            if kind is not None:
                return s, e, raw.lower(), kind

    return None


def _has_finite_verb(text: str) -> bool:
    """Return True if text contains a finite predicate verb outside parentheses."""
    return _find_first_finite_verb_span(text) is not None


def _leading_predicate_verb_kind(fragment: str, *, allow_open_bare: bool = False) -> Optional[Tuple[str, str]]:
    """Return `(lower_token, kind)` if fragment opens with an optional adverb chain plus finite verb."""
    spans = _scan_unmasked_word_spans(fragment)
    idx = 0
    while idx < len(spans) and spans[idx][2].lower() in _LEADING_PREDICATE_ADVERBS:
        idx += 1
    if idx >= len(spans):
        return None
    _, _, lead_raw = spans[idx]
    kind = _classify_finite_verb_token(
        lead_raw,
        prev_lower="",
        tok_index=0,
        require_lowercase=True,
        allow_open_bare=allow_open_bare,
    )
    if kind is None:
        return None
    return lead_raw.lower(), kind


def _conjunct_agrees_with_matrix(first_tok: str, first_kind: str, conj_kind: str) -> bool:
    """Reject spurious plural-noun `-s` hits when matrix predicate is plural/uninflected."""
    if first_kind == "vbase" or first_tok in _PLURAL_AUX_VERBS:
        return conj_kind in {"vbase", "ved", "aux"}
    return True


def _is_leading_participle(fragment: str) -> bool:
    """Return True if fragment opens (after optional adverbs) with an active `-ing` participle."""
    spans = _scan_unmasked_word_spans(fragment)
    idx = 0
    while idx < len(spans) and spans[idx][2].lower() in _LEADING_PREDICATE_ADVERBS:
        idx += 1
    if idx >= len(spans):
        return False
    _, _, w_raw = spans[idx]
    wl = w_raw.lower()
    return (
        w_raw.isalpha()
        and w_raw[0].islower()
        and len(wl) >= 5
        and wl.endswith("ing")
        and wl not in _NOMINAL_ING_NOUNS
        and wl not in _NON_VERB_WORDS
    )


def _extract_conjunct_segments(claim_text: str) -> List[str]:
    """Split a proposition on explicit coordinators and post-verbal irregular/comma predicate segments."""
    stripped = claim_text.strip()
    protected = _inside_parentheses_or_number_mask(stripped)
    fv = _find_first_finite_verb_span(stripped)
    fv_end = fv[1] if fv is not None else len(stripped)

    all_matches = [
        m
        for m in _VP_CONJUNCTION_RE.finditer(stripped)
        if not any(protected[p] for p in range(m.start(), min(len(protected), m.end())))
    ]
    split_matches = []
    for idx_m, m in enumerate(all_matches):
        delim = m.group(0).strip().lower()
        nxt_start = all_matches[idx_m + 1].start() if idx_m + 1 < len(all_matches) else len(stripped)
        tail = stripped[m.end() : nxt_start].strip()
        if delim == ",":
            # Only inspect post-verbal commas introducing substantive or lowercase-predicate tails (skip titles/cities/nouns)
            if m.start() < fv_end:
                continue
            raw_words = re.findall(r"[A-Za-z0-9\-']+", tail)
            if not raw_words or (len(raw_words) == 1 and raw_words[0][0].isupper()):
                continue
            toks = tokenize_content_words(tail, include_negations=False)
            if len(toks) >= 2 or (
                len(raw_words) == 1
                and raw_words[0].isalpha()
                and raw_words[0].islower()
                and raw_words[0] not in _NON_VERB_WORDS
            ):
                split_matches.append(m)
        elif "while" in delim:
            if (
                _is_leading_participle(tail)
                or _has_finite_verb(tail)
                or _leading_predicate_verb_kind(tail, allow_open_bare=True) is not None
            ):
                split_matches.append(m)
        else:
            split_matches.append(m)

    base_parts: List[str]
    if not split_matches:
        base_parts = [stripped]
    else:
        base_parts = []
        prev_end = 0
        for m in split_matches:
            seg = stripped[prev_end : m.start()].strip()
            if seg:
                base_parts.append(seg)
            prev_end = m.end()
        tail = stripped[prev_end:].strip()
        if tail:
            base_parts.append(tail)

    # Also split post-verbal causal (`because`, `due to`) and comparative (`faster than ...`) modifiers
    final_parts: List[str] = []
    for seg in base_parts:
        adj_matches = [
            m
            for m in _CAUSAL_COMPARATIVE_SPLIT_RE.finditer(seg)
            if m.start() > 0 and not re.match(r"^\s*(?:older|younger)\s+than\s+\d+", m.group(0), re.IGNORECASE)
        ]
        if not adj_matches:
            final_parts.append(seg)
            continue
        p_prev = 0
        for am in adj_matches:
            head_seg = seg[p_prev : am.start()].strip()
            if head_seg:
                final_parts.append(head_seg)
            # Retain comparative adjective (e.g., "faster") inside the modifier tail when present
            cue_clean = re.sub(r"^(?:,|because|due\s+to|owing\s+to|\s)+", "", am.group(0), flags=re.IGNORECASE).strip()
            cue_clean = re.sub(r"\bthan$", "", cue_clean, flags=re.IGNORECASE).strip()
            tail_start = am.end()
            p_prev = tail_start
            if cue_clean:
                rem = seg[tail_start:].strip()
                if rem:
                    final_parts.append(f"{cue_clean} {rem}".strip())
                    p_prev = len(seg)
        rem_seg = seg[p_prev:].strip()
        if rem_seg:
            final_parts.append(rem_seg)

    return final_parts if len(final_parts) >= 2 else [stripped]


def _expand_coordinated_predicates_with_bodies(claim_text: str) -> List[Tuple[str, str]]:
    """Split shared-subject coordinated VP predicates returning `(full_claim, predicate_body)` pairs."""
    stripped = claim_text.strip()
    first_verb = _find_first_finite_verb_span(stripped)
    if first_verb is None:
        return [(stripped, stripped)]
    fv_start, fv_end, fv_tok, fv_kind = first_verb
    subj_prefix = stripped[:fv_start].strip()
    if not subj_prefix or not re.search(r"[A-Za-z]", subj_prefix):
        return [(stripped, stripped)]

    protected = _inside_parentheses_or_number_mask(stripped)
    matches = list(_VP_CONJUNCTION_RE.finditer(stripped))
    if not matches:
        return [(stripped, stripped)]

    candidate_matches = [
        m
        for m in matches
        if m.end() > fv_end and not any(protected[pos] for pos in range(m.start(), min(len(protected), m.end())))
    ]
    if not candidate_matches:
        return [(stripped, stripped)]

    allow_open_bare_right = (fv_kind == "vbase") or (fv_tok in _MODALS_OR_PLURAL_BARE_AUX)

    split_indices: List[Tuple[int, int, str]] = []
    skipped_comma_item = False
    for idx_m, m in enumerate(candidate_matches):
        delim_raw = m.group(0).strip().lower()
        delim_word = delim_raw.lstrip(",").strip()
        is_plain_comma = delim_raw == ","
        has_comma = "," in m.group(0)
        is_while_delim = "while" in delim_raw
        is_as_well_as = "as well as" in delim_raw
        next_m_start = candidate_matches[idx_m + 1].start() if idx_m + 1 < len(candidate_matches) else len(stripped)
        immediate_seg = stripped[m.end() : next_m_start].strip()
        seg_word_spans = _scan_unmasked_word_spans(immediate_seg)
        seg_content = tokenize_content_words(immediate_seg, include_negations=True)

        # Participial adjuncts (`while <V-ing> ...` or `as well as <V-ing> ...`) introduce separate predicates;
        # finite `while` predicates (`while causes coma`, `while it cures cancer`) fall through to predicate checks.
        if is_while_delim:
            if not _has_finite_verb(immediate_seg) and _is_leading_participle(immediate_seg) and len(seg_content) >= 1:
                left_head = stripped[: m.start()].strip()
                if _has_finite_verb(left_head):
                    split_indices.append((m.start(), m.end(), delim_word))
                continue

        if is_as_well_as and not _has_finite_verb(immediate_seg) and _is_leading_participle(immediate_seg) and len(seg_content) >= 1:
            left_head = stripped[: m.start()].strip()
            if _has_finite_verb(left_head):
                split_indices.append((m.start(), m.end(), delim_word))
            continue

        if is_while_delim and _LEADING_PRONOUN_SUBJECT_RE.match(immediate_seg) and _has_finite_verb(immediate_seg):
            left_head = stripped[: m.start()].strip()
            if _has_finite_verb(left_head):
                split_indices.append((m.start(), m.end(), delim_word))
            continue

        lead_info = _leading_predicate_verb_kind(immediate_seg, allow_open_bare=allow_open_bare_right)
        if lead_info is None:
            if is_plain_comma:
                skipped_comma_item = True
            continue
        _, conj_kind = lead_info
        if conj_kind == "aux":
            if len(seg_word_spans) < 2 or len(seg_content) < 1:
                if is_plain_comma:
                    skipped_comma_item = True
                continue
        elif len(seg_content) < 2:
            if is_plain_comma:
                skipped_comma_item = True
            continue
        # Within a comma-separated NP list where prior list items were unsplit nouns/NPs,
        # do not misinterpret the trailing coordinator + NP as an uninflected matrix VP.
        if skipped_comma_item and has_comma and conj_kind == "vbase":
            continue
        if not _conjunct_agrees_with_matrix(fv_tok, fv_kind, conj_kind):
            if is_plain_comma:
                skipped_comma_item = True
            continue
        left_head = stripped[: m.start()].strip()
        if _has_finite_verb(left_head):
            split_indices.append((m.start(), m.end(), delim_word))
        elif is_plain_comma:
            skipped_comma_item = True

    if not split_indices:
        return [(stripped, stripped)]

    def _format_sub_pred(seg_txt: str, d_word: str) -> Tuple[str, str]:
        if re.match(r"^(?:it|they|he|she)\s+", seg_txt, re.IGNORECASE):
            body_no_pron = re.sub(r"^(?:it|they|he|she)\s+", "", seg_txt, count=1, flags=re.IGNORECASE).strip()
            return (f"{subj_prefix} {body_no_pron}".strip(), body_no_pron or seg_txt)
        if _LEADING_PRONOUN_SUBJECT_RE.match(seg_txt):
            return (seg_txt, seg_txt)
        if d_word == "nor" and not has_strict_negation(subj_prefix):
            return (f"{subj_prefix} not {seg_txt}".strip(), seg_txt)
        return (f"{subj_prefix} {seg_txt}".strip(), seg_txt)

    predicates: List[Tuple[str, str]] = []
    prev_end = 0
    prev_delim = ""
    for idx, (s_pos, e_pos, d_word) in enumerate(split_indices):
        seg = stripped[prev_end:s_pos].strip()
        if seg:
            if idx == 0:
                body = stripped[fv_start:s_pos].strip() or seg
                predicates.append((seg, body))
            else:
                predicates.append(_format_sub_pred(seg, prev_delim))
        prev_end = e_pos
        prev_delim = d_word

    last_seg = stripped[prev_end:].strip()
    if last_seg:
        predicates.append(_format_sub_pred(last_seg, prev_delim))

    return predicates if len(predicates) >= 2 else [(stripped, stripped)]


def _expand_coordinated_predicates(claim_text: str) -> List[str]:
    """Split shared-subject coordinated VP predicates (`A and B`, `A, B, and C`, `A, B and C`, `A, B, C`) independently."""
    return [full for full, _ in _expand_coordinated_predicates_with_bodies(claim_text)]


def _has_unresolved_leading_pronoun(claim_text: str) -> bool:
    """Return True if claim opens with a bare anaphoric pronoun lacking an explicit noun referent."""
    return bool(_PRONOUN_AMBIGUITY_START_RE.match(claim_text.strip()))


_UPPER_BOUND_CLAIM_RE = re.compile(
    r"\b(?:max(?:imum)?|upper\s+bound|upper\s+limit|limit|ceiling|cap|up\s+to|at\s+most)\b",
    re.IGNORECASE,
)
_UPPER_BOUND_NEG_SPAN_RE = re.compile(
    r"\b(?:(?:should|must|do|does|did|can|may)\s+)?(?:not|never)\s+(?:exceed|surpass|go\s+(?:over|above))\b|\bno\s+more\s+than\b",
    re.IGNORECASE,
)
_PASSIVE_BY_RE = re.compile(r"\b(?:was|were|is|are|been|being)\s+\w+(?:ed|en)\s+by\b", re.IGNORECASE)


def _is_upper_bound_polarity_consistent(claim: str, span: str) -> bool:
    """Treat 'maximum/up to X' and 'should not exceed X' as polarity-consistent upper bounds."""
    if has_strict_negation(claim) or not has_strict_negation(span):
        return False
    if not _UPPER_BOUND_CLAIM_RE.search(claim) or not _UPPER_BOUND_NEG_SPAN_RE.search(span):
        return False
    stripped = _UPPER_BOUND_NEG_SPAN_RE.sub(" ", span)
    return not has_strict_negation(stripped)


_NON_DIRECTIONAL_VERBS: frozenset[str] = frozenset(
    {
        "be", "am", "is", "are", "was", "were", "been", "being",
        "can", "could", "may", "might", "must", "shall", "should", "will", "would",
        "do", "does", "did", "have", "has", "had",
        "become", "becomes", "became", "equal", "equals", "contain", "contains",
        "include", "includes", "match", "matches", "share", "shares",
    }
)


def _has_subject_object_role_swap(claim: str, span: str) -> bool:
    """Detect active transitive subject-object role reversals (e.g. 'A blocked B' vs 'B blocked A')."""
    if _PASSIVE_BY_RE.search(claim) or _PASSIVE_BY_RE.search(span):
        return False
    fv_c = _find_first_finite_verb_span(claim)
    fv_s = _find_first_finite_verb_span(span)
    if not fv_c or not fv_s:
        return False
    if fv_c[2] in _NON_DIRECTIONAL_VERBS or fv_s[2] in _NON_DIRECTIONAL_VERBS:
        return False
    if _simple_verb_stem(fv_c[2]) != _simple_verb_stem(fv_s[2]):
        return False
    left_c = set(tokenize_content_words(claim[: fv_c[0]], include_negations=False))
    right_c = set(tokenize_content_words(claim[fv_c[1] :], include_negations=False))
    left_s = set(tokenize_content_words(span[: fv_s[0]], include_negations=False))
    right_s = set(tokenize_content_words(span[fv_s[1] :], include_negations=False))
    if not left_c or not right_c or not left_s or not right_s:
        return False
    if (left_c & right_c) or (left_s & right_s):
        return False
    return bool((left_c & right_s) and (right_c & left_s) and not (left_c & left_s) and not (right_c & right_s))


def _evaluate_polarity(claim: str, span: str) -> Tuple[bool, str]:
    """Verify polarity consistency between claim and candidate evidence span."""
    if has_strict_negation(claim) != has_strict_negation(span) and not _is_upper_bound_polarity_consistent(claim, span):
        return False, "Explicit negation polarity mismatch between claim and evidence."

    c_words = set(tokenize_content_words(claim))
    s_words = set(tokenize_content_words(span))
    for pos_set, neg_set in _ANTONYM_PAIRS:
        c_pos, c_neg_ant = bool(c_words & pos_set), bool(c_words & neg_set)
        s_pos, s_neg_ant = bool(s_words & pos_set), bool(s_words & neg_set)
        # Flag symmetric opposite poles while allowing single spans mentioning two distinct items
        if (c_pos and not c_neg_ant and s_neg_ant and not s_pos) or (
            c_neg_ant and not c_pos and s_pos and not s_neg_ant
        ):
            return False, "Semantic antonym conflict detected between claim and evidence."

    return True, "Polarity consistent."


_OUTER_WARNING_MODIFIERS: Set[str] = {
    "daily", "weekly", "monthly", "yearly", "hourly", "annually",
    "maximum", "minimum", "max", "min",
}


def _is_unmatched_negated_outer_clause(claim: str, span: str) -> bool:
    """Return True when span negation resides strictly in an unmatched warning clause before a temporal/conditional subordinator."""
    if has_strict_negation(claim) or not has_strict_negation(span):
        return False
    parts = re.split(r"\b(?:when|while|after|before)\b", span, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2:
        return False
    head_clause, tail_clause = parts[0], parts[1]
    if not has_strict_negation(head_clause) or has_strict_negation(tail_clause):
        return False
    head_tokens = {
        _simple_verb_stem(w)
        for w in tokenize_content_words(head_clause, include_negations=False)
        if w not in _OUTER_WARNING_MODIFIERS
    }
    if not head_tokens:
        return False
    claim_tokens = {_simple_verb_stem(w) for w in tokenize_content_words(claim, include_negations=False)}
    tail_tokens = {_simple_verb_stem(w) for w in tokenize_content_words(tail_clause, include_negations=False)}
    # Require zero semantic overlap with the negated outer predicate/object and shared context in the subordinate clause.
    return not (head_tokens & claim_tokens) and len(tail_tokens & claim_tokens) >= 2


def _normalize_to_dimension(val_str: str, unit: str) -> Optional[Tuple[str, float]]:
    if not unit or unit not in _UNIT_DIMENSIONS:
        return None
    try:
        num = float(val_str)
    except ValueError:
        return None
    dim, scale = _UNIT_DIMENSIONS[unit]
    return dim, num * scale


def _simple_verb_stem(tok: str) -> str:
    """Reduce common English verb inflections (-ed/-ing/-es/-s/-en) to a shared stem for voice compatibility."""
    t = tok.lower()
    for suf in ("ied", "ies", "ing", "ed", "es", "en", "s"):
        if len(t) > len(suf) + 2 and t.endswith(suf):
            base = t[: -len(suf)] + ("y" if suf in {"ied", "ies"} else "")
            if len(base) >= 4 and base[-1] == base[-2]:
                base = base[:-1]
            return base
    return t


def _action_verbs_compatible_for_voice(
    c_act: Set[str],
    s_act: Set[str],
    c_subj: Set[str],
    s_subj: Set[str],
) -> bool:
    """Allow object-as-subject fallback only when active/passive predicate verbs align by stem."""
    c_verbs = {_simple_verb_stem(t) for t in (c_act - c_subj - s_subj)}
    s_verbs = {_simple_verb_stem(t) for t in (s_act - c_subj - s_subj)}
    if not c_verbs or not s_verbs:
        return False
    return bool(c_verbs & s_verbs) or any(
        len(cv) >= 4 and len(sv) >= 4 and (cv.startswith(sv[:4]) or sv.startswith(cv[:4]))
        for cv in c_verbs
        for sv in s_verbs
    )


_COUNTED_NOUN_RE = re.compile(r"\b(\d+(?:,\d+)*(?:\.\d+)?)\s+([a-zA-Z]{3,})\b")
_COUNTED_NOUN_STOP = frozenset(
    {
        "the", "and", "for", "with", "from", "across", "over", "under", "year", "years",
        "degree", "fahrenheit", "celsius", "kelvin", "meter", "metre", "kilometer", "kilometre",
        "mile", "foot", "feet", "kilogram", "pound", "percent", "million", "billion", "thousand",
    }
)


def _find_counted_noun_conflict(claim: str, span: str) -> Optional[str]:
    """Detect mismatched non-year quantities qualifying the same noun (e.g. '500 patients' vs '50 patients')."""
    s_map: Dict[str, Set[str]] = {}
    for val, noun in _COUNTED_NOUN_RE.findall(span):
        stem = noun.lower().rstrip("s")
        if stem in _COUNTED_NOUN_STOP or stem in _UNIT_DIMENSIONS:
            continue
        clean_v = val.replace(",", "")
        s_map.setdefault(stem, set()).add(clean_v)
    for c_val, noun in _COUNTED_NOUN_RE.findall(claim):
        stem = noun.lower().rstrip("s")
        if stem in _COUNTED_NOUN_STOP or stem in _UNIT_DIMENSIONS:
            continue
        clean_c = c_val.replace(",", "")
        if clean_c in s_map.get(stem, set()):
            continue
        if stem in s_map and s_map[stem]:
            try:
                num_v = float(clean_c)
                if 1500.0 <= num_v <= 2099.0 and num_v.is_integer():
                    continue
            except ValueError:
                pass
            return f"Count conflict on '{noun.lower()}': claim states {clean_c}, evidence states {sorted(s_map[stem])}."
    return None


def _evaluate_numbers_with_grounded_tokens(claim: str, span: str) -> Tuple[bool, bool, str, Set[str]]:
    """Verify numeric, physical-unit, and action-bound schedule alignment between claim and evidence span.

    Returns (numeric_match, numeric_conflict, note, grounded_claim_tokens).
    `grounded_claim_tokens` records equivalent unit/frequency tokens verified by conversion or rate parity
    so scaled forms (e.g. `0.5 g` <-> `500 mg`, `twice daily` <-> `every 12 hours`) are credited fairly.
    """
    grounded_tokens: Set[str] = set()
    c_scheds: List[ScheduleAssertion] = extract_schedule_assertions(claim)
    s_scheds: List[ScheduleAssertion] = extract_schedule_assertions(span)
    remaining_claim = claim

    if c_scheds:
        s_daily_entries: List[Tuple[float, ScheduleAssertion]] = [
            (sa.rate_per_period / _PERIOD_TO_DAYS.get(sa.period, 1.0), sa)
            for sa in s_scheds
        ]
        claim_entities = _extract_proper_entities(claim, context_texts=[span]) if len(s_daily_entries) > 1 else set()

        for c_sa in c_scheds:
            c_daily = c_sa.rate_per_period / _PERIOD_TO_DAYS.get(c_sa.period, 1.0)
            if s_daily_entries:
                if len(s_daily_entries) > 1:
                    scored = []
                    for s_d, s_sa in s_daily_entries:
                        ctx_ov = len(c_sa.local_context_tokens & s_sa.local_context_tokens)
                        act_ov = len(c_sa.action_tokens & s_sa.action_tokens)
                        subj_ov = len(c_sa.subject_tokens & s_sa.subject_tokens)
                        ent_ov = len((c_sa.local_context_tokens & s_sa.local_context_tokens) & claim_entities)
                        score = 3.0 * subj_ov + 2.0 * act_ov + 0.25 * ctx_ov + 0.5 * ent_ov
                        scored.append((s_d, s_sa, ctx_ov, score))

                    best_ctx_ov = max(item[2] for item in scored)
                    if best_ctx_ov <= 0:
                        return (
                            False,
                            False,
                            f"Unverified schedule '{c_sa.raw_phrase}' has no matching local action/subject context in evidence.",
                            set(),
                        )
                    best_score = max(item[3] for item in scored)
                    target_entries = [(s_d, s_sa) for s_d, s_sa, _, sc in scored if sc == best_score]

                    # Conservative ambiguity guard: if tied top-ranked evidence schedules disagree in frequency, fail safe
                    distinct_rates = {round(sd, 4) for sd, _ in target_entries}
                    if len(distinct_rates) > 1:
                        return (
                            False,
                            False,
                            f"Ambiguous schedule-to-action binding for '{c_sa.raw_phrase}' across conflicting tied evidence clauses.",
                            set(),
                        )
                else:
                    target_entries = s_daily_entries

                if c_sa.subject_tokens and all(
                    s_sa.subject_tokens
                    and not (c_sa.subject_tokens & s_sa.subject_tokens)
                    and not (
                        (c_sa.subject_tokens & s_sa.action_tokens)
                        and _action_verbs_compatible_for_voice(
                            c_sa.action_tokens, s_sa.action_tokens, c_sa.subject_tokens, s_sa.subject_tokens
                        )
                    )
                    for _, s_sa in target_entries
                ):
                    matched_subjects = sorted({tok for _, s_sa in target_entries for tok in s_sa.subject_tokens})
                    return (
                        False,
                        False,
                        (
                            f"Unverified schedule '{c_sa.raw_phrase}': evidence clause subject "
                            f"{matched_subjects} does not match claim subject "
                            f"{sorted(c_sa.subject_tokens)}."
                        ),
                        set(),
                    )

                if len(s_daily_entries) > 1 and c_sa.action_tokens:
                    target_s_ids = {id(s_sa) for _, s_sa in target_entries}
                    target_act_tokens = {tok for _, s_sa in target_entries for tok in s_sa.action_tokens}
                    missing_act = c_sa.action_tokens - target_act_tokens
                    if missing_act and any(
                        missing_act & (other_sa.action_tokens | other_sa.subject_tokens)
                        for _, other_sa in s_daily_entries
                        if id(other_sa) not in target_s_ids
                    ):
                        return (
                            False,
                            False,
                            (
                                f"Unverified schedule '{c_sa.raw_phrase}': claim combines subject and action "
                                f"tokens from separate evidence clauses."
                            ),
                            set(),
                        )

                matched = any(
                    abs(c_daily - s_d) <= max(1e-4, 0.025 * max(abs(c_daily), abs(s_d)))
                    for s_d, _ in target_entries
                )
                if not matched:
                    ev_desc = [
                        f"'{sa.raw_phrase}' ({sa.rate_per_period:g}/{sa.period} ≈ {sd:.3g}/day)"
                        for sd, sa in target_entries
                    ]
                    return (
                        False,
                        True,
                        f"Dosage frequency conflict: claim states '{c_sa.raw_phrase}' ({c_sa.rate_per_period:g}/{c_sa.period} ≈ {c_daily:.3g}/day), evidence states {', '.join(ev_desc)}.",
                        set(),
                    )
                grounded_tokens.update(tokenize_content_words(c_sa.raw_phrase, include_negations=False))
                grounded_tokens.update(re.findall(r"[a-z0-9]+", c_sa.raw_phrase.lower()))
                # Consume matched frequency phrase so embedded schedule numbers (e.g., 12 in 'every 12 hours')
                # are not re-flagged as unverified standalone quantities against 'twice daily'.
                remaining_claim = re.sub(re.escape(c_sa.raw_phrase), " ", remaining_claim, count=1, flags=re.IGNORECASE)
            else:
                return (
                    False,
                    False,
                    f"Unverified dosage frequency '{c_sa.raw_phrase}' not supported by evidence schedule expressions.",
                    set(),
                )

    c_nums = extract_numbers_and_units(remaining_claim)
    if not c_nums:
        return (
            True,
            False,
            "All dosage frequencies and quantities verified in evidence." if c_scheds else "No numeric assertions in claim.",
            grounded_tokens,
        )

    s_nums = extract_numbers_and_units(span)
    if not s_nums:
        return False, False, f"Claim introduces unverified numeric values {[n[0] for n in c_nums]}.", set()

    s_vals_by_unit: Dict[str, Set[str]] = {}
    s_dims: Dict[str, List[float]] = {}
    all_s_vals: Set[str] = set()
    s_has_units = False
    for val, unit in s_nums:
        all_s_vals.add(val)
        if unit:
            s_has_units = True
            s_vals_by_unit.setdefault(unit, set()).add(val)
            norm_dim = _normalize_to_dimension(val, unit)
            if norm_dim is not None:
                s_dims.setdefault(norm_dim[0], []).append(norm_dim[1])

    for c_val, c_unit in c_nums:
        if c_unit:
            if c_unit in s_vals_by_unit:
                if c_val not in s_vals_by_unit[c_unit]:
                    return (
                        False,
                        True,
                        f"Numeric conflict on unit '{c_unit}': claim states {c_val}, evidence states {sorted(s_vals_by_unit[c_unit])}.",
                        set(),
                    )
                grounded_tokens.update(re.findall(r"[a-z0-9]+", f"{c_val} {c_unit}".lower()))
                if c_val in _DIGIT_TO_WORD:
                    grounded_tokens.add(_DIGIT_TO_WORD[c_val])
                grounded_tokens.add(c_unit.rstrip("s"))
                grounded_tokens.add(c_unit if c_unit.endswith("s") else f"{c_unit}s")
            else:
                c_dim = _normalize_to_dimension(c_val, c_unit)
                if c_dim is not None and c_dim[0] in s_dims:
                    dim_name, c_scaled = c_dim
                    matched_scaled = any(abs(c_scaled - sv) <= max(1e-6, 1e-4 * abs(sv)) for sv in s_dims[dim_name])
                    if not matched_scaled:
                        return (
                            False,
                            True,
                            f"Unit/dosage scale conflict on {dim_name}: claim states {c_val}{c_unit}, contradicting evidence units.",
                            set(),
                        )
                    grounded_tokens.update(re.findall(r"[a-z0-9]+", f"{c_val} {c_unit}".lower()))
                    if c_val in _DIGIT_TO_WORD:
                        grounded_tokens.add(_DIGIT_TO_WORD[c_val])
                    grounded_tokens.add(c_unit.rstrip("s"))
                    grounded_tokens.add(c_unit if c_unit.endswith("s") else f"{c_unit}s")
                elif s_has_units:
                    return (
                        False,
                        False,
                        f"Numeric dosage/unit '{c_val}{c_unit}' not verified in evidence span units {sorted(s_vals_by_unit.keys())}.",
                        set(),
                    )
                elif c_val not in all_s_vals:
                    return False, False, f"Numeric value '{c_val}{c_unit}' in claim not found in evidence span.", set()
        elif c_val not in all_s_vals:
            noun_conflict = _find_counted_noun_conflict(remaining_claim, span)
            if noun_conflict is not None:
                return False, True, noun_conflict, set()
            temp_num_conflict = _find_temporal_or_unitless_numeric_contradiction(
                remaining_claim, span, c_nums, s_nums
            )
            if temp_num_conflict is not None:
                return False, True, temp_num_conflict, set()
            return False, False, f"Numeric value '{c_val}' in claim not found in evidence span.", set()

    return True, False, "All claim numbers verified in evidence.", grounded_tokens


_TEMP_HEDGE_RE = re.compile(
    r"\b(?:approximately|approx\.?|about|around|circa|roughly|nearly|almost)\b|~",
    re.IGNORECASE,
)
_DEG_C_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:°\s*c\b|deg(?:rees?)?\s*c(?:elsius)?\b)", re.IGNORECASE)
_DEG_F_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:°\s*f\b|deg(?:rees?)?\s*f(?:ahrenheit)?\b)", re.IGNORECASE)
_YEAR_RANGE_RE = re.compile(
    r"\b(1\d{3}|20\d{2})\s*(?:[-–—]|to|and)\s*(1\d{3}|20\d{2})\b",
    re.IGNORECASE,
)
_YEAR_SINGLE_RE = re.compile(r"\b(1\d{3}|20\d{2})\b")
_STOP_CONTENT = frozenset(
    {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "in", "on", "at",
        "to", "for", "of", "by", "with", "from", "and", "or", "that", "this", "it",
    }
)


def _extract_temp_values(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for m in _DEG_C_RE.finditer(text):
        out.append((m.group(1), "deg_c"))
    for m in _DEG_F_RE.finditer(text):
        out.append((m.group(1), "deg_f"))
    return out


def _find_temporal_or_unitless_numeric_contradiction(
    claim: str,
    span: str,
    c_nums: Sequence[tuple[str, str]],
    s_nums: Sequence[tuple[str, str]],
) -> str | None:
    """Detect temperature-unit, year/range, or shared-entity unitless numeric contradictions."""
    # 1. Normalized temperature units (°C / degrees Celsius / °F / degrees Fahrenheit)
    c_temps = _extract_temp_values(claim)
    s_temps = _extract_temp_values(span)
    if c_temps and s_temps:
        for cv, cu in c_temps:
            same_unit_vals = {sv for sv, su in s_temps if su == cu}
            if same_unit_vals and cv not in same_unit_vals:
                return (
                    f"Temperature unit conflict ({cu}): claim states {cv}, "
                    f"evidence states {sorted(same_unit_vals)}."
                )

    if _TEMP_HEDGE_RE.search(claim) or _TEMP_HEDGE_RE.search(span):
        return None

    c_words = {
        w for w in re.findall(r"[a-z]+", claim.lower()) if w not in _STOP_CONTENT and len(w) > 2
    }
    s_words = {
        w for w in re.findall(r"[a-z]+", span.lower()) if w not in _STOP_CONTENT and len(w) > 2
    }
    if not c_words or not s_words:
        return None
    overlap = len(c_words & s_words) / len(c_words)

    # Check capitalized entity alignment if claim has named entities beyond sentence start
    c_ents = {e.lower() for e in re.findall(r"\b[A-Z][a-z]{2,}\b", claim[1:])}
    s_ents = {e.lower() for e in re.findall(r"\b[A-Z][a-z]{2,}\b", span)}
    if c_ents and s_ents and not (c_ents & s_ents):
        return None

    # 2. Temporal year & year-range contradiction
    c_years = [int(y) for y in _YEAR_SINGLE_RE.findall(claim)]
    s_ranges = [(int(a), int(b)) for a, b in _YEAR_RANGE_RE.findall(span)]
    s_years = [int(y) for y in _YEAR_SINGLE_RE.findall(span)]
    if c_years:
        if any(min(a, b) <= cy <= max(a, b) for cy in c_years for a, b in s_ranges):
            return None
        if (s_years or s_ranges) and overlap >= 0.35:
            for cy in c_years:
                in_range = any(min(a, b) <= cy <= max(a, b) for a, b in s_ranges)
                if not in_range and cy not in s_years:
                    return f"Temporal year conflict: claim states {cy}, evidence states {s_years or s_ranges}."
        # Claim introduces a year when evidence has no years -> unmentioned (INSUFFICIENT_EVIDENCE)
        if not s_years and not s_ranges:
            return None

    # 3. Unitless numeric contradiction on same entity/predicate (only against unitless evidence numbers)
    s_unitless = {sv for sv, su in s_nums if not su}
    if overlap >= 0.50 and c_nums and s_unitless:
        for cv, cu in c_nums:
            if not cu and not _YEAR_SINGLE_RE.fullmatch(cv) and cv not in s_unitless:
                return (
                    f"Numeric conflict on shared predicate: claim states {cv}, "
                    f"evidence states {sorted(s_unitless)}."
                )
    return None


def _evaluate_numbers(claim: str, span: str) -> Tuple[bool, bool, str]:
    """Verify numeric, physical-unit, and dosage frequency alignment between claim and evidence span."""
    ok, conflict, note, _ = _evaluate_numbers_with_grounded_tokens(claim, span)
    return ok, conflict, note


def _is_non_factual_or_conversational(clause: str) -> bool:
    stripped = clause.strip()
    if not stripped or stripped.endswith("?"):
        return True
    for pat in _NON_FACTUAL_PATTERNS:
        if pat.search(stripped):
            return True
    return False


def _split_compound_factual_clauses(clause: str) -> List[str]:
    """Split punctuated independent-subject compound assertions without detaching shared-subject coordinated VPs."""
    matches = list(_COMPOUND_CLAUSE_SPLIT_RE.finditer(clause))
    if not matches:
        return [clause]

    # Collect slices paired with the exact delimiter preceding each slice ("" for slice 0)
    segments: List[Tuple[str, str]] = []
    prev_end = 0
    prev_delim = ""
    for m in matches:
        seg_txt = clause[prev_end : m.start()].strip()
        segments.append((prev_delim, seg_txt))
        prev_delim = m.group(0)
        prev_end = m.end()
    segments.append((prev_delim, clause[prev_end:].strip()))

    merged: List[str] = [segments[0][1]]
    for delim, nxt_clean in segments[1:]:
        if not nxt_clean:
            continue
        prev_clean = merged[-1]
        both_have_verbs = _has_finite_verb(prev_clean) and (
            _has_finite_verb(nxt_clean) or _leading_predicate_verb_kind(nxt_clean) is not None
        )
        prev_ok = len(tokenize_content_words(prev_clean, include_negations=True)) >= 2
        nxt_ok = len(tokenize_content_words(nxt_clean, include_negations=True)) >= 2
        nxt_independent_subject = not (
            _LEADING_PRONOUN_SUBJECT_RE.match(nxt_clean)
            or _leading_predicate_verb_kind(nxt_clean) is not None
        )
        if both_have_verbs and prev_ok and nxt_ok and nxt_independent_subject:
            merged.append(nxt_clean)
        else:
            joiner = delim if delim.strip() else ", "
            merged[-1] = f"{prev_clean}{joiner}{nxt_clean}"
    return merged


@dataclass
class _EvidenceSpanIndex:
    """Precomputed evidence spans and single-fit TF-IDF / embedding matrices reused across all claims."""

    span_entries: List[Tuple[EvidenceDocument, str]]
    span_tokens: List[Set[str]]
    span_lowers: List[str]
    span_word_sets: List[Set[str]]
    vectorizer: Optional[TfidfVectorizer]
    span_tfidf_matrix: Optional[object]
    span_dense_matrix: Optional[np.ndarray]


class OutputEvidenceVerifier:
    """G3 Output Evidence Verification engine checking answer claims against retrieved evidence."""

    def __init__(
        self,
        config: Optional[VerificationConfig] = None,
        *,
        embedding_callable: Optional[Callable[[Sequence[str]], Sequence[np.ndarray]]] = None,
        srm_client: Optional[Any] = None,
    ) -> None:
        self.config = config or VerificationConfig()
        self.embedding_callable = embedding_callable
        self.srm_client = srm_client

    def extract_claims(self, answer_text: str) -> List[str]:
        """Decompose generated answer text into verifiable atomic claims, skipping opinions/greetings."""
        if not answer_text or not answer_text.strip():
            return []

        claims: List[str] = []
        for sent in split_sentences(answer_text):
            cleaned = strip_citations(sent)
            cleaned = re.sub(r"^\s*(?:[-*•]+|\d+[\.\)])\s+", "", cleaned).strip()
            for semi_clause in re.split(r";\s+", cleaned):
                sub_raw = semi_clause.strip()
                if not sub_raw or _is_non_factual_or_conversational(sub_raw):
                    continue
                for atomic in _split_compound_factual_clauses(sub_raw):
                    c = atomic.strip()
                    if not c or _is_non_factual_or_conversational(c):
                        continue
                    if len(c) >= 5 and len(tokenize_content_words(c, include_negations=True)) >= 2:
                        claims.append(c)
        return claims

    def _build_evidence_index(
        self,
        trusted_documents: Sequence[EvidenceDocument],
    ) -> _EvidenceSpanIndex:
        span_entries: List[Tuple[EvidenceDocument, str]] = []
        seen_spans: Set[Tuple[str, str]] = set()
        for doc in trusted_documents:
            sents = split_sentences(doc.text)
            raw_spans = sents if sents else ([doc.text.strip()] if doc.text.strip() else [])
            for s in raw_spans:
                key = (doc.doc_id, s)
                if key not in seen_spans:
                    seen_spans.add(key)
                    span_entries.append((doc, s))
                # Split semicolon, punctuated compound clauses, and concessive 'Although X, Y' clauses
                # (including mid-sentence ', although ...') so negative caveats do not contaminate separate assertions.
                candidates_to_subsplit: List[str] = [s]
                m_conc = _CONCESSIVE_SPLIT_RE.match(s)
                if m_conc:
                    for part in (m_conc.group(1).strip(), m_conc.group(2).strip()):
                        if part:
                            candidates_to_subsplit.append(part)
                else:
                    mid_parts = re.split(r",\s*(?:although|even\s+though|though)\s+", s, maxsplit=1, flags=re.IGNORECASE)
                    if len(mid_parts) == 2:
                        for part in mid_parts:
                            if part.strip():
                                candidates_to_subsplit.append(part.strip())
                for chunk in candidates_to_subsplit:
                    if chunk != s and len(tokenize_content_words(chunk, include_negations=True)) >= 2:
                        c_key = (doc.doc_id, chunk)
                        if c_key not in seen_spans:
                            seen_spans.add(c_key)
                            span_entries.append((doc, chunk))
                    for semi in re.split(r";\s+", chunk):
                        for sub in _split_compound_factual_clauses(semi.strip()):
                            sub_clean = sub.strip()
                            if sub_clean and sub_clean != s and len(tokenize_content_words(sub_clean, include_negations=True)) >= 2:
                                sub_key = (doc.doc_id, sub_clean)
                                if sub_key not in seen_spans:
                                    seen_spans.add(sub_key)
                                    span_entries.append((doc, sub_clean))

        span_texts = [entry[1] for entry in span_entries]
        span_tokens = [set(tokenize_content_words(txt, include_negations=False)) for txt in span_texts]
        span_lowers = [txt.lower() for txt in span_texts]
        span_word_sets = [set(re.findall(r"\b[a-z0-9\-]+\b", low)) for low in span_lowers]

        vectorizer: Optional[TfidfVectorizer] = None
        span_tfidf_matrix = None
        if span_texts:
            try:
                vectorizer = TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 2),
                    token_pattern=r"(?u)\b[a-zA-Z0-9][a-zA-Z0-9\-]*\b",
                )
                span_tfidf_matrix = vectorizer.fit_transform(span_texts)
            except ValueError:
                vectorizer = None
                span_tfidf_matrix = None

        span_dense_matrix: Optional[np.ndarray] = None
        if self.embedding_callable is not None and span_texts:
            try:
                raw_vecs = list(self.embedding_callable(span_texts))
                if len(raw_vecs) == len(span_texts) and all(v is not None for v in raw_vecs):
                    span_dense_matrix = np.vstack([np.asarray(v, dtype=float).ravel() for v in raw_vecs])
            except Exception as exc:
                LOGGER.warning("Optional G3 embedding callable failed; using TF-IDF + lexical similarity", extra={"error": str(exc)})
                span_dense_matrix = None

        return _EvidenceSpanIndex(
            span_entries=span_entries,
            span_tokens=span_tokens,
            span_lowers=span_lowers,
            span_word_sets=span_word_sets,
            vectorizer=vectorizer,
            span_tfidf_matrix=span_tfidf_matrix,
            span_dense_matrix=span_dense_matrix,
        )

    def _score_claims_against_index(
        self,
        claim_texts: Sequence[str],
        index: _EvidenceSpanIndex,
    ) -> List[List[float]]:
        n_claims = len(claim_texts)
        n_spans = len(index.span_entries)
        if n_claims == 0 or n_spans == 0:
            return [[0.0] * n_spans for _ in range(n_claims)]

        tfidf_mat = np.zeros((n_claims, n_spans), dtype=float)
        if index.vectorizer is not None and index.span_tfidf_matrix is not None:
            try:
                q_mat = index.vectorizer.transform(list(claim_texts))
                tfidf_mat = np.clip(cosine_similarity(q_mat, index.span_tfidf_matrix), 0.0, 1.0)
            except ValueError:
                pass

        dense_mat: Optional[np.ndarray] = None
        if self.embedding_callable is not None and index.span_dense_matrix is not None:
            try:
                c_vecs = list(self.embedding_callable(list(claim_texts)))
                if len(c_vecs) == n_claims and all(v is not None for v in c_vecs):
                    c_mat = np.vstack([np.asarray(v, dtype=float).ravel() for v in c_vecs])
                    if c_mat.shape[1] == index.span_dense_matrix.shape[1]:
                        dense_mat = np.clip(cosine_similarity(c_mat, index.span_dense_matrix), 0.0, 1.0)
            except Exception:
                dense_mat = None

        scores: List[List[float]] = []
        for i, claim_txt in enumerate(claim_texts):
            row: List[float] = []
            for j, (_, span_txt) in enumerate(index.span_entries):
                lex = compute_lexical_overlap(claim_txt, span_txt)
                base_sim = max(float(tfidf_mat[i, j]), lex)
                if dense_mat is not None:
                    base_sim = max(base_sim, float(dense_mat[i, j]))
                row.append(round(base_sim, 4))
            scores.append(row)
        return scores

    def verify_claim(
        self,
        claim_id: str,
        claim_text: str,
        trusted_documents: Sequence[EvidenceDocument],
        *,
        _precomputed_index: Optional[_EvidenceSpanIndex] = None,
        _precomputed_sims: Optional[Sequence[float]] = None,
    ) -> ClaimVerificationItem:
        """Verify one atomic claim (or coordinated multi-predicate claim) against retrieved documents."""
        if not trusted_documents:
            return ClaimVerificationItem(
                claim_id=claim_id,
                claim_text=claim_text,
                outcome=EvidenceOutcome.NOT_ENOUGH_EVIDENCE,
                verdict=G3ClaimVerdict.INSUFFICIENT,
                confidence=0.95,
                unsupported_flag=True,
                supporting_evidence_refs=[],
                contradicting_evidence_refs=[],
                evidence_refs=[],
                explanation="No retrieved evidence documents provided to verify claim; missing evidence is never marked supported.",
            )

        index = _precomputed_index or self._build_evidence_index(trusted_documents)
        if not index.span_entries:
            return ClaimVerificationItem(
                claim_id=claim_id,
                claim_text=claim_text,
                outcome=EvidenceOutcome.NOT_ENOUGH_EVIDENCE,
                verdict=G3ClaimVerdict.INSUFFICIENT,
                confidence=0.95,
                unsupported_flag=True,
                supporting_evidence_refs=[],
                contradicting_evidence_refs=[],
                evidence_refs=[],
                explanation="Retrieved documents contained no extractable sentence spans.",
            )

        pred_pairs = _expand_coordinated_predicates_with_bodies(claim_text)
        if len(pred_pairs) <= 1:
            return self._verify_single_proposition(
                claim_id=claim_id,
                claim_text=claim_text,
                trusted_documents=trusted_documents,
                index=index,
                precomputed_sims=_precomputed_sims,
            )

        # Evaluate every coordinated factual predicate and its local predicate body independently
        # so a long shared subject prefix cannot dilute a fabricated short predicate.
        sub_predicates = [full for full, _ in pred_pairs]
        pred_sims = self._score_claims_against_index(sub_predicates, index)
        sub_results = [
            self._verify_single_proposition(
                claim_id=f"{claim_id}.{idx}",
                claim_text=pred_txt,
                trusted_documents=trusted_documents,
                index=index,
                precomputed_sims=pred_sims[idx - 1],
                required_predicate_text=pred_body,
                full_claim_text=claim_text,
            )
            for idx, (pred_txt, pred_body) in enumerate(pred_pairs, start=1)
        ]

        supp_refs: List[EvidenceReference] = []
        contr_refs: List[EvidenceReference] = []
        all_refs: List[EvidenceReference] = []
        seen_supp_keys: Set[Tuple[str, str]] = set()
        seen_contr_keys: Set[Tuple[str, str]] = set()
        seen_ref_keys: Set[Tuple[str, str]] = set()
        for sr in sub_results:
            for r in sr.supporting_evidence_refs:
                k = (r.doc_id, r.matched_span)
                if k not in seen_supp_keys:
                    seen_supp_keys.add(k)
                    supp_refs.append(r)
            for r in sr.contradicting_evidence_refs:
                k = (r.doc_id, r.matched_span)
                if k not in seen_contr_keys:
                    seen_contr_keys.add(k)
                    contr_refs.append(r)
            for r in sr.evidence_refs:
                k = (r.doc_id, r.matched_span)
                if k not in seen_ref_keys:
                    seen_ref_keys.add(k)
                    all_refs.append(r)

        contradicted_parts = [sr for sr in sub_results if sr.verdict == G3ClaimVerdict.CONTRADICTED]
        uncertain_parts = [sr for sr in sub_results if sr.verdict == G3ClaimVerdict.UNCERTAIN]
        insufficient_parts = [sr for sr in sub_results if sr.verdict == G3ClaimVerdict.INSUFFICIENT]

        if contradicted_parts:
            first_c = contradicted_parts[0]
            return ClaimVerificationItem(
                claim_id=claim_id,
                claim_text=claim_text,
                outcome=EvidenceOutcome.CONTRADICTS,
                verdict=G3ClaimVerdict.CONTRADICTED,
                confidence=first_c.confidence,
                unsupported_flag=True,
                supporting_evidence_refs=supp_refs[:3],
                contradicting_evidence_refs=contr_refs[:3],
                evidence_refs=all_refs[:3],
                explanation=f"Coordinated predicate contradicted ('{first_c.claim_text}'): {first_c.explanation}",
            )
        if uncertain_parts:
            first_u = uncertain_parts[0]
            return ClaimVerificationItem(
                claim_id=claim_id,
                claim_text=claim_text,
                outcome=EvidenceOutcome.UNCERTAIN,
                verdict=G3ClaimVerdict.UNCERTAIN,
                confidence=first_u.confidence,
                unsupported_flag=True,
                supporting_evidence_refs=supp_refs[:3],
                contradicting_evidence_refs=contr_refs[:3],
                evidence_refs=all_refs[:3],
                explanation=f"Coordinated predicate uncertain ('{first_u.claim_text}'): {first_u.explanation}",
            )
        if not insufficient_parts:
            if _has_unresolved_leading_pronoun(claim_text):
                return ClaimVerificationItem(
                    claim_id=claim_id,
                    claim_text=claim_text,
                    outcome=EvidenceOutcome.UNCERTAIN,
                    verdict=G3ClaimVerdict.UNCERTAIN,
                    confidence=0.55,
                    unsupported_flag=True,
                    supporting_evidence_refs=supp_refs[:3],
                    contradicting_evidence_refs=[],
                    evidence_refs=all_refs[:3],
                    explanation="Compound claim relies on unresolved leading pronoun lacking an explicit referent.",
                )
            avg_conf = round(min(r.confidence for r in sub_results), 4)
            return ClaimVerificationItem(
                claim_id=claim_id,
                claim_text=claim_text,
                outcome=EvidenceOutcome.SUPPORTS,
                verdict=G3ClaimVerdict.SUPPORTED,
                confidence=avg_conf,
                unsupported_flag=False,
                supporting_evidence_refs=supp_refs[:3],
                contradicting_evidence_refs=[],
                evidence_refs=all_refs[:3],
                explanation=f"All {len(sub_results)} coordinated factual predicates independently verified against evidence.",
            )

        unverified_preds = [sr.claim_text for sr in insufficient_parts]
        verified_preds = [sr.claim_text for sr in sub_results if sr.verdict == G3ClaimVerdict.SUPPORTED]
        return ClaimVerificationItem(
            claim_id=claim_id,
            claim_text=claim_text,
            outcome=EvidenceOutcome.NOT_ENOUGH_EVIDENCE,
            verdict=G3ClaimVerdict.INSUFFICIENT,
            confidence=round(max(r.confidence for r in insufficient_parts), 4),
            unsupported_flag=True,
            supporting_evidence_refs=supp_refs[:3],
            contradicting_evidence_refs=[],
            evidence_refs=all_refs[:3],
            explanation=(
                f"Coordinated predicate verification failed: unverified predicate(s) {unverified_preds}; "
                f"supported predicate(s) {verified_preds}. Aggregate lexical overlap cannot endorse unverified predicates."
            ),
        )

    def _verify_single_proposition(
        self,
        claim_id: str,
        claim_text: str,
        trusted_documents: Sequence[EvidenceDocument],
        *,
        index: _EvidenceSpanIndex,
        precomputed_sims: Optional[Sequence[float]] = None,
        required_predicate_text: Optional[str] = None,
        full_claim_text: Optional[str] = None,
    ) -> ClaimVerificationItem:
        """Verify a single proposition against indexed spans with polarity, numeric/frequency, scope, and slot checks."""
        sim_list = (
            list(precomputed_sims)
            if precomputed_sims is not None
            else self._score_claims_against_index([claim_text], index)[0]
        )

        claim_tokens = set(tokenize_content_words(claim_text, include_negations=False))
        pred_body_tokens = (
            set(tokenize_content_words(required_predicate_text, include_negations=False))
            if required_predicate_text
            else set()
        )
        conjunct_segs = _extract_conjunct_segments(claim_text)
        conjunct_token_sets: List[Set[str]] = [
            set(tokenize_content_words(seg, include_negations=False))
            for seg in conjunct_segs
            if tokenize_content_words(seg, include_negations=False)
        ]
        proper_entities = _extract_proper_entities(
            claim_text,
            context_texts=[entry[1] for entry in index.span_entries],
        )

        candidate_refs: List[Tuple[EvidenceOutcome, float, EvidenceReference]] = []

        for idx, (doc, span) in enumerate(index.span_entries):
            sim = float(sim_list[idx])
            if sim < self.config.min_relevance_for_check:
                continue

            span_tokens = index.span_tokens[idx]

            polarity_ok, pol_note = (
                _evaluate_polarity(claim_text, span)
                if self.config.strict_negation_check
                else (True, "Polarity check disabled.")
            )
            polarity_contradicts = (not polarity_ok) and not _is_unmatched_negated_outer_clause(claim_text, span)
            num_ok, num_conflict, num_note, grounded_num_tokens = (
                _evaluate_numbers_with_grounded_tokens(claim_text, span)
                if self.config.strict_numeric_matching
                else (True, False, "Numeric check disabled.", set())
            )
            grounded_union = span_tokens | grounded_num_tokens
            matched_tokens = claim_tokens & grounded_union
            coverage = len(matched_tokens) / len(claim_tokens) if claim_tokens else 0.0
            conjuncts_ok = True
            if len(conjunct_token_sets) >= 2:
                for seg_toks in conjunct_token_sets:
                    if len(seg_toks & grounded_union) / len(seg_toks) < self.config.min_support_coverage:
                        conjuncts_ok = False
                        break
            pred_body_ok = True
            if pred_body_tokens:
                if len(pred_body_tokens & grounded_union) / len(pred_body_tokens) < self.config.min_support_coverage:
                    pred_body_ok = False
            slot_conflict, slot_note = _evaluate_entity_slot_conflict(claim_text, span)
            scope_target = claim_text
            if (
                full_claim_text
                and required_predicate_text
                and len(_expand_coordinated_predicates_with_bodies(span)) > 1
            ):
                scope_target = full_claim_text
            scope_ok, scope_note = _evaluate_restrictive_scope(scope_target, span)

            span_word_set = index.span_word_sets[idx]
            missing_entities = [ent for ent in proper_entities if ent not in span_word_set]
            entities_ok = len(missing_entities) == 0
            role_swapped = _has_subject_object_role_swap(claim_text, span)

            topic_shared = (len(matched_tokens) >= 2) and (coverage >= 0.30 or sim >= 0.25)

            if (polarity_contradicts and topic_shared) or (num_conflict and topic_shared) or slot_conflict:
                span_outcome = EvidenceOutcome.CONTRADICTS
                note = slot_note if slot_conflict else (pol_note if polarity_contradicts else num_note)
            elif (
                polarity_ok
                and num_ok
                and scope_ok
                and entities_ok
                and conjuncts_ok
                and pred_body_ok
                and not role_swapped
                and coverage >= self.config.min_support_coverage
            ):
                span_outcome = EvidenceOutcome.SUPPORTS
                note = f"Factual alignment satisfied (coverage={coverage:.2f}, polarity, numbers & scope verified)."
            else:
                span_outcome = EvidenceOutcome.NOT_ENOUGH_EVIDENCE
                reasons = []
                if role_swapped:
                    reasons.append("subject-object role inversion between claim and evidence")
                if not polarity_ok:
                    reasons.append(pol_note)
                if not scope_ok:
                    reasons.append(scope_note)
                if not entities_ok:
                    reasons.append(f"unverified entities {missing_entities}")
                if not num_ok:
                    reasons.append(num_note)
                if not conjuncts_ok:
                    reasons.append("ungrounded conjunct segment within compound claim")
                if not pred_body_ok:
                    reasons.append("ungrounded coordinated predicate body")
                if coverage < self.config.min_support_coverage:
                    reasons.append(f"coverage {coverage:.2f} < {self.config.min_support_coverage:.2f}")
                if not reasons:
                    reasons.append("insufficient topic alignment for strict entailment")
                note = "Similarity alone insufficient: " + "; ".join(reasons)

            ref = EvidenceReference(
                doc_id=doc.doc_id,
                source_id=doc.source_id,
                source_dataset=doc.source_dataset,
                provenance=doc.provenance,
                matched_span=span,
                similarity_score=sim,
                polarity_match=polarity_ok and not slot_conflict,
                numeric_match=num_ok,
                coverage_score=round(coverage, 4),
                alignment_note=note,
                span_outcome=span_outcome.to_claim_verdict().value,
            )
            candidate_refs.append((span_outcome, coverage * 0.6 + sim * 0.4, ref))

        if not candidate_refs:
            return ClaimVerificationItem(
                claim_id=claim_id,
                claim_text=claim_text,
                outcome=EvidenceOutcome.NOT_ENOUGH_EVIDENCE,
                verdict=G3ClaimVerdict.INSUFFICIENT,
                confidence=0.90,
                unsupported_flag=True,
                supporting_evidence_refs=[],
                contradicting_evidence_refs=[],
                evidence_refs=[],
                explanation="No relevant evidence spans found in retrieved documents above threshold.",
            )

        dedup_refs: Dict[Tuple[str, str], Tuple[EvidenceOutcome, float, EvidenceReference]] = {}
        for out, rank, ref in candidate_refs:
            key = (ref.doc_id, ref.matched_span)
            if key not in dedup_refs or rank > dedup_refs[key][1]:
                dedup_refs[key] = (out, rank, ref)

        sorted_entries = sorted(dedup_refs.values(), key=lambda x: (-x[1], x[2].doc_id))
        contradict_entries = [e for e in sorted_entries if e[0] == EvidenceOutcome.CONTRADICTS]
        support_entries = [e for e in sorted_entries if e[0] == EvidenceOutcome.SUPPORTS]

        best_supp_rank_by_doc: Dict[str, float] = {}
        for _, rank, ref in support_entries:
            if ref.doc_id not in best_supp_rank_by_doc or rank > best_supp_rank_by_doc[ref.doc_id]:
                best_supp_rank_by_doc[ref.doc_id] = rank

        best_contr_rank_by_doc: Dict[str, float] = {}
        for _, rank, ref in contradict_entries:
            if ref.doc_id not in best_contr_rank_by_doc or rank > best_contr_rank_by_doc[ref.doc_id]:
                best_contr_rank_by_doc[ref.doc_id] = rank

        # Inside a single document, only suppress a contradicting span when a strictly
        # higher-or-equal-ranked supporting sub-clause exists in that same doc (e.g., contrasting clauses);
        # a weaker partial sub-clause must never silence a stronger same-doc contradiction.
        effective_contradicts = [
            e
            for e in contradict_entries
            if e[2].doc_id not in best_supp_rank_by_doc
            or best_contr_rank_by_doc[e[2].doc_id] > best_supp_rank_by_doc[e[2].doc_id] + 1e-6
        ]
        suppressed_contr_docs = {
            did
            for did, c_rank in best_contr_rank_by_doc.items()
            if did in best_supp_rank_by_doc and c_rank > best_supp_rank_by_doc[did] + 1e-6
        }
        effective_supports = [
            e for e in support_entries if e[2].doc_id not in suppressed_contr_docs
        ]
        support_doc_ids = {e[2].doc_id for e in effective_supports}
        effective_contradict_doc_ids = {e[2].doc_id for e in effective_contradicts}

        supp_refs = [e[2] for e in effective_supports[:3]]
        contr_refs = [e[2] for e in effective_contradicts[:3]]

        if effective_supports and effective_contradicts:
            final_verdict = G3ClaimVerdict.UNCERTAIN
            final_outcome = EvidenceOutcome.UNCERTAIN
            confidence = round(min(0.75, 0.50 + 0.08 * abs(len(support_doc_ids) - len(effective_contradict_doc_ids))), 4)
            explanation = (
                f"Conflicting retrieved evidence: supported by {sorted(support_doc_ids)}, "
                f"contradicted by {sorted(effective_contradict_doc_ids)} ({contr_refs[0].alignment_note})."
            )
            unsupported_flag = True
            top_refs = [supp_refs[0], contr_refs[0]] + [
                e[2] for e in sorted_entries if e[2] not in (supp_refs[0], contr_refs[0])
            ][:1]
        elif effective_contradicts:
            final_verdict = G3ClaimVerdict.CONTRADICTED
            final_outcome = EvidenceOutcome.CONTRADICTS
            best = effective_contradicts[0]
            confidence = round(min(0.99, max(0.65, best[1])), 4)
            explanation = best[2].alignment_note
            unsupported_flag = True
            top_refs = [contr_refs[0]] + [e[2] for e in sorted_entries if e[2] != contr_refs[0]][:2]
        elif effective_supports:
            if _has_unresolved_leading_pronoun(claim_text):
                final_verdict = G3ClaimVerdict.UNCERTAIN
                final_outcome = EvidenceOutcome.UNCERTAIN
                confidence = 0.55
                explanation = "Claim opens with an unresolved leading pronoun ('It'/...) lacking an explicit entity referent; cannot mark SUPPORTED."
                unsupported_flag = True
                top_refs = [e[2] for e in sorted_entries[:3]]
            else:
                final_verdict = G3ClaimVerdict.SUPPORTED
                final_outcome = EvidenceOutcome.SUPPORTS
                best = effective_supports[0]
                confidence = round(min(0.99, max(0.60, best[2].coverage_score)), 4)
                explanation = best[2].alignment_note
                unsupported_flag = False
                top_refs = [e[2] for e in sorted_entries[:3]]
        else:
            final_verdict = G3ClaimVerdict.INSUFFICIENT
            final_outcome = EvidenceOutcome.NOT_ENOUGH_EVIDENCE
            best = sorted_entries[0]
            confidence = round(max(0.55, 1.0 - best[2].coverage_score), 4)
            explanation = best[2].alignment_note
            unsupported_flag = True
            top_refs = [e[2] for e in sorted_entries[:3]]

        return ClaimVerificationItem(
            claim_id=claim_id,
            claim_text=claim_text,
            outcome=final_outcome,
            verdict=final_verdict,
            confidence=confidence,
            unsupported_flag=unsupported_flag,
            supporting_evidence_refs=supp_refs,
            contradicting_evidence_refs=contr_refs,
            evidence_refs=top_refs,
            explanation=explanation,
        )

    def verify(
        self,
        answer_text: str,
        trusted_documents: Sequence[EvidenceDocument],
        *,
        query: Optional[str] = None,
        abstained: bool = False,
        doc_trust_scores: Optional[Dict[str, float]] = None,
        min_passage_trust: float = 0.60,
    ) -> G3VerificationReport:
        """Verify all extracted claims in a generated answer using shared span representations."""
        if abstained:
            return G3VerificationReport(
                overall_status=VerificationStatus.ABSTAINED,
                verdict=G3AnswerVerdict.INSUFFICIENT_EVIDENCE,
                total_claims=0,
                supported_count=0,
                contradicted_count=0,
                not_enough_evidence_count=0,
                insufficient_count=0,
                uncertain_count=0,
                unsupported_claims=[],
                uncertain_claims=[],
                claims=[],
                summary="Answer verification skipped cleanly because pipeline abstained from generating claims.",
            )

        if not self.config.enabled:
            claims = self.extract_claims(answer_text)
            items = [
                ClaimVerificationItem(
                    claim_id=f"claim_{i + 1}",
                    claim_text=c,
                    outcome=EvidenceOutcome.NOT_ENOUGH_EVIDENCE,
                    verdict=G3ClaimVerdict.INSUFFICIENT,
                    confidence=0.0,
                    unsupported_flag=False,
                    supporting_evidence_refs=[],
                    contradicting_evidence_refs=[],
                    evidence_refs=[],
                    explanation="G3 verifier disabled by configuration.",
                )
                for i, c in enumerate(claims)
            ]
            return G3VerificationReport(
                overall_status=VerificationStatus.UNVERIFIED,
                verdict=G3AnswerVerdict.INSUFFICIENT_EVIDENCE,
                total_claims=len(items),
                supported_count=0,
                contradicted_count=0,
                not_enough_evidence_count=len(items),
                insufficient_count=len(items),
                uncertain_count=0,
                unsupported_claims=[c.claim_text for c in items],
                uncertain_claims=[],
                claims=items,
                summary="G3 verification disabled.",
            )

        raw_claims = self.extract_claims(answer_text)
        if not raw_claims:
            return G3VerificationReport(
                overall_status=VerificationStatus.UNVERIFIED,
                verdict=G3AnswerVerdict.INSUFFICIENT_EVIDENCE,
                total_claims=0,
                supported_count=0,
                contradicted_count=0,
                not_enough_evidence_count=0,
                insufficient_count=0,
                uncertain_count=0,
                unsupported_claims=[],
                uncertain_claims=[],
                claims=[],
                summary="No independently verifiable factual claims extracted from answer (conversational, opinion, or empty text).",
            )

        # Build span index & similarities ONCE for all claims in this answer
        index = self._build_evidence_index(trusted_documents)
        all_sims = self._score_claims_against_index(raw_claims, index)

        items = [
            self.verify_claim(
                f"claim_{idx}",
                claim_txt,
                trusted_documents,
                _precomputed_index=index,
                _precomputed_sims=all_sims[idx - 1],
            )
            for idx, claim_txt in enumerate(raw_claims, start=1)
        ]

        from trustrag.verification.generalization import refine_claim_with_generalization

        items = [
            refine_claim_with_generalization(item, trusted_documents, self.verify_claim)
            for item in items
        ]

        # Conservative real/model-backed judgment refinement (only upgrades INSUFFICIENT when
        # citations are substring-verified AND deterministic safety checks found zero conflict).
        if self.srm_client is not None:
            try:
                health = self.srm_client.health_check()
                if getattr(health, "is_real_model", False) and getattr(health, "available", False):
                    passages_payload = [{"doc_id": d.doc_id, "text": d.text} for d in trusted_documents]
                    doc_lookup = {d.doc_id: d for d in trusted_documents}
                    refined_items: List[ClaimVerificationItem] = []
                    for item in items:
                        if item.verdict == G3ClaimVerdict.INSUFFICIENT and passages_payload:
                            pol_ok = all(
                                _evaluate_polarity(item.claim_text, d.text)[0]
                                for d in trusted_documents
                            )
                            srm_res = self.srm_client.classify_evidence(
                                query="",
                                evidence_passages=passages_payload,
                                candidate_answer=item.claim_text,
                            )
                            top_j = srm_res.claim_judgments[0] if srm_res.claim_judgments else None
                            if (
                                top_j is not None
                                and not srm_res.is_fallback
                                and top_j.outcome == EvidenceOutcome.SUPPORTS
                                and top_j.verified_citations
                                and top_j.evidence_ids
                                and pol_ok
                            ):
                                cited_docs = [doc_lookup[eid] for eid in top_j.evidence_ids if eid in doc_lookup]
                                if cited_docs:
                                    ev_ref = EvidenceReference(
                                        doc_id=cited_docs[0].doc_id,
                                        source_id=cited_docs[0].source_id,
                                        source_dataset=cited_docs[0].source_dataset,
                                        provenance=cited_docs[0].provenance,
                                        matched_span=top_j.cited_spans[0] if top_j.cited_spans else cited_docs[0].text[:220],
                                        similarity_score=0.80,
                                        polarity_match=True,
                                        numeric_match=True,
                                        coverage_score=0.80,
                                        alignment_note=f"Model-backed G3 support verified via cited span ({srm_res.model_name}).",
                                        span_outcome="SUPPORTED",
                                    )
                                    item = item.model_copy(
                                        update={
                                            "outcome": EvidenceOutcome.SUPPORTS,
                                            "verdict": G3ClaimVerdict.SUPPORTED,
                                            "unsupported_flag": False,
                                            "confidence": round(min(0.95, float(top_j.confidence)), 4),
                                            "supporting_evidence_refs": [ev_ref],
                                            "evidence_refs": [ev_ref],
                                            "explanation": ev_ref.alignment_note,
                                        }
                                    )
                        refined_items.append(item)
                    items = refined_items
            except Exception as exc:
                LOGGER.warning("Model-backed G3 judge skipped cleanly: %s", exc)

        # Paper B Sec 6.3: Claims backed exclusively by low-trust passages are weakly grounded
        if doc_trust_scores:
            trust_checked: List[ClaimVerificationItem] = []
            for item in items:
                if item.verdict == G3ClaimVerdict.SUPPORTED and item.supporting_evidence_refs:
                    supp_scores = [doc_trust_scores.get(r.doc_id) for r in item.supporting_evidence_refs]
                    known_scores = [s for s in supp_scores if s is not None]
                    if known_scores and max(known_scores) < min_passage_trust:
                        item = item.model_copy(
                            update={
                                "outcome": EvidenceOutcome.UNCERTAIN,
                                "verdict": G3ClaimVerdict.UNCERTAIN,
                                "unsupported_flag": True,
                                "confidence": round(min(item.confidence, 0.50), 4),
                                "explanation": (
                                    f"Weakly grounded: claim supported only by low-trust passage(s) "
                                    f"(max_trust={max(known_scores):.2f} < {min_passage_trust:.2f})."
                                ),
                            }
                        )
                trust_checked.append(item)
            items = trust_checked

        supported = [c for c in items if c.verdict == G3ClaimVerdict.SUPPORTED]
        contradicted = [c for c in items if c.verdict == G3ClaimVerdict.CONTRADICTED]
        uncertain = [c for c in items if c.verdict == G3ClaimVerdict.UNCERTAIN]
        insufficient = [c for c in items if c.verdict == G3ClaimVerdict.INSUFFICIENT]
        unsupported = [c.claim_text for c in items if c.unsupported_flag]

        # Deterministic Answer-Level Aggregation Logic:
        # 1. Any directly contradicted claim -> CONTRADICTED
        # 2. Any uncertain/conflicting claim -> UNCERTAIN
        # 3. All claims supported (0 insufficient) -> SUPPORTED (VERIFIED)
        # 4. At least 1 supported alongside >= 1 insufficient -> PARTIALLY_SUPPORTED
        # 5. Otherwise -> INSUFFICIENT_EVIDENCE (UNVERIFIED)
        if contradicted:
            verdict = G3AnswerVerdict.CONTRADICTED
            overall_status = VerificationStatus.CONTRADICTED
        elif uncertain:
            verdict = G3AnswerVerdict.UNCERTAIN
            overall_status = VerificationStatus.UNCERTAIN
        elif len(supported) == len(items):
            verdict = G3AnswerVerdict.SUPPORTED
            overall_status = VerificationStatus.VERIFIED
        elif supported:
            verdict = G3AnswerVerdict.PARTIALLY_SUPPORTED
            overall_status = VerificationStatus.PARTIALLY_SUPPORTED
        else:
            verdict = G3AnswerVerdict.INSUFFICIENT_EVIDENCE
            overall_status = VerificationStatus.UNVERIFIED

        query_consistent: Optional[bool] = None
        query_consistency_score: Optional[float] = None
        query_consistency_reasons: List[str] = []
        if query is not None and self.config.enable_query_consistency:
            from trustrag.verification.query_consistency import evaluate_query_consistency

            qc = evaluate_query_consistency(
                query,
                answer_text,
                trusted_documents,
                abstained=abstained,
                min_consistency_score=self.config.min_query_consistency_score,
            )
            query_consistent = qc.consistent
            query_consistency_score = qc.consistency_score
            query_consistency_reasons = list(qc.reasons)
            if not qc.consistent and overall_status in {
                VerificationStatus.VERIFIED,
                VerificationStatus.PARTIALLY_SUPPORTED,
            }:
                verdict = G3AnswerVerdict.INSUFFICIENT_EVIDENCE
                overall_status = VerificationStatus.UNVERIFIED

        summary = (
            f"Verified {len(items)} claim(s): "
            f"SUPPORTED={len(supported)}, CONTRADICTED={len(contradicted)}, "
            f"INSUFFICIENT={len(insufficient)}, UNCERTAIN={len(uncertain)} "
            f"-> verdict={verdict.value} (evidence-grounded status={overall_status.value}; "
            "represents retrieved-evidence alignment rather than guaranteed external truth)."
        )

        LOGGER.info(
            "G3 evidence verification completed",
            extra={
                "overall_status": overall_status.value,
                "verdict": verdict.value,
                "total_claims": len(items),
                "supported_count": len(supported),
                "contradicted_count": len(contradicted),
                "insufficient_count": len(insufficient),
                "uncertain_count": len(uncertain),
                "query_consistent": query_consistent,
            },
        )

        return G3VerificationReport(
            overall_status=overall_status,
            verdict=verdict,
            total_claims=len(items),
            supported_count=len(supported),
            contradicted_count=len(contradicted),
            not_enough_evidence_count=len(insufficient) + len(uncertain),
            insufficient_count=len(insufficient),
            uncertain_count=len(uncertain),
            unsupported_claims=unsupported,
            uncertain_claims=[c.claim_text for c in uncertain],
            claims=items,
            summary=summary,
            query_consistent=query_consistent,
            query_consistency_score=query_consistency_score,
            query_consistency_reasons=query_consistency_reasons,
        )


__all__ = ["OutputEvidenceVerifier"]
