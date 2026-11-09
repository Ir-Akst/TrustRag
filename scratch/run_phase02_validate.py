import os, sys, json, hashlib, shutil
from pathlib import Path
import importlib

# Ensure src is on PYTHONPATH
src_path = Path.cwd() / 'src'
os.environ['PYTHONPATH'] = str(src_path)

# Imports
from trustrag.data.benchmarks.builder import BENCHMARK_CATEGORIES
from trustrag.data.manifest import ManifestManager
from trustrag.data.storage import DatasetStorage

bench_root = Path('data/benchmarks')
validation_reports = {}

for cat in BENCHMARK_CATEGORIES:
    cat_dir = bench_root / cat
    manifest_path = cat_dir / 'manifest.json'
    if not manifest_path.exists():
        validation_reports[cat] = {'error': 'manifest missing'}
        continue
    # Load manifest
    try:
        manifest = ManifestManager.load_manifest(cat_dir)
    except Exception as e:
        validation_reports[cat] = {'error': f'manifest load failed: {e}'}
        continue
    # Validate each split file
    split_info = {}
    for split in ['train', 'val', 'test']:
        split_file = cat_dir / f"{split}.jsonl"
        if not split_file.exists():
            split_info[split] = {'exists': False}
            continue
        # Load records
        records = list(DatasetStorage.load_jsonl(split_file))
        # Compute SHA256 of file
        sha256 = hashlib.sha256(split_file.read_bytes()).hexdigest().upper()
        # Count unique record IDs (assume each record has .record_id)
        try:
            unique_ids = {getattr(r, 'record_id') for r in records}
        except Exception:
            unique_ids = set()
        split_info[split] = {
            'exists': True,
            'record_count': len(records),
            'unique_record_ids': len(unique_ids),
            'sha256': sha256,
        }
    validation_reports[cat] = {
        'manifest_valid': True,
        'split_info': split_info,
    }

# Write summary JSON
out_path = Path('reports/benchmark_validation_summary.json')
with out_path.open('w', encoding='utf-8') as f:
    json.dump(validation_reports, f, indent=2)
print('Validation summary written to', out_path)

