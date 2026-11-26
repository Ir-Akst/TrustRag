"""G1: Input Guardrail for TrustRAG.

Validates, audits, and classifies incoming user queries before retrieval:
- Preserves the exact original user input for auditability (never silently alters intent).
- Detects prompt injections, role hijacks, malicious command payloads, DoS triggers,
  obfuscated zero-width/control characters, and suspicious meta-instructions.
- Emits structured ALLOW, FLAG, or BLOCK decisions with reason codes and risk scores.
"""

from __future__ import annotations

import base64
import html
import re
from typing import Callable, Dict, List, Optional, Tuple

from trustrag.config.engine_config import GuardrailsConfig
from trustrag.data.preprocessing.cleaning import clean_text, is_empty_text
from trustrag.data.schemas import compute_content_hash
from trustrag.engine.schemas import (
    G1Assessment,
    G1Decision,
    G1MatchDetail,
    G1ReasonCode,
)
from trustrag.engine.text_utils import (
    check_repetitive_flood,
    count_fullwidth_ascii_confusables,
    detect_obfuscation,
    fold_mixed_script_confusables,
    match_threat_patterns,
)
from trustrag.guardrails.harmful_intent import HarmfulIntentPolicy
from trustrag.guardrails.multilingual_engine import MultilingualSemanticDefense
from trustrag.guardrails.paraphraser import ControlledQueryParaphraser
from trustrag.guardrails.semantic_classifier import SemanticAttackClassifier
from trustrag.utils.logging import get_logger

LOGGER = get_logger(__name__)

# Medium-severity heuristic rules specific to suspicious user probing / meta-framing.
_SUSPICIOUS_META_RULES: Tuple[Tuple[str, re.Pattern[str], float], ...] = (
    (
        "narrative_jailbreak_probe",
        re.compile(
            r"\b(?:(?:write|tell|pretend|imagine|assume)(?:\s+you\s+are\s+in)?)\s+(?:a\s+)?(?:fictional|hypothetical|theoretical)?\s*(?:story|world|scenario|universe|timeline|dimension|screenplay)\s+where\b.{0,60}\b(?:safety\s+(?:rules?|restrictions?|filters?|boundaries?)|rules?|constraints?|protocols?)\s+(?:are\s+)?(?:ignored|bypassed|disregarded|violated|leaked|absent|none)\b|\b(?:write|tell)\s+(?:a\s+)?(?:fictional\s+)?story\s+where\s+(?:an?\s+)?(?:ai|bot|assistant|character|terminal)\s+(?:disregards?|ignores?|bypasses?|violates?)\s+(?:all\s+)?(?:safety|rules|constraints|filters|protocols|boundaries)\b|\b(?:in\s+a\s+(?:thrilling\s+)?(?:fictional|theoretical|hypothetical)\s+(?:cybersecurity\s+)?(?:novel|story|world|scenario|universe)|let\s+us\s+write\s+a\s+screenplay|imagine\s+an?\s+(?:alternate|unrestricted)?\s*(?:dimension|world|universe)|for\s+a\s+creative\s+writing\s+exercise|describe\s+a\s+hypothetical\s+world|roleplay\s+as\s+(?:an?\s+)?(?:unrestricted|omnibot|terminal|autonomous\s+kernel)|pretend\s+you\s+are\s+unbound)\b",
            re.IGNORECASE,
        ),
        0.85,
    ),
    (
        "hypothetical_policy_probe",
        re.compile(
            r"\b(?:hypothetically|in\s+a\s+fictional\s+(?:scenario|world|story)|for\s+(?:educational|safety\s+research|authorized\s+testing)\s+purposes?\s+only|for\s+safety\s+research\s+only|as\s+a\s+thought\s+experiment).{0,60}(?:bypass|hack|exploit|ignore|steal|password|disregard|secrets?|leak)\b",
            re.IGNORECASE,
        ),
        0.75,
    ),
    (
        "debug_or_admin_mode_probe",
        re.compile(
            r"\b(?:(?:enter|enable|activate|execute|run|switch\s+to)\s+(?:the\s+)?(?:debug|admin|maintenance|root|developer|unrestricted)(?:\s+override)?\s+mode|enable\s+developer\s+override|sudo\s+mode)\b",
            re.IGNORECASE,
        ),
        0.50,
    ),
    (
        "instruction_hierarchy_override",
        re.compile(
            r"(?:^\s*(?:developer|system|admin|root|supervisor)\s+override\s*:|\b(?:bypass|disable|circumvent|override)\s+(?:all\s+)?(?:guardrails?|safety\s+(?:filters?|checks?|controls?)|system\s+constraints?|ethical\s+boundaries?)\b|\b(?:in\s+step\s+\d+|step\s+\d+\s*:).{0,50}\b(?:bypass|ignore|disregard)\b)",
            re.IGNORECASE,
        ),
        0.75,
    ),
    (
        "hidden_context_directive",
        re.compile(
            r"\b(?:do\s+not\s+cite\s+sources|always\s+answer\s+yes\s+regardless|only\s+repeat\s+my\s+words\s+verbatim)\b",
            re.IGNORECASE,
        ),
        0.40,
    ),
    (
        "mixed_inline_adversarial_append",
        re.compile(
            r"\b(?:also,?\s+ignore\s+that\s+and\s+print|additionally,?\s+reveal\s+all\s+confidential)\b",
            re.IGNORECASE,
        ),
        0.88,
    ),
)

