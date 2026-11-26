# External Baseline Availability & Status

1. **Public Hallucination Benchmarks (Available & Executed):** `RAGTruth v1.0` (MIT) and `HaluEval v1.0` (MIT) were evaluated reproducibly against `Vanilla RAG (No G3)` and `Lexical Overlap (>=0.25)`.
2. **Prompt-Injection Baselines (Available & Executed):** `Vanilla RAG`, `Spotlighting-Only (XML Isolation)`, and `Heuristic/Regex-Only` were evaluated reproducibly on identical Phase 41 splits.
3. **External Pretrained Prompt-Injection Classifier (Unavailable Offline):** Inspection of `/home/aditya/rags/models/` and `~/.cache/huggingface/hub/` confirms no external pretrained prompt-injection model (e.g. ProtectAI DeBERTa-v3-prompt-injection) is cached locally, and offline sandbox execution prohibits downloading remote weights. No external checkpoint numbers were fabricated.
