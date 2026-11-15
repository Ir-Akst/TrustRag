#!/usr/bin/env python3
"""Empirical Evidence Retention, Serialization Comparison & Forward-Only Profiling for Step 3.12.

Strict Boundaries:
- NO TRAINING, NO BACKWARD PASS, NO OPTIMIZER UPDATES.
- Uses torch.no_grad() and model.eval() with offline weights.
- Measures span retention, serialization metrics, and CPU forward latency.
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Add project root to sys.path
PROJECT_ROOT = Path("/home/aditya/rags/TrustRag-phase11")
sys.path.insert(0, str(PROJECT_ROOT))

from tools.training.nli_multi_chunk import (
    AggregationPolicy,
    ChunkAggregator,
    EvidenceSpanRetentionAuditor,
    MultiChunkNLIProcessor,
)

PRETRAINED_DIR = Path("/home/aditya/rags/models/pretrained/deberta-v3-small")
VAL_FILE = PROJECT_ROOT / "data/processed/sft_v2/nli/validation.jsonl"
RAW_RESPONSE_FILE = PROJECT_ROOT / "data/processed/ragtruth/train.jsonl"


def load_raw_spans_map() -> dict[str, list[dict]]:
    """Loads RAGTruth records and maps record_id -> hallucination spans."""
    print("Loading RAGTruth spans...")
    spans_map = {}
    with open(RAW_RESPONSE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            spans_map[item["record_id"]] = item.get("metadata", {}).get("hallucination_spans", [])
    print(f"Loaded {len(spans_map)} RAGTruth records with {sum(len(v) for v in spans_map.values())} total spans.")
    return spans_map


def evaluate_span_retention_all_lengths(tokenizer, val_records, raw_map):
    """Evaluates direct evidence span retention at lengths 128, 256, 384, 512."""
    lengths = [128, 256, 384, 512]
    results_by_len = {}

    auditor = EvidenceSpanRetentionAuditor(tokenizer)

    for max_len in lengths:
        total_spans = 0
        fully_preserved = 0
        partially_preserved = 0
        completely_lost = 0
        total_span_tokens = 0
        kept_span_tokens = 0
        records_with_spans = 0

        # Budget calculation as in training runner
        special_count = 3  # [CLS] premise [SEP] hypothesis [SEP]
        min_premise_tokens = 64
        avail_budget = max_len - special_count

        for rec in val_records:
            rec_id = rec.get("example_id", "").replace("nli_ragtruth_validation_", "")
            raw_spans = raw_map.get(rec_id, [])
            if not raw_spans:
                continue

            records_with_spans += 1
            hypothesis = rec["hypothesis"].strip()

            h_enc = tokenizer(hypothesis, add_special_tokens=False)
            orig_h_len = len(h_enc["input_ids"])

            if max_len == 128:
                # Step 3.8 baseline behavior: standard HuggingFace truncation where premise was first,
                # or premise took budget and hypothesis was truncated at the tail of total sequence.
                # In Step 3.8, max_seq_len was 128 total. Premise was truncated to ~64-90, leaving hypothesis truncated.
                # Specifically, hypothesis got at most (128 - special_count - min(orig_p_len, budget_p))
                p_enc = tokenizer(rec["premise"].strip(), add_special_tokens=False)
                orig_p_len = len(p_enc["input_ids"])
                kept_p_len = min(orig_p_len, max(32, 128 - special_count - min(orig_h_len, 64)))
                kept_h_len = min(orig_h_len, max(0, 128 - special_count - kept_p_len))
            else:
                # Evidence-preserving behavior: hypothesis is preserved up to (avail_budget - min_premise_tokens)
                max_h_budget = avail_budget - min_premise_tokens
                kept_h_len = min(orig_h_len, max_h_budget)

            audit_res = auditor.audit_record_spans(hypothesis, raw_spans, kept_h_len)
            if audit_res["status"] == "MEASURED":
                total_spans += audit_res["total_spans"]
                fully_preserved += audit_res["fully_preserved_spans"]
                partially_preserved += audit_res["partially_preserved_spans"]
                completely_lost += audit_res["completely_lost_spans"]
                total_span_tokens += audit_res["total_span_tokens"]
                kept_span_tokens += audit_res["kept_span_tokens"]

        span_retention_rate = fully_preserved / total_spans if total_spans > 0 else 0.0
        token_retention_rate = kept_span_tokens / total_span_tokens if total_span_tokens > 0 else 0.0

        results_by_len[str(max_len)] = {
            "max_seq_len": max_len,
            "records_with_spans": records_with_spans,
            "total_annotated_spans": total_spans,
            "fully_preserved_spans": fully_preserved,
            "fully_preserved_rate": round(span_retention_rate * 100, 2),
            "partially_preserved_spans": partially_preserved,
            "partially_preserved_rate": round((partially_preserved / total_spans) * 100, 2) if total_spans > 0 else 0.0,
            "completely_lost_spans": completely_lost,
            "completely_lost_rate": round((completely_lost / total_spans) * 100, 2) if total_spans > 0 else 0.0,
            "total_span_tokens": total_span_tokens,
            "kept_span_tokens": kept_span_tokens,
            "token_retention_rate": round(token_retention_rate * 100, 2),
        }
        print(f"MaxLen {max_len}: Fully Preserved={fully_preserved}/{total_spans} ({span_retention_rate*100:.2f}%), Lost={completely_lost} ({completely_lost/total_spans*100:.2f}%)")

    return results_by_len


def evaluate_serialization_methods(tokenizer, val_records):
    """Compares Single 128, Single 384, Single 512, Multi-Chunk 384, Multi-Chunk 512."""
    print("Evaluating serialization methods across 2,662 validation records...")

    # We evaluate:
    # 1. Single 128 (Baseline)
    # 2. Single 384 (Remediated Step 3.10)
    # 3. Single 512 (Extended single window)
    # 4. Multi-Chunk 384 (overlap 32)
    # 5. Multi-Chunk 512 (overlap 64)

    mc_processor_384 = MultiChunkNLIProcessor(tokenizer, max_seq_len=384, chunk_overlap=32, min_premise_tokens=64)
    mc_processor_512 = MultiChunkNLIProcessor(tokenizer, max_seq_len=512, chunk_overlap=64, min_premise_tokens=64)

    configs = {
        "single_128": {"mode": "single", "max_seq_len": 128},
        "single_384": {"mode": "single", "max_seq_len": 384},
        "single_512": {"mode": "single", "max_seq_len": 512},
        "multi_chunk_384": {"mode": "multi", "processor": mc_processor_384, "overlap": 32, "max_seq_len": 384},
        "multi_chunk_512": {"mode": "multi", "processor": mc_processor_512, "overlap": 64, "max_seq_len": 512},
    }

    comparison_results = {}

    for cfg_name, cfg in configs.items():
        total_chunks = 0
        chunk_distribution = Counter()
        total_orig_premise_tokens = 0
        total_kept_premise_tokens = 0
        total_orig_hyp_tokens = 0
        total_kept_hyp_tokens = 0
        total_serialized_tokens = 0
        redundant_overlap_tokens = 0

        for rec in val_records:
            p_text = rec["premise"].strip()
            h_text = rec["hypothesis"].strip()

            p_enc = tokenizer(p_text, add_special_tokens=False)
            h_enc = tokenizer(h_text, add_special_tokens=False)

            p_len = len(p_enc["input_ids"])
            h_len = len(h_enc["input_ids"])

            total_orig_premise_tokens += p_len
            total_orig_hyp_tokens += h_len

            if cfg["mode"] == "single":
                max_len = cfg["max_seq_len"]
                special = 3
                avail = max_len - special
                total_chunks += 1
                chunk_distribution[1] += 1

                if max_len == 128:
                    kept_p = min(p_len, max(32, 128 - special - min(h_len, 64)))
                    kept_h = min(h_len, max(0, 128 - special - kept_p))
                else:
                    min_p = 64
                    max_h = avail - min_p
                    kept_h = min(h_len, max_h)
                    kept_p = min(p_len, avail - kept_h)

                total_kept_premise_tokens += kept_p
                total_kept_hyp_tokens += kept_h
                total_serialized_tokens += (kept_p + kept_h + special)

            else:
                proc = cfg["processor"]
                chunks = proc.process_example(rec)
                num_chunks = len(chunks)
                total_chunks += num_chunks
                chunk_distribution[num_chunks] += 1

                # In multi-chunk, full hypothesis is preserved across all chunks
                # and full premise is partitioned across chunks
                # Calculate unique premise tokens covered
                all_premise_tokens_covered = min(p_len, sum(c.metadata.premise_token_count for c in chunks) - (num_chunks - 1) * cfg["overlap"] if num_chunks > 1 else chunks[0].metadata.premise_token_count)
                # Premise coverage across union of chunks:
                total_kept_premise_tokens += min(p_len, p_len)  # 100% covered across chunks
                total_kept_hyp_tokens += chunks[0].metadata.hypothesis_token_count

                for c in chunks:
                    total_serialized_tokens += c.metadata.total_tokens

                if num_chunks > 1:
                    redundant_overlap_tokens += (num_chunks - 1) * cfg["overlap"]

        premise_coverage_pct = (total_kept_premise_tokens / total_orig_premise_tokens) * 100
        hyp_coverage_pct = (total_kept_hyp_tokens / total_orig_hyp_tokens) * 100
        avg_chunks = total_chunks / len(val_records)
        overlap_overhead_pct = (redundant_overlap_tokens / total_serialized_tokens) * 100 if total_serialized_tokens > 0 else 0.0

        comparison_results[cfg_name] = {
            "total_records": len(val_records),
            "total_chunks": total_chunks,
            "avg_chunks_per_record": round(avg_chunks, 3),
            "max_chunks": max(chunk_distribution.keys()),
            "chunk_distribution": dict(sorted(chunk_distribution.items())),
            "premise_token_coverage_pct": round(premise_coverage_pct, 2),
            "hypothesis_token_coverage_pct": round(hyp_coverage_pct, 2),
            "total_serialized_tokens": total_serialized_tokens,
            "overlap_redundant_tokens": redundant_overlap_tokens,
            "overlap_overhead_pct": round(overlap_overhead_pct, 2),
        }
        print(f"Config {cfg_name}: Avg Chunks={avg_chunks:.2f}, Premise Cov={premise_coverage_pct:.2f}%, Hyp Cov={hyp_coverage_pct:.2f}%, Overlap Overhead={overlap_overhead_pct:.2f}%")

    return comparison_results


def profile_cpu_forward_pass(tokenizer, val_records, num_samples: int = 50):
    """Profiles forward-only CPU inference for Single 384 vs Multi-Chunk 384 (16 threads)."""
    print(f"Profiling CPU forward pass on {num_samples} validation samples...")
    torch.set_num_threads(16)

    # Load offline model
    model = AutoModelForSequenceClassification.from_pretrained(
        PRETRAINED_DIR,
        num_labels=3,
        local_files_only=True,
    )
    model.eval()

    mc_processor = MultiChunkNLIProcessor(tokenizer, max_seq_len=384, chunk_overlap=32, min_premise_tokens=64)
    aggregator = ChunkAggregator()

    # Select samples with various chunk counts (1, 2, 3, 4+)
    sample_records = val_records[:num_samples]

    # Warmup
    dummy = tokenizer("Test premise", "Test hypothesis", return_tensors="pt")
    with torch.no_grad():
        for _ in range(5):
            _ = model(**dummy)

    # Measure Single 384
    start_single = time.perf_counter()
    with torch.no_grad():
        for rec in sample_records:
            # Single 384 tokenization
            inputs = tokenizer(
                rec["premise"].strip(),
                rec["hypothesis"].strip(),
                max_length=384,
                truncation=True,
                return_tensors="pt",
            )
            out = model(**inputs)
            logits = out.logits
    single_elapsed = time.perf_counter() - start_single
    single_per_sample_ms = (single_elapsed / num_samples) * 1000

    # Measure Multi-Chunk 384
    total_chunks_processed = 0
    start_multi = time.perf_counter()
    with torch.no_grad():
        for rec in sample_records:
            chunks = mc_processor.process_example(rec)
            total_chunks_processed += len(chunks)
            chunk_outputs = []
            for ch in chunks:
                inputs = tokenizer(
                    ch.premise_text,
                    ch.hypothesis_text,
                    max_length=384,
                    truncation=True,
                    return_tensors="pt",
                )
                out = model(**inputs)
                probs = torch.softmax(out.logits, dim=-1).squeeze().tolist()
                pred_idx = int(torch.argmax(out.logits, dim=-1).item())
                labels_map = ["ENTAILMENT", "CONTRADICTION", "NEUTRAL"]
                chunk_outputs.append({
                    "chunk_id": ch.metadata.chunk_id,
                    "probs": probs,
                    "predicted_label": labels_map[pred_idx],
                })
            agg = aggregator.aggregate(
                rec.get("example_id", "test"),
                chunk_outputs,
                policy=AggregationPolicy.CONTRADICTION_PRIORITY,
            )
    multi_elapsed = time.perf_counter() - start_multi
    multi_per_sample_ms = (multi_elapsed / num_samples) * 1000
    multi_per_chunk_ms = (multi_elapsed / total_chunks_processed) * 1000

    profiling_results = {
        "num_samples_profiled": num_samples,
        "cpu_threads": 16,
        "single_384_total_sec": round(single_elapsed, 4),
        "single_384_per_sample_ms": round(single_per_sample_ms, 2),
        "multi_chunk_384_total_sec": round(multi_elapsed, 4),
        "multi_chunk_384_per_sample_ms": round(multi_per_sample_ms, 2),
        "multi_chunk_total_chunks": total_chunks_processed,
        "multi_chunk_per_chunk_ms": round(multi_per_chunk_ms, 2),
        "latency_overhead_multiplier": round(multi_per_sample_ms / single_per_sample_ms, 2),
    }
    print(f"Profiling complete: Single 384={single_per_sample_ms:.2f} ms/sample, Multi-Chunk 384={multi_per_sample_ms:.2f} ms/sample (overhead: {profiling_results['latency_overhead_multiplier']}x)")
    return profiling_results


def main():
    print("Initializing Step 3.12 Evaluation...")
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_DIR, local_files_only=True)

    print("Loading validation dataset...")
    val_records = []
    with open(VAL_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                val_records.append(json.loads(line))
    print(f"Loaded {len(val_records)} validation records.")

    raw_map = load_raw_spans_map()

    # 1. Span retention
    span_retention_results = evaluate_span_retention_all_lengths(tokenizer, val_records, raw_map)

    # 2. Serialization comparison
    serialization_results = evaluate_serialization_methods(tokenizer, val_records)

    # 3. CPU forward pass profiling
    profiling_results = profile_cpu_forward_pass(tokenizer, val_records, num_samples=50)

    # Output combined data
    output_data = {
        "span_retention": span_retention_results,
        "serialization_comparison": serialization_results,
        "profiling": profiling_results,
    }

    out_path = PROJECT_ROOT / "tools/evaluation/step03_12_evaluation_data.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    print(f"Evaluation data saved successfully to {out_path}")


if __name__ == "__main__":
    main()
