# Git Ancestry, Manifest & Checkpoint Integrity Audit

- **HEAD at Audit Start:** `4818a7ce075adf961e062862a04cb21c095ea7c2` (`phase-40.1-benign-utility-and-independent-verification`).
- **Ancestry Verified:** `531bff32745ede1bd1b38609cc6daf653d3eff24` (`trustrag-v1.0.0-rc1`, tag object `7d4315e10fe4b7cc2cea6d6d2f9403d22af45f86`) $\rightarrow$ `e6908d26a13089d108a09977f4f05e864c7dab82` (Phase 40) $\rightarrow$ `4818a7ce075adf961e062862a04cb21c095ea7c2` (Phase 40.1).
- **Dirty File Observation:** At audit start, `reports/phase40_1/scripts/compile_phase40_1_reports.py` had 1 unstaged trailing newline causing 1 mismatch in `reports/phase40_1/ARTIFACT_SHA256_MANIFEST.txt`. Restoring via `git checkout -- reports/phase40_1/` yielded 100% `OK` on both Phase 40 and Phase 40.1 manifests.
- **Frozen Checkpoint:** All 8 SHA-256 hashes in `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch/checksums.sha256` verified `OK`.
