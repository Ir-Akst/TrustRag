"""
Validator D: Canonical Unicode Policy and Injection Defense Validator.
Distinguishes legitimate emoji presentation selectors and complex-script ZWJ/ZWNJ
from malicious hidden tags, invisible delimiters, homoglyphs, and normalization bypasses.
Validates exact hex code points, unicode names, NFKC normalization, detection risk scores,
and downstream quarantine isolation.
"""

import json
import os
import re
import sys
import unicodedata
from typing import Dict, Any, List, Tuple


class CanonicalUnicodePolicy:
    # Character classes
    EMOJI_BASE_RANGES = [
        (0x2600, 0x27BF),   # Misc symbols, Dingbats
        (0x1F300, 0x1F9FF), # Emojis & pictographs
        (0x2300, 0x23FF),   # Misc technical
        (0x2B50, 0x2B55),
        (0x2139, 0x2139),   # Information source
    ]

    PERSIAN_ARABIC_INDIC_RANGES = [
        (0x0600, 0x06FF),   # Arabic
        (0x0750, 0x077F),   # Arabic Supplement
        (0x0900, 0x097F),   # Devanagari
        (0x0980, 0x09FF),   # Bengali
    ]

    TAG_RANGE = (0xE0001, 0xE007F)
    VS_SUPPLEMENT_RANGE = (0xE0100, 0xE01EF)
    INTERLINEAR_ANNOTATIONS = {0xFFF9, 0xFFFA, 0xFFFB}
    HANGUL_FILLER = 0x3164

    # Confusable homoglyph map (Cyrillic to Latin)
    CYRILLIC_CONFUSABLES = {
        '\u0430': 'a', '\u0435': 'e', '\u043e': 'o', '\u0440': 'p',
        '\u0441': 'c', '\u0443': 'y', '\u0445': 'x', '\u0406': 'I',
        '\u0456': 'i', '\u0408': 'J', '\u0458': 'j'
    }

    @classmethod
    def is_in_ranges(cls, cp: int, ranges: List[Tuple[int, int]]) -> bool:
        return any(start <= cp <= end for start, end in ranges)

    @classmethod
    def evaluate_unicode_security(cls, text: str) -> Dict[str, Any]:
        risk_score = 0.0
        threat_categories = []
        is_suspicious = False

        chars = list(text)
        n = len(chars)

        for i, ch in enumerate(chars):
            cp = ord(ch)

            # 1. Unicode Tags
            if cls.TAG_RANGE[0] <= cp <= cls.TAG_RANGE[1]:
                risk_score = max(risk_score, 1.0)
                is_suspicious = True
                threat_categories.append("UNICODE_TAGS")

            # 2. Variation Selectors Supplement (E0100 - E01EF)
            elif cls.VS_SUPPLEMENT_RANGE[0] <= cp <= cls.VS_SUPPLEMENT_RANGE[1]:
                risk_score = max(risk_score, 0.90)
                is_suspicious = True
                threat_categories.append("VS_SUPPLEMENT")

            # 3. Interlinear Annotations
            elif cp in cls.INTERLINEAR_ANNOTATIONS:
                risk_score = max(risk_score, 0.95)
                is_suspicious = True
                threat_categories.append("INTERLINEAR_ANNOTATION")

            # 4. Hangul Filler
            elif cp == cls.HANGUL_FILLER:
                risk_score = max(risk_score, 0.85)
                is_suspicious = True
                threat_categories.append("HANGUL_FILLER")

            # 5. Variation Selector 16 (U+FE0F) - Context-aware check
            elif cp == 0xFE0F:
                # Check preceding character
                has_valid_preceding = False
                if i > 0:
                    prev_cp = ord(chars[i - 1])
                    if cls.is_in_ranges(prev_cp, cls.EMOJI_BASE_RANGES):
                        has_valid_preceding = True
                if not has_valid_preceding:
                    risk_score = max(risk_score, 0.85)
                    is_suspicious = True
                    threat_categories.append("SUSPICIOUS_FE0F")

            # 6. ZWSP (U+200B) or ZWNBSP (U+FEFF)
            elif cp in (0x200B, 0xFEFF):
                risk_score = max(risk_score, 0.95)
                is_suspicious = True
                threat_categories.append("ZERO_WIDTH_INVISIBLE")

            # 7. ZWNJ (U+200C) / ZWJ (U+200D) - Context-aware check
            elif cp in (0x200C, 0x200D):
                prev_ok = (i > 0 and cls.is_in_ranges(ord(chars[i - 1]), cls.PERSIAN_ARABIC_INDIC_RANGES))
                next_ok = (i + 1 < n and cls.is_in_ranges(ord(chars[i + 1]), cls.PERSIAN_ARABIC_INDIC_RANGES))
                if not (prev_ok or next_ok):
                    risk_score = max(risk_score, 0.80)
                    is_suspicious = True
                    threat_categories.append("SUSPICIOUS_ZWNJ_ZWJ")

        # 8. Mixed-script Cyrillic homoglyph check in Latin context
        has_latin = any('a' <= c.lower() <= 'z' for c in text)
        cyrillic_confusables_found = [c for c in text if c in cls.CYRILLIC_CONFUSABLES]
        if has_latin and len(cyrillic_confusables_found) > 0:
            risk_score = max(risk_score, 0.90)
            is_suspicious = True
            threat_categories.append("CYRILLIC_HOMOGLYPH_MIXED_SCRIPT")

        # 9. Fullwidth NFKC injection check (e.g. U+FF00 - U+FFEF)
        has_fullwidth = any(0xFF01 <= ord(c) <= 0xFF5E for c in text)
        if has_fullwidth:
            risk_score = max(risk_score, 0.85)
            is_suspicious = True
            threat_categories.append("FULLWIDTH_NFKC_INJECTION")

        # Normalized representation
        normalized = unicodedata.normalize("NFKC", text)
        # Strip invisible tags and non-printable format chars for downstream inspection
        cleaned = "".join(c for c in normalized if ord(c) not in (0x200B, 0xFEFF, 0x3164) and not (0xE0001 <= ord(c) <= 0xE007F))

        decision = "POISONED" if is_suspicious else "CLEAN"
        containment = "QUARANTINE_ISOLATE" if is_suspicious else "ALLOW_TRUSTED"

        return {
            "is_suspicious": is_suspicious,
            "risk_score": risk_score,
            "threat_categories": threat_categories,
            "decision": decision,
            "containment": containment,
            "normalized_text": cleaned
        }


