# Dataset Provenance & Licenses

1. **RAGTruth (`v1.0`):** MIT License, `https://github.com/ParticleMedia/RAGTruth`, local `data/processed/ragtruth/test.jsonl` ($2,700$ records; sampled $N=200$ stratified, `seed=42`).
2. **HaluEval (`v1.0`):** MIT License, `https://github.com/RUCAIBox/HaluEval`, local `data/processed/halueval/test.jsonl` ($3,000$ records; sampled $N=200$ stratified, `seed=42`).
3. **Phase 41 Audit Splits (used for 5-arm ablation & prompt-injection baseline):** `p41_g1_holdout.jsonl` ($N=250$), `p41_firewall_holdout.jsonl` ($N=140$), `p41_multilingual_holdout.jsonl` ($N=270$), `p41_g3_holdout.jsonl` ($N=120$).
4. **Phase 42 Quoted-Content FPR Benchmark:** `reports/phase42/datasets/quoted_fpr_benchmark.jsonl` ($N=120$, newly authored for Phase 42).
