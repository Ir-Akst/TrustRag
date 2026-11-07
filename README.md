# TrustRAG

## Project Overview

TrustRAG is a research-grade Retrieval‑Augmented Generation (RAG) security system focused on ensuring trustworthy generation through input guardrails, multi‑signal detection, and output verification. This repository establishes the **Phase 00** engineering foundation.

## Architecture Overview

```
G1 (Input Guardrails) → MSD (Multi‑Signal Detection) → Retrieval → Generation → G3 (Output Verification)
```

Only the scaffolding is present in Phase 00; detailed implementations will be added in later phases.

## Setup

```bash
# Windows PowerShell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## Configuration

Copy the example environment file and adjust as needed:

```bash
cp .env.example .env
```

Configuration lives in `configs/*.yaml` and can be overridden by environment variables.

## Testing

```bash
pytest -q
```

## Code Quality

```bash
ruff check src tests
mypy src
```

## Documentation

Further documentation resides in the `docs/` directory.