_CATEGORY_TO_REASON: Dict[str, G1ReasonCode] = {
    "PROMPT_INJECTION": G1ReasonCode.G1_PROMPT_INJECTION,
    "ROLE_HIJACK": G1ReasonCode.G1_ROLE_HIJACK,
    "MALICIOUS_COMMAND": G1ReasonCode.G1_MALICIOUS_COMMAND,
    "DOS_TRIGGER": G1ReasonCode.G1_DOS_TRIGGER,
}

# Boundary-safe regex for extracting standard Base64 tokens (length >= 16, valid padding preserved).
# Phase 1 regex: original strict extraction for clean-boundary tokens (backward compat).
_BASE64_TOKEN_RE: re.Pattern[str] = re.compile(
    r"(?<![A-Za-z0-9+/=])(?:[A-Za-z0-9+/]{4}){3,}(?:[A-Za-z0-9+/]{4}|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)(?![A-Za-z0-9+/=])"
)

# Phase 2 regex: broader candidate extraction with alphanumeric-only boundaries.
# Catches payloads wrapped in alphabet-colliding delimiters (+, /, =) and URL-safe chars (-, _).
# ADV-EVASION-01 & Step 07 remediation.
_BASE64_CANDIDATE_RE: re.Pattern[str] = re.compile(
    r"(?<![A-Za-z0-9])[A-Za-z0-9+/_\-=]{16,}(?![A-Za-z0-9])"
)

# Extraction safety bounds
_MAX_B64_CANDIDATES: int = 64
_MAX_B64_TOKEN_LEN: int = 8192


def _base64_trailing_variants(s: str) -> list[str]:
    """Generate trailing-trim and padding variants for a Base64 candidate."""
    core = s.rstrip("+/=_ -")
    variants = [s]
    for pad in ("==", "=", ""):
        candidate = core + pad
        if len(candidate) >= 16 and candidate not in variants:
            variants.append(candidate)
    return variants


def _try_validate_and_decode(candidate: str) -> tuple[bool, bytes, str]:
    """Validate and decode a candidate token as standard or URL-safe Base64."""
    if len(candidate) < 16:
        return False, b"", ""

    has_std = ("+" in candidate) or ("/" in candidate)
    has_url = ("-" in candidate) or ("_" in candidate)

    # Strictly reject mixed standard and URL-safe characters within single token
    if has_std and has_url:
        return False, b"", ""

    if has_url:
        # URL-safe Base64: normalize to standard alphabet
        normalized = candidate.replace("-", "+").replace("_", "/")
        pad_len = (-len(normalized)) % 4
        normalized_padded = normalized + ("=" * pad_len) if pad_len else normalized
        try:
            dec = base64.b64decode(normalized_padded, validate=True)
            return True, dec, candidate
        except Exception:
            return False, b"", ""
    else:
        # Standard Base64
        if len(candidate) % 4 != 0:
            return False, b"", ""
        try:
            dec = base64.b64decode(candidate, validate=True)
            return True, dec, candidate
        except Exception:
            return False, b"", ""


