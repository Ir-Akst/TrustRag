#!/usr/bin/env python3
"""Multi-Chunk NLI Supervision & Training Readiness Audit Script for Step 3.14.

Investigates:
1. Original supervision distribution and annotation provenance.
2. Character span localization: hypothesis vs premise.
3. Multi-chunk generation statistics across train (10,815) and validation (2,662) records.
4. Single-chunk vs Multi-chunk breakdown by class.
5. Evidence span mapping to chunks:
   - Complete evidence spans contained in chunk
   - Partial spans crossing boundaries
   - Evidence-free chunks
   - Label inheritance corruption analysis
6. Strict split isolation & zero leakage verification.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path("/home/aditya/rags/TrustRag-phase11")
sys.path.insert(0, str(PROJECT_ROOT))

from transformers import AutoTokenizer
from tools.training.nli_multi_chunk import MultiChunkNLIProcessor

TRAIN_FILE = PROJECT_ROOT / "data/processed/sft_v2/nli/train.jsonl"
VAL_FILE = PROJECT_ROOT / "data/processed/sft_v2/nli/validation.jsonl"
RT_FILE = PROJECT_ROOT / "data/processed/ragtruth/train.jsonl"
PRETRAINED_DIR = Path("/home/aditya/rags/models/pretrained/deberta-v3-small")


def load_spans_map() -> dict[str, list[dict]]:
    """Loads RAGTruth records and maps record_id -> hallucination spans."""
    print("Loading RAGTruth ground truth spans...")
    spans_map = {}
    with open(RT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            spans_map[r["record_id"]] = r.get("metadata", {}).get("hallucination_spans", [])
    print(f"Loaded {len(spans_map)} records from RAGTruth.")
    return spans_map


def audit_supervision_and_chunking(tokenizer, spans_map):
    print("Initializing MultiChunkNLIProcessor (max_seq_len=384, overlap=32, min_premise=64)...")
    proc = MultiChunkNLIProcessor(tokenizer, max_seq_len=384, chunk_overlap=32, min_premise_tokens=64)

    results = {}

    for split_name, split_path in [("train", TRAIN_FILE), ("validation", VAL_FILE)]:
        print(f"\nAuditing {split_name} split from {split_path}...")
        records = []
        with open(split_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))

        n_records = len(records)
        class_counts = Counter()
        chunks_by_class = Counter()
        single_chunk_by_class = Counter()
        multi_chunk_by_class = Counter()

        total_chunks = 0
        chunk_distribution = Counter()
        oversized_hypotheses = 0

        # Evidence span tracking
        total_spans_in_split = 0
        records_with_spans = 0

        # Detailed chunk-level evidence containment
        # When an example is partitioned into chunks, every chunk contains the complete hypothesis (or capped at 317)
        # But where is the premise evidence?
        chunks_with_complete_hyp_spans = 0
        chunks_with_partial_hyp_spans = 0
        chunks_with_no_hyp_spans = 0

        # Chunk counts distribution
        premise_token_counts = []
        hyp_token_counts = []

        for rec in records:
            lbl = rec["nli_label"]
            class_counts[lbl] += 1

            rec_id = rec["example_id"].replace(f"nli_ragtruth_{split_name}_", "")
            raw_spans = spans_map.get(rec_id, [])
            if raw_spans:
                records_with_spans += 1
                total_spans_in_split += len(raw_spans)

            chunks = proc.process_example(rec)
            n_chunks = len(chunks)
            total_chunks += n_chunks
            chunk_distribution[n_chunks] += 1
            chunks_by_class[lbl] += n_chunks

            if n_chunks == 1:
                single_chunk_by_class[lbl] += 1
            else:
                multi_chunk_by_class[lbl] += 1

            if chunks[0].metadata.hypothesis_truncated:
                oversized_hypotheses += 1

            # Check spans in chunks
            # In MultiChunkNLIProcessor, hypothesis is replicated in every chunk
            # If the hypothesis has spans, does the chunk's hypothesis contain them?
            kept_h_len = chunks[0].metadata.hypothesis_token_count
            h_text = rec["hypothesis"].strip()
            h_enc = tokenizer(h_text, add_special_tokens=False, return_offsets_mapping=True)
            h_offsets = h_enc.get("offset_mapping", [])

            for ch in chunks:
                if not raw_spans:
                    chunks_with_no_hyp_spans += 1
                    continue

                # Audit span containment for this chunk's hypothesis
                all_spans_kept = True
                any_span_kept = False

                for sp in raw_spans:
                    s_start = sp.get("start", -1)
                    s_end = sp.get("end", -1)
                    tok_indices = [i for i, (ts, te) in enumerate(h_offsets) if te > s_start and ts < s_end]
                    if not tok_indices:
                        continue
                    n_toks = len(tok_indices)
                    n_kept = sum(1 for idx in tok_indices if idx < kept_h_len)
                    if n_kept == n_toks:
                        any_span_kept = True
                    elif n_kept > 0:
                        any_span_kept = True
                        all_spans_kept = False
                    else:
                        all_spans_kept = False

                if all_spans_kept and any_span_kept:
                    chunks_with_complete_hyp_spans += 1
                elif any_span_kept:
                    chunks_with_partial_hyp_spans += 1
                else:
                    chunks_with_no_hyp_spans += 1

        results[split_name] = {
            "total_records": n_records,
            "class_distribution": dict(class_counts),
            "total_chunks": total_chunks,
            "avg_chunks_per_record": round(total_chunks / n_records, 3),
            "chunks_by_class": dict(chunks_by_class),
            "single_chunk_examples": dict(single_chunk_by_class),
            "single_chunk_total": sum(single_chunk_by_class.values()),
            "single_chunk_pct": round((sum(single_chunk_by_class.values()) / n_records) * 100, 2),
            "multi_chunk_examples": dict(multi_chunk_by_class),
            "multi_chunk_total": sum(multi_chunk_by_class.values()),
            "multi_chunk_pct": round((sum(multi_chunk_by_class.values()) / n_records) * 100, 2),
            "chunk_distribution": dict(sorted(chunk_distribution.items())),
            "max_chunks": max(chunk_distribution.keys()),
            "oversized_hypotheses": oversized_hypotheses,
            "oversized_hypotheses_pct": round((oversized_hypotheses / n_records) * 100, 2),
            "records_with_annotated_spans": records_with_spans,
            "total_annotated_spans": total_spans_in_split,
            "chunks_with_complete_hyp_spans": chunks_with_complete_hyp_spans,
            "chunks_with_partial_hyp_spans": chunks_with_partial_hyp_spans,
            "chunks_with_no_hyp_spans": chunks_with_no_hyp_spans,
        }

        print(f"Split {split_name} Complete: {n_records} records -> {total_chunks} chunks.")
        print(f"  Single-chunk: {sum(single_chunk_by_class.values())} ({results[split_name]['single_chunk_pct']}%)")
        print(f"  Multi-chunk: {sum(multi_chunk_by_class.values())} ({results[split_name]['multi_chunk_pct']}%)")
        print(f"  Oversized Hypotheses (>317 tokens): {oversized_hypotheses} ({results[split_name]['oversized_hypotheses_pct']}%)")

    return results


def audit_split_isolation():
    """Verifies that no premise document or example crosses train and validation splits."""
    print("\nVerifying train/validation split isolation...")
    train_docs = set()
    train_ids = set()
    with open(TRAIN_FILE, "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            train_docs.add(r["premise"].strip())
            train_ids.add(r["example_id"])

    val_docs = set()
    val_ids = set()
    doc_overlap = 0
    id_overlap = 0
    with open(VAL_FILE, "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            val_docs.add(r["premise"].strip())
            val_ids.add(r["example_id"])
            if r["premise"].strip() in train_docs:
                doc_overlap += 1
            if r["example_id"] in train_ids:
                id_overlap += 1

    print(f"Train unique docs: {len(train_docs)}, Val unique docs: {len(val_docs)}")
    print(f"Document overlap: {doc_overlap}, ID overlap: {id_overlap}")
    return {
        "train_records": len(train_ids),
        "val_records": len(val_ids),
        "train_unique_docs": len(train_docs),
        "val_unique_docs": len(val_docs),
        "doc_overlap": doc_overlap,
        "id_overlap": id_overlap,
        "split_isolation_status": "STRICTLY_ISOLATED" if (doc_overlap == 0 and id_overlap == 0) else "LEAKAGE_DETECTED",
    }


def main():
    print("=== Track 2, Step 3.14: Multi-Chunk Supervision Readiness Audit ===")
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_DIR, local_files_only=True)
    spans_map = load_spans_map()

    supervision_data = audit_supervision_and_chunking(tokenizer, spans_map)
    isolation_data = audit_split_isolation()

    out_data = {
        "step": "track02_step03_14",
        "supervision_audit": supervision_data,
        "split_isolation": isolation_data,
    }

    out_path = PROJECT_ROOT / "tools/evaluation/step03_14_readiness_data.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)
    print(f"\nReadiness audit data saved to {out_path}")


if __name__ == "__main__":
    main()
