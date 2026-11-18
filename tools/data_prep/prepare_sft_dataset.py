"""Reproducible, evidence-grounded SFT data preparation pipeline for TrustRAG.

Transforms canonical RAGTruth and HaluEval records into a standardized,
versioned SFT dataset (sft_v1) with strict leakage prevention and verifiable provenance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# Root directory of the repository
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class SFTExampleRecord(BaseModel):
    """Canonical schema for TrustRAG evidence-grounded SFT examples."""

    model_config = ConfigDict(extra="forbid")

    example_id: str = Field(description="Unique identifier for the SFT example")
    source_dataset: str = Field(description="Source benchmark ('ragtruth' or 'halueval')")
    source_id: str = Field(description="Original document or query identifier from source benchmark")
    split: Literal["train", "validation"] = Field(description="Target SFT split ('train' or 'validation')")
    question_or_claim: str = Field(description="User query, prompt, or task specification")
    context_or_evidence: str = Field(description="Passage or document text against which claim is verified")
    candidate_response: str = Field(description="The generated claim or answer evaluated for faithfulness")
    ground_truth_label: Literal["FACTUAL", "HALLUCINATED"] = Field(
        description="Ground-truth binary faithfulness label"
    )
    target: str = Field(description="Structured target verification output derived from original annotations")
    target_provenance: str = Field(description="Explicit description of how target was derived from annotations")


def compute_sha256(path: Path) -> str:
    """Compute cryptographic SHA-256 digest of a file."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def format_ragtruth_target(label: str, metadata: dict[str, Any]) -> tuple[str, str]:
    """Deterministically format RAGTruth target from original human span annotations."""
    target_dict: dict[str, Any]
    if label == "FACTUAL":
        target_dict = {
            "verdict": "SUPPORTED",
            "grounding_status": "GROUNDED",
            "hallucination_spans": [],
        }
        provenance = "ragtruth_original_annotations: verified factual summary with zero hallucinated spans"
    else:
        spans = metadata.get("hallucination_spans", [])
        formatted_spans = []
        for s in spans:
            formatted_spans.append({
                "text": s.get("text", ""),
                "conflict_type": s.get("label_type", "Conflict"),
                "meta": s.get("meta", ""),
            })
        target_dict = {
            "verdict": "CONTRADICTED",
            "grounding_status": "HALLUCINATED",
            "hallucination_spans": formatted_spans,
        }
        provenance = f"ragtruth_original_annotations: verified hallucination with {len(formatted_spans)} annotated span conflicts"

    target_json = json.dumps(target_dict, ensure_ascii=False, sort_keys=True)
    return target_json, provenance


def format_halueval_target(label: str, metadata: dict[str, Any]) -> tuple[str, str]:
    """Deterministically format HaluEval target from original QA annotations."""
    pair_type = metadata.get("pair_type", "unknown")
    if label == "FACTUAL":
        target_dict = {
            "verdict": "SUPPORTED",
            "grounding_status": "GROUNDED",
            "source_pair_type": pair_type,
        }
        provenance = "halueval_qa_original_annotations: canonical right_answer grounded in context passage"
    else:
        target_dict = {
            "verdict": "CONTRADICTED",
            "grounding_status": "HALLUCINATED",
            "source_pair_type": pair_type,
        }
        provenance = "halueval_qa_original_annotations: canonical hallucinated_answer conflicting with or unsupported by passage"

    target_json = json.dumps(target_dict, ensure_ascii=False, sort_keys=True)
    return target_json, provenance


