# Natural Benchmark Validation & Accounting

1. **HaluEval (`data/processed/halueval/test.jsonl`):**
   - Original size: 3,000 test records (MIT License, `https://github.com/RUCAIBox/HaluEval`).
   - Selected: $N=200$ stratified (100 `FACTUAL`, 100 `HALLUCINATED`, `seed=42`).
   - Excluded: 0 (70/200 had `< 3 words` and were evaluated in both raw and sentence-wrapped modes).
2. **RAGTruth (`data/processed/ragtruth/test.jsonl`):**
   - Original size: 2,700 test records (MIT License, `https://github.com/ParticleMedia/RAGTruth`).
   - Excluded: 1,800 records (`QA` and `Data2txt`) whose `document` field is a structured `dict` rather than prose.
   - Selected: $N=50$ `Summary` prose records (25 `FACTUAL`, 25 `HALLUCINATED`, `seed=42`) in Phase 43 stratified analysis (in addition to $N=200$ in Phase 42).
