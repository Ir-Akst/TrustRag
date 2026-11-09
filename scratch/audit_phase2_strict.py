import pathlib, json, hashlib, sys, collections

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()

def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest().upper()

def load_jsonl(path: pathlib.Path):
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def verify_custom_security(root: pathlib.Path):
    path = root / 'data' / 'raw' / 'custom_security' / 'raw_train.jsonl'
    total = 0
    record_ids = set()
    pair_ids = set()
    source_ids = set()
    pair_groups = collections.defaultdict(list)
    hash_mismatches = []
    for rec in load_jsonl(path):
        total += 1
        record_ids.add(rec.get('record_id'))
        pid = rec.get('metadata', {}).get('pair_id')
        pair_ids.add(pid)
        source_ids.add(rec.get('source_id'))
        pair_groups[pid].append(rec)
        # recompute hash of document field
        doc = rec.get('document', '')
        computed = sha256_bytes(doc.encode('utf-8'))
        if computed != rec.get('content_hash', '').upper():
            hash_mismatches.append((rec.get('record_id'), computed, rec.get('content_hash')))
    # check pairs
    incomplete_pairs = []
    clean_poison_counts = collections.Counter()
    attack_family_counts = collections.Counter()
    for pid, recs in pair_groups.items():
        if len(recs) != 2:
            incomplete_pairs.append(pid)
            continue
        labels = {r.get('clean_poison_label') for r in recs}
        if labels != {'clean', 'poisoned'}:
            incomplete_pairs.append(pid)
        # assume both have same attack_family
        families = {r.get('attack_family') for r in recs}
        if len(families) == 1:
            attack_family_counts[next(iter(families))] += 1
        else:
            attack_family_counts['MISMATCH'] += 1
        clean_poison_counts[pid] = labels
    return {
        'total_records': total,
        'unique_record_ids': len(record_ids),
        'unique_pair_ids': len(pair_ids),
        'unique_source_ids': len(source_ids),
        'incomplete_pairs': incomplete_pairs,
        'hash_mismatches': hash_mismatches,
        'attack_family_pair_counts': dict(attack_family_counts),
        'pair_groups': {pid: [r.get('clean_poison_label') for r in recs] for pid, recs in pair_groups.items()},
    }

def benchmark_stats(root: pathlib.Path, name: str):
    bench_dir = root / 'data' / 'benchmarks' / name
    splits = ['train', 'val', 'test']
    stats = {}
    for split in splits:
        file_path = bench_dir / f"{split}.jsonl"
        if not file_path.exists():
            continue
        line_count = sum(1 for _ in open(file_path, 'r', encoding='utf-8'))
        size = file_path.stat().st_size
        sha = sha256_file(file_path)
        # collect IDs and families
        record_ids = set()
        source_ids = set()
        label_counts = collections.Counter()
        family_counts = collections.Counter()
        for rec in load_jsonl(file_path):
            record_ids.add(rec.get('record_id'))
            source_ids.add(rec.get('source_id'))
            label_counts[rec.get('clean_poison_label')] += 1
            family_counts[rec.get('attack_family')] += 1
        stats[split] = {
            'record_count': line_count,
            'file_size_bytes': size,
            'sha256': sha,
            'unique_record_ids': len(record_ids),
            'unique_source_ids': len(source_ids),
            'label_distribution': dict(label_counts),
            'family_distribution': dict(family_counts),
        }
    # load manifest
    manifest_path = bench_dir / 'manifest.json'
    manifest = {}
    if manifest_path.exists():
        manifest = json.load(open(manifest_path, 'r', encoding='utf-8'))
    return {'name': name, 'splits': stats, 'manifest': manifest, 'dir': str(bench_dir)}

def compare_files(path1: pathlib.Path, path2: pathlib.Path):
    if not path1.exists() or not path2.exists():
        return False
    return sha256_file(path1) == sha256_file(path2)

