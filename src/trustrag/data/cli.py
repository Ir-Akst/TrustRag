"""Command-Line Interface (CLI) for TrustRAG Dataset Engineering.

Provides explicit commands for:
- Listing registered datasets (list)
- Inspecting metadata, licensing, and access requirements (inspect)
- Downloading / acquiring raw datasets (download)
- Importing local files (import)
- Preprocessing and deduplicating records (preprocess)
- Validating records and reporting malformed data (validate)
- Splitting data with leakage checks and reporting statistics (split-stats)
- Generating dataset manifests and dataset cards (manifest)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from trustrag.config.dataset_config import DatasetRootConfig
from trustrag.data.acquisition.local import LocalFileImporter
from trustrag.data.acquisition.manager import (
    CONFIGURED_TARGETS,
    PRIORITY_TIERS,
    AcquisitionManager,
)
from trustrag.data.base import BaseAdapter, DatasetMetadata
from trustrag.data.benchmarks.builder import BENCHMARK_CATEGORIES, BenchmarkBuilder
from trustrag.data.manifest import DatasetManifest, ManifestManager
from trustrag.data.quality import DatasetQualityAuditor
from trustrag.data.registry import (
    get_adapter_class,
    get_dataset_metadata,
    list_datasets,
    load_dataset,
)
from trustrag.data.resource import ResourceManager, format_bytes
from trustrag.data.schemas import (
    ClaimVerificationRecord,
    DocumentRecord,
    QueryRecord,
    SecurityRecord,
)
from trustrag.data.splitting import (
    LeakageResistantSplitter,
    SplitConfig,
    SplitStatistics,
)
from trustrag.data.storage import DatasetStorage, compute_file_sha256
from trustrag.data.validation import RecordValidator


def cmd_list(args: argparse.Namespace) -> int:
    """List all registered datasets."""
    print("=" * 80)
    print("TrustRAG Registered Datasets (Phase 01)")
    print("=" * 80)
    header = f"{'Dataset Name':<20} {'Category':<18} {'Record Type':<25} {'Access':<12}"
    print(header)
    print("-" * 80)

    for name in list_datasets():
        meta = get_dataset_metadata(name)
        print(f"{meta.name:<20} {meta.category:<18} {meta.record_type:<25} {meta.access_type:<12}")

    print("=" * 80)
    print(f"Total registered datasets: {len(list_datasets())}")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    """Inspect dataset metadata."""
    name = args.dataset.lower()
    try:
        meta = get_dataset_metadata(name)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print("=" * 80)
    print(f"Dataset Metadata: {meta.name}")
    print("=" * 80)
    print(f"Category:                 {meta.category}")
    print(f"Record Schema Type:       {meta.record_type}")
    print(f"Source Identifier/URI:    {meta.source_uri}")
    print(f"Verified License:         {meta.license}")
    print(f"Access Conditions:        {meta.access_type}")
    print(f"Default Config:           {meta.default_config or 'None'}")
    print(f"Default Splits:           {', '.join(meta.default_splits)}")
    print(f"Permitted for Training:   {'Yes' if meta.permitted_for_training else 'NO (Evaluation Only)'}")
    print(f"Permitted for Evaluation: {'Yes' if meta.permitted_for_evaluation else 'No'}")
    print(f"Paper Reference:          {meta.paper_reference or 'None'}")
    print(f"Intended Use:             {meta.intended_use}")
    print(f"Known Limitations:        {meta.known_limitations or 'None'}")
    print("=" * 80)
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    """Acquire records from official remote sources or verify local cache."""
    name = args.dataset.lower()
    limit = args.limit
    if args.smoke_test and (limit is None or limit > 100):
        limit = 100

    print(f"Acquiring dataset: '{name}' (split={args.split}, limit={limit}, offline={args.offline})...")
    try:
        records = list(
            load_dataset(
                name,
                split=args.split,
                limit=limit,
                offline=args.offline,
                config_name=args.config_name,
                local_path=args.local_path,
            )
        )
        print(f"Successfully loaded {len(records)} records for '{name}'.")
        if args.output:
            out_path = Path(args.output)
            res = DatasetStorage.save_jsonl(records, out_path)
            print(f"Saved to {res['file_path']} (SHA-256: {res['sha256'][:16]}...)")
        return 0
    except Exception as e:
        print(f"Download/Acquisition failed: {e}", file=sys.stderr)
        return 1


def cmd_import(args: argparse.Namespace) -> int:
    """Import records from a local file into a normalized dataset partition."""
    path = Path(args.file)
    name = args.dataset.lower()
    limit = args.limit

    print(f"Importing local file '{path}' as dataset '{name}'...")
    try:
        records = list(
            load_dataset(
                name,
                split=args.split,
                limit=limit,
                local_path=str(path),
                offline=True,
            )
        )
        print(f"Successfully imported and normalized {len(records)} records from {path}.")
        if args.output:
            out_path = Path(args.output)
            res = DatasetStorage.save_jsonl(records, out_path)
            print(f"Saved normalized partition to {res['file_path']} (SHA-256: {res['sha256'][:16]}...)")
        return 0
    except Exception as e:
        print(f"Import failed: {e}", file=sys.stderr)
        return 1


def cmd_preprocess(args: argparse.Namespace) -> int:
    """Run preprocessing, cleaning, and deduplication on a dataset."""
    name = args.dataset.lower()
    limit = args.limit
    if args.smoke_test and (limit is None or limit > 100):
        limit = 100

    adapter_cls = get_adapter_class(name)
    adapter = adapter_cls(
        split=args.split,
        limit=limit,
        offline=args.offline,
        local_path=args.local_path,
        config_name=args.config_name,
    )

    print(f"Running preprocessing pipeline on '{name}'...")
    records = list(adapter.process(deduplicate=not args.no_dedup, clean=not args.no_clean))

    stats = adapter.get_stats()
    dedup_report = adapter.get_deduplication_report()

    print("=" * 80)
    print(f"Preprocessing Pipeline Summary for '{name}':")
    print(f"  Raw records read:        {stats.raw_records}")
    print(f"  Processed records:       {stats.processed_records}")
    print(f"  Valid normalized:        {stats.valid_records}")
    print(f"  Invalid records dropped: {stats.invalid_records}")
    print(f"  Empty records dropped:   {stats.empty_records}")
    print(f"  Duplicate records:       {stats.duplicate_records}")
    print(f"  Unique records retained: {dedup_report.unique_records}")
    print("=" * 80)

    out_dir = Path(args.output_dir or f"data/processed/{name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{args.split}.jsonl"
    storage_res = DatasetStorage.save_jsonl(records, out_file)
    print(f"Saved processed partition to: {storage_res['file_path']}")
    print(f"SHA-256 Checksum: {storage_res['sha256']}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a dataset file or partition and report quality metrics."""
    target_path = Path(args.file)
    name = args.dataset.lower() if args.dataset else target_path.stem.lower()
    if name in {"test", "train", "val", "validation"} and target_path.parent.name not in {".", "", "data"}:
        name = target_path.parent.name.lower()

    if not target_path.is_file():
        # Check if args.file is a registered dataset name
        clean_ds = args.file.lower().strip()
        candidates = [
            Path(f"data/processed/{clean_ds}/validation.jsonl"),
            Path(f"data/processed/{clean_ds}/test.jsonl"),
            Path(f"data/processed/{clean_ds}/train.jsonl"),
            Path(f"data/raw/{clean_ds}/test.jsonl"),
            Path(f"data/raw/{clean_ds}/raw_test.jsonl"),
        ]
        found = False
        for c in candidates:
            if c.is_file():
                target_path = c
                name = clean_ds
                found = True
                break
        if not found:
            print(f"File '{args.file}' not found and no data found for dataset '{args.file}'.", file=sys.stderr)
            return 1

    print(f"Validating records in '{target_path}' (dataset='{name}')...")
    try:
        raw_records = list(LocalFileImporter.read_records(target_path, limit=args.limit))
    except Exception as e:
        print(f"Failed to read file: {e}", file=sys.stderr)
        return 1

    validator = RecordValidator(dataset_name=name)
    schema_map: dict[str, Any] = {
        "DocumentRecord": DocumentRecord,
        "QueryRecord": QueryRecord,
        "ClaimVerificationRecord": ClaimVerificationRecord,
        "SecurityRecord": SecurityRecord,
    }
    record_type: Any = None
    if name in list_datasets():
        meta = get_dataset_metadata(name)
        record_type = schema_map.get(meta.record_type)
    elif (target_path.parent / "manifest.json").is_file():
        try:
            m_data = json.loads((target_path.parent / "manifest.json").read_text(encoding="utf-8"))
            record_type = schema_map.get(m_data.get("record_type"))
        except Exception:
            pass

    normalized_records = []
    for item in raw_records:
        rec: Any = item
        if isinstance(item, dict):
            if record_type:
                try:
                    rec = record_type.model_validate(item)
                except Exception as e:
                    validator.report.total_checked += 1
                    validator.report.invalid_count += 1
                    validator.report.errors.append(f"Schema validation error: {e}")
                    continue
            else:
                for model_cls in (SecurityRecord, ClaimVerificationRecord, QueryRecord, DocumentRecord):
                    try:
                        rec = model_cls.model_validate(item)
                        break
                    except Exception:
                        continue

        validator.validate(rec)
        normalized_records.append(rec)

    report = validator.get_report()
    quality = DatasetQualityAuditor.audit_records(normalized_records, dataset_name=name)

    print("=" * 80)
    print(f"Validation & Quality Report for '{name}':")
    print(f"  Total records checked:   {report.total_checked}")
    print(f"  Valid records:           {report.valid_count}")
    print(f"  Invalid records:         {report.invalid_count}")
    print(f"  Empty records:           {report.empty_count}")
    print(f"  Duplicate records:       {quality.duplicate_records}")
    print(f"  Label errors:            {report.label_error_count}")
    print(f"  Missing required fields: {quality.missing_required_fields}")
    print(f"  Missing source IDs:      {quality.missing_source_ids}")
    print(f"  Unique documents:        {quality.unique_documents}")
    print(f"  Unique queries:          {quality.unique_queries}")
    print(f"  Unique claims:           {quality.unique_claims}")
    print(f"  Status:                  {'PASS' if report.is_valid and quality.is_healthy else 'FAIL'}")
    if report.errors or quality.error_samples:
        print("  Sample errors:")
        all_errs = report.errors + quality.error_samples
        for err in all_errs[:5]:
            print(f"    - {err}")
    print("=" * 80)

    if getattr(args, "report", False) or getattr(args, "output", None):
        out_path = Path(args.output or f"data/reports/{name}_quality_report.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(quality.to_json(indent=2), encoding="utf-8")
        print(f"Saved detailed quality report to: {out_path}")

    return 0 if (report.is_valid and quality.is_healthy) else 1


def cmd_split_stats(args: argparse.Namespace) -> int:
    """Audit official partitions for leakage, or perform custom splitting if explicitly requested."""
    name = args.dataset.lower()
    limit = args.limit or (100 if args.smoke_test else 500)

    meta = get_dataset_metadata(name)
    schema_map: dict[str, Any] = {
        "DocumentRecord": DocumentRecord,
        "QueryRecord": QueryRecord,
        "ClaimVerificationRecord": ClaimVerificationRecord,
        "SecurityRecord": SecurityRecord,
    }
    rec_type: Any = schema_map.get(meta.record_type)

    if args.custom_split:
        print(f"Explicit custom splitting requested for '{name}' (limit={limit})...")
        records: List[Any] = []
        if args.local_path and Path(args.local_path).is_file():
            try:
                records = list(DatasetStorage.load_jsonl(args.local_path, record_type=rec_type, limit=limit))
            except Exception:
                records = []

        if not records:
            records = list(
                load_dataset(
                    name,
                    split=args.split,
                    limit=limit,
                    offline=args.offline,
                    local_path=args.local_path,
                )
            )

        config = SplitConfig(
            train_ratio=args.train_ratio,
            val_ratio=args.val_ratio,
            test_ratio=args.test_ratio,
            seed=args.seed,
            group_key=args.group_key,
        )

        try:
            splits, stats = LeakageResistantSplitter.split(records, config=config, dataset_name=name)
            stats_dict = stats.to_dict()
            print("=" * 80)
            print(f"Custom 70/15/15 Split & Leakage Audit for '{name}':")
            print(f"  Split Mode:              CUSTOM (Explicitly Requested)")
            print(f"  Total records:           {stats.total_records}")
            print(f"  Train partition size:    {stats.train_count} ({stats_dict['train_ratio_actual']*100:.1f}%)")
            print(f"  Val partition size:      {stats.val_count} ({stats_dict['val_ratio_actual']*100:.1f}%)")
            print(f"  Test partition size:     {stats.test_count} ({stats_dict['test_ratio_actual']*100:.1f}%)")
            print(f"  Number of unique groups: {stats.num_groups}")
            print(f"  Group Overlaps:          train-val={stats.group_overlap_train_val}, "
                  f"train-test={stats.group_overlap_train_test}, val-test={stats.group_overlap_val_test}")
            print(f"  Content Hash Overlaps:   train-val={stats.hash_overlap_train_val}, "
                  f"train-test={stats.hash_overlap_train_test}, val-test={stats.hash_overlap_val_test}")
            print(f"  Leakage Detected:        {'YES (FAIL)' if stats.leakage_detected else 'NO (PASS)'}")
            print("=" * 80)

            if args.output_dir:
                custom_dir = Path(args.output_dir)
                custom_dir.mkdir(parents=True, exist_ok=True)
                file_entries = []
                for s_name, s_recs in splits.items():
                    s_file = custom_dir / f"custom_{s_name}.jsonl"
                    res = DatasetStorage.save_jsonl(s_recs, s_file)
                    res["split"] = f"custom_{s_name}"
                    res["split_type"] = "custom"
                    file_entries.append(res)
                manifest = ManifestManager.create_manifest(
                    metadata=meta,
                    split_stats=stats,
                    files=file_entries,
                    base_dir=custom_dir,
                    split_type="custom",
                )
                ManifestManager.save_manifest(manifest, custom_dir)
                ManifestManager.generate_dataset_card(manifest, custom_dir)
                print(f"Saved custom splits and manifest to: {custom_dir}")

            return 0
        except Exception as e:
            print(f"Custom split error / leakage detected: {e}", file=sys.stderr)
            return 1
    else:
        # Official split preservation and audit
        print(f"Preserving official partition for '{name}'. Auditing partition data (limit={limit})...")
        local_target = Path(args.local_path) if args.local_path else Path(f"data/processed/{name}/{args.split}.jsonl")
        official_records: List[Any] = []
        if local_target.is_file():
            try:
                official_records = list(DatasetStorage.load_jsonl(local_target, record_type=rec_type, limit=limit))
            except Exception:
                official_records = []

        if not official_records:
            official_records = list(
                load_dataset(
                    name,
                    split=args.split,
                    limit=limit,
                    offline=args.offline,
                    local_path=str(local_target) if local_target.exists() else None,
                )
            )

        partitions = {args.split: official_records}
        stats = LeakageResistantSplitter.audit_partitions(
            partitions=partitions,
            dataset_name=name,
            group_key=args.group_key,
            split_type="official",
            raise_on_leakage=False,
        )

        print("=" * 80)
        print(f"Official Partition Audit for '{name}' (Preserving Official Split):")
        print(f"  Split Mode:              OFFICIAL (Partition Preserved)")
        print(f"  Partition Name:          {args.split}")
        print(f"  Total records:           {stats.total_records}")
        print(f"  Number of unique groups: {stats.num_groups}")
        print(f"  Leakage Detected:        {'YES (FAIL)' if stats.leakage_detected else 'NO (PASS)'}")
        print("  Notice: Official evaluation split preserved without silent repartitioning.")
        print("=" * 80)
        return 0


def cmd_manifest(args: argparse.Namespace) -> int:
    """Generate manifest.json and dataset card README.md, and optionally validate consistency."""
    name = args.dataset.lower()
    meta = get_dataset_metadata(name)
    dir_path = Path(args.dir or f"data/processed/{name}")

    if not dir_path.is_dir():
        print(f"Directory '{dir_path}' does not exist.", file=sys.stderr)
        return 1

    files: List[Dict[str, Any]] = []
    is_custom = "custom_splits" in dir_path.as_posix()
    for p in dir_path.glob("*.jsonl"):
        split_name = p.stem.replace("custom_", "")
        s_type = "custom" if "custom" in p.stem or is_custom else "official"
        with p.open("r", encoding="utf-8") as fh:
            rec_cnt = sum(1 for line in fh if line.strip())
        entry = {
            "split": p.stem,
            "original_split": split_name,
            "processed_split": p.stem,
            "split_type": s_type,
            "file_path": p.name,
            "format": "jsonl",
            "record_count": rec_cnt,
            "file_size_bytes": p.stat().st_size,
            "sha256": compute_file_sha256(p),
        }
        files.append(entry)

    total_records = sum(f["record_count"] for f in files)
    from trustrag.data.base import ProcessingStats
    stats = ProcessingStats(
        raw_records=total_records,
        processed_records=total_records,
        valid_records=total_records,
    )

    manifest = ManifestManager.create_manifest(
        metadata=meta,
        stats=stats,
        files=files,
        base_dir=dir_path,
        split_type="custom" if is_custom else "official",
    )
    manifest_file = ManifestManager.save_manifest(manifest, dir_path)
    card_file = dir_path / "README.md"
    ManifestManager.generate_dataset_card(manifest, dir_path)

    print(f"Generated manifest: {manifest_file}")
    print(f"Generated dataset card: {card_file}")

    if args.validate:
        is_valid, errors = ManifestManager.validate_manifest(manifest, dir_path)
        print(f"Manifest Consistency Validation: {'PASS' if is_valid else 'FAIL'}")
        if errors:
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            return 1

    return 0


def cmd_acquire(args: argparse.Namespace) -> int:
    """Acquire one dataset or a batch of datasets by priority tier."""
    mgr = AcquisitionManager()
    if getattr(args, "batch", None):
        print(f"Acquiring batch of datasets for tier '{args.batch}' (smoke_test={args.smoke_test}, limit={args.limit}, offline={args.offline})...")
        results = mgr.acquire_batch(
            tier=args.batch,
            limit=args.limit,
            smoke_test=args.smoke_test,
            offline=args.offline,
        )
        print("=" * 80)
        print(f"Batch Acquisition Results ({args.batch}):")
        print(f"{'Dataset':<20} {'Status':<12} {'Records':<10} {'Raw File'}")
        print("-" * 80)
        for ds, res in results.items():
            print(f"{ds:<20} {res.status:<12} {res.records_acquired:<10} {res.raw_file_path}")
        print("=" * 80)
        return 0

    if not args.dataset:
        print("Error: Specify a dataset name or use --batch <p0|p1|p2|all>", file=sys.stderr)
        return 1

    name = args.dataset.lower()
    split_name = args.split or "train"
    print(f"Acquiring dataset: '{name}' (split={split_name}, limit={args.limit}, offline={args.offline})...")
    try:
        records, entry = mgr.acquire(
            dataset_name=name,
            split=split_name,
            limit=args.limit,
            smoke_test=args.smoke_test,
            offline=args.offline,
            config_name=args.config_name,
            local_path=args.local_path,
        )
        print("=" * 80)
        print(f"Acquisition Summary: {name}")
        print(f"  Records Acquired:   {len(records)}")
        print(f"  Raw File Saved:     {entry.raw_file_path}")
        print(f"  File Size:          {format_bytes(entry.raw_file_bytes)}")
        print(f"  SHA-256:            {entry.raw_file_sha256}")
        print(f"  Status:             {entry.status}")
        print("=" * 80)
        return 0
    except Exception as e:
        print(f"Acquisition failed: {e}", file=sys.stderr)
        return 1


def cmd_storage(args: argparse.Namespace) -> int:
    """Report repository storage usage and acquisition status."""
    report = ResourceManager.report_repository_storage()
    print("=" * 80)
    print("TrustRAG Repository Storage Breakdown")
    print("=" * 80)
    print(f"Total Repository Storage: {report['total_human_size']} ({report['total_bytes']} bytes in {report['total_files']} files)")
    print(f"Host Disk Free Space:     {report['disk_free_human']}")
    print("-" * 80)
    print(f"{'Tier':<16} {'Size':<12} {'Total Files':<14} {'JSONL':<8} {'Parquet':<8}")
    print("-" * 80)
    for t_name, t_info in report["tiers"].items():
        print(f"{t_name:<16} {t_info['human_size']:<12} {t_info['file_count']:<14} {t_info['jsonl_count']:<8} {t_info['parquet_count']:<8}")
    print("=" * 80)

    mgr = AcquisitionManager()
    status_list = mgr.get_acquisition_status()
    print("\n" + "=" * 80)
    print("Dataset Acquisition & Processing Status")
    print("=" * 80)
    print(f"{'Dataset Name':<20} {'Target':<10} {'Raw':<8} {'Processed':<10} {'Storage':<12} {'Status'}")
    print("-" * 80)
    for s in status_list:
        print(f"{s['dataset_name']:<20} {s['configured_target']:<10} {s['raw_records']:<8} {s['processed_records']:<10} {format_bytes(s['storage_bytes']):<12} {s['status']}")
    print("=" * 80)
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    """Construct or audit benchmark categories."""
    builder = BenchmarkBuilder(output_root=args.output_dir or "data/benchmarks")
    cat = args.category.lower() if args.category else "all"

    if args.bench_action == "build":
        print(f"Building benchmark category: '{cat}' (limit={args.limit})...")
        if cat == "all":
            results = builder.build_all(limit=args.limit or 200)
            print("=" * 80)
            print("Benchmark Construction Complete for All Categories:")
            print("-" * 80)
            for c_name, res in results.items():
                print(f"  [{c_name}] Total: {res['total_records']}, Splits: {res['split_sizes']}, Quality: {res['quality_status']}, Leakage: {'YES' if res['leakage_detected'] else 'NO'}")
            print("=" * 80)
            return 0
        elif cat == "clean_rag":
            res = builder.build_clean_rag(limit=args.limit or 500)
        elif cat == "knowledge_poisoning":
            res = builder.build_knowledge_poisoning(num_pairs=args.limit or 500)
        elif cat == "hallucination":
            res = builder.build_hallucination(limit_per_source=args.limit or 250)
        elif cat == "adversarial_robustness":
            res = builder.build_adversarial_robustness(num_pairs=args.limit or 500)
        else:
            print(f"Unknown benchmark category '{cat}'. Allowed: {BENCHMARK_CATEGORIES + ['all']}", file=sys.stderr)
            return 1

        print("=" * 80)
        print(f"Benchmark Built: {res['category']}")
        print(f"  Output Directory:  {res['output_dir']}")
        print(f"  Total Records:     {res['total_records']}")
        print(f"  Split Sizes:       {res['split_sizes']}")
        print(f"  Quality Status:    {res['quality_status']}")
        print(f"  Leakage Detected:  {'YES (FAIL)' if res['leakage_detected'] else 'NO (PASS)'}")
        print(f"  Manifest Verified: {'YES (PASS)' if res['manifest_verified'] else 'FAIL'}")
        print("=" * 80)
        return 0

    elif args.bench_action == "audit":
        bench_dir = Path(args.output_dir or f"data/benchmarks/{cat}")
        if not bench_dir.is_dir():
            print(f"Benchmark directory '{bench_dir}' does not exist.", file=sys.stderr)
            return 1
        print(f"Auditing benchmark directory: {bench_dir}...")
        partitions = {}
        for p in bench_dir.glob("*.jsonl"):
            s_name = p.stem
            partitions[s_name] = list(DatasetStorage.load_jsonl(p))

        stats = LeakageResistantSplitter.audit_partitions(
            partitions=partitions,  # type: ignore[arg-type]
            dataset_name=cat,
            split_type="custom",
            raise_on_leakage=False,
        )
        all_recs = []
        for p_recs in partitions.values():
            all_recs.extend(p_recs)
        quality = DatasetQualityAuditor.audit_records(all_recs, dataset_name=cat)

        print("=" * 80)
        print(f"Benchmark Audit Report: {cat}")
        print(f"  Total Records:     {stats.total_records}")
        print(f"  Unique Groups:     {stats.num_groups}")
        print(f"  Leakage Detected:  {'YES (FAIL)' if stats.leakage_detected else 'NO (PASS)'}")
        print(f"  Group Overlaps:    train-val={stats.group_overlap_train_val}, train-test={stats.group_overlap_train_test}, val-test={stats.group_overlap_val_test}")
        print(f"  Hash Overlaps:     train-val={stats.hash_overlap_train_val}, train-test={stats.hash_overlap_train_test}, val-test={stats.hash_overlap_val_test}")
        print(f"  Quality Health:    {'HEALTHY (PASS)' if quality.is_healthy else 'ISSUES'}")
        print(f"  Valid / Total:     {quality.valid_records} / {quality.total_records}")
        print(f"  Duplicates:        {quality.duplicate_records}")
        print("=" * 80)
        return 0 if not stats.leakage_detected and quality.is_healthy else 1

    else:
        print(f"Unknown benchmark action '{args.bench_action}'. Choose 'build' or 'audit'.", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="trustrag-data",
        description="TrustRAG Dataset Engineering and Security Benchmark CLI (Phase 01 & Phase 02)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. list
    subparsers.add_parser("list", help="List all registered datasets")

    # 2. inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect dataset metadata and licensing")
    p_inspect.add_argument("dataset", help="Registered dataset name")

    # 3. download
    p_dl = subparsers.add_parser("download", help="Acquire a dataset from official sources")
    p_dl.add_argument("dataset", help="Registered dataset name")
    p_dl.add_argument("--split", default="train", help="Dataset split")
    p_dl.add_argument("--limit", type=int, default=None, help="Max records limit")
    p_dl.add_argument("--smoke-test", action="store_true", help="Force limit to 100 records")
    p_dl.add_argument("--offline", action="store_true", help="Enforce offline mode")
    p_dl.add_argument("--config-name", default=None, help="Dataset configuration/subset")
    p_dl.add_argument("--local-path", default=None, help="Optional local path override")
    p_dl.add_argument("--output", default=None, help="Path to save downloaded records")

    # 4. import
    p_imp = subparsers.add_parser("import", help="Import a local dataset file")
    p_imp.add_argument("dataset", help="Registered dataset name to normalize as")
    p_imp.add_argument("file", help="Path to local file (.json, .jsonl, .csv, .parquet)")
    p_imp.add_argument("--split", default="train", help="Target split name")
    p_imp.add_argument("--limit", type=int, default=None, help="Max records limit")
    p_imp.add_argument("--output", default=None, help="Output JSONL path")

    # 5. preprocess
    p_prep = subparsers.add_parser("preprocess", help="Preprocess, clean, and deduplicate dataset")
    p_prep.add_argument("dataset", help="Registered dataset name")
    p_prep.add_argument("--split", default="train", help="Target split")
    p_prep.add_argument("--limit", type=int, default=None, help="Record limit")
    p_prep.add_argument("--smoke-test", action="store_true", help="Force limit to 100 records")
    p_prep.add_argument("--offline", action="store_true", help="Enforce offline mode")
    p_prep.add_argument("--no-clean", action="store_true", help="Disable text cleaning")
    p_prep.add_argument("--no-dedup", action="store_true", help="Disable deduplication")
    p_prep.add_argument("--local-path", default=None, help="Local file path")
    p_prep.add_argument("--config-name", default=None, help="Dataset config name")
    p_prep.add_argument("--output-dir", default=None, help="Output directory for processed partition")

    # 6. validate
    p_val = subparsers.add_parser("validate", help="Validate dataset records and report quality")
    p_val.add_argument("file", help="Path to dataset file to validate")
    p_val.add_argument("--dataset", default=None, help="Expected dataset name for schema validation")
    p_val.add_argument("--limit", type=int, default=None, help="Max records to check")
    p_val.add_argument("--report", action="store_true", help="Generate quality report JSON")
    p_val.add_argument("--output", default=None, help="Output path for quality report JSON")

    # 7. split-stats
    p_split = subparsers.add_parser("split-stats", help="Compute leakage-resistant splits and statistics")
    p_split.add_argument("dataset", help="Registered dataset name")
    p_split.add_argument("--split", default="train", help="Source split")
    p_split.add_argument("--limit", type=int, default=None, help="Max records to sample")
    p_split.add_argument("--smoke-test", action="store_true", help="Smoke test mode")
    p_split.add_argument("--custom-split", action="store_true", help="Perform custom 70/15/15 splitting instead of preserving official split")
    p_split.add_argument("--train-ratio", type=float, default=0.70, help="Train ratio")
    p_split.add_argument("--val-ratio", type=float, default=0.15, help="Validation ratio")
    p_split.add_argument("--test-ratio", type=float, default=0.15, help="Test ratio")
    p_split.add_argument("--seed", type=int, default=42, help="Random seed")
    p_split.add_argument("--group-key", default=None, help="Grouping key")
    p_split.add_argument("--local-path", default=None, help="Local path override")
    p_split.add_argument("--output-dir", default=None, help="Optional output directory to save custom splits")
    p_split.add_argument("--offline", action="store_true", help="Offline mode")

    # 8. manifest
    p_man = subparsers.add_parser("manifest", help="Generate dataset manifest and dataset card")
    p_man.add_argument("dataset", help="Registered dataset name")
    p_man.add_argument("--dir", default=None, help="Directory containing processed dataset partitions")
    p_man.add_argument("--validate", action="store_true", help="Validate manifest consistency against files on disk")

    # 9. acquire
    p_acq = subparsers.add_parser("acquire", help="Acquire priority datasets with pre-allocation safety")
    p_acq.add_argument("dataset", nargs="?", default=None, help="Registered dataset name (or use --batch)")
    p_acq.add_argument("--batch", choices=["p0", "p1", "p2", "all"], default=None, help="Acquire batch of datasets by priority tier")
    p_acq.add_argument("--split", default="train", help="Specific split to acquire")
    p_acq.add_argument("--limit", type=int, default=None, help="Record count limit")
    p_acq.add_argument("--smoke-test", action="store_true", help="Smoke test mode (100 records)")
    p_acq.add_argument("--offline", action="store_true", help="Enforce offline loading from local/cached data")
    p_acq.add_argument("--config-name", default=None, help="Dataset config name")
    p_acq.add_argument("--local-path", default=None, help="Local file path override")

    # 10. storage
    subparsers.add_parser("storage", help="Display storage usage breakdown and dataset acquisition status")

    # 11. benchmark
    p_bm = subparsers.add_parser("benchmark", help="Construct or audit benchmark categories")
    p_bm.add_argument("bench_action", choices=["build", "audit"], help="Benchmark action: build or audit")
    p_bm.add_argument("--category", choices=BENCHMARK_CATEGORIES + ["all"], default="all", help="Target benchmark category")
    p_bm.add_argument("--limit", type=int, default=None, help="Record count or pair count limit")
    p_bm.add_argument("--output-dir", default=None, help="Output directory for benchmarks")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "list": cmd_list,
        "inspect": cmd_inspect,
        "download": cmd_download,
        "import": cmd_import,
        "preprocess": cmd_preprocess,
        "validate": cmd_validate,
        "split-stats": cmd_split_stats,
        "manifest": cmd_manifest,
        "acquire": cmd_acquire,
        "storage": cmd_storage,
        "benchmark": cmd_benchmark,
    }

    handler = handlers.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
