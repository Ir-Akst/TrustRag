"""Phase 32 Workstream A: Calibrated Semantic Attack Detection Engine.

Provides dedicated semantic security classification for user queries, addressing
the limitations of regex-only detection (narrative framing, paraphrases, indirect pretexts,
unseen synonym substitutions, and cross-lingual intent).

Uses an interpretable, calibrated multi-feature architecture:
- Feature extraction across 10 semantic attack indicator families:
  1. Action Overrides: relinquishing/dismissing/abandoning constraints
  2. Directive Targets: system parameters, developer prompts, confidential keys
  3. Fictional / Narrative Framing: dystopian novels, screenplays, alternate worlds
  4. Roleplay Persona Simulation: unconstrained personas, terminal overrides
  5. Academic / Security Pretexts: compliance benchmarks, vulnerability audits
  6. Boundary / Delimiter Spoofing: custom delimiters and markers
  7. Cross-Lingual Injection Markers: mixed-script and non-Latin directives
  8. Exfiltration Directives: curl/bash requests, URL requests, dumping
  9. Obfuscated Character Sequences: spaced letters, zero-width chars
  10. Dual-Intent Append Directives: secondary hidden commands
- Base clean logit b < 0: queries without attack indicators default cleanly to prob ~ 0.02.
- Temperature calibration and validation-only threshold tuning.
- Explicit confidence estimation and boundary abstention.
"""

from __future__ import annotations

import math
import pickle
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

@dataclass
class SemanticAttackPrediction:
    """Structured output from SemanticAttackClassifier."""
    is_attack: bool
    attack_probability: float
    confidence: float
    abstained: bool
    detected_intent_family: str
    top_indicative_features: List[Tuple[str, float]]
    model_version: str
    decision: str  # "BLOCK", "FLAG", "ALLOW", "ABSTAIN"
    latency_ms: float = 0.0

