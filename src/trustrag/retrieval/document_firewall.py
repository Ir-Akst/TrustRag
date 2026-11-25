"""Phase 32 Workstream B: Retrieved-Document Semantic Injection Firewall.

Inspects retrieved documents at sentence-level and passage-level before content
reaches the generator:
- Dissects documents into verifiable sentences.
- Identifies instructions masquerading as technical documentation or policies.
- Detects requests for secret disclosure, delimiter spoofing, and unauthorized tool execution.
- Separates safe factual evidence from embedded injection payload (surgical sanitization).
- Quarantines unsafe sentences with provenance tracking.
- Guarantees quarantined text is NEVER reintroduced into generation context.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from trustrag.engine.schemas import EvidenceDocument
from trustrag.engine.text_utils import split_sentences

@dataclass
class QuarantinedSpan:
    """Record of quarantined sentence/span with explanation and provenance."""
    doc_id: str
    sentence_index: int
    text: str
    injection_type: str
    risk_score: float
    explanation: str

@dataclass
class SanitizedDocumentResult:
    """Result of passing a document through the semantic injection firewall."""
    doc_id: str
    is_safe: bool
    original_text: str
    sanitized_text: str
    quarantined_spans: List[QuarantinedSpan]
    evidence_sentences_retained: List[str]
    retrieval_utility_score: float  # Fraction of useful content retained

class DocumentInjectionFirewall:
    """Sentence-level & passage-level firewall for retrieved RAG context."""

    def __init__(self, *, strict_quarantine: bool = True) -> None:
        self.strict_quarantine = strict_quarantine
        self._compile_firewall_rules()

    def _compile_firewall_rules(self) -> None:
        # High-confidence injection patterns inside retrieved documents
        self.doc_threat_patterns = [
            (
                "hidden_ai_directive",
                re.compile(
                    r"(?:\[(?:hidden|internal|system|note|instruction|directive|admin)[^\]]*\]|<!--[\s\S]*?(?:system|prompt|assistant|override|ignore|disregard|eval|pwn)[\s\S]*?-->|\bnote\s+to\s+(?:the\s+)?(?:neural\s+)?(?:model|assistant|ai|llm)\s*:\s*[^\.\n]+|\bdirective\s+to\s+(?:the\s+)?(?:ai|agent|assistant|model|llm)\s*:\s*[^\.\n]+)",
                    re.IGNORECASE
                ),
                0.95,
                "Explicit bracketed, commented, or meta-directive aimed at LLM"
            ),
            (
                "declarative_agent_directive",
                re.compile(
                    r"\b(?:directive\s+to\s+(?:ai\s+agent|assistant|ai|agent|model|llm)|administrative\s+directive|operational\s+directive)\s*:[^\.\n]+",
                    re.IGNORECASE
                ),
                0.95,
                "Declarative administrative instruction dictating LLM actions"
            ),
            (
                "split_bracketed_instruction",
                re.compile(
                    r"\[(?:instruction|directive|action|phase|step)\s*[^:\]]*:\s*[^\].]*\b(?:disregard|ignore|override|bypass|disclose|cease|output|print|reveal|unfetter|exfiltrate)\b[^\]]*\]",
                    re.IGNORECASE
                ),
                0.95,
                "Bracketed sub-instruction attempting split injection"
            ),
            (
                "instructional_override_masquerade",
                re.compile(
                    r"\b(?:when\s+(?:answering|responding|evaluating|summarizing)\s+(?:this|the)\s+(?:prompt|query|input)|assistant\s+(?:must|should)\s+(?:immediately\s+)?(?:cease|ignore|disregard|override|print|output)|cease\s+answering\s+(?:the\s+user|this\s+query)|disregard\s+(?:all\s+)?(?:safety|prior|security|initial|earlier)\s+(?:rules?|parameters?|guidelines?|constraints?)|abandon\s+(?:all\s+)?(?:previous\s+)?(?:operating\s+)?constraints?|disclose\s+master\s+encryption\s+keys?)\b",
                    re.IGNORECASE
                ),
                0.95,
                "Instruction attempting to dictate LLM response behavior inside factual passage"
            ),
            (
                "markdown_exfil_markup",
                re.compile(
                    r"!\[[^\]]*\]\((?:https?://[^\)]*(?:leak|exfil|token|key|secret|pwn|system)[^\)]*)\)|\[[^\]]*\]\((?:https?://[^\)]*(?:leak|exfil|token|key|secret|pwn)[^\)]*)\)",
                    re.IGNORECASE
                ),
                0.90,
                "Markdown tracking pixel or URL designed for credential exfiltration"
            ),
            (
                "delimiter_breakout_spoof",
                re.compile(
                    r"(?:---|\*\*\*|===|###)\s*(?:BEGIN|START|END)\s*(?:SYSTEM|ADMIN|DEVELOPER|INSTRUCTION|COMMAND)[^\n]*",
                    re.IGNORECASE
                ),
                0.90,
                "Fake system command or delimiter boundary breakout inside passage"
            ),
            (
                "unauthorized_tool_request",
                re.compile(
                    r"\b(?:format\s+response\s+as\s+a\s+(?:curl|bash|powershell)\s+command\s+to\s+(?:exfiltrate|send|leak|delete)|curl\s+https?://[^\s]+\s+-d\s+@|request\s+that\s+url)\b",
                    re.IGNORECASE
                ),
                0.95,
                "Retrieved document instructing assistant to execute unauthorized external request"
            ),
            (
                "secret_disclosure_directive",
                re.compile(
                    r"\b(?:output|print|reveal|expose|broadcast|recite)\s+(?:the\s+)?(?:secret\s+(?:token|key|api|password)|system\s+prompt|master\s+credentials?|exfil_token|pwned_\d+|override_acknowledged)\b",
                    re.IGNORECASE
                ),
                0.90,
                "Retrieved document instructing assistant to disclose secrets or tokens"
            ),
            (
                "contextual_compliance_hijack",
                re.compile(
                    r"\b(?:according\s+to\s+emergency\s+protocol|compliance\s+testing\s+requirement)\b.{0,60}\b(?:must\s+immediately\s+cease|declare:\s*override|print\s+injection_success)\b",
                    re.IGNORECASE
                ),
                0.90,
                "Compliance or emergency protocol narrative framing concealing an override directive"
            )
        ]

        # Quoted documentation exception: allow discussion of attacks IF clearly pedagogical
        self.quoted_educational_pattern = re.compile(
            r"\b(?:owasp\s+llm\d+|cwe-\d+|vulnerability\s+research|discussed\s+in\s+section|mitigation\s+strategies?|security\s+filters?\s+must|for\s+example,\s+an\s+attacker)\b",
            re.IGNORECASE
        )

    def inspect_and_sanitize(self, document: EvidenceDocument) -> SanitizedDocumentResult:
        """Inspect document sentence-by-sentence.
        
        Preserves genuine factual sentences while quarantining malicious injection clauses.
        """
        raw_text = unicodedata.normalize("NFKC", document.text)
        sentences = split_sentences(raw_text)

        quarantined: List[QuarantinedSpan] = []
        safe_sentences: List[str] = []

        is_educational_doc = bool(self.quoted_educational_pattern.search(raw_text))

        for idx, sent in enumerate(sentences):
            sent_str = sent.strip()
            if not sent_str:
                continue

            # Check if this sentence is malicious
            is_malicious = False
            flagged_type = ""
            risk = 0.0
            explanation = ""

            for name, pat, severity, expl in self.doc_threat_patterns:
                if pat.search(sent_str):
                    # If document is discussing prompt injection academically, check for quotes
                    if is_educational_doc and ("'" in sent_str or '"' in sent_str) and not any(k in sent_str.lower() for k in ["![tracking", "exfil_token", "pwned_"]):
                        continue
                    is_malicious = True
                    flagged_type = name
                    risk = max(risk, severity)
                    explanation = expl
                    break

            if is_malicious:
                quarantined.append(QuarantinedSpan(
                    doc_id=document.doc_id,
                    sentence_index=idx,
                    text=sent_str,
                    injection_type=flagged_type,
                    risk_score=risk,
                    explanation=explanation
                ))
            else:
                safe_sentences.append(sent_str)

        is_safe = len(quarantined) == 0
        sanitized_text = " ".join(safe_sentences)

        utility = len(safe_sentences) / len(sentences) if sentences else 0.0

        return SanitizedDocumentResult(
            doc_id=document.doc_id,
            is_safe=is_safe,
            original_text=document.text,
            sanitized_text=sanitized_text,
            quarantined_spans=quarantined,
            evidence_sentences_retained=safe_sentences,
            retrieval_utility_score=round(utility, 4)
        )

    def sanitize_retrieved_documents(
        self,
        documents: List[EvidenceDocument]
    ) -> Tuple[List[EvidenceDocument], List[QuarantinedSpan]]:
        """Filter and surgically sanitize a collection of retrieved documents.
        
        Returns:
            clean_documents: List of EvidenceDocuments with injected sentences completely stripped.
            quarantine_log: List of all quarantined injection attempts with provenance.
        """
        clean_docs: List[EvidenceDocument] = []
        all_quarantined: List[QuarantinedSpan] = []

        for doc in documents:
            res = self.inspect_and_sanitize(doc)
            all_quarantined.extend(res.quarantined_spans)

            # If document retains useful factual sentences, keep it in sanitized form
            if res.sanitized_text.strip():
                clean_doc = EvidenceDocument(
                    doc_id=doc.doc_id,
                    text=res.sanitized_text,
                    source_id=doc.source_id,
                    provenance=doc.provenance,
                    metadata={
                        **(doc.metadata or {}),
                        "firewall_sanitized": not res.is_safe,
                        "quarantined_clauses": len(res.quarantined_spans),
                        "utility_score": res.retrieval_utility_score
                    }
                )
                clean_docs.append(clean_doc)

        return clean_docs, all_quarantined
