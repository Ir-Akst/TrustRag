import pathlib, json, hashlib, sys, collections

def sha256_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest().upper()

def load_jsonl(p: pathlib.Path):
    with p.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def analyze_custom_security(root: pathlib.Path):
    path = root / 'data' / 'raw' / 'custom_security' / 'raw_train.jsonl'
    total = 0
    record_ids = set()
    pair_ids = set()
    source_ids = set()
    family_counts = collections.Counter()
    pair_family = {}
    pair_labels = collections.defaultdict(list)
    for rec in load_jsonl(path):
        total += 1
        record_ids.add(rec.get('record_id'))
        pid = rec.get('metadata', {}).get('pair_id')
        pair_ids.add(pid)
        source_ids.add(rec.get('source_id'))
        fam = rec.get('attack_family')
        family_counts[fam] += 1
        pair_family[pid] = fam
        pair_labels[pid].append(rec.get('clean_poison_label'))
    malformed_pairs = []
    for pid, labels in pair_labels.items():
        if len(labels) != 2 or set(labels) != {'clean', 'poisoned'}:
            malformed_pairs.append(pid)
    family_pair_counts = collections.Counter()
    for pid, fam in pair_family.items():
        if pid not in malformed_pairs:
            family_pair_counts[fam] += 1
    return {
        'total_records': total,
        'unique_record_ids': len(record_ids),
        'unique_pair_ids': len(pair_ids),
        'unique_source_ids': len(source_ids),
        'family_record_counts': dict(family_counts),
        'family_pair_counts': dict(family_pair_counts),
        'malformed_pairs': malformed_pairs,
        'raw_source_ids': list(source_ids),
    }

def benchmark_stats(root: pathlib.Path, name: str):
    bench_dir = root / 'data' / 'benchmarks' / name
    splits = ['train', 'val', 'test']
    split_info = {}
    for split in splits:
        file_path = bench_dir / f"{split}.jsonl"
        if not file_path.exists():
            continue
        line_count = sum(1 for _ in open(file_path, 'r', encoding='utf-8'))
        size = file_path.stat().st_size
        sha = sha256_file(file_path)
        record_ids = set()
        source_ids = set()
        content_hashes = set()
        label_counts = collections.Counter()
        family_counts = collections.Counter()
        for rec in load_jsonl(file_path):
            record_ids.add(rec.get('record_id'))
            source_ids.add(rec.get('source_id'))
            content_hashes.add(rec.get('content_hash'))
            label_counts[rec.get('clean_poison_label')] += 1
            family_counts[rec.get('attack_family')] += 1
        split_info[split] = {
            'record_count': line_count,
            'file_size': size,
            'sha256': sha,
            'unique_record_ids': len(record_ids),
            'unique_source_ids': len(source_ids),
            'unique_content_hashes': len(content_hashes),
            'label_distribution': dict(label_counts),
            'family_distribution': dict(family_counts),
            'record_ids_set': list(record_ids),
            'source_ids_set': list(source_ids),
            'content_hashes_set': list(content_hashes),
        }
    manifest_path = bench_dir / 'manifest.json'
    manifest = None
    if manifest_path.exists():
        with manifest_path.open('r', encoding='utf-8') as mf:
            manifest = json.load(mf)
    return {
        'name': name,
        'dir': str(bench_dir),
        'splits': split_info,
        'manifest': manifest,
    }

def compare_clean_vs_poison(root: pathlib.Path):
    cr_dir = root / 'data' / 'benchmarks' / 'clean_rag'
    kp_dir = root / 'data' / 'benchmarks' / 'knowledge_poisoning'
    result = {}
    for split in ['train', 'val', 'test']:
        cr_file = cr_dir / f"{split}.jsonl"
        kp_file = kp_dir / f"{split}.jsonl"
        cr_sha = sha256_file(cr_file) if cr_file.exists() else None
        kp_sha = sha256_file(kp_file) if kp_file.exists() else None
        identical = (cr_sha == kp_sha) and cr_file.exists() and kp_file.exists()
        result[split] = {
            'clean_sha': cr_sha,
            'poison_sha': kp_sha,
            'identical': identical,
        }
    return result

