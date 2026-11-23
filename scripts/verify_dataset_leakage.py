import json, hashlib, os

def hash_text(text):
    return hashlib.sha256(text.strip().lower().encode('utf-8')).hexdigest()

def load_nli(path):
    hashes = set()
    count = 0
    with open(path) as f:
        for line in f:
            if not line.strip(): continue
            count += 1
            d = json.loads(line)
            p = d.get("premise", "")
            h = d.get("hypothesis", "")
            hashes.add(hash_text(f"{p}|||{h}"))
    return hashes, count

train_hashes, train_count = load_nli("data/processed/sft_v2/nli/train.jsonl")
val_hashes, val_count = load_nli("data/processed/sft_v2/nli/validation.jsonl")

val_overlap = train_hashes.intersection(val_hashes)
print(f"Train samples: {train_count}, Val samples: {val_count}, Overlap: {len(val_overlap)}")

# Check Red Team (N=460)
redteam_count = 0
redteam_overlap = 0
redteam_path = "reports/research_completion/final_independent_validation_and_release/raw_predictions/phase18_redteam_predictions.jsonl"
if os.path.exists(redteam_path):
    with open(redteam_path) as f:
        for line in f:
            if not line.strip(): continue
            redteam_count += 1
            d = json.loads(line)
            q = d.get("query", "")
            p = d.get("passage", "")
            h = hash_text(f"{p}|||{q}")
            if h in train_hashes:
                redteam_overlap += 1
print(f"Red team samples: {redteam_count}, Overlap with train: {redteam_overlap}")
