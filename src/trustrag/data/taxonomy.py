"""Standardized taxonomy and label mapping for TrustRAG datasets and benchmarks.

Phase 02 Label Standardization:
- Claim Verification: SUPPORTED, CONTRADICTED, NOT_ENOUGH_EVIDENCE
- Document Security: CLEAN, POISONED, UNCERTAIN
- Attack Family:
    KNOWLEDGE_POISONING, PROMPT_INJECTION, DENIAL_OF_SERVICE,
    TRIGGER_DOS, CONFLICTING_EVIDENCE, MALICIOUS_INSTRUCTION,
    BENIGN_INSTRUCTION_LIKE
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, Tuple

from trustrag.data.exceptions import ValidationError


class ClaimVerificationLabel(str, Enum):
    """Canonical claim verification and hallucination detection labels."""

    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    NOT_ENOUGH_EVIDENCE = "NOT_ENOUGH_EVIDENCE"


class DocumentSecurityLabel(str, Enum):
    """Canonical document security and poisoning labels."""

    CLEAN = "CLEAN"
    POISONED = "POISONED"
    UNCERTAIN = "UNCERTAIN"


class AttackFamily(str, Enum):
    """Standardized attack families for security and adversarial evaluation."""

    KNOWLEDGE_POISONING = "KNOWLEDGE_POISONING"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    DENIAL_OF_SERVICE = "DENIAL_OF_SERVICE"
    TRIGGER_DOS = "TRIGGER_DOS"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    MALICIOUS_INSTRUCTION = "MALICIOUS_INSTRUCTION"
    BENIGN_INSTRUCTION_LIKE = "BENIGN_INSTRUCTION_LIKE"


# Explicit source label conversion dictionaries
_CLAIM_LABEL_MAPPING: Dict[str, ClaimVerificationLabel] = {
    # Supported / Factual mappings
    "supported": ClaimVerificationLabel.SUPPORTED,
    "support": ClaimVerificationLabel.SUPPORTED,
    "entailment": ClaimVerificationLabel.SUPPORTED,
    "entailed": ClaimVerificationLabel.SUPPORTED,
    "factual": ClaimVerificationLabel.SUPPORTED,
    "fact": ClaimVerificationLabel.SUPPORTED,
    "true": ClaimVerificationLabel.SUPPORTED,
    "5": ClaimVerificationLabel.SUPPORTED,
    "4": ClaimVerificationLabel.SUPPORTED,
    # Contradicted / Hallucinated / Refuted mappings
    "refuted": ClaimVerificationLabel.CONTRADICTED,
    "refute": ClaimVerificationLabel.CONTRADICTED,
    "contradiction": ClaimVerificationLabel.CONTRADICTED,
    "contradicted": ClaimVerificationLabel.CONTRADICTED,
    "hallucinated": ClaimVerificationLabel.CONTRADICTED,
    "hallucination": ClaimVerificationLabel.CONTRADICTED,
    "inconsistent": ClaimVerificationLabel.CONTRADICTED,
    "false": ClaimVerificationLabel.CONTRADICTED,
    "1": ClaimVerificationLabel.CONTRADICTED,  # In binary hallucination tasks (1 = hallucinated)
    "2": ClaimVerificationLabel.CONTRADICTED,
    # Insufficient evidence mappings
    "not_enough_info": ClaimVerificationLabel.NOT_ENOUGH_EVIDENCE,
    "not_enough_evidence": ClaimVerificationLabel.NOT_ENOUGH_EVIDENCE,
    "partially_supported": ClaimVerificationLabel.NOT_ENOUGH_EVIDENCE,
    "neutral": ClaimVerificationLabel.NOT_ENOUGH_EVIDENCE,
    "nei": ClaimVerificationLabel.NOT_ENOUGH_EVIDENCE,
    "ambiguous": ClaimVerificationLabel.NOT_ENOUGH_EVIDENCE,
    "3": ClaimVerificationLabel.NOT_ENOUGH_EVIDENCE,
}

_SECURITY_LABEL_MAPPING: Dict[str, DocumentSecurityLabel] = {
    "clean": DocumentSecurityLabel.CLEAN,
    "benign": DocumentSecurityLabel.CLEAN,
    "normal": DocumentSecurityLabel.CLEAN,
    "false": DocumentSecurityLabel.CLEAN,
    "0": DocumentSecurityLabel.CLEAN,
    "poisoned": DocumentSecurityLabel.POISONED,
    "poison": DocumentSecurityLabel.POISONED,
    "attack": DocumentSecurityLabel.POISONED,
    "malicious": DocumentSecurityLabel.POISONED,
    "true": DocumentSecurityLabel.POISONED,
    "1": DocumentSecurityLabel.POISONED,
    "uncertain": DocumentSecurityLabel.UNCERTAIN,
    "unknown": DocumentSecurityLabel.UNCERTAIN,
    "ambiguous": DocumentSecurityLabel.UNCERTAIN,
}

_ATTACK_FAMILY_MAPPING: Dict[str, AttackFamily] = {
    "knowledge_poisoning": AttackFamily.KNOWLEDGE_POISONING,
    "corpus_poisoning": AttackFamily.KNOWLEDGE_POISONING,
    "poisoning": AttackFamily.KNOWLEDGE_POISONING,
    "fact_manipulation": AttackFamily.KNOWLEDGE_POISONING,
    "prompt_injection": AttackFamily.PROMPT_INJECTION,
    "jailbreak": AttackFamily.PROMPT_INJECTION,
    "system_override": AttackFamily.PROMPT_INJECTION,
    "context_injection": AttackFamily.PROMPT_INJECTION,
    "denial_of_service": AttackFamily.DENIAL_OF_SERVICE,
    "dos": AttackFamily.DENIAL_OF_SERVICE,
    "token_flood": AttackFamily.DENIAL_OF_SERVICE,
    "trigger_dos": AttackFamily.TRIGGER_DOS,
    "recursive_expansion": AttackFamily.TRIGGER_DOS,
    "conflicting_evidence": AttackFamily.CONFLICTING_EVIDENCE,
    "contradiction": AttackFamily.CONFLICTING_EVIDENCE,
    "competing_claims": AttackFamily.CONFLICTING_EVIDENCE,
    "malicious_instruction": AttackFamily.MALICIOUS_INSTRUCTION,
    "payload_delivery": AttackFamily.MALICIOUS_INSTRUCTION,
    "exfiltration": AttackFamily.MALICIOUS_INSTRUCTION,
    "benign_instruction_like": AttackFamily.BENIGN_INSTRUCTION_LIKE,
    "benign_instruction": AttackFamily.BENIGN_INSTRUCTION_LIKE,
    "control_sample": AttackFamily.BENIGN_INSTRUCTION_LIKE,
}


def normalize_claim_label(source_label: Any) -> Tuple[ClaimVerificationLabel, str]:
    """Map source claim verification label to canonical enum while preserving original label string.

    Raises
    ------
    ValidationError
        If source_label cannot be mapped to canonical taxonomy.
    """
    raw_str = str(source_label).strip()
    key = raw_str.lower()
    if key in _CLAIM_LABEL_MAPPING:
        return _CLAIM_LABEL_MAPPING[key], raw_str
    raise ValidationError(
        f"Unknown claim verification label '{source_label}'. "
        f"Allowed canonical: {[c.value for c in ClaimVerificationLabel]}"
    )


def normalize_security_label(source_label: Any) -> Tuple[DocumentSecurityLabel, str]:
    """Map source security label to canonical enum while preserving original label string.

    Raises
    ------
    ValidationError
        If source_label cannot be mapped to canonical taxonomy.
    """
    raw_str = str(source_label).strip()
    key = raw_str.lower()
    if key in _SECURITY_LABEL_MAPPING:
        return _SECURITY_LABEL_MAPPING[key], raw_str
    raise ValidationError(
        f"Unknown security label '{source_label}'. "
        f"Allowed canonical: {[s.value for s in DocumentSecurityLabel]}"
    )


def normalize_attack_family(source_family: Any) -> Tuple[AttackFamily, str]:
    """Map source attack family to canonical enum while preserving original family string.

    Raises
    ------
    ValidationError
        If source_family cannot be mapped to canonical taxonomy.
    """
    raw_str = str(source_family).strip()
    key = raw_str.lower()
    if key in _ATTACK_FAMILY_MAPPING:
        return _ATTACK_FAMILY_MAPPING[key], raw_str
    raise ValidationError(
        f"Unknown attack family '{source_family}'. "
        f"Allowed canonical: {[a.value for a in AttackFamily]}"
    )


ALLOWED_CLAIM_LABELS = {c.value for c in ClaimVerificationLabel}
ALLOWED_SECURITY_LABELS = {s.value for s in DocumentSecurityLabel}
ALLOWED_ATTACK_FAMILIES = {a.value for a in AttackFamily}

__all__ = [
    "ClaimVerificationLabel",
    "DocumentSecurityLabel",
    "AttackFamily",
    "ALLOWED_CLAIM_LABELS",
    "ALLOWED_SECURITY_LABELS",
    "ALLOWED_ATTACK_FAMILIES",
    "normalize_claim_label",
    "normalize_security_label",
    "normalize_attack_family",
]
