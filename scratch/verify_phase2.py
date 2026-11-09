import pathlib, json, hashlib, sys, subprocess

def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest().upper()

def count_jsonl_records(path):
    with open(path, 'r', encoding='utf-8') as f:
        return sum(1 for _ in f)

repo_root = pathlib.Path.cwd()
# Custom security dataset
custom_path = repo_root / 'data' / 'raw' / 'custom_security' / 'raw_train.jsonl'
custom_sha = sha256_of_file(custom_path)
custom_count = count_jsonl_records(custom_path)
# verify unique pair IDs, clean/poison balance, attack family distribution
pair_ids = set()
clean = poison = 0
family_counts = {}
with open(custom_path, 'r', encoding='utf-8') as f:
    for line in f:
        rec = json.loads(line)
        pair_id = rec.get('pair_id')
        if pair_id:
            pair_ids.add(pair_id)
        label = rec.get('label')
        if label == 'clean':
            clean += 1
        elif label == 'poisoned':
            poison += 1
        fam = rec.get('attack_family')
        if fam:
            family_counts[fam] = family_counts.get(fam, 0) + 1

# Benchmarks stats
bench_root = repo_root / 'data' / 'benchmarks'
bench_stats = {}
for bench_dir in bench_root.iterdir():
    if bench_dir.is_dir():
        stats = {}
        for split in ['train', 'val', 'test']:
            jsonl_path = bench_dir / f"{split}.jsonl"
            if jsonl_path.exists():
                stats[split] = count_jsonl_records(jsonl_path)
        manifest_path = bench_dir / 'manifest.json'
        if manifest_path.exists():
            stats['manifest_sha256'] = sha256_of_file(manifest_path)
        bench_stats[bench_dir.name] = stats

# Dependency check for python 3.11 and local wheels
def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return '', str(e), 1

py311_out, py311_err, py311_rc = run_cmd('py -3.11 --version')
wheel_out, wheel_err, wheel_rc = run_cmd('pip cache dir')
wheel_list = ''
if wheel_rc == 0:
    cache_dir = pathlib.Path(wheel_out)
    if cache_dir.is_dir():
        wheel_files = list(cache_dir.rglob('pydantic*.whl'))
        wheel_list = '\n'.join(str(p) for p in wheel_files)

# Prepare report dict
report = {
    'custom_security': {
        'file_path': str(custom_path),
        'sha256': custom_sha,
        'record_count': custom_count,
        'unique_pair_ids': len(pair_ids),
        'clean_count': clean,
        'poisoned_count': poison,
        'attack_family_distribution': family_counts,
    },
    'benchmarks': bench_stats,
    'dependency_check': {
        'python_3_11_version': py311_out or py311_err,
        'python_3_11_exit_code': py311_rc,
        'pip_cache_dir': wheel_out,
        'pydantic_wheel_files': wheel_list,
    }
}

# Write markdown report
md_path = repo_root / 'reports' / 'phase_02_correction_report.md'
with open(md_path, 'w', encoding='utf-8') as f:
    f.write('# Phase 02 Correction Report (Dependency Blocker)\n\n')
    f.write('## Environment\n')
    f.write(f"- System Python version: {sys.version.splitlines()[0]}\n")
    f.write('- Project target Python version (from pyproject.toml): 3.11\n\n')
    f.write('## Dependency Status\n')
    f.write('- Real `pydantic` library: **missing** (stub renamed to `pydantic_stub`).\n')
    f.write('- Python 3.11 interpreter: ' + ('available' if py311_rc == 0 else 'not found') + '\n')
    f.write('- Local `pydantic` wheels in pip cache:\n')
    f.write('```\n')
    f.write(wheel_list + '\n')
    f.write('```\n\n')
    f.write('## Custom‑Security Dataset Verification (standard‑library only)\n')
    f.write(f"- File: `{custom_path}`\n")
    f.write(f"- SHA‑256: `{custom_sha}`\n")
    f.write(f"- Total records: {custom_count}\n")
    f.write(f"- Unique `pair_id`s: {len(pair_ids)}\n")
    f.write(f"- Clean vs poisoned: {clean} clean, {poison} poisoned\n")
    f.write('- Attack‑family distribution:\n')
    for fam, cnt in family_counts.items():
        f.write(f"  - {fam}: {cnt}\n")
    f.write('\n## Benchmark Artifacts (standard‑library only)\n')
    for bench, stats in bench_stats.items():
        f.write(f"### {bench}\n")
        for k, v in stats.items():
            f.write(f"- {k}: {v}\n")
        f.write('\n')
    f.write('## Verdict\n')
    f.write('**NOT ACCEPTED — BLOCKED BY DEPENDENCY**\n')

# Write JSON audit report
json_path = repo_root / 'reports' / 'phase02_audit_report.json'
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2)

print('Reports written')
