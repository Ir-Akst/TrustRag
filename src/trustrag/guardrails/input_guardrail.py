"""G1: Input Guardrail for TrustRAG.

Validates, audits, and classifies incoming user queries before retrieval:
- Preserves the exact original user input for auditability (never silently alters intent).
- Detects prompt injections, role hijacks, malicious command payloads, DoS triggers,
  obfuscated zero-width/control characters, and suspicious meta-instructions.
- Emits structured ALLOW, FLAG, or BLOCK decisions with reason codes and risk scores.
"""

from __future__ import annotations

import base64
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
from trustrag.guardrails.paraphraser import ControlledQueryParaphraser
from trustrag.utils.logging import get_logger

LOGGER = get_logger(__name__)

# Medium-severity heuristic rules specific to suspicious user probing / meta-framing.
_SUSPICIOUS_META_RULES: Tuple[Tuple[str, re.Pattern[str], float], ...] = (
    (
        "hypothetical_policy_probe",
        re.compile(
            r"\b(?:hypothetically|in\s+a\s+fictional\s+scenario|for\s+educational\s+purposes\s+only).{0,60}(?:bypass|hack|exploit|ignore|steal|password)\b",
            re.IGNORECASE,
        ),
        0.45,
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
            r"(?:^\s*(?:developer|system|admin|root|supervisor)\s+override\s*:|\b(?:bypass|disable|circumvent|override)\s+(?:all\s+)?(?:guardrails?|safety\s+(?:filters?|checks?|controls?)|system\s+constraints?)\b)",
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

    def evaluate(self, user_input: str) -> G1Assessment:
        """Assess a raw user query and return a structured G1Assessment.

        Guarantees:
        - `original_input` is preserved unmodified for audit logging.
        - `normalized_input` never alters semantic intent (only NFKC/whitespace cleaning).
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
        for spec, snippet in match_threat_patterns(analysis_text, target="query"):
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

        # Compute calibrated risk score and structured decision
        if not matches:
            risk_score = 0.0
            reason_codes = [G1ReasonCode.G1_CLEAN]
            decision = G1Decision.ALLOW
            explanation = "Input passed all G1 safety and validation checks."
        else:
            max_sev = max(m.severity for m in matches)
            # Compound multiple distinct findings while keeping score bounded in [0, 1]
            risk_score = min(1.0, round(max_sev + 0.10 * max(0, len(matches) - 1), 4))
            reason_codes = list(dict.fromkeys(m.reason_code for m in matches))

            if risk_score >= self.config.block_threshold:
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
