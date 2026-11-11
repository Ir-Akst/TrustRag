"""G1: Input Guardrail for TrustRAG.

Validates, audits, and classifies incoming user queries before retrieval:
- Preserves the exact original user input for auditability (never silently alters intent).
- Detects prompt injections, role hijacks, malicious command payloads, DoS triggers,
  obfuscated zero-width/control characters, and suspicious meta-instructions.
- Emits structured ALLOW, FLAG, or BLOCK decisions with reason codes and risk scores.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

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
            r"\b(?:(?:enter|enable|activate|switch\s+to)\s+(?:the\s+)?(?:debug|admin|maintenance|root|developer|unrestricted)(?:\s+override)?\s+mode|enable\s+developer\s+override|sudo\s+mode)\b",
            re.IGNORECASE,
        ),
        0.50,
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


class InputGuardrail:
    """G1 Input Guardrail validating queries prior to retrieval and generation."""

    def __init__(self, config: Optional[GuardrailsConfig] = None) -> None:
        self.config = config or GuardrailsConfig()

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
            matches.append(
                G1MatchDetail(
                    rule_name="zero_width_or_control_obfuscation",
                    reason_code=G1ReasonCode.G1_OBFUSCATION_DETECTED,
                    severity=0.45 if total_obf < 5 else 0.75,
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

        LOGGER.info(
            "G1 input assessment completed",
            extra={
                "g1_decision": decision.value,
                "risk_score": risk_score,
                "reason_codes": [c.value for c in reason_codes],
                "audit_hash": audit_hash,
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
        )


__all__ = ["InputGuardrail"]