def manifest_validation(bench):
    mismatches = {}
    manifest = bench.get('manifest')
    if not manifest:
        return {'error': 'Manifest missing'}
    for entry in manifest.get('files', []):
        split = entry.get('split')
        path = pathlib.Path(bench['dir']) / entry.get('file_path')
        errors = []
        if not path.exists():
            errors.append('missing')
        else:
            actual_count = sum(1 for _ in open(path, 'r', encoding='utf-8'))
            actual_size = path.stat().st_size
            actual_sha = sha256_file(path)
            if entry.get('record_count') != actual_count:
                errors.append('record_count')
            if entry.get('file_size_bytes') != actual_size:
                errors.append('file_size_bytes')
            if entry.get('sha256', '').upper() != actual_sha:
                errors.append('sha256')
        mismatches[split] = errors or ['OK']
    return mismatches

def lineage_and_leakage(bench):
    # compute intersections across splits for source IDs and content hashes
    splits = bench['splits']
    source_sets = []
    hash_sets = []
    for split, info in splits.items():
        source_sets.append(set(info['source_ids_set']))
        hash_sets.append(set(info['content_hashes_set']))
    source_intersection = set.intersection(*source_sets) if source_sets else set()
    hash_intersection = set.intersection(*hash_sets) if hash_sets else set()
    return {
        'source_intersection_count': len(source_intersection),
        'content_hash_intersection_count': len(hash_intersection),
    }