def main():
    repo_root = pathlib.Path.cwd()
    report = {}
    # Custom security verification
    report['custom_security'] = verify_custom_security(repo_root)
    # Benchmark analysis
    benchmark_names = ['clean_rag', 'knowledge_poisoning', 'hallucination', 'adversarial_robustness']
    benches = []
    for name in benchmark_names:
        benches.append(benchmark_stats(repo_root, name))
    report['benchmarks'] = benches
    # Compare clean_rag vs knowledge_poisoning files
    compare_results = {}
    cr_dir = repo_root / 'data' / 'benchmarks' / 'clean_rag'
    kp_dir = repo_root / 'data' / 'benchmarks' / 'knowledge_poisoning'
    for split in ['train', 'val', 'test']:
        cr_file = cr_dir / f"{split}.jsonl"
        kp_file = kp_dir / f"{split}.jsonl"
        identical = compare_files(cr_file, kp_file)
        compare_results[split] = {'clean_rag_sha256': sha256_file(cr_file) if cr_file.exists() else None,
                                  'knowledge_poisoning_sha256': sha256_file(kp_file) if kp_file.exists() else None,
                                  'identical': identical}
    report['clean_vs_knowledge_poisoning'] = compare_results
    # Leakage analysis per benchmark
    leakage = {}
    for bench in benches:
        name = bench['name']
        splits = bench['splits']
        # intersect source ids and content hashes across splits
        source_sets = {s: set() for s in splits}
        hash_sets = {s: set() for s in splits}
        for split, meta in splits.items():
            # reopen file to collect hashes of documents
            file_path = pathlib.Path(bench['dir']) / f"{split}.jsonl"
            if not file_path.exists():
                continue
            for rec in load_jsonl(file_path):
                source_sets[split].add(rec.get('source_id'))
                doc = rec.get('document', '')
                hash_sets[split].add(sha256_bytes(doc.encode('utf-8')))
        # compute intersections
        inter_sources = set.intersection(*source_sets.values()) if source_sets else set()
        inter_hashes = set.intersection(*hash_sets.values()) if hash_sets else set()
        leakage[name] = {
            'source_intersection_count': len(inter_sources),
            'content_hash_intersection_count': len(inter_hashes),
        }
    report['leakage'] = leakage
    # Write markdown report
    md_path = repo_root / 'reports' / 'phase_02_correction_report.md'
    with md_path.open('w', encoding='utf-8') as f:
        f.write('# Phase 02 Strict Standard‑Library Audit Report\n\n')
        f.write('## Environment\n')
        f.write(f"- System Python version: {sys.version.splitlines()[0]}\n")
        f.write('- Real `pydantic` library: **missing** (stub renamed to `pydantic_stub`).\n')
        f.write('- Python 3.11 interpreter: not available.\n\n')
        f.write('## Custom‑Security Dataset Verification\n')
        cs = report['custom_security']
        f.write(f"- Total records: {cs['total_records']}\n")
        f.write(f"- Unique record IDs: {cs['unique_record_ids']}\n")
        f.write(f"- Unique pair IDs: {cs['unique_pair_ids']}\n")
        f.write(f"- Unique source IDs: {cs['unique_source_ids']}\n")
        f.write(f"- Incomplete or malformed pairs: {len(cs['incomplete_pairs'])}\n")
        if cs['incomplete_pairs']:
            f.write('  - Pair IDs with issues: ' + ', '.join(cs['incomplete_pairs'][:10]) + ('...' if len(cs['incomplete_pairs'])>10 else '') + '\n')
        f.write(f"- Content‑hash mismatches: {len(cs['hash_mismatches'])}\n\n")
        f.write('### Attack‑Family Pair Counts\n')
        for fam, cnt in cs['attack_family_pair_counts'].items():
            f.write(f"- {fam}: {cnt} pairs\n")
        f.write('\n## Benchmark Statistics\n')
        for bench in report['benchmarks']:
            f.write(f"### {bench['name']}\n")
            for split, meta in bench['splits'].items():
                f.write(f"- **{split}**: {meta['record_count']} records, {meta['file_size_bytes']} bytes, SHA256 {meta['sha256']}\n")
                f.write(f"  - Unique record IDs: {meta['unique_record_ids']}\n")
                f.write(f"  - Unique source IDs: {meta['unique_source_ids']}\n")
                f.write(f"  - Label distribution: {meta['label_distribution']}\n")
                f.write(f"  - Attack‑family distribution: {meta['family_distribution']}\n")
            f.write('\n')
        f.write('## Clean RAG vs Knowledge Poisoning File Comparison\n')
        for split, comp in report['clean_vs_knowledge_poisoning'].items():
            f.write(f"- {split}: identical = {comp['identical']}\n")
            f.write(f"  - Clean RAG SHA256: {comp['clean_rag_sha256']}\n")
            f.write(f"  - Knowledge Poisoning SHA256: {comp['knowledge_poisoning_sha256']}\n")
        f.write('\n## Manifest Validation\n')
        for bench in report['benchmarks']:
            f.write(f"### {bench['name']} manifest checks\n")
            manifest = bench['manifest']
            if not manifest:
                f.write('  - No manifest found.\n')
                continue
            # compare each file entry
            for entry in manifest.get('files', []):
                split = entry.get('split')
                fpath = pathlib.Path(bench['dir']) / entry.get('file_path')
                exists = fpath.exists()
                actual_count = sum(1 for _ in open(fpath, 'r', encoding='utf-8')) if exists else None
                actual_size = fpath.stat().st_size if exists else None
                actual_sha = sha256_file(fpath) if exists else None
                mismatch = []
                if exists:
                    if entry.get('record_count') != actual_count:
                        mismatch.append('record_count')
                    if entry.get('file_size_bytes') != actual_size:
                        mismatch.append('file_size_bytes')
                    if entry.get('sha256').upper() != actual_sha:
                        mismatch.append('sha256')
                else:
                    mismatch.append('missing')
                f.write(f"  - {split}: {'; '.join(mismatch) if mismatch else 'OK'}\n")
            f.write('\n')
        f.write('## Leakage Analysis\n')
        for bench_name, leak in report['leakage'].items():
            f.write(f"- {bench_name}: source ID intersection across splits = {leak['source_intersection_count']}, content‑hash intersection = {leak['content_hash_intersection_count']}\n")
        f.write('\n## Verdict\n')
        f.write('**NOT ACCEPTED — BLOCKED BY DEPENDENCY**\n')
    # Write JSON report
    json_path = repo_root / 'reports' / 'phase02_audit_report.json'
    with json_path.open('w', encoding='utf-8') as jf:
        json.dump(report, jf, indent=2)
    print('Audit completed')

if __name__ == '__main__':
    main()

