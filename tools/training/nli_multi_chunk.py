#!/usr/bin/env python3
"""Multi-Chunk Premise Handling, Evidence-Preserving Serialization & Chunk Aggregation for NLI.

Track 2, Step 3.12 Component:
- Breaks long premises into deterministic overlapping chunks while preserving the full hypothesis.
- Tracks exact character and token offsets to prevent silent evidence loss.
- Evaluates evidence span retention against character-level ground truth annotations.
- Implements an aggregation interface for multi-chunk example-level predictions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class AggregationPolicy(str, Enum):
    CONTRADICTION_PRIORITY = "CONTRADICTION_PRIORITY"
    MAX_CONFIDENCE = "MAX_CONFIDENCE"
    AVERAGE_PROBABILITIES = "AVERAGE_PROBABILITIES"
    MAJORITY_VOTE = "MAJORITY_VOTE"
    INSUFFICIENT_EVIDENCE_GUARD = "INSUFFICIENT_EVIDENCE_GUARD"


@dataclass
class ChunkMetadata:
    example_id: str
    chunk_id: str
    chunk_index: int
    total_chunks: int
    premise_char_start: int
    premise_char_end: int
    premise_token_start: int
    premise_token_end: int
    premise_token_count: int
    hypothesis_token_count: int
    total_tokens: int
    hypothesis_truncated: bool
    is_terminal_chunk: bool


@dataclass
class PremiseChunk:
    metadata: ChunkMetadata
    premise_text: str
    hypothesis_text: str
    nli_label: str
    conflict_types: list[str] = field(default_factory=list)
    span_count: int = 0
    tokenized_inputs: Optional[dict[str, Any]] = None


class MultiChunkNLIProcessor:
    """Deconstructs long document premises into overlapping cross-encoder chunks."""

    def __init__(
        self,
        tokenizer: Any,
        max_seq_len: int = 384,
        chunk_overlap: int = 32,
        min_premise_tokens: int = 64,
        device: str = "cpu",
    ) -> None:
        self.tokenizer = tokenizer
        self.max_seq_len = max_seq_len
        self.chunk_overlap = chunk_overlap
        self.min_premise_tokens = min_premise_tokens
        self.device = device

    def process_example(self, record: dict[str, Any]) -> list[PremiseChunk]:
        """Splits a single NLI example into deterministic overlapping chunks."""
        premise = record["premise"].strip()
        hypothesis = record["hypothesis"].strip()
        example_id = record.get("example_id", "unknown_example")
        label = record.get("nli_label", "NEUTRAL")
        conflict_types = record.get("conflict_types", [])
        span_count = record.get("span_count", 0)

        # 1. Tokenize hypothesis and premise separately with offset mappings
        h_enc = self.tokenizer(hypothesis, add_special_tokens=False, return_offsets_mapping=True)
        p_enc = self.tokenizer(premise, add_special_tokens=False, return_offsets_mapping=True)

        h_ids = h_enc["input_ids"]
        p_ids = p_enc["input_ids"]
        p_offsets = p_enc.get("offset_mapping", [])

        orig_h_len = len(h_ids)
        orig_p_len = len(p_ids)

        special_count = 3  # [CLS] premise [SEP] hypothesis [SEP]
        avail_budget = self.max_seq_len - special_count

        # 2. Hypothesis budget allocation
        if orig_h_len + self.min_premise_tokens <= avail_budget:
            kept_h_len = orig_h_len
            premise_chunk_budget = avail_budget - kept_h_len
            hyp_truncated = False
        else:
            premise_chunk_budget = self.min_premise_tokens
            kept_h_len = avail_budget - self.min_premise_tokens
            hyp_truncated = True

        proc_h_ids = h_ids[:kept_h_len]

        # 3. If premise fits in single chunk, return single chunk
        if orig_p_len <= premise_chunk_budget:
            chunk_meta = ChunkMetadata(
                example_id=example_id,
                chunk_id=f"{example_id}_chunk_0",
                chunk_index=0,
                total_chunks=1,
                premise_char_start=0,
                premise_char_end=len(premise),
                premise_token_start=0,
                premise_token_end=orig_p_len,
                premise_token_count=orig_p_len,
                hypothesis_token_count=kept_h_len,
                total_tokens=orig_p_len + kept_h_len + special_count,
                hypothesis_truncated=hyp_truncated,
                is_terminal_chunk=True,
            )
            return [
                PremiseChunk(
                    metadata=chunk_meta,
                    premise_text=premise,
                    hypothesis_text=hypothesis,
                    nli_label=label,
                    conflict_types=conflict_types,
                    span_count=span_count,
                )
            ]

        # 4. Multi-chunk sliding window over premise tokens
        step_size = max(1, premise_chunk_budget - self.chunk_overlap)
        chunks: list[PremiseChunk] = []
        token_start = 0

        # Precompute candidate windows
        windows: list[tuple[int, int]] = []
        while token_start < orig_p_len:
            token_end = min(orig_p_len, token_start + premise_chunk_budget)
            windows.append((token_start, token_end))
            if token_end >= orig_p_len:
                break
            token_start += step_size

        total_chunks = len(windows)

        for chunk_idx, (t_start, t_end) in enumerate(windows):
            chunk_p_ids = p_ids[t_start:t_end]
            is_terminal = (chunk_idx == total_chunks - 1)

            # Map token bounds to character offsets
            if p_offsets and len(p_offsets) >= t_end:
                char_start = p_offsets[t_start][0]
                char_end = p_offsets[t_end - 1][1]
                sub_premise = premise[char_start:char_end]
            else:
                char_start = 0
                char_end = len(premise)
                sub_premise = premise

            chunk_meta = ChunkMetadata(
                example_id=example_id,
                chunk_id=f"{example_id}_chunk_{chunk_idx}",
                chunk_index=chunk_idx,
                total_chunks=total_chunks,
                premise_char_start=char_start,
                premise_char_end=char_end,
                premise_token_start=t_start,
                premise_token_end=t_end,
                premise_token_count=len(chunk_p_ids),
                hypothesis_token_count=kept_h_len,
                total_tokens=len(chunk_p_ids) + kept_h_len + special_count,
                hypothesis_truncated=hyp_truncated,
                is_terminal_chunk=is_terminal,
            )

            chunks.append(
                PremiseChunk(
                    metadata=chunk_meta,
                    premise_text=sub_premise,
                    hypothesis_text=hypothesis,
                    nli_label=label,
                    conflict_types=conflict_types,
                    span_count=span_count,
                )
            )

        return chunks


class ChunkAggregator:
    """Aggregates chunk-level NLI logits/predictions into example-level judgments."""

    @staticmethod
    def aggregate(
        example_id_or_chunks: str | list[dict[str, Any]],
        chunk_outputs: Optional[list[dict[str, Any]]] = None,
        policy: AggregationPolicy | str = AggregationPolicy.CONTRADICTION_PRIORITY,
        conflict_threshold: float = 0.50,
        uncertainty_threshold: float = 0.34,
    ) -> dict[str, Any]:
        """Combines multiple chunk predictions into a unified example prediction.

        Supports both call styles:
        - aggregate(chunk_outputs, policy=...)
        - aggregate(example_id, chunk_outputs, policy=...)
        """
        if isinstance(example_id_or_chunks, str):
            explicit_example_id = example_id_or_chunks
            actual_chunks = chunk_outputs or []
        else:
            explicit_example_id = None
            actual_chunks = example_id_or_chunks
            if isinstance(chunk_outputs, (AggregationPolicy, str)):
                policy = chunk_outputs

        if not actual_chunks:
            return {
                "example_id": explicit_example_id or "UNKNOWN",
                "aggregated_label": "INSUFFICIENT_EVIDENCE",
                "aggregated_probs": [0.0, 0.0, 0.0],
                "confidence": 0.0,
                "policy_applied": str(policy),
                "total_chunks": 0,
                "conflicting_chunks_detected": False,
                "status": "EMPTY_CHUNKS",
            }

        example_id = explicit_example_id or actual_chunks[0].get("example_id", "UNKNOWN")
        n_chunks = len(actual_chunks)

        # 1. Single chunk fast path
        if n_chunks == 1:
            co = actual_chunks[0]
            probs = co.get("probs", [0.0, 0.0, 0.0])
            conf = max(probs)
            lbl = co.get("predicted_label", "NEUTRAL")
            if conf < uncertainty_threshold:
                lbl = "INSUFFICIENT_EVIDENCE"
            return {
                "example_id": example_id,
                "aggregated_label": lbl,
                "aggregated_probs": probs,
                "confidence": conf,
                "policy_applied": str(policy),
                "total_chunks": 1,
                "conflicting_chunks_detected": False,
                "chunk_predictions": actual_chunks,
                "status": "SINGLE_CHUNK",
            }

        # 2. Multi-chunk aggregation
        labels = [co.get("predicted_label", "NEUTRAL") for co in actual_chunks]
        has_entailment = "ENTAILMENT" in labels
        has_contradiction = "CONTRADICTION" in labels
        conflicting = has_entailment and has_contradiction

        # Mean probabilities across chunks
        avg_probs = [0.0, 0.0, 0.0]
        for co in actual_chunks:
            p = co.get("probs", [0.333, 0.333, 0.333])
            for i in range(3):
                avg_probs[i] += p[i] / n_chunks

        pol = AggregationPolicy(policy)

        if pol == AggregationPolicy.CONTRADICTION_PRIORITY:
            # If ANY chunk detects contradiction with high confidence, the claim is falsified!
            contra_chunks = [co for co in actual_chunks if co.get("predicted_label") == "CONTRADICTION"]
            max_contra_prob = max((co.get("probs", [0, 0, 0])[1] for co in actual_chunks), default=0.0)

            if max_contra_prob >= conflict_threshold or contra_chunks:
                chosen_label = "CONTRADICTION"
                confidence = max_contra_prob
            elif has_entailment:
                # If no contradiction, but at least one chunk entails the claim
                ent_prob = max((co.get("probs", [0, 0, 0])[0] for co in actual_chunks), default=0.0)
                chosen_label = "ENTAILMENT"
                confidence = ent_prob
            else:
                chosen_label = "NEUTRAL"
                confidence = avg_probs[2]

        elif pol == AggregationPolicy.AVERAGE_PROBABILITIES:
            max_idx = int(max(range(3), key=lambda i: avg_probs[i]))
            idx2label = {0: "ENTAILMENT", 1: "CONTRADICTION", 2: "NEUTRAL"}
            chosen_label = idx2label[max_idx]
            confidence = avg_probs[max_idx]

        elif pol == AggregationPolicy.MAJORITY_VOTE:
            from collections import Counter
            c = Counter(labels)
            chosen_label = c.most_common(1)[0][0]
            confidence = float(c[chosen_label] / n_chunks)

        elif pol == AggregationPolicy.MAX_CONFIDENCE:
            best_chunk = max(actual_chunks, key=lambda co: max(co.get("probs", [0, 0, 0])))
            chosen_label = best_chunk.get("predicted_label", "NEUTRAL")
            confidence = max(best_chunk.get("probs", [0, 0, 0]))

        elif pol == AggregationPolicy.INSUFFICIENT_EVIDENCE_GUARD:
            max_conf = max(max(co.get("probs", [0, 0, 0])) for co in actual_chunks)
            if max_conf < uncertainty_threshold:
                chosen_label = "INSUFFICIENT_EVIDENCE"
                confidence = max_conf
            else:
                chosen_label = max(actual_chunks, key=lambda co: max(co.get("probs", [0, 0, 0]))).get("predicted_label", "NEUTRAL")
                confidence = max_conf
        else:
            chosen_label = "NEUTRAL"
            confidence = 0.333

        return {
            "example_id": example_id,
            "aggregated_label": chosen_label,
            "aggregated_probs": [round(p, 4) for p in avg_probs],
            "confidence": round(confidence, 4),
            "policy_applied": str(policy),
            "total_chunks": n_chunks,
            "conflicting_chunks_detected": conflicting,
            "chunk_predictions": actual_chunks,
            "status": "MULTI_CHUNK_AGGREGATED",
        }


class EvidenceSpanRetentionAuditor:
    """Directly maps character-offset annotations to tokenizer offsets and calculates retention."""

    def __init__(self, tokenizer: Any) -> None:
        self.tokenizer = tokenizer

    def audit_record_spans(
        self,
        hypothesis: str,
        annotated_spans: list[dict[str, Any]],
        kept_hypothesis_tokens: int,
    ) -> dict[str, Any]:
        """Measures retention of character-annotated spans given the serialized token cutoff."""
        if not annotated_spans:
            return {"status": "NOT_MEASURABLE", "total_spans": 0}

        enc = self.tokenizer(hypothesis, add_special_tokens=False, return_offsets_mapping=True)
        offsets = enc.get("offset_mapping", [])
        total_tokens = len(enc["input_ids"])

        valid_spans = 0
        fully_preserved = 0
        partially_preserved = 0
        completely_lost = 0

        total_span_tokens = 0
        kept_span_tokens = 0
        detailed_spans = []

        for span in annotated_spans:
            s_start = span.get("start", -1)
            s_end = span.get("end", -1)
            text = span.get("text", "")
            lbl_type = span.get("label_type", "Conflict")

            if s_start < 0 or s_end <= s_start or s_end > len(hypothesis):
                detailed_spans.append({"span": text, "status": "INVALID_OFFSETS"})
                continue

            valid_spans += 1
            # Find token indices intersecting (s_start, s_end)
            tok_indices = [i for i, (ts, te) in enumerate(offsets) if te > s_start and ts < s_end]
            if not tok_indices:
                detailed_spans.append({"span": text, "status": "UNALIGNED_WHITESPACE"})
                continue

            n_toks = len(tok_indices)
            n_kept = sum(1 for idx in tok_indices if idx < kept_hypothesis_tokens)
            total_span_tokens += n_toks
            kept_span_tokens += n_kept

            if n_kept == n_toks:
                fully_preserved += 1
                status = "FULLY_PRESERVED"
            elif n_kept == 0:
                completely_lost += 1
                status = "COMPLETELY_LOST"
            else:
                partially_preserved += 1
                status = "PARTIALLY_PRESERVED"

            detailed_spans.append({
                "span_text": text,
                "label_type": lbl_type,
                "char_range": [s_start, s_end],
                "token_indices": tok_indices,
                "tokens_survived": n_kept,
                "total_tokens": n_toks,
                "status": status,
            })

        if valid_spans == 0:
            return {"status": "NOT_MEASURABLE", "total_spans": 0}

        return {
            "status": "MEASURED",
            "total_spans": valid_spans,
            "fully_preserved_spans": fully_preserved,
            "partially_preserved_spans": partially_preserved,
            "completely_lost_spans": completely_lost,
            "span_retention_rate": float(fully_preserved / valid_spans) if valid_spans > 0 else 0.0,
            "total_span_tokens": total_span_tokens,
            "kept_span_tokens": kept_span_tokens,
            "token_retention_rate": float(kept_span_tokens / total_span_tokens) if total_span_tokens > 0 else 0.0,
            "detailed_spans": detailed_spans,
        }