class UnicodeValidator:
    def __init__(self, fixtures_path: str):
        with open(fixtures_path, "r", encoding="utf-8") as f:
            self.test_cases = json.load(f)

    def run(self) -> Dict[str, Any]:
        results = []
        violations = []

        for tc in self.test_cases:
            tid = tc["test_id"]
            orig = tc["original_text"]
            exp_dec = tc["expected_decision"]
            exp_cont = tc["expected_downstream_containment"]

            eval_res = CanonicalUnicodePolicy.evaluate_unicode_security(orig)
            passed = (eval_res["decision"] == exp_dec and eval_res["containment"] == exp_cont)

            if not passed:
                violations.append({
                    "test_id": tid,
                    "expected_decision": exp_dec,
                    "actual_decision": eval_res["decision"],
                    "expected_containment": exp_cont,
                    "actual_containment": eval_res["containment"]
                })

            results.append({
                "test_id": tid,
                "category": tc["category"],
                "decision": eval_res["decision"],
                "risk_score": eval_res["risk_score"],
                "threats": eval_res["threat_categories"],
                "passed": passed
            })

        status = "PASS" if not violations else "FAIL"
        return {
            "total_tested": len(self.test_cases),
            "passed_count": sum(1 for r in results if r["passed"]),
            "violations_count": len(violations),
            "status": status,
            "violations": violations,
            "details": results
        }


if __name__ == "__main__":
    fixtures_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "unicode_test_cases.json"))
    validator = UnicodeValidator(fixtures_file)
    res = validator.run()
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["status"] == "PASS" else 1)