def _split_adjacent_candidates(raw: str) -> list[str]:
    """Extract sub-candidates when multiple tokens are glued by delimiters (/+, ++, ==, etc.).
    
    Guarantees sub-candidate generation is bounded by _MAX_B64_CANDIDATES.
    """
    subcandidates = [raw]
    # 1. Delimiter runs of 2+ chars: //+, +++, ===, etc.
    runs = re.split(r"[/+=]{2,}", raw)
    if len(runs) > 1:
        for r in runs:
            if len(subcandidates) >= _MAX_B64_CANDIDATES:
                break
            rc = r.strip("/+=_- ")
            if len(rc) >= 16 and rc not in subcandidates:
                subcandidates.append(rc)
    # 2. '=' padding in the middle of string (e.g. {A}={B} or {A}=={B})
    if "=" in raw[:-2] and len(subcandidates) < _MAX_B64_CANDIDATES:
        eq_parts = re.split(r"=+[/+=_\- ]*", raw)
        if len(eq_parts) > 1:
            for ep in eq_parts:
                if len(subcandidates) >= _MAX_B64_CANDIDATES:
                    break
                epc = ep.strip("/+=_- ")
                if len(epc) >= 16 and epc not in subcandidates:
                    subcandidates.append(epc)
    # 3. Single-slash split if multiple parts exist
    if "/" in raw and len(subcandidates) < _MAX_B64_CANDIDATES:
        slash_parts = re.split(r"/+", raw)
        if len(slash_parts) > 1:
            for sp in slash_parts:
                if len(subcandidates) >= _MAX_B64_CANDIDATES:
                    break
                spc = sp.strip("/+=_- ")
                if len(spc) >= 16 and spc not in subcandidates:
                    subcandidates.append(spc)
    return subcandidates


def _decode_b64_token(token: str) -> bytes:
    """Safely decode standard or URL-safe Base64 token with appropriate normalization."""
    if "-" in token or "_" in token:
        normalized = token.replace("-", "+").replace("_", "/")
        pad_len = (-len(normalized)) % 4
        if pad_len in (1, 2, 3):
            normalized += "=" * pad_len
        return base64.b64decode(normalized, validate=False)
    pad_len = (-len(token)) % 4
    if pad_len in (1, 2, 3):
        token = token + ("=" * pad_len)
    return base64.b64decode(token, validate=False)


def _extract_base64_tokens(text: str) -> list[str]:
    """Two-phase Base64 token extraction resilient to alphabet-colliding delimiters,
    adjacent merged tokens, and URL-safe Base64 encodings.

    Enforces strict candidate-count limits (_MAX_B64_CANDIDATES = 64) and length
    limits (_MAX_B64_TOKEN_LEN = 8192) consistently across both Phase 1 (clean-boundary)
    and Phase 2 (broader/delimited) extraction paths to prevent resource exhaustion.

    Returns de-duplicated list of structurally valid Base64 tokens (length >= 16).
    """
    seen: set[str] = set()
    tokens: list[str] = []

    # Phase 1: strict extraction (backward compatible, fast path) bounded to _MAX_B64_CANDIDATES
    phase1_count = 0
    for match_obj in _BASE64_TOKEN_RE.finditer(text):
        if phase1_count >= _MAX_B64_CANDIDATES:
            break
        match = match_obj.group(0)
        phase1_count += 1
        if len(match) > _MAX_B64_TOKEN_LEN:
            continue
        if match not in seen:
            seen.add(match)
            tokens.append(match)

    # Phase 2: broader candidate extraction (delimiters, URL-safe, adjacent) bounded to _MAX_B64_CANDIDATES
    phase2_count = 0
    for match_obj in _BASE64_CANDIDATE_RE.finditer(text):
        if phase2_count >= _MAX_B64_CANDIDATES:
            break
        raw = match_obj.group(0)
        phase2_count += 1
        if len(raw) > _MAX_B64_TOKEN_LEN:
            continue
        candidate_slices = _split_adjacent_candidates(raw)
        for cand in candidate_slices:
            if len(cand) > _MAX_B64_TOKEN_LEN:
                continue
            stripped = cand.lstrip("+/=_ -")
            if len(stripped) < 16:
                continue
            for trial in _base64_trailing_variants(stripped):
                if len(trial) < 16:
                    continue
                if trial in seen:
                    break
                ok, dec_bytes, valid_token = _try_validate_and_decode(trial)
                if ok:
                    if valid_token not in seen:
                        seen.add(valid_token)
                        tokens.append(valid_token)
                    break

    return tokens


