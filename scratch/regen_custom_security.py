import sys, os

# Ensure repository root is on sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_root)
# Also add src directory for package
src_path = os.path.join(repo_root, 'src')
sys.path.append(src_path)

from trustrag.data.acquisition.manager import AcquisitionManager

if __name__ == '__main__':
    manager = AcquisitionManager()
    # Force regeneration by removing existing raw file if present
    raw_path = os.path.join(repo_root, 'data', 'raw', 'custom_security', 'raw_train.jsonl')
    if os.path.exists(raw_path):
        os.remove(raw_path)
        print(f"Removed existing raw file: {raw_path}")
    records, audit = manager.acquire('custom_security', split='train', smoke_test=False, offline=False)
    print(f"Acquired {len(records)} records")
    print(f"Audit entry: {audit}")