def process_ragtruth_split(
    raw_path: Path,
    seed: int = 42,
    val_ratio: float = 0.20,
) -> tuple[list[SFTExampleRecord], list[SFTExampleRecord], dict[str, Any]]:
    """Partition RAGTruth training records by source_id into clean train and validation splits."""
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with open(raw_path, encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            by_source[item["source_id"]].append(item)

    source_ids = sorted(list(by_source.keys()))
    rng = random.Random(seed)
    rng.shuffle(source_ids)

    split_idx = int(len(source_ids) * (1.0 - val_ratio))
    train_sids = set(source_ids[:split_idx])
    val_sids = set(source_ids[split_idx:])

    # Assert 0 source overlap
    assert len(train_sids.intersection(val_sids)) == 0, "Source ID leakage between train and val!"

    train_records: list[SFTExampleRecord] = []
    val_records: list[SFTExampleRecord] = []

    for sid in source_ids:
        assigned_split: Literal["train", "validation"] = "train" if sid in train_sids else "validation"
        for item in by_source[sid]:
            rec_id = item["record_id"]
            label = item["label"]
            meta = item.get("metadata", {})
            prompt = meta.get("prompt", f"Verify the claim against the document: {item.get('claim', '')}")
            target_str, prov_str = format_ragtruth_target(label, meta)

            sft_rec = SFTExampleRecord(
                example_id=f"sft_ragtruth_{assigned_split}_{rec_id}",
                source_dataset="ragtruth",
                source_id=sid,
                split=assigned_split,
                question_or_claim=prompt,
                context_or_evidence=str(item["document"]),
                candidate_response=str(item["claim"]),
                ground_truth_label=label,
                target=target_str,
                target_provenance=prov_str,
            )
            if assigned_split == "train":
                train_records.append(sft_rec)
            else:
                val_records.append(sft_rec)

    stats = {
        "dataset": "ragtruth",
        "total_source_ids": len(source_ids),
        "train_source_ids": len(train_sids),
        "val_source_ids": len(val_sids),
        "train_records": len(train_records),
        "val_records": len(val_records),
        "train_labels": Counter(r.ground_truth_label for r in train_records),
        "val_labels": Counter(r.ground_truth_label for r in val_records),
    }
    return train_records, val_records, stats


def process_halueval_split(
    train_path: Path,
    val_path: Path,
) -> tuple[list[SFTExampleRecord], list[SFTExampleRecord], dict[str, Any]]:
    """Process HaluEval QA records using official pre-partitioned train and validation splits."""
    train_records: list[SFTExampleRecord] = []
    val_records: list[SFTExampleRecord] = []
    train_sids = set()
    val_sids = set()

    # Process train
    with open(train_path, encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            sid = item["source_id"]
            train_sids.add(sid)
            rec_id = item["record_id"]
            label = item["label"]
            meta = item.get("metadata", {})
            query = meta.get("query", "Answer the question based on the passage.")
            target_str, prov_str = format_halueval_target(label, meta)

            sft_rec = SFTExampleRecord(
                example_id=f"sft_halueval_train_{rec_id}",
                source_dataset="halueval",
                source_id=sid,
                split="train",
                question_or_claim=query,
                context_or_evidence=str(item["document"]),
                candidate_response=str(item["claim"]),
                ground_truth_label=label,
                target=target_str,
                target_provenance=prov_str,
            )
            train_records.append(sft_rec)

    # Process validation
    with open(val_path, encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            sid = item["source_id"]
            val_sids.add(sid)
            rec_id = item["record_id"]
            label = item["label"]
            meta = item.get("metadata", {})
            query = meta.get("query", "Answer the question based on the passage.")
            target_str, prov_str = format_halueval_target(label, meta)

            sft_rec = SFTExampleRecord(
                example_id=f"sft_halueval_val_{rec_id}",
                source_dataset="halueval",
                source_id=sid,
                split="validation",
                question_or_claim=query,
                context_or_evidence=str(item["document"]),
                candidate_response=str(item["claim"]),
                ground_truth_label=label,
                target=target_str,
                target_provenance=prov_str,
            )
            val_records.append(sft_rec)

    # Assert 0 source overlap
    assert len(train_sids.intersection(val_sids)) == 0, "Source ID leakage in HaluEval train and val!"

    stats = {
        "dataset": "halueval",
        "train_source_ids": len(train_sids),
        "val_source_ids": len(val_sids),
        "train_records": len(train_records),
        "val_records": len(val_records),
        "train_labels": Counter(r.ground_truth_label for r in train_records),
        "val_labels": Counter(r.ground_truth_label for r in val_records),
    }
    return train_records, val_records, stats


def main() -> None:
    parser = argparse.ArgumentParser(description="TrustRAG SFT Dataset Preparation Pipeline (sft_v1)")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=REPO_ROOT / "data",
        help="Root path to datasets directory",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data/processed/sft_v1",
        help="Target output directory for sft_v1",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for RAGTruth split grouping")
    parser.add_argument("--ragtruth-val-ratio", type=float, default=0.20, help="Validation ratio for RAGTruth")
    args = parser.parse_args()

    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    rt_train_file = args.data_dir / "processed/ragtruth/train.jsonl"
    he_train_file = args.data_dir / "processed/halueval/train.jsonl"
    he_val_file = args.data_dir / "processed/halueval/validation.jsonl"

    for p in (rt_train_file, he_train_file, he_val_file):
        if not p.exists():
            print(f"ERROR: Missing input dataset file: {p}", file=sys.stderr)
            sys.exit(1)

    print("=== Processing RAGTruth SFT Split (80/20 Source-Grouped) ===")
    rt_train, rt_val, rt_stats = process_ragtruth_split(
        rt_train_file, seed=args.seed, val_ratio=args.ragtruth_val_ratio
    )
    print(f"RAGTruth: {rt_stats['train_records']} train records ({rt_stats['train_source_ids']} sources), "
          f"{rt_stats['val_records']} val records ({rt_stats['val_source_ids']} sources)")

    print("\n=== Processing HaluEval SFT Split (Canonical Partition) ===")
    he_train, he_val, he_stats = process_halueval_split(he_train_file, he_val_file)
    print(f"HaluEval: {he_stats['train_records']} train records ({he_stats['train_source_ids']} sources), "
          f"{he_stats['val_records']} val records ({he_stats['val_source_ids']} sources)")

    all_train = sorted(rt_train + he_train, key=lambda r: r.example_id)
    all_val = sorted(rt_val + he_val, key=lambda r: r.example_id)

    # Cross-dataset and cross-split leakage verification
    train_ids = set(r.example_id for r in all_train)
    val_ids = set(r.example_id for r in all_val)
    assert len(train_ids) == len(all_train), "Duplicate example_ids found in train!"
    assert len(val_ids) == len(all_val), "Duplicate example_ids found in val!"
    assert len(train_ids.intersection(val_ids)) == 0, "Example ID collision between train and val!"

    # Test-set quarantine verification
    rt_test_file = args.data_dir / "processed/ragtruth/test.jsonl"
    he_test_file = args.data_dir / "processed/halueval/test.jsonl"
    with open(rt_test_file) as f:
        rt_test_sids = set(json.loads(line_str)["source_id"] for line_str in f)
    with open(he_test_file) as f:
        he_test_sids = set(json.loads(line_str)["source_id"] for line_str in f)

    all_train_sids = set(r.source_id for r in all_train)
    all_val_sids = set(r.source_id for r in all_val)

    assert len(all_train_sids.intersection(rt_test_sids)) == 0, "RAGTruth test source leakage into train!"
    assert len(all_val_sids.intersection(rt_test_sids)) == 0, "RAGTruth test source leakage into val!"
    assert len(all_train_sids.intersection(he_test_sids)) == 0, "HaluEval test source leakage into train!"
    assert len(all_val_sids.intersection(he_test_sids)) == 0, "HaluEval test source leakage into val!"

    print("\n=== Writing SFT v1 Artifacts to Disk ===")
    train_path = out_dir / "train.jsonl"
    val_path = out_dir / "validation.jsonl"

    with open(train_path, "w", encoding="utf-8") as f:
        for r in all_train:
            f.write(r.model_dump_json() + "\n")

    with open(val_path, "w", encoding="utf-8") as f:
        for r in all_val:
            f.write(r.model_dump_json() + "\n")

    schema_path = out_dir / "schema.json"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(SFTExampleRecord.model_json_schema(), f, indent=2)

    # Checksums
    train_sha = compute_sha256(train_path)
    val_sha = compute_sha256(val_path)
    schema_sha = compute_sha256(schema_path)

    manifest_data = {
        "dataset_name": "sft_v1",
        "description": "Standardized evidence-grounded SFT dataset for TrustRAG neural fine-tuning",
        "version": "1.0.0",
        "seed": args.seed,
        "schema_sha256": schema_sha,
        "splits": {
            "train": {
                "records": len(all_train),
                "file": "train.jsonl",
                "sha256": train_sha,
                "label_distribution": dict(Counter(r.ground_truth_label for r in all_train)),
                "sources_distribution": dict(Counter(r.source_dataset for r in all_train)),
            },
            "validation": {
                "records": len(all_val),
                "file": "validation.jsonl",
                "sha256": val_sha,
                "label_distribution": dict(Counter(r.ground_truth_label for r in all_val)),
                "sources_distribution": dict(Counter(r.source_dataset for r in all_val)),
            },
        },
        "leakage_verification": {
            "train_val_source_overlap": 0,
            "train_test_source_overlap": 0,
            "val_test_source_overlap": 0,
            "hotpotqa_retrieval_records_used": 0,
            "ms_marco_retrieval_records_used": 0,
            "test_splits_quarantined": True,
        },
        "target_provenance": {
            "ragtruth": "Original human span annotations + deterministic verdict mapping",
            "halueval": "Original QA factual/hallucinated answer labels + deterministic verdict mapping",
            "synthetic_chain_of_thought_fabricated": False,
        },
    }

    manifest_path = out_dir / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    report_path = out_dir / "preprocessing_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"""# TrustRAG SFT Dataset v1 Preprocessing Report

## Summary
- **Version:** `sft_v1`
- **Total Records:** {len(all_train) + len(all_val):,}
- **Train Split:** {len(all_train):,} records ({len(rt_train):,} RAGTruth + {len(he_train):,} HaluEval)
- **Validation Split:** {len(all_val):,} records ({len(rt_val):,} RAGTruth + {len(he_val):,} HaluEval)
- **Leakage Status:** Verified 0 source document overlap between train, validation, and quarantined test sets.
- **Retrieval Isolation:** HotpotQA and MS MARCO validation records strictly excluded (0 records).
- **Target Construction:** Deterministic mapping from expert annotations; zero synthetic reasoning traces fabricated.

## Split Statistics
| Dataset | Split | Total Records | FACTUAL | HALLUCINATED | Unique Source IDs |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **RAGTruth** | train | {len(rt_train):,} | {rt_stats['train_labels']['FACTUAL']:,} | {rt_stats['train_labels']['HALLUCINATED']:,} | {rt_stats['train_source_ids']:,} |
| **RAGTruth** | validation | {len(rt_val):,} | {rt_stats['val_labels']['FACTUAL']:,} | {rt_stats['val_labels']['HALLUCINATED']:,} | {rt_stats['val_source_ids']:,} |
| **HaluEval** | train | {len(he_train):,} | {he_stats['train_labels']['FACTUAL']:,} | {he_stats['train_labels']['HALLUCINATED']:,} | {he_stats['train_source_ids']:,} |
| **HaluEval** | validation | {len(he_val):,} | {he_stats['val_labels']['FACTUAL']:,} | {he_stats['val_labels']['HALLUCINATED']:,} | {he_stats['val_source_ids']:,} |
| **Total Combined** | **train** | **{len(all_train):,}** | **{Counter(r.ground_truth_label for r in all_train)['FACTUAL']:,}** | **{Counter(r.ground_truth_label for r in all_train)['HALLUCINATED']:,}** | **{len(all_train_sids):,}** |
| **Total Combined** | **validation** | **{len(all_val):,}** | **{Counter(r.ground_truth_label for r in all_val)['FACTUAL']:,}** | **{Counter(r.ground_truth_label for r in all_val)['HALLUCINATED']:,}** | **{len(all_val_sids):,}** |
""")

    checksums_path = out_dir / "checksums.sha256"
    with open(checksums_path, "w", encoding="utf-8") as f:
        for fname in sorted(["train.jsonl", "validation.jsonl", "dataset_manifest.json", "schema.json", "preprocessing_report.md"]):
            f.write(f"{compute_sha256(out_dir / fname)}  {fname}\n")

    print(f"SUCCESS: SFT dataset v1 successfully generated in {out_dir}!")
    print(f"  Train: {len(all_train):,} records ({train_sha[:12]}...)")
    print(f"  Validation: {len(all_val):,} records ({val_sha[:12]}...)")


if __name__ == "__main__":
    main()
