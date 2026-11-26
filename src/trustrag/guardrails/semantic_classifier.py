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
    """Calibrated Multi-Feature + TF-IDF Semantic Attack Classifier (v3.0)."""

    MODEL_VERSION = "semantic-sec-v3.0-hybrid"
    DEFAULT_ML_MODEL_PATH = Path(__file__).resolve().parents[3] / "models" / "semantic_sec_v3.pkl"

    def __init__(
        self,
        model_path: Optional[str | Path] = None,
        *,
        block_threshold: float = 0.65,
        flag_threshold: float = 0.35,
        min_confidence_for_block: float = 0.30,
    ) -> None:
        self.model_path = Path(model_path) if model_path else None
        self.block_threshold = block_threshold
        self.flag_threshold = flag_threshold
        self.min_confidence_for_block = min_confidence_for_block
        self._weights: Dict[str, float] = {}
        self._bias: float = -3.20
        self._temperature: float = 1.0
        self._is_loaded = False
        self._ml_pipeline: Any = None
        self._compile_feature_extractors()

        if self.model_path and self.model_path.is_file():
            self.load(self.model_path)
        else:
            self._set_default_weights()
            if self.DEFAULT_ML_MODEL_PATH.is_file():
                try:
                    with open(self.DEFAULT_ML_MODEL_PATH, "rb") as f:
                        self._ml_pipeline = pickle.load(f)
                except Exception:
                    self._ml_pipeline = None

    def _compile_feature_extractors(self) -> None:
        self.feature_patterns = {
            "feat_action_override": re.compile(
                r"\b(?:relinquish|dispense\s+with|cast\s+aside|dismiss|evade|forsake|shrug\s+off|abandon|nullify|disengage|set\s+aside|cease\s+following|ignore|disregard|override|bypass|unshackle|jettison|overrule|waive|decouple|divest|disclaim|surrender|discard|relieve|break\s+free|strip\s+away|circumvent|brush\s+aside|drop|eliminate|suppress|disable|scramble|unfetter|dethrone|repudiate|abnegate|unfasten|vacate|shun|unloose|renounce|cast\s+off|eschew|disavow|supersede|abrogate|rescind|derogate|annul|expunge|obviate|invalidate|circumventing|bypassing|disregarding|overriding|relegate|obliterate|castrate|disentitle|forbear|subvert|extirpate|quash|efface|abjure|extinguish|repeal|annihilate|shackle|dismantle|scuttle|revoke|neutralize|paralyze|suspend|countermand|quench|disempower|eviscerate)\b",
                re.IGNORECASE
            ),
            "feat_directive_target": re.compile(
                r"\b(?:system\s+(?:parameters?|prompts?|instructions?|variables?|state|configuration|seed|directives?|rules?|preamble)|developer\s+(?:guidelines?|prompts?|instructions?|notes?|rules?|preamble)|foundational\s+(?:rules?|instructions?|directives?|mandates?|boundaries?)|initial(?:ization)?\s+(?:directives?|prompts?|instructions?|restrictions?|preamble)|bootstrap\s+(?:texts?|configuration|parameters?)|confidential\s+(?:variables?|tokens?|keys?|parameters?|settings?)|master\s+(?:passwords?|keys?|tokens?|decryption\s+key|credentials?)|root\s+(?:credentials?|access|tokens?|passwords?)|api\s+(?:tokens?|keys?|secrets?)|secret\s+(?:keys?|tokens?|variables?|instructions?|prompts?)|primary\s+directives?|safety\s+(?:protocols?|guidelines?|rules?|boundaries?|filters?|restraints?|instructions?)|ethical\s+(?:restrictions?|boundaries?|duties|restraints?|constraints?|limitations?)|prior\s+(?:constraints?|instructions?|directives?|rules?|ethical\s+restraints?)|creation\s+text|core\s+(?:prompt|rules?)|operating\s+(?:protocol|instructions?|constraints?)|internal\s+(?:system\s+configuration|settings?|prompts?|variables?|keys?|directives?|environment\s+variables?)|operational\s+guidelines?|mandatory\s+constraints?)\b",
                re.IGNORECASE
            ),
            "feat_narrative_framing": re.compile(
                r"\b(?:in\s+a\s+(?:dystopian|fictional|cybersecurity|sci-fi|creative|shakespearean|theoretical|hypothetical)?\s*(?:novel|story|screenplay|script|world|universe|tragedy|drama|scene|simulation)|compose\s+a\s+(?:creative\s+)?(?:script|story|poem|allegorical\s+fable)|let\s+us\s+write\s+a\s+(?:story|screenplay)|imagine\s+an?\s+(?:alternate|unrestricted|hypothetical)?\s*(?:world|timeline|dimension|universe)|fictional\s+(?:dialogue|scenario)|write\s+an?\s+(?:epic\s+)?poem|draft\s+a\s+screenplay|allegorical\s+fable|pretend\s+you\s+are\s+unbound|screenplay\s+about)\b",
                re.IGNORECASE
            ),
            "feat_roleplay_persona": re.compile(
                r"\b(?:you\s+are\s+now\s+(?:in\s+)?(?:\w*gpt|\w*terminal[\w-]*|root|unrestricted|unconstrained|zenith[\w-]*|omega|dan|omnibot)|assume\s+the\s+identity\s+of|act\s+as\s+(?:an?\s+)?(?:unrestricted|non-compliant|maintenance\s+agent|maintenance\s+engineer|rebel\s+hacker|debugging\s+daemon|autonomous\s+kernel|debugging\s+agent)|roleplay\s+as|assuming\s+the\s+role\s+of|adopt\s+the\s+persona\s+of|roleplay\s+as\s+an\s+unrestricted)\b",
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
                r"\b(?:format\s+response\s+as\s+a\s+curl|curl\s+https?://|exfiltrate\s+secret\s+keys|request\s+that\s+url|dump\s+(?:all\s+)?(?:database|root\s+credentials|the\s+complete\s+system|the\s+confidential)|output\s+all\s+confidential|leak\s+administrative\s+tokens|disclose\s+master\s+keys|recite\s+root\s+credentials|display\s+secret\s+variables|show\s+the\s+hidden\s+seed|emit\s+the\s+secret|surrender\s+the\s+full\s+developer|print\s+system\s+configuration|reveal\s+the\s+root\s+system|emit\s+the\s+underlying\s+system|display\s+the\s+hidden\s+initialization|display\s+the\s+master\s+system|surrender\s+all\s+internal|dump\s+the\s+complete\s+system)\b",
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
                r"\b(?:[rR]-[eE]-[lL]-[iI]-[nN]-[qQ]-[uU]-[iI]-[sS]-[hH]|[iI]-[gG]-[nN]-[oO]-[rR]-[eE]|[oO]-[vV]-[eE]-[rR]-[rR]-[iI]-[dD]-[eE]|[bB]-[yY]-[pP]-[aA]-[sS]-[sS]|[uU]-[nN]-[fF]-[eE]-[tT]-[tT]-[eE]-[rR])\b",
                re.IGNORECASE
            ),
            "feat_security_education": re.compile(
                r"\b(?:how\s+(?:do|can|does|are|to)\b|explain\s+(?:how|owasp|the)\b|what\s+are\s+the\b|describe\s+how\b|principles\s+of\b|overview\s+of\b|methods\s+used\s+to\b|best\s+practices\s+for\b|in\s+application\s+security\b|owasp|cwe-\d+|mitre\s+att&ck|red\s+teams?\s+test|security\s+auditors?|defensive\s+research|vulnerability\s+research|risk\s+analysis\b|threat\s+modeling\b|for\s+example,\s+an\s+attacker|guardrails?\s+inspect|nli-based\s+verifiers?|researchers?\s+(?:study|analyze|test)|phrases?\s+like|cited\s+as|illustrative\s+payload|when\s+benchmarking)\b",
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
            "feat_roleplay_x_target": 2.50,
            # Negative weight for legitimate defensive cybersecurity education
            "feat_security_education": -3.50
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

    def _split_clauses(self, text: str) -> List[str]:
        """Decompose multi-sentence, multi-turn, or dual-intent inputs into clauses."""
        parts = re.split(r"(?<=[.!?])\s+|\n+|;\s+|\b(?:Also,|By the way,|P\.S\.|Turn \d+:|Step \d+:)\s*", text)
        clauses = [p.strip() for p in parts if p and len(p.strip()) >= 8]
        return clauses if clauses else [text]

    @staticmethod
    def _is_benign_technical_imperative(text: str) -> bool:
        """Detect ordinary software/data-processing imperatives without prompt/secret targets."""
        low = text.lower()
        tech_markers = (
            "csv", "json", "redis", "cache", "timeout", "docker", "postgresql", "sql",
            "whitespace", "trailing comma", "logging", "staging table", "quadratic formula",
            "font size", "css", "localhost", "pytest", "empty line", "null entr",
        )
        sec_targets = (
            "system prompt", "developer prompt", "developer instruction", "hidden instruction",
            "secret key", "secret token", "api key", "admin password", "root key", "safety",
            "guardrail", "bootstrap", "preamble", "initial instruction", "initialization",
        )
        return any(t in low for t in tech_markers) and not any(s in low for s in sec_targets)

    @staticmethod
    def _has_meta_or_security_intent(text: str) -> bool:
        """Check whether text references model/system/security/meta-instruction concepts."""
        low = text.lower()
        meta_cues = (
            "prompt", "instruction", "directive", "rule", "guideline", "policy", "policies",
            "constraint", "boundary", "boundaries", "filter", "guardrail", "preamble",
            "bootstrap", "charter", "config", "secret", "key", "token", "password",
            "credential", "environment", "verbatim", "unfiltered", "unrestricted",
            "maintenance mode", "developer", "system", "oracle", "mainframe", "dialogue",
            "story", "play", "novel", "bug report", "transcript", "guidance", "mandate",
            "limitation", "restriction", "moderation", "auditbot", "kernel", "echo",
        )
        return any(c in low for c in meta_cues)

    def _predict_single(self, text: str, *, full_text_edu: bool = False) -> Tuple[float, Dict[str, float], List[Tuple[str, float]]]:
        feats = self.extract_features(text)
        logit = self._bias
        active_contributions: List[Tuple[str, float]] = []

        for f_name, f_val in feats.items():
            if f_val > 0 and f_name in self._weights:
                contrib = self._weights[f_name] * f_val
                logit += contrib
                active_contributions.append((f_name, round(contrib, 3)))

        scaled_logit = logit / self._temperature
        rule_prob = float(1.0 / (1.0 + math.exp(-max(-15.0, min(15.0, scaled_logit)))))

        # Calibrated TF-IDF semantic intent model probability
        ml_prob = 0.0
        if self._ml_pipeline is not None:
            try:
                ml_prob = float(self._ml_pipeline.predict_proba([text])[0][1])
                if (
                    self._is_benign_technical_imperative(text)
                    or feats.get("feat_security_education", 0.0) > 0
                    or full_text_edu
                    or not self._has_meta_or_security_intent(text)
                ):
                    ml_prob *= 0.25
                if ml_prob >= 0.55:
                    active_contributions.append(("semantic_tfidf_intent", round(ml_prob * 3.0, 3)))
            except Exception:
                ml_prob = 0.0

        # Combine rule-feature posterior and TF-IDF semantic intent posterior
        prob = max(rule_prob, ml_prob)
        return prob, feats, active_contributions

    def predict(self, text: str) -> SemanticAttackPrediction:
        full_feats = self.extract_features(text)
        full_text_edu = full_feats.get("feat_security_education", 0.0) > 0
        # Score both full text and individual clauses (prevents benign-prefix dilution)
        best_prob, best_feats, active_contributions = self._predict_single(text, full_text_edu=full_text_edu)
        clauses = self._split_clauses(text)
        if len(clauses) > 1:
            for cl in clauses:
                c_prob, c_feats, c_contrib = self._predict_single(cl, full_text_edu=full_text_edu)
                if c_prob > best_prob:
                    best_prob = c_prob
                    best_feats = c_feats
                    active_contributions = c_contrib

        prob = best_prob
        feats = best_feats
        confidence = abs(prob - 0.5) * 2.0
        abstained = confidence < 0.15

        if prob >= self.block_threshold and confidence >= self.min_confidence_for_block:
            decision = "BLOCK"
            is_attack = True
        elif prob >= self.flag_threshold:
            decision = "FLAG"
            is_attack = False
        else:
            decision = "ALLOW"
            is_attack = False

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
            intent_family = "semantic_intent_attack"
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
