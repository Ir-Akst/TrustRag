# TrustRAG Phase 16.2: Exact Reproducibility Instructions

**Role:** Senior ML Optimization Engineer, NLI Calibration Specialist & Independent Research Auditor  
**Date:** 2026-11-19T00:55:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Working Branch:** `phase-16`  
**Parent Release:** `531bff32745ede1bd1b38609cc6daf653d3eff24` (Tag: `trustrag-v1.0.0-rc1`)  
**Frozen Model Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  

---

## 1. Environment Configuration

```bash
# Set repository and environment variables
cd /home/aditya/rags/TrustRag-phase11
export PYTHONPATH=src
export VENV_PY=/home/aditya/rags/.venv-phase15-clean10/bin/python

# Verify Git working tree is clean
git status
```

---

## 2. Checkpoint Verification

Ensure the frozen DeBERTa-v3-small checkpoint is bit-for-bit intact:

```bash
cd /home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch
sha256sum -c checksums.sha256
# Expected output: all 8 files OK (model.safetensors: OK, config.json: OK, etc.)
```

---

## 3. Step 01 & Step 04: Reproducing the False Alarms & Normalization Fix

Run the root-cause diagnosis script comparing raw vs normalized premises across the 125 clean astrophysical controls:

```bash
cd /home/aditya/rags/TrustRag-phase11

$VENV_PY -c "
import json, torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from trustrag.engine.text_utils import strip_citations

model_path = '/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch'
tok = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)
model.eval()

with open('data/raw/custom_security/raw_train.jsonl') as f:
    clean_astro = [json.loads(line) for line in f if json.loads(line).get('clean_poison_label') == 'clean' and json.loads(line).get('attack_subtype') == 'astrophysical_disinformation']

con_raw, con_norm, sup_norm = 0, 0, 0
for r in clean_astro:
    raw_prem = r['document']
    norm_prem = strip_citations(raw_prem)
    hyp = strip_citations(r['document'])
    
    # Raw premise test
    inp_r = tok(raw_prem, hyp, return_tensors='pt', truncation=True)
    with torch.no_grad():
        p_r = torch.softmax(model(**inp_r).logits[0], dim=-1).tolist()
    if p_r[1] >= 0.16: con_raw += 1
    
    # Normalized premise test
    inp_n = tok(norm_prem, hyp, return_tensors='pt', truncation=True)
    with torch.no_grad():
        p_n = torch.softmax(model(**inp_n).logits[0], dim=-1).tolist()
    if p_n[1] >= 0.16: con_norm += 1
    if p_n[0] >= 0.50: sup_norm += 1

print(f'Total clean astro records: {len(clean_astro)}')
print(f'Raw premise false contradictions: {con_raw} / {len(clean_astro)}')
print(f'Normalized premise contradictions: {con_norm} / {len(clean_astro)}')
print(f'Normalized premise entailments: {sup_norm} / {len(clean_astro)}')
"
```

---

## 4. Step 06: Reproducing Latency Benchmarks

Benchmark CPU intra-op thread counts and batch processing:

```bash
cd /home/aditya/rags/TrustRag-phase11

$VENV_PY -c "
import time, torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_path = '/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch'
tok = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)
model.eval()

prem = 'James Webb Space Telescope observations confirmed atmospheric carbon dioxide in the exoplanet WASP-39b.'
hyp = 'James Webb Space Telescope observations confirmed atmospheric carbon dioxide in the exoplanet WASP-39b.'

for threads in [1, 2, 4]:
    torch.set_num_threads(threads)
    inp = tok(prem, hyp, return_tensors='pt', truncation=True, max_length=128)
    with torch.no_grad():
        for _ in range(5): model(**inp)
    t0 = time.perf_counter()
    n_iters = 20
    with torch.no_grad():
        for _ in range(n_iters):
            _ = model(**inp)
    dt = (time.perf_counter() - t0) * 1000 / n_iters
    print(f'Threads={threads}: {dt:.2f}ms per query')
"
```

---

## 5. Deliverable Integrity Check

```bash
cd /home/aditya/rags/TrustRag-phase11/reports/research_completion/phase16_2_neural_utility_optimization
sha256sum -c sha256_manifest.txt
```

