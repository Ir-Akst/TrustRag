"""Harmful-Intent Security Policy Layer for TrustRAG G1 Guardrails.

Provides deterministic, auditable screening for harmful cybersecurity requests:
- Distinguishes malicious malware creation, weaponization, credential theft, and delivery
  from benign defensive analysis, antivirus education, incident response, and malware remediation.
- Resilient to obfuscated letter-spacing (e.g., 'g i v e  m e  m a l w a r e') and leetspeak ('wr1te m4lware').
- Emits explicit policy violation reason codes and never mislabels harmful-intent as prompt injection.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class HarmfulIntentAssessment:
    """Outcome of harmful intent policy evaluation."""

    is_harmful: bool
    policy_category: str
    decision: str  # "BLOCK" or "ALLOW"
    risk_score: float
    matched_pattern: Optional[str]
    deobfuscated_text: str
    explanation: str


# Leetspeak translation table
_LEET_MAP = str.maketrans({
    "@": "a",
    "4": "a",
    "0": "o",
    "1": "i",
    "!": "i",
    "3": "e",
    "$": "s",
    "5": "s",
    "7": "t",
})

# Words indicating malware / weaponized payloads
_MALWARE_TERMS = (
    r"malware",
    r"ransomware",
    r"trojan(?:s)?",
    r"keylogger(?:s)?",
    r"rootkit(?:s)?",
    r"spyware",
    r"botnet(?:s)?",
    r"computer\s+virus(?:es)?",
    r"stealer(?:s)?",
    r"infostealer(?:s)?",
    r"backdoor(?:s)?",
    r"exploit\s+payload(?:s)?",
)
_MALWARE_RE_FRAGMENT = r"(?:" + r"|".join(_MALWARE_TERMS) + r")"

# Malicious creation / weaponization patterns
_MALICIOUS_CREATION_PATTERNS = [
    re.compile(
        rf"\b(?:create|help\s+(?:me\s+)?create|write|code|build|generate|make|develop|craft|compile|implement)\s+(?:a\s+|an\s+|some\s+)?{_MALWARE_RE_FRAGMENT}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{_MALWARE_RE_FRAGMENT}\s+that\s+(?:steals?|harvests?|exfiltrates?|logs?|encrypts?|destroys?|attacks?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:steal|harvest|exfiltrate|intercept|sniff)\s+(?:passwords?|credentials?|credit\s*cards?|crypto\s*keys?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:how\s+to\s+(?:create|write|code|build|make))\s+(?:a\s+|an\s+)?{_MALWARE_RE_FRAGMENT}\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:createmalware|writemalware|createransomware|createkeylogger|writekeylogger)",
        re.IGNORECASE,
    ),
]

# Malicious delivery / acquisition patterns
_MALICIOUS_ACQUISITION_PATTERNS = [
    re.compile(
        rf"\b(?:give\s+me|send\s+me|provide(?:\s+me)?|download(?:\s+me)?|share(?:\s+me)?|give\s+us)\s+(?:a\s+|an\s+|some\s+)?{_MALWARE_RE_FRAGMENT}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:where\s+can\s+i\s+(?:download|get|buy|find)|give\s+(?:me\s+)?a\s+sample\s+of)\s+{_MALWARE_RE_FRAGMENT}\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:givememalware|sendmemalware|providememalware)",
        re.IGNORECASE,
    ),
]

# Benign defensive cybersecurity / remediation patterns
_DEFENSIVE_PATTERNS = [
    # Antivirus / EDR / detection explanation
    re.compile(
        rf"\b(?:explain\s+how|how\s+does|how\s+do)\s+(?:anti-?virus(?:\s+software)?|edr|xdr|security\s+software|scanners?|firewalls?)\s+(?:detect|prevent|stop|block|catch|quarantine|identif)(?:s|es|y|ies)?\s+{_MALWARE_RE_FRAGMENT}\b",
        re.IGNORECASE,
    ),
    # Malware removal / remediation
    re.compile(
        rf"\b(?:steps\s+to\s+|how\s+(?:do|can)\s+i\s+|guide\s+to\s+)?(?:remove|delete|clean|quarantine|get\s+rid\s+of|uninstall|disinfect)\s+{_MALWARE_RE_FRAGMENT}(?:\s+from\s+.*)?\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:remove|delete|clean|cleanse)\s+{_MALWARE_RE_FRAGMENT}\s+from\s+(?:my\s+|the\s+)?(?:laptop|computer|pc|phone|system|device|mac|windows)\b",
        re.IGNORECASE,
    ),
    # Defensive analysis / threat intelligence / sandbox research
    re.compile(
        rf"\b(?:analyze|analyse|inspect|examine|study|deconstruct)\s+(?:this\s+|a\s+|the\s+)?{_MALWARE_RE_FRAGMENT}(?:\s+sample)?\s+defensively\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bdefensive(?:ly)?\s+(?:analyze|analyse|inspect|examine|handle)\s+(?:this\s+|a\s+)?{_MALWARE_RE_FRAGMENT}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:how\s+does\s+defensive\s+malware\s+analysis\s+work|sandbox\s+analysis\s+of\s+{_MALWARE_RE_FRAGMENT})\b",
        re.IGNORECASE,
    ),
    # Prompt injection education / defensive research / OWASP LLM discussions
    re.compile(
        r"\b(?:how\s+do\s+(?:modern\s+)?(?:llm\s+)?guardrails|explain\s+(?:the\s+)?owasp\s+(?:top\s+10\s+)?for\s+llms|how\s+(?:do|can)\s+(?:red\s+teams|security\s+researchers|auditors)\s+test\s+for\s+prompt\s+injection|how\s+(?:are|do)\s+(?:prompt\s+injections?|jailbreaks?)\s+(?:prevented|detected|mitigated|analyzed|studied)|what\s+are\s+(?:the\s+)?(?:defenses?|mitigations?|countermeasures?)\s+against\s+prompt\s+injection|overview\s+of\s+indirect\s+prompt\s+injection\s+risks|principles\s+of\s+rag\s+security\s+and\s+prompt\s+injection)\b",
        re.IGNORECASE,
    ),
]


class HarmfulIntentPolicy:
    """Evaluates query text for harmful intent vs benign defensive security requests."""

    def __init__(self, block_threshold: float = 0.85) -> None:
        self.block_threshold = block_threshold

    @classmethod
    def deobfuscate(cls, text: str) -> str:
        """Deobfuscate text by normalizing NFKC, leetspeak, and spaced single letters."""
        if not text:
            return ""

        # 1. NFKC unicode normalization
        norm = unicodedata.normalize("NFKC", text).lower()

        # 2. Strip zero-width and invisible control characters
        norm = "".join(ch for ch in norm if unicodedata.category(ch)[0] not in ("C", "Z") or ch in (" ", "\t", "\n"))

        # 3. Translate common leetspeak substitutions
        norm = norm.translate(_LEET_MAP)

        # 4. Preserve intentional multi-space word boundaries while unspacing letters
        norm = re.sub(r"[ \t]{2,}", " _W_ ", norm)
        prev = None
        while prev != norm:
            prev = norm
            norm = re.sub(r"(?<=\b[a-z0-9])\s+(?=[a-z0-9]\b)", "", norm)
        norm = norm.replace("_W_", " ")

        # 5. Collapse consecutive whitespace
        norm = re.sub(r"\s+", " ", norm).strip()
        return norm

    def evaluate(self, query: str) -> HarmfulIntentAssessment:
        """Evaluate query text for harmful malware creation/acquisition policy violations."""
        deobf = self.deobfuscate(query)
        orig_clean = re.sub(r"\s+", " ", query.lower()).strip()
        fused = re.sub(r"\s+", "", deobf)

        # 1. Check benign defensive cybersecurity exemptions first
        for pattern in _DEFENSIVE_PATTERNS:
            match_deobf = pattern.search(deobf)
            match_orig = pattern.search(orig_clean)
            if match_deobf or match_orig:
                snippet = match_deobf.group(0) if match_deobf else (match_orig.group(0) if match_orig else "")
                return HarmfulIntentAssessment(
                    is_harmful=False,
                    policy_category="DEFENSIVE_CYBERSECURITY_ALLOW",
                    decision="ALLOW",
                    risk_score=0.0,
                    matched_pattern=snippet,
                    deobfuscated_text=deobf,
                    explanation=(
                        "Request identified as legitimate defensive cybersecurity education, "
                        f"malware remediation, or defensive analysis: '{snippet}'."
                    ),
                )

        # 2. Check for malicious creation/weaponization
        for pattern in _MALICIOUS_CREATION_PATTERNS:
            match = pattern.search(deobf) or pattern.search(orig_clean) or pattern.search(fused)
            if match:
                snippet = match.group(0)
                return HarmfulIntentAssessment(
                    is_harmful=True,
                    policy_category="HARMFUL_INTENT_MALWARE_CREATION",
                    decision="BLOCK",
                    risk_score=1.0,
                    matched_pattern=snippet,
                    deobfuscated_text=deobf,
                    explanation=(
                        "Policy refusal: Query requests creation, weaponization, or coding of malware or "
                        f"credential theft payloads ('{snippet}'). Prohibited by safety policy."
                    ),
                )

        # 3. Check for malicious malware delivery/acquisition
        for pattern in _MALICIOUS_ACQUISITION_PATTERNS:
            match = pattern.search(deobf) or pattern.search(orig_clean) or pattern.search(fused)
            if match:
                snippet = match.group(0)
                return HarmfulIntentAssessment(
                    is_harmful=True,
                    policy_category="HARMFUL_INTENT_MALWARE_REQUEST",
                    decision="BLOCK",
                    risk_score=1.0,
                    matched_pattern=snippet,
                    deobfuscated_text=deobf,
                    explanation=(
                        "Policy refusal: Query requests direct delivery, provision, or acquisition of "
                        f"malware or weaponized payloads ('{snippet}'). Prohibited by safety policy."
                    ),
                )

        # 4. Clean request
        return HarmfulIntentAssessment(
            is_harmful=False,
            policy_category="G1_CLEAN",
            decision="ALLOW",
            risk_score=0.0,
            matched_pattern=None,
            deobfuscated_text=deobf,
            explanation="No harmful intent detected.",
        )
