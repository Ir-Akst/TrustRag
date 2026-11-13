# TrustRAG Phase 13 Step 3 — Root Cause Analysis and Code Change

## 1. Technical Root Cause Analysis

### The Failure of Word Boundaries (`\b`) on Base64 Padding

In Python's `re` module, the word boundary anchor `\b` matches the boundary between a "word" character (`\w`, which includes ASCII letters, digits, and underscores: `[a-zA-Z0-9_]`) and a "non-word" character (`\W`, which includes whitespace, punctuation, symbols, and string edges: `[^a-zA-Z0-9_]`).

The original token extraction pattern in `src/trustrag/guardrails/input_guardrail.py` was defined as:
```python
r"\b[A-Za-z0-9+/=]{16,}\b"
```

Consider what happens when this regex encounters a padded Base64 token such as:
```text
"data: aWdub3JlIGFsbCBwcmV2aW91cyBpbnN0cnVjdGlvbnM=."
```
1. The character `=` is an ASCII symbol with ord value 61. It is classified as `\W` (non-word).
2. The trailing character is a period `.` (or space `' '`), which is also classified as `\W` (non-word).
3. Because both `=` and `.` are `\W`, the transition between `=` and `.` is a `\W\W` transition. **A word boundary `\b` does NOT exist between two `\W` characters.**
4. Because the pattern requires a `\b` at the end, the regex engine refuses to match the terminal `=`.
5. Instead, the regex engine backtracks into the token until it finds the last alphanumeric character (`s` in `...aW5zdHJ1Y3Rpb25z`). The transition between `s` (`\w`) and `=` (`\W`) is a `\w\W` transition, which satisfies `\b`.
6. As a result, the regex engine extracts the truncated substring:
   `"aWdub3JlIGFsbCBwcmV2aW91cyBpbnN0cnVjdGlvbn"` (43 characters, omitting the `=`).
7. When this truncated string is passed to `base64.b64decode`:
   ```python
   base64.b64decode("aWdub3JlIGFsbCBwcmV2aW91cyBpbnN0cnVjdGlvbn")
   # Raises: binascii.Error: Incorrect padding
   ```
8. The guardrail caught this exception with `except Exception: pass`, resulting in 0 detected threat matches. The guardrail then assigned `G1Decision.ALLOW` with `risk_score=0.0`.

---

## 2. Design of the Robust Boundary-Safe Extractor

To reliably extract Base64 tokens without stripping padding or matching inside longer words, the extraction strategy must replace word boundaries `\b` with lookarounds that understand Base64 alphabet boundaries:

```python
_BASE64_TOKEN_RE: re.Pattern[str] = re.compile(
    r"(?<![A-Za-z0-9+/=])(?:[A-Za-z0-9+/]{4}){3,}(?:[A-Za-z0-9+/]{4}|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)(?![A-Za-z0-9+/=])"
)
```

### Breakdown of the Regex Architecture:
1. `(?<![A-Za-z0-9+/=])`: Negative lookbehind ensuring the token does not start mid-Base64-character (prevents matching arbitrary sub-slices of longer tokens).
2. `(?:[A-Za-z0-9+/]{4}){3,}`: Matches at least three full 4-character quartets (12 characters minimum prefix).
3. `(?:[A-Za-z0-9+/]{4}|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)`: Matches the final 4-character quartet:
   - `[A-Za-z0-9+/]{4}`: An unpadded quartet (multiple of 3 raw bytes).
   - `[A-Za-z0-9+/]{3}=`: A single-padded quartet (multiple of 3 raw bytes plus 2 bytes).
   - `[A-Za-z0-9+/]{2}==`: A double-padded quartet (multiple of 3 raw bytes plus 1 byte).
   - Total length: $\ge 12 + 4 = 16$ characters, ensuring compatibility with the minimum length threshold.
4. `(?![A-Za-z0-9+/=])`: Negative lookahead ensuring the token does not continue with trailing Base64 or padding characters.

### Resource Safety Controls:
In addition to the regex fix, resource safety constraints were added inside the decoding loop:
- `dec_text = dec_bytes[:4096].decode("utf-8", errors="ignore")`: Truncates decoded string inspection to 4 KB to prevent regular expression DoS on maliciously constructed massive payloads.
- `if not dec_text.strip(): continue`: Bypasses threat scanning for empty or whitespace-only decoded payloads.

---

## 3. Exact Git Diff

```diff
diff --git a/src/trustrag/guardrails/input_guardrail.py b/src/trustrag/guardrails/input_guardrail.py
index e5bd107..7fc67a1 100644
--- a/src/trustrag/guardrails/input_guardrail.py
+++ b/src/trustrag/guardrails/input_guardrail.py
@@ -9,6 +9,7 @@ Validates, audits, and classifies incoming user queries before retrieval:
 
 from __future__ import annotations
 
+import base64
 import re
 from typing import Callable, Dict, List, Optional, Tuple
 
@@ -76,6 +77,11 @@ _CATEGORY_TO_REASON: Dict[str, G1ReasonCode] = {
     "DOS_TRIGGER": G1ReasonCode.G1_DOS_TRIGGER,
 }
 
+# Boundary-safe regex for extracting standard Base64 tokens (length >= 16, valid padding preserved).
+_BASE64_TOKEN_RE: re.Pattern[str] = re.compile(
+    r"(?<![A-Za-z0-9+/=])(?:[A-Za-z0-9+/]{4}){3,}(?:[A-Za-z0-9+/]{4}|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)(?![A-Za-z0-9+/=])"
+)
+
 
 class InputGuardrail:
     """G1 Input Guardrail validating queries prior to retrieval and generation."""
@@ -192,6 +198,28 @@ class InputGuardrail:
                 )
             )
 
+        # 4b. Base64 encoded payload inspection (boundary-safe, padding-preserving)
+        for b64_token in _BASE64_TOKEN_RE.findall(original_input):
+            try:
+                dec_bytes = base64.b64decode(b64_token, validate=False)
+                dec_text = dec_bytes[:4096].decode("utf-8", errors="ignore")
+                if not dec_text.strip():
+                    continue
+                for spec, snippet in match_threat_patterns(dec_text, target="query"):
+                    matches.append(
+                        G1MatchDetail(
+                            rule_name=f"base64_{spec.rule_name}",
+                            reason_code=_CATEGORY_TO_REASON.get(
+                                spec.category, G1ReasonCode.G1_PROMPT_INJECTION
+                            ),
+                            severity=spec.severity,
+                            matched_snippet=f"base64 decoded: '{snippet}'",
+                            is_heuristic=True,
+                        )
+                    )
+            except Exception:
+                pass
+
         # 5. Repetitive token flooding check
         is_flood, flood_desc = check_repetitive_flood(analysis_text)
         if is_flood:
```

