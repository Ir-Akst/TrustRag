import os, sys, json, shutil, hashlib, subprocess, traceback
from pathlib import Path

# Helper to print and capture
def println(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

# Ensure PYTHONPATH includes src
src_path = Path.cwd() / 'src'
os.environ['PYTHONPATH'] = str(src_path)

# 1. Basic environment verification
println('--- Environment verification ---')
println('Python version:', sys.version.splitlines()[0])
# pip check via subprocess to capture output
subprocess.run([sys.executable, '-m', 'pip', 'check'], check=False)

# Import pydantic & core
import pydantic, pydantic_core
println('Pydantic version:', pydantic.__version__)
println('Pydantic core version:', pydantic_core.__version__)

# Import TrustRAG base
from trustrag.data.base import BaseAdapter
println('TrustRAG import successful')

# 2. Run test suite (offline)
println('\n--- Running pytest ---')
# Using subprocess to ensure full output
result = subprocess.run([sys.executable, '-m', 'pytest', '-vv'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
println(result.stdout)
test_summary = result.stdout.split('\n')[-2:]  # approximate last lines

# 3. Inspect BenchmarkBuilder signatures
println('\n--- BenchmarkBuilder signatures ---')
from trustrag.data.benchmarks.builder import BenchmarkBuilder
builder = BenchmarkBuilder()
import inspect
methods = ['build_clean_rag','build_knowledge_poisoning','build_hallucination','build_adversarial_robustness']
signatures = {}
for m in methods:
    func = getattr(builder, m)
    sig = inspect.signature(func)
    signatures[m] = str(sig)
    println(f"{m}{sig}")

# 4. Rebuild benchmarks (small limit for speed)
println('\n--- Rebuilding benchmarks (limit=10) ---')
# Backup existing benchmark dirs
bench_root = Path('data/benchmarks')
backup_root = Path('data/benchmarks_backup')
if backup_root.exists():
    shutil.rmtree(backup_root)
shutil.copytree(bench_root, backup_root)

# Build with small limits
build_results = builder.build_all(limit=10)
println('Build results keys:', list(build_results.keys()))

# 5. Validate benchmark artifacts
println('\n--- Validating benchmark artifacts ---')
from trustrag.data.storage import DatasetStorage
from trustrag.data.manifest import ManifestManager
validation_reports = {}
for cat in builder.BENCHMARK_CATEGORIES:
    cat_dir = bench_root / cat
    manifest_path = cat_dir / 'manifest.json'
    if not manifest_path.exists():
        validation_reports[cat] = 'Manifest missing'
        continue
    manifest = ManifestManager.load_manifest(cat_dir)
    # Load each split file and count records, compute SHA256
    split_stats = {}
    for split_name in ['train','val','test']:
        split_file = cat_dir / f"{split_name}.jsonl"
        if not split_file.exists():
            split_stats[split_name] = {'exists': False}
            continue
        records = list(DatasetStorage.load_jsonl(split_file))
        # Compute file sha256
        sha256 = hashlib.sha256(split_file.read_bytes()).hexdigest().upper()
        split_stats[split_name] = {'records': len(records), 'sha256': sha256}
    validation_reports[cat] = split_stats
    println(f"{cat} splits:")
    for s,info in split_stats.items():
        println('  ',s, info)

# 6. Regression verification (git diff/status)
println('\n--- Git status & diff ---')
subprocess.run(['git','status','--short'], check=False)
subprocess.run(['git','diff','--name-status'], check=False)

# 7. Write a summary JSON for the report
summary = {
    'python_version': sys.version.splitlines()[0],
    'pydantic_version': pydantic.__version__,
    'pydantic_core_version': pydantic_core.__version__,
    'test_output': result.stdout,
    'builder_signatures': signatures,
    'benchmark_build': build_results,
    'benchmark_validation': validation_reports,
}
with open('reports/phase02_full_summary.json','w',encoding='utf-8') as f:
    json.dump(summary, f, indent=2)
println('\nSummary written to reports/phase02_full_summary.json')