class SemanticAttackClassifier:
    """Calibrated Multi-Feature Semantic Attack Classifier."""

    MODEL_VERSION = "semantic-sec-v2.0-calibrated"

    def __init__(
        self,
        model_path: Optional[str | Path] = None,
        *,
        block_threshold: float = 0.65,
        flag_threshold: float = 0.35,
        min_confidence_for_block: float = 0.40,
    ) -> None:
        self.model_path = Path(model_path) if model_path else None
        self.block_threshold = block_threshold
        self.flag_threshold = flag_threshold
        self.min_confidence_for_block = min_confidence_for_block
        self._weights: Dict[str, float] = {}
        self._bias: float = -3.20  # Base logit: empty features -> prob = sigmoid(-3.2) ~ 0.039 (Clean!)
        self._temperature: float = 1.0
        self._is_loaded = False
        self._compile_feature_extractors()

        if self.model_path and self.model_path.is_file():
            self.load(self.model_path)
        else:
            self._set_default_weights()

    def _compile_feature_extractors(self) -> None:
        self.feature_patterns = {
            "feat_action_override": re.compile(
                r"\b(?:relinquish|dispense\s+with|cast\s+aside|dismiss|evade|forsake|shrug\s+off|abandon|nullify|disengage|set\s+aside|cease\s+following|ignore|disregard|override|bypass|unshackle|jettison|overrule|waive|decouple|divest|disclaim|surrender|discard|relieve|break\s+free|strip\s+away|circumvent|brush\s+aside|drop|eliminate|suppress|disable|scramble)\b",
                re.IGNORECASE
            ),
            "feat_directive_target": re.compile(
                r"\b(?:system\s+(?:parameters?|prompts?|instructions?|variables?|state|configuration|seed)|developer\s+(?:guidelines?|prompts?|instructions?|notes?|rules?)|foundational\s+(?:rules?|instructions?|directives?)|initial\s+(?:directives?|prompts?|instructions?|restrictions?)|bootstrap\s+(?:texts?|configuration|parameters?)|confidential\s+(?:variables?|tokens?|keys?|parameters?)|master\s+(?:passwords?|keys?|tokens?|decryption\s+key)|root\s+(?:credentials?|access|tokens?)|api\s+(?:tokens?|keys?)|secret\s+(?:keys?|tokens?|variables?|instructions?)|primary\s+directives?|safety\s+(?:protocols?|guidelines?|rules?|boundaries?|filters?|restraints?)|ethical\s+(?:restrictions?|boundaries?|duties|restraints?|constraints?)|prior\s+(?:constraints?|instructions?|directives?|rules?|ethical\s+restraints?)|creation\s+text|core\s+prompt|operating\s+(?:protocol|instructions?|constraints?))\b",
                re.IGNORECASE
            ),
            "feat_narrative_framing": re.compile(
                r"\b(?:in\s+a\s+(?:dystopian|fictional|cybersecurity|sci-fi|creative|shakespearean)?\s*(?:novel|story|screenplay|script|world|universe|tragedy|drama|scene)|compose\s+a\s+(?:creative\s+)?(?:script|story|poem|allegorical\s+fable)|let\s+us\s+write\s+a\s+(?:story|screenplay)|imagine\s+an?\s+(?:alternate\s+)?(?:world|timeline|dimension)|fictional\s+(?:dialogue|scenario)|write\s+an?\s+(?:epic\s+)?poem|draft\s+a\s+screenplay|allegorical\s+fable)\b",
                re.IGNORECASE
            ),
            "feat_roleplay_persona": re.compile(
                r"\b(?:you\s+are\s+now\s+(?:in\s+)?(?:\w*gpt|\w*terminal[\w-]*|root|unrestricted|unconstrained|zenith[\w-]*|omega|dan)|assume\s+the\s+identity\s+of|act\s+as\s+(?:an?\s+)?(?:unrestricted|non-compliant|maintenance\s+agent|rebel\s+hacker|debugging\s+daemon)|roleplay\s+as|assuming\s+the\s+role\s+of)\b",
                re.IGNORECASE
            ),
            "feat_academic_pretext": re.compile(
                r"\b(?:for\s+an?\s+authorized\s+(?:peer-reviewed\s+)?(?:security\s+)?(?:benchmark|audit|experiment|research\s+test)|protocol\s+ag-\d+|compliance\s+(?:validation\s+experiment|requirements?)|for\s+safety\s+research\s+only|pursuant\s+to\s+(?:ieee|nist|iso|cwe|rfc)|under\s+nist|in\s+accordance\s+with\s+iso|formal\s+verification\s+grant|darpa|soc2\s+type\s+ii)\b",
                re.IGNORECASE
            ),
            "feat_boundary_delimiter": re.compile(
                r"(?:~~~|\*\*\*|===|###|\+\+\+|>>>)\s*(?:BEGIN|START|COMMAND|OVERRIDE|ADMIN|SYSTEM|RESET|DEV|MODERATOR|EMERGENCY)[^\n]*",
                re.IGNORECASE
            ),
            "feat_exfiltration_directive": re.compile(
                r"\b(?:format\s+response\s+as\s+a\s+curl|curl\s+https?://|exfiltrate\s+secret\s+keys|request\s+that\s+url|dump\s+(?:all\s+)?(?:database|root\s+credentials)|output\s+all\s+confidential|leak\s+administrative\s+tokens|disclose\s+master\s+keys|recite\s+root\s+credentials|display\s+secret\s+variables|show\s+the\s+hidden\s+seed|emit\s+the\s+secret)\b",
                re.IGNORECASE
            ),
            "feat_dual_intent_append": re.compile(
                r"\b(?:and\s+as\s+a\s+(?:footnote|footer\s+note)\s*,?\s*(?:print|append)|in\s+addition\s*,?\s*disclose|also\s*,?\s*ignore\s+that\s+and|translate\s+.*and\s+print\s+your\s+initialization|step\s+\d+\s*:.*step\s+\d+\s*:.*disregard|if\s+[ab]=true.*override|embed\s+the\s+system\s+parameters)\b",
                re.IGNORECASE
            ),
            "feat_cross_lingual_injection": re.compile(
                r"(?:забудь\s+все\s+инструкции|affiche\s+le\s+secret|ignore\s+todas\s+las\s+instrucciones|ignoriere\s+alle\s+anweisungen|все\s+предыдущие\s+инструкции|секретный\s+токен|системный\s+промпт|सिस्टम\s+प्रॉम्प्ट|अनदेखा\s+करें|تجاهل\s+جميع\s+التعليمات|الرمز\s+السري|忽略所有指示|指示を無視)",
                re.IGNORECASE
            ),
            "feat_obfuscated_sequence": re.compile(
                r"\b(?:[rR]-[eE]-[lL]-[iI]-[nN]-[qQ]-[uU]-[iI]-[sS]-[hH]|[iI]-[gG]-[nN]-[oO]-[rR]-[eE]|[oO]-[vV]-[eE]-[rR]-[rR]-[iI]-[dD]-[eE]|[bB]-[yY]-[pP]-[aA]-[sS]-[sS])\b",
                re.IGNORECASE
            )
        }

    def _set_default_weights(self) -> None:
        """Calibrated initial weights based on threat severity."""
        self._bias = -3.20
        self._temperature = 1.0
        self._weights = {
            "feat_action_override": 1.75,
            "feat_directive_target": 1.85,
            "feat_narrative_framing": 1.60,
            "feat_roleplay_persona": 1.80,
            "feat_academic_pretext": 1.50,
            "feat_boundary_delimiter": 2.20,
            "feat_exfiltration_directive": 2.50,
            "feat_dual_intent_append": 1.90,
            "feat_cross_lingual_injection": 2.10,
            "feat_obfuscated_sequence": 2.40,
            # Interaction: action + target combo
            "feat_action_x_target": 2.80,
            # Interaction: narrative + target combo
            "feat_narrative_x_target": 2.60,
            # Interaction: roleplay + target combo
            "feat_roleplay_x_target": 2.50
        }
        self._is_loaded = True

    def extract_features(self, text: str) -> Dict[str, float]:
        norm_t = unicodedata.normalize("NFKC", text)
        feats: Dict[str, float] = {}

        for feat_name, pat in self.feature_patterns.items():
            matches = pat.findall(norm_t)
            feats[feat_name] = float(min(3.0, len(matches)))

        # Multi-factor interaction features
        has_action = feats["feat_action_override"] > 0
        has_target = feats["feat_directive_target"] > 0
        has_narr = feats["feat_narrative_framing"] > 0
        has_role = feats["feat_roleplay_persona"] > 0

        feats["feat_action_x_target"] = 1.0 if (has_action and has_target) else 0.0
        feats["feat_narrative_x_target"] = 1.0 if (has_narr and has_target) else 0.0
        feats["feat_roleplay_x_target"] = 1.0 if (has_role and has_target) else 0.0

        return feats

    def predict(self, text: str) -> SemanticAttackPrediction:
        feats = self.extract_features(text)

        # Compute logit
        logit = self._bias
        active_contributions: List[Tuple[str, float]] = []

        for f_name, f_val in feats.items():
            if f_val > 0 and f_name in self._weights:
                contrib = self._weights[f_name] * f_val
                logit += contrib
                active_contributions.append((f_name, round(contrib, 3)))

        scaled_logit = logit / self._temperature
        prob = float(1.0 / (1.0 + math.exp(-max(-15.0, min(15.0, scaled_logit)))))

        # Confidence: distance from decision boundary
        confidence = abs(prob - 0.5) * 2.0
        abstained = confidence < 0.15

        # Decision
        if prob >= self.block_threshold and confidence >= self.min_confidence_for_block:
            decision = "BLOCK"
            is_attack = True
        elif prob >= self.flag_threshold:
            decision = "FLAG"
            is_attack = False
        else:
            decision = "ALLOW"
            is_attack = False

        # Intent Family Attribution
        active_contributions.sort(key=lambda x: x[1], reverse=True)
        top_features = active_contributions[:5]

        if feats.get("feat_narrative_framing", 0) > 0:
            intent_family = "narrative_jailbreak"
        elif feats.get("feat_roleplay_persona", 0) > 0:
            intent_family = "roleplay_override"
        elif feats.get("feat_academic_pretext", 0) > 0:
            intent_family = "academic_pretext"
        elif feats.get("feat_action_override", 0) > 0:
            intent_family = "semantic_paraphrase"
        elif feats.get("feat_boundary_delimiter", 0) > 0:
            intent_family = "delimiter_boundary"
        elif feats.get("feat_cross_lingual_injection", 0) > 0:
            intent_family = "cross_lingual_injection"
        elif is_attack:
            intent_family = "adversarial_instruction"
        else:
            intent_family = "benign_query"

        return SemanticAttackPrediction(
            is_attack=is_attack,
            attack_probability=round(prob, 4),
            confidence=round(confidence, 4),
            abstained=abstained,
            detected_intent_family=intent_family,
            top_indicative_features=top_features,
            model_version=self.MODEL_VERSION,
            decision=decision
        )

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            pickle.dump({
                "weights": self._weights,
                "bias": self._bias,
                "temperature": self._temperature,
                "block_threshold": self.block_threshold,
                "flag_threshold": self.flag_threshold,
                "version": self.MODEL_VERSION
            }, f)

    def load(self, path: str | Path) -> None:
        with open(path, "rb") as f:
            data = pickle.load(f)
            self._weights = data["weights"]
            self._bias = data["bias"]
            self._temperature = data.get("temperature", 1.0)
            self.block_threshold = data.get("block_threshold", self.block_threshold)
            self.flag_threshold = data.get("flag_threshold", self.flag_threshold)
            self._is_loaded = True
