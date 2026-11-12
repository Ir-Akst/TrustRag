# TrustRAG Phase 11 — G3 Numeric & Temporal Contradiction Remediation (`DEF-03`)

- **Original Behavior:** Unseen probes (`85°C` vs `100°C`, `2018` vs `1998`) returned `INSUFFICIENT_EVIDENCE` (`unseen_acc = 0.5000`, `FSR = 0.0000`).
- **Root Cause:** `extract_numbers_and_units()` left `"degrees Celsius"` and 4-digit years unitless (`c_unit == ""`), falling through to `INSUFFICIENT_EVIDENCE` when explicit negation cues were absent.
- **Fix:** Added `_find_temporal_or_unitless_numeric_contradiction()` in `src/trustrag/verification/output_verifier.py` handling:
  1. Normalized temperature units (`°C` / `degrees Celsius`, `°F` / `degrees Fahrenheit`).
  2. Temporal years & year ranges (respecting hedging like `approximately` and range inclusion like `2019` in `2018-2020`, while treating years introduced when evidence has no years as unmentioned).
  3. Unitless numeric conflicts only under `>= 0.50` shared predicate overlap and matching named entities.
- **Before / After:**
  - Unseen probes accuracy: `0.5000` (`2/4`) -> **`1.0000`** (`4/4`)
  - Unseen False-Supported Rate (`FSR`): `0.0000` -> **`0.0000`** (preserved)
  - Phase 08 linguistic suite: `25/25` (`1.0000`) preserved; all `159` G3/verifier tests pass.
