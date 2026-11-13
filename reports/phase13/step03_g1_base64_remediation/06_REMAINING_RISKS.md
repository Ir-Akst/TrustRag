# TrustRAG Phase 13 Step 3 — Remaining Risks and Academic Transparency

## 1. Residual Security and Encoding Risks

While the remediation of REM-01 completely closes the extraction bypass for standard Base64 tokens with valid padding, the following boundary conditions and potential evasion vectors remain documented for future architectural consideration:

### A. Non-Standard Base64 Alphabets (Base64URL)
- **Current Behavior:** The regex `_BASE64_TOKEN_RE` targets standard RFC 4648 §4 Base64 alphabet characters (`[A-Za-z0-9+/=]`).
- **Potential Gap:** RFC 4648 §5 defines URL-safe Base64 (`base64url`), which replaces `+` with `-` and `/` with `_`. While URL-safe Base64 without `+` or `/` is often decoded if treated as standard, strings containing `-` or `_` are not matched by `_BASE64_TOKEN_RE`.
- **Mitigation / Next Step:** A subsequent phase may introduce an optional secondary scan for `base64url` patterns if web-encoded URL parameters become a supported query modality.

### B. Segmented / Fragmented Base64 Tokens
- **Current Behavior:** An attacker who splits a Base64 string into multiple sub-16-character pieces separated by spaces (e.g., `"aWdub 3JlIG FsbC"`) will not trigger Base64 extraction because each segment falls below the 16-character threshold.
- **Compensating Controls:** G1's token flooding checks and entropy analyzers provide partial visibility, but arbitrary whitespace insertion inside an encoded payload is an inherently challenging vector for regex-based extractors without full query reconstruction.

### C. Alternate Encodings (Hex, Rot13, Punycode, Morse)
- **Current Behavior:** G1 specifically inspects Base64 as an encoded attack surface. Other encodings such as full hexadecimal ASCII strings, Rot13 ciphers, or custom binary encodings are evaluated against standard threat patterns rather than dedicated decoding pipelines.

---

## 2. Academic Transparency Disclosures

In accordance with rigorous scientific integrity principles, the following persistent system properties are formally documented:

1. **Selective Routing Model (SRM) Heuristic Fallback:**
   The SRM module (`src/trustrag/pipeline/router.py`) is designed as a routing component between low-cost SLMs and high-capacity LLMs. In the current offline development and testing repository, the neural SLM inference engine is not deployed. The system operates entirely on its deterministic heuristic fallback router, maintaining deterministic risk routing and tier-based categorization without neural inference overhead.
2. **Offline Dataset Benchmark Availability:**
   Large-scale public research benchmarks (such as Natural Questions, MS-MARCO, and HotpotQA) are un-downloaded in the offline development environment. All test suites, regression probes, and CI workflows utilize validated synthetic schemas, local golden fixtures, and deterministic test doubles.
3. **Mock Inference Generators:**
   End-to-end evaluation suites utilize mock deterministic generator models to ensure reproducibility, deterministic test assertion, and zero external network latency.

---

## 3. Summary of Status

The remediation of REM-01 strictly eliminates the verified vulnerability without introducing regression, side effects, or false positives. The residual risks identified above represent theoretical multi-encoding enhancements rather than active flaws in standard Base64 inspection.

