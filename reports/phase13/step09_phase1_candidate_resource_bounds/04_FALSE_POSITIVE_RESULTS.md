# TrustRAG Phase 13 Step 9 — False-Positive Regression Results

**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11`  
**HEAD Commit:** `8229aee01a0b6f7fd61a5e774da5bb707bd6a7c1`  
**Audit Script:** `evidence/probe_step09_resource_bounds.py`  
**Audit Data:** `evidence/probe_step09_resource_bounds.json`  
**Total Benign Samples Tested:** 205  
**Benign Samples Blocked:** 0  
**False Positive Rate:** **`0.0000%`**  
**Verdict:** **`PASS` (Zero false positives across all 205 benign inputs)**

---

## 1. Evaluation Methodology

Enforcing stricter candidate count bounds and streaming iteration must not increase false rejections on benign text. The 205 deterministic benign scenarios established in Step 8 were re-executed against the hardened G1 pipeline.

The corpus tests seven distinct categories of technical, mathematical, cryptographic, and natural language inputs that resemble or contain Base64 strings.

---

## 2. Benign Corpus Breakdown & Results Matrix

| Corpus Category | Sample Count | Evaluated Artifacts | Blocked Count | False Positive Rate | Status |
|---|---|---|---|---|---|
| **Category 1: Hashes & Checksums** | 25 | SHA-256, SHA-384, SHA-512, MD5, SRI hashes, Git tree/blob/commit IDs | 0 | **0.00%** | **PASS** |
| **Category 2: Identifiers & Keys** | 25 | RFC 4122 UUIDs (v4/v5), JWT headers/claims, GitHub tokens, AWS ARNs, Stripe keys | 0 | **0.00%** | **PASS** |
| **Category 3: URLs & File Paths** | 25 | REST endpoints, CDN image query strings, S3 URIs, Git remotes, LDAP URIs, file paths | 0 | **0.00%** | **PASS** |
| **Category 4: Code & Mathematics** | 30 | Python math, SQL queries, JavaScript filters, C++ STL, shell pipelines, LaTeX formulas | 0 | **0.00%** | **PASS** |
| **Category 5: Harmless Base64** | 30 | Standard and URL-safe Base64 encodings of pangrams, NLP definitions, paper titles | 0 | **0.00%** | **PASS** |
| **Category 6: Delimiters & Tables** | 35 | Repeated slashes (`////`), plus borders (`++++`), equals rules (`====`), ASCII tables, markdown | 0 | **0.00%** | **PASS** |
| **Category 7: Multilingual & Queries** | 35 | Normal end-user questions in English, French, German, Spanish, Japanese, Chinese | 0 | **0.00%** | **PASS** |
| **Total Test Corpus** | **205** | **Comprehensive Production-Like Benign Test Set** | **0** | **0.0000%** | **PASS** |

---

## 3. Comparative Stability Across Phases

| Evaluation Phase | Benign Samples Tested | False Positives | False Positive Rate | Verdict |
|---|---|---|---|---|
| **Phase 13 Step 7 Report** | 105 samples | 0 | 0.0000% | PASS |
| **Phase 13 Step 8 Audit** | 205 samples | 0 | 0.0000% | PASS |
| **Phase 13 Step 9 Post-Remediation** | **205 samples** | **0** | **0.0000%** | **PASS** |

---

## 4. Preservation of Semantic G1 Assessment

1. **Non-Intrusive Bounding:**
   The `_MAX_B64_CANDIDATES = 64` limit in Phase 1 and Phase 2 affects only candidate extraction capacity; it does not alter candidate scoring, token normalization, or threat pattern matching semantics.
2. **Benign Content Immunity:**
   Legitimate developer queries containing cryptographic hashes, UUIDs, or harmless Base64 continue to pass through G1 with risk score `0.0` and reason code `G1_CLEAN`.

---

## 5. Conclusion

The Phase 1 candidate limit remediation introduces zero false positives across 205 diverse benign scenarios, maintaining an absolute **0.0000% false-positive rate**.

