import json
from collections import defaultdict
import pathlib

raw_path = pathlib.Path('data/raw/custom_security/raw_train.jsonl')
pair_counts = defaultdict(list)
attack_families = defaultdict(int)

with raw_path.open('r', encoding='utf-8') as f:
    for line in f:
        rec = json.loads(line)
        rid = rec.get('record_id')
        label = rec.get('clean_poison_label')
        family = rec.get('attack_family')
        if rid:
            pair_id = rid.rsplit('_', 1)[0]
            pair_counts[pair_id].append(label)
        if family:
            attack_families[family] += 1

# Verify each pair has exactly two entries, one clean one poisoned
bad_pairs = {pid: labs for pid, labs in pair_counts.items() if len(labs) != 2 or set(labs) != {'clean', 'poisoned'}}

report_path = pathlib.Path('reports/custom_security_verification.txt')
with report_path.open('w', encoding='utf-8') as out:
    out.write(f"Total records: {sum(len(v) for v in pair_counts.values())}\n")
    out.write(f"Unique pair IDs: {len(pair_counts)}\n")
    out.write(f"Bad pairs (should be 0): {len(bad_pairs)}\n")
    if bad_pairs:
        out.write('Example bad pair IDs:\n')
        for i, (pid, labs) in enumerate(bad_pairs.items()):
            if i >= 5:
                break
            out.write(f"  {pid}: {labs}\n")
    out.write('\nAttack family distribution:\n')
    for family, cnt in attack_families.items():
        out.write(f"  {family}: {cnt}\n")

print('Verification written to', report_path)

