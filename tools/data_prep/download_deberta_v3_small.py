"""Download and stage official microsoft/deberta-v3-small snapshot.

Records upstream commit SHA, computes SHA-256 digests, and generates
an immutable staging manifest.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    repo_id = "microsoft/deberta-v3-small"
    target_dir = Path("/home/aditya/rags/models/pretrained/deberta-v3-small")
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== OFFICIAL MODEL ACQUISITION: {repo_id} ===")
    t0 = time.perf_counter()

    # 1. Resolve upstream commit SHA
    api = HfApi()
    try:
        model_info = api.model_info(repo_id)
        upstream_commit = model_info.sha
        print(f"Resolved upstream commit SHA: {upstream_commit}")
    except Exception as exc:
        print(f"[ERROR] Failed to query model info for {repo_id}: {exc}")
        return 1

    # 2. Download snapshot into target_dir
    print(f"Downloading snapshot into: {target_dir}")
    try:
        downloaded_path = snapshot_download(
            repo_id=repo_id,
            revision=upstream_commit,
            local_dir=str(target_dir),
            ignore_patterns=["*.h5", "*.ot", "*.msgpack", "flax_model.msgpack", "tf_model.h5"],
        )
        print(f"Snapshot downloaded to: {downloaded_path}")
    except Exception as exc:
        print(f"[ERROR] Snapshot download failed: {exc}")
        return 1

    elapsed = time.perf_counter() - t0
    print(f"Download completed in {elapsed:.2f}s")

    # 3. Catalog and hash all staged files
    file_inventory = []
    checksum_lines = []
    total_bytes = 0

    for root, dirs, files in os.walk(target_dir):
        # Ignore .git or internal hub cache directories if any
        if ".git" in root or ".cache" in root:
            continue
        for fname in sorted(files):
            if fname in ["manifest.json", "checksums.sha256"]:
                continue
            fpath = Path(root) / fname
            rel_name = str(fpath.relative_to(target_dir))
            size = fpath.stat().st_size
            digest = sha256_file(fpath)
            total_bytes += size

            file_inventory.append({
                "filename": rel_name,
                "size_bytes": size,
                "sha256": digest,
            })
            checksum_lines.append(f"{digest}  {rel_name}")
            print(f"  {rel_name:30s} {size:>12,d} bytes  SHA256: {digest[:16]}...")

    # 4. Write manifest.json
    manifest = {
        "model_id": repo_id,
        "upstream_commit": upstream_commit,
        "source_url": f"https://huggingface.co/{repo_id}/tree/{upstream_commit}",
        "acquisition_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "local_directory": str(target_dir),
        "total_files": len(file_inventory),
        "total_size_bytes": total_bytes,
        "files": file_inventory,
        "license": "MIT",
    }

    manifest_path = target_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    checksums_path = target_dir / "checksums.sha256"
    with open(checksums_path, "w") as f:
        f.write("\n".join(checksum_lines) + "\n")

    print(f"\nManifest saved to: {manifest_path}")
    print(f"Checksums saved to: {checksums_path}")
    print(f"Total staged size: {total_bytes / (1024*1024):.2f} MB across {len(file_inventory)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