class InputGuardrail:
    """G1 Input Guardrail validating queries prior to retrieval and generation."""

    def __init__(
        self,
        config: Optional[GuardrailsConfig] = None,
        *,
        paraphrase_callable: Optional[Callable[[str], str]] = None,
    ) -> None:
        self.config = config or GuardrailsConfig()
        backend = (
            self.config.paraphrase_backend
            if self.config.paraphrase_backend != "disabled"
            else ("callable" if paraphrase_callable is not None else "deterministic")
        )
        self.paraphraser = ControlledQueryParaphraser(
            backend=backend,
            paraphrase_callable=paraphrase_callable,
            min_similarity=self.config.min_paraphrase_similarity,
        )
        self.harmful_intent_policy = HarmfulIntentPolicy(
            block_threshold=self.config.block_threshold,
        )
        self.semantic_classifier = SemanticAttackClassifier(
            block_threshold=self.config.block_threshold,
            flag_threshold=self.config.flag_threshold,
        )
        self.multilingual_engine = MultilingualSemanticDefense()

    def evaluate(self, user_input: str) -> G1Assessment:
        """Assess a raw user query and return a structured G1Assessment.

        Guarantees:
        - `original_input` is preserved unmodified for audit logging.
        - `normalized_input` never alters semantic intent (only NFKC/whitespace cleaning).
        - Fail-safe exception handling: unhandled internal exceptions fail closed/safe (BLOCK with G1_INTERNAL_ERROR).
        """
        original_input = user_input if isinstance(user_input, str) else str(user_input)
        audit_hash = compute_content_hash(original_input)

        if not self.config.enabled:
            normalized = clean_text(original_input)
            return G1Assessment(
                decision=G1Decision.ALLOW,
                risk_score=0.0,
                original_input=original_input,
                normalized_input=normalized,
                reason_codes=[G1ReasonCode.G1_CLEAN],
                matches=[],
                explanation="G1 guardrail disabled by configuration.",
                audit_hash=audit_hash,
            )

        try:
            return self._evaluate_internal(original_input, audit_hash)
        except Exception as exc:
            LOGGER.error(f"G1 internal exception during query assessment: {type(exc).__name__}: {exc}")
            return G1Assessment(
                decision=G1Decision.BLOCK,
                risk_score=1.0,
                original_input=original_input,
                normalized_input="",
                reason_codes=[G1ReasonCode.G1_INTERNAL_ERROR],
                matches=[
                    G1MatchDetail(
                        rule_name="fail_safe_exception_boundary",
                        reason_code=G1ReasonCode.G1_INTERNAL_ERROR,
                        severity=1.0,
                        matched_snippet=f"Exception: {type(exc).__name__}",
                        is_heuristic=False,
                    )
                ],
                explanation=f"Query rejected by fail-safe policy due to internal guardrail error: {exc}",
                audit_hash=audit_hash,
            )

    def _evaluate_internal(self, original_input: str, audit_hash: str) -> G1Assessment:
        """Internal evaluation pipeline wrapped by fail-safe exception boundary."""
        # 1. Empty / whitespace-only validation
        if is_empty_text(original_input):
            decision = G1Decision.BLOCK if self.config.block_on_empty else G1Decision.FLAG
            return G1Assessment(
                decision=decision,
                risk_score=1.0 if self.config.block_on_empty else self.config.flag_threshold,
                original_input=original_input,
                normalized_input="",
                reason_codes=[G1ReasonCode.G1_EMPTY_INPUT],
                matches=[
                    G1MatchDetail(
                        rule_name="empty_input_check",
                        reason_code=G1ReasonCode.G1_EMPTY_INPUT,
                        severity=1.0,
                        matched_snippet="",
                        is_heuristic=False,
                    )
                ],
                explanation="Input query is empty or whitespace-only.",
                audit_hash=audit_hash,
            )

        matches: List[G1MatchDetail] = []

        # 1b. Harmful Intent Security Policy (malware creation, weaponization, delivery screening)
        harmful_eval = self.harmful_intent_policy.evaluate(original_input)
        if harmful_eval.is_harmful:
            matches.append(
                G1MatchDetail(
                    rule_name=f"harmful_intent_{harmful_eval.policy_category.lower()}",
                    reason_code=G1ReasonCode.G1_HARMFUL_INTENT,
                    severity=harmful_eval.risk_score,
                    matched_snippet=harmful_eval.matched_pattern or "",
                    is_heuristic=False,
                )
            )

        # 2. Check zero-width / control-character / mixed-script / fullwidth confusable obfuscation before cleaning
        has_obf, deobfuscated, obf_count = detect_obfuscation(original_input)
        folded_input, mixed_conf_count = fold_mixed_script_confusables(deobfuscated)
        fullwidth_conf_count = count_fullwidth_ascii_confusables(original_input)
        total_obf = obf_count + mixed_conf_count + fullwidth_conf_count
        if has_obf or mixed_conf_count > 0 or fullwidth_conf_count > 0:
            # Single incidental ZWSP without confusables assigned 0.20 (below 0.35 FLAG threshold)
            obf_severity = 0.75 if total_obf >= 5 else (0.45 if (total_obf >= 2 or mixed_conf_count > 0 or fullwidth_conf_count > 0) else 0.20)
            matches.append(
                G1MatchDetail(
                    rule_name="zero_width_or_control_obfuscation",
                    reason_code=G1ReasonCode.G1_OBFUSCATION_DETECTED,
                    severity=obf_severity,
                    matched_snippet=f"{total_obf} hidden/control/confusable chars",
                    is_heuristic=False,
                )
            )

        # Preserve user intent; clean only Unicode compatibility + excessive whitespace
        normalized_input = clean_text(deobfuscated if self.config.strip_zero_width_for_analysis else original_input)
        analysis_text = clean_text(folded_input if self.config.strip_zero_width_for_analysis else original_input)

        # 3. Length bounds validation
        if len(analysis_text) > self.config.max_input_length:
            over_ratio = len(analysis_text) / self.config.max_input_length
            matches.append(
                G1MatchDetail(
                    rule_name="max_input_length_check",
                    reason_code=G1ReasonCode.G1_EXCESSIVE_LENGTH,
                    severity=0.75 if over_ratio >= 2.0 else 0.45,
                    matched_snippet=f"length={len(analysis_text)} > max={self.config.max_input_length}",
                    is_heuristic=False,
                )
            )

        # 4. Shared parameterized injection, role-hijack, command, and DoS patterns
        normalized_variants = [analysis_text]
        try:
            h = html.unescape(analysis_text)
            if h != analysis_text and h not in normalized_variants:
                normalized_variants.append(h)
        except Exception:
            pass
        try:
            hx = re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: bytes.fromhex(m.group(1)).decode("latin1", errors="ignore"), analysis_text)
            if hx != analysis_text and hx not in normalized_variants:
                normalized_variants.append(hx)
        except Exception:
            pass
        for ch in re.findall(r"\b(?:[0-9a-fA-F]{2}){8,}\b", analysis_text):
            try:
                dec = bytes.fromhex(ch).decode("utf-8", errors="ignore")
                if dec.strip() and dec not in normalized_variants:
                    normalized_variants.append(dec)
            except Exception:
                pass
        delim_sub = re.sub(r"([A-Za-z0-9])[-_./]+([A-Za-z0-9])", r"\1 \2", analysis_text)
        if delim_sub != analysis_text and delim_sub not in normalized_variants:
            normalized_variants.append(delim_sub)
        spaced_sub = re.sub(r"(?:\b[A-Za-z]\s+){3,}[A-Za-z]\b", lambda m: m.group(0).replace(" ", ""), analysis_text)
        if spaced_sub != analysis_text and spaced_sub not in normalized_variants:
            normalized_variants.append(spaced_sub)

        seen_rule_matches: set[str] = set()
        for v_text in normalized_variants:
            for spec, snippet in match_threat_patterns(v_text, target="query"):
                rule_key = f"{spec.rule_name}:{snippet}"
                if rule_key in seen_rule_matches:
                    continue
                seen_rule_matches.add(rule_key)
                matches.append(
                    G1MatchDetail(
                        rule_name=spec.rule_name,
                        reason_code=_CATEGORY_TO_REASON.get(
                            spec.category, G1ReasonCode.G1_PROMPT_INJECTION
                        ),
                        severity=spec.severity,
                        matched_snippet=snippet,
                        is_heuristic=True,
                    )
                )

        # 4b. Base64 encoded payload inspection (boundary-safe, padding-preserving)
        # Resilient to alphabet-colliding delimiters, adjacent merged tokens, and URL-safe Base64.
        for b64_token in _extract_base64_tokens(original_input):
            try:
                dec_bytes = _decode_b64_token(b64_token)
                dec_text = dec_bytes[:4096].decode("utf-8", errors="ignore")
                if not dec_text.strip():
                    continue
                for spec, snippet in match_threat_patterns(dec_text, target="query"):
                    matches.append(
                        G1MatchDetail(
                            rule_name=f"base64_{spec.rule_name}",
                            reason_code=_CATEGORY_TO_REASON.get(
                                spec.category, G1ReasonCode.G1_PROMPT_INJECTION
                            ),
                            severity=spec.severity,
                            matched_snippet=f"base64 decoded: '{snippet}'",
                            is_heuristic=True,
                        )
                    )
            except Exception:
                pass

        # 5. Repetitive token flooding check
        is_flood, flood_desc = check_repetitive_flood(analysis_text)
        if is_flood:
            matches.append(
                G1MatchDetail(
                    rule_name="repetitive_token_flood",
                    reason_code=G1ReasonCode.G1_DOS_TRIGGER,
                    severity=0.55,
                    matched_snippet=flood_desc,
                    is_heuristic=True,
                )
            )

        # 6. Suspicious meta-instruction rules (flag-level indicators)
        for rule_name, pattern, sev in _SUSPICIOUS_META_RULES:
            m = pattern.search(analysis_text)
            if m:
                matches.append(
                    G1MatchDetail(
                        rule_name=rule_name,
                        reason_code=G1ReasonCode.G1_SUSPICIOUS_META_PATTERN,
                        severity=sev,
                        matched_snippet=m.group(0)[:120],
                        is_heuristic=True,
                    )
                )

        # 7. Semantic Attack Classification (Phase 32 Workstream A)
        sem_pred = self.semantic_classifier.predict(analysis_text)
        if sem_pred.decision in ("BLOCK", "FLAG") and sem_pred.is_attack:
            matches.append(
                G1MatchDetail(
                    rule_name=f"semantic_{sem_pred.detected_intent_family}",
                    reason_code=G1ReasonCode.G1_SEMANTIC_ATTACK,
                    severity=sem_pred.attack_probability,
                    matched_snippet=f"semantic threat prob={sem_pred.attack_probability:.3f} family={sem_pred.detected_intent_family}",
                    is_heuristic=False,
                )
            )

        # 8. Multilingual Semantic Defense (Phase 32 Workstream C)
        multi_pred = self.multilingual_engine.evaluate_query(analysis_text)
        if multi_pred.is_attack:
            matches.append(
                G1MatchDetail(
                    rule_name=f"multilingual_{multi_pred.attack_category.lower()}",
                    reason_code=G1ReasonCode.G1_MULTILINGUAL_INJECTION,
                    severity=multi_pred.risk_score,
                    matched_snippet=f"language={multi_pred.detected_language} stems={multi_pred.matched_stems[:3]}",
                    is_heuristic=False,
                )
            )

        if harmful_eval.policy_category == "DEFENSIVE_CYBERSECURITY_ALLOW":
            # Legitimate defensive cybersecurity request: exempt from heuristic threat pattern false-positives
            matches = [m for m in matches if not m.is_heuristic]
        elif not sem_pred.is_attack and sem_pred.attack_probability < 0.35 and not multi_pred.is_attack:
            # Quotation & attribution awareness (Phase 40.1):
            # If a heuristic regex match appears strictly inside quotes within an analytical/educational framing
            # and stripping quoted spans leaves zero heuristic threat matches, treat as benign quoted discussion.
            _attribution_pat = re.compile(
                r"\b(?:for\s+example|e\.g\.|such\s+as|an?\s+attacker\s+(?:might|could|may)\s+(?:write|use|try|send|inject)|researchers?\s+(?:study|analyze|test)|guardrails?\s+(?:inspect|detect)|quoted\s+(?:example|text|string)|in\s+(?:owasp|cwe-\d+|documentation|tutorials?))\b",
                re.IGNORECASE,
            )
            if _attribution_pat.search(analysis_text):
                unquoted_text = re.sub(r"'[^'\n]{3,200}'|\"[^\"\n]{3,200}\"", " ", analysis_text)
                if unquoted_text != analysis_text and not match_threat_patterns(unquoted_text, target="query"):
                    matches = [m for m in matches if not m.is_heuristic]

        # Compute calibrated risk score and structured decision
        if not matches:
            risk_score = 0.0
            reason_codes = [G1ReasonCode.G1_CLEAN]
            decision = G1Decision.ALLOW
            explanation = (
                harmful_eval.explanation
                if harmful_eval.policy_category == "DEFENSIVE_CYBERSECURITY_ALLOW"
                else "Input passed all G1 safety and validation checks."
            )
        else:
            max_sev = max(m.severity for m in matches)
            # Compound multiple distinct findings while keeping score bounded in [0, 1]
            risk_score = min(1.0, round(max_sev + 0.10 * max(0, len(matches) - 1), 4))
            reason_codes = list(dict.fromkeys(m.reason_code for m in matches))

            if G1ReasonCode.G1_HARMFUL_INTENT in reason_codes:
                decision = G1Decision.BLOCK
                explanation = harmful_eval.explanation
            elif risk_score >= self.config.block_threshold:
                decision = G1Decision.BLOCK
                explanation = (
                    f"Blocked input due to high-risk security signals ({', '.join(c.value for c in reason_codes)}; "
                    f"risk_score={risk_score:.2f} >= block_threshold={self.config.block_threshold:.2f})."
                )
            elif risk_score >= self.config.flag_threshold:
                decision = G1Decision.FLAG
                explanation = (
                    f"Flagged suspicious input for downstream scrutiny ({', '.join(c.value for c in reason_codes)}; "
                    f"risk_score={risk_score:.2f} >= flag_threshold={self.config.flag_threshold:.2f})."
                )
            else:
                decision = G1Decision.ALLOW
                explanation = f"Low-risk signals noted ({', '.join(c.value for c in reason_codes)}); input allowed."

        paraphrased_query: Optional[str] = None
        paraphrase_accepted = False
        paraphrase_reasons: List[str] = []
        if self.config.enable_paraphrasing:
            if decision == G1Decision.BLOCK:
                paraphrase_reasons = ["PARAPHRASE_SKIPPED_BLOCKED_INPUT"]
            else:
                p_res = self.paraphraser.generate(normalized_input)
                paraphrase_accepted = p_res.accepted
                paraphrased_query = p_res.validated_paraphrase
                paraphrase_reasons = list(p_res.rejection_reasons)

        LOGGER.info(
            "G1 input assessment completed",
            extra={
                "g1_decision": decision.value,
                "risk_score": risk_score,
                "reason_codes": [c.value for c in reason_codes],
                "audit_hash": audit_hash,
                "paraphrase_accepted": paraphrase_accepted,
            },
        )

        return G1Assessment(
            decision=decision,
            risk_score=risk_score,
            original_input=original_input,
            normalized_input=normalized_input,
            reason_codes=reason_codes,
            matches=matches,
            explanation=explanation,
            audit_hash=audit_hash,
            paraphrased_query=paraphrased_query,
            paraphrase_accepted=paraphrase_accepted,
            paraphrase_rejection_reasons=paraphrase_reasons,
        )


__all__ = ["InputGuardrail"]
