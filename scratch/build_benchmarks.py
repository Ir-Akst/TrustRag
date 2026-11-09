import sys, os, pathlib

# Ensure repository root on sys.path
repo_root = pathlib.Path(__file__).parents[1]
sys.path.append(str(repo_root))
# also add src
sys.path.append(str(repo_root / 'src'))

from trustrag.data.benchmarks.builder import BenchmarkBuilder

if __name__ == '__main__':
    builder = BenchmarkBuilder()
    results = {}
    # Build Clean RAG with modest limit
    results['clean_rag'] = builder.build_clean_rag(limit=200)
    # Build Knowledge Poisoning with 200 pairs (400 records)
    results['knowledge_poisoning'] = builder.build_knowledge_poisoning(num_pairs=200)
    # Build Hallucination benchmark (may need generation function, assume exists)
    try:
        results['hallucination'] = builder.build_hallucination(limit=200)
    except Exception as e:
        results['hallucination'] = f'Error: {e}'
    # Build Adversarial Robustness benchmark
    try:
        results['adversarial_robustness'] = builder.build_adversarial_robustness(limit=200)
    except Exception as e:
        results['adversarial_robustness'] = f'Error: {e}'
    # Write results summary
    out_path = repo_root / 'reports' / 'benchmark_build_summary.txt'
    with out_path.open('w', encoding='utf-8') as f:
        for name, res in results.items():
            f.write(f'{name}: {res}\n')
    print('Benchmark build summary written to', out_path)