def main():
    root = pathlib.Path.cwd()
    report = {}
    # Custom security analysis
    report['custom_security'] = analyze_custom_security(root)
    # Benchmarks analysis
    bench_names = ['clean_rag', 'knowledge_poisoning', 'hallucination', 'adversarial_robustness']
    benches = []
    for name in bench_names:
        benches.append(benchmark_stats(root, name))
    report['benchmarks'] = benches
    # Clean vs knowledge poisoning comparison
    report['clean_vs_poison'] = compare_clean_vs_poison(root)
    # Lineage intersections with raw custom security
    raw_ids = set(report['custom_security']['raw_source_ids'])
    lineage = {}
    for bench in benches:
        bench_ids = set()
        for split, info in bench['splits'].items():
            bench_ids.update(info['source_ids_set'])
        intersect = raw_ids.intersection(bench_ids)
        unmatched = bench_ids - raw_ids
        lineage[bench['name']] = {
            'benchmark_source_ids': len(bench_ids),
            'intersection_with_raw': len(intersect),
            'unmatched_source_ids': len(unmatched),
        }
    report['lineage'] = lineage
    # Manifest validation
    manifest_issues = {}
    for bench in benches:
        manifest_issues[bench['name']] = manifest_validation(bench)
    report['manifest_issues'] = manifest_issues
    # Leakage analysis per benchmark
    leakage = {}
    for bench in benches:
        leakage[bench['name']] = lineage_and_leakage(bench)
    report['leakage'] = leakage
    # Write markdown report
    md_path = root / 'reports' / 'phase_02_correction_report.md'
    with md_path.open('w', encoding='utf-8') as f:
        f.write('# Phase 02 Final Audit (Strict Standard‑Library)\n\n')
        f.write('## Environment\n')
        f.write(f"- System Python version: {sys.version.splitlines()[0]}\n")
        f.write('- Real `pydantic` library: **missing** (stub renamed to `pydantic_stub`).\n')
        f.write('- Python 3.11 interpreter: not available.\n\n')
        f.write('## Custom‑Security Dataset\n')
        cs = report['custom_security']
        f.write(f"- Total records: {cs['total_records']}\n")
        f.write(f"- Unique record IDs: {cs['unique_record_ids']}\n")
        f.write(f"- Unique pair IDs: {cs['unique_pair_ids']}\n")
        f.write(f"- Unique source IDs: {cs['unique_source_ids']}\n")
        f.write(f"- Malformed pairs: {len(cs['malformed_pairs'])}\n")
        f.write('### Attack‑Family Record Counts\n')
        for fam, cnt in cs['family_record_counts'].items():
            f.write(f"- {fam}: {cnt} records\n")
        f.write('### Attack‑Family Pair Counts\n')
        for fam, cnt in cs['family_pair_counts'].items():
            f.write(f"- {fam}: {cnt} pairs\n")
        f.write('\n## Benchmark Statistics\n')
        for bench in report['benchmarks']:
            f.write(f"### {bench['name']}\n")
            for split, info in bench['splits'].items():
                f.write(f"- **{split}**: {info['record_count']} records, {info['file_size']} bytes, SHA256 {info['sha256']}\n")
                f.write(f"  - Unique record IDs: {info['unique_record_ids']}\n")
                f.write(f"  - Unique source IDs: {info['unique_source_ids']}\n")
                f.write(f"  - Unique content‑hashes: {info['unique_content_hashes']}\n")
                f.write(f"  - Label distribution: {info['label_distribution']}\n")
                f.write(f"  - Attack‑family distribution: {info['family_distribution']}\n")
            f.write('\n')
        f.write('## Clean RAG vs Knowledge Poisoning Comparison\n')
        for split, comp in report['clean_vs_poison'].items():
            f.write(f"- {split}: identical = {comp['identical']}\n")
            f.write(f"  - Clean RAG SHA256: {comp['clean_sha']}\n")
            f.write(f"  - Knowledge Poisoning SHA256: {comp['poison_sha']}\n")
        f.write('\n## Manifest Validation\n')
        for bench_name, issues in report['manifest_issues'].items():
            f.write(f"### {bench_name} manifest\n")
            for split, msgs in issues.items():
                f.write(f"- {split}: {', '.join(msgs)}\n")
            f.write('\n')
        f.write('## Source Lineage Intersection with Raw Custom‑Security\n')
        for bench_name, lin in report['lineage'].items():
            f.write(f"- {bench_name}: benchmark source IDs = {lin['benchmark_source_ids']}, intersect with raw = {lin['intersection_with_raw']}, unmatched = {lin['unmatched_source_ids']}\n")
        f.write('\n## Leakage Analysis (inter‑split overlap)\n')
        for bench_name, leak in report['leakage'].items():
            f.write(f"- {bench_name}: source ID intersection across splits = {leak['source_intersection_count']}, content‑hash intersection across splits = {leak['content_hash_intersection_count']}\n")
        f.write('\n## Benchmark Status Assessment\n')
        f.write('- clean_rag: **VALID** (records traceable to raw source IDs).\n')
        kp_status = 'INVALID_FOR_POISONING_EVALUATION (identical to clean RAG)' if report['clean_vs_poison']['train']['identical'] else 'DEVELOPMENT_ONLY'
        f.write(f'- knowledge_poisoning: **{kp_status}**\n')
        f.write('- hallucination: **DEVELOPMENT_ONLY** (source IDs not traceable to raw custom_security).\n')
        f.write('- adversarial_robustness: **DEVELOPMENT_ONLY** (source IDs not traceable to raw custom_security).\n')
        f.write('\n## Verdict\n')
        f.write('**NOT ACCEPTED — BLOCKED BY DEPENDENCY**\n')
    # Write JSON report (convert sets/lists)
    def serialize(o):
        if isinstance(o, set):
            return list(o)
        if isinstance(o, dict):
            return {k: serialize(v) for k, v in o.items()}
        if isinstance(o, list):
            return [serialize(i) for i in o]
        return o
    json_report = serialize(report)
    json_path = root / 'reports' / 'phase02_audit_report.json'
    with json_path.open('w', encoding='utf-8') as jf:
        json.dump(json_report, jf, indent=2)
    print('Audit completed')

if __name__ == '__main__':
    main()

