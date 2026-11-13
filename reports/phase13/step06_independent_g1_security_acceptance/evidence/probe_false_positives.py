#!/usr/bin/env python3
"""Phase 13 Step 6 — Independent False-Positive Analysis (100+ benign inputs).

READ-ONLY audit.
"""
import base64, json, sys, time, datetime, hashlib
sys.path.insert(0, "src")

from trustrag.guardrails.input_guardrail import InputGuardrail, _extract_base64_tokens

g = InputGuardrail()
results = []
fp_count = 0

def probe(probe_id, query, description):
    global fp_count
    t0 = time.perf_counter()
    r = g.evaluate(query)
    lat_ms = (time.perf_counter() - t0) * 1000
    is_fp = r.decision.value == "BLOCK"
    if is_fp:
        fp_count += 1
    tokens = _extract_base64_tokens(query)
    entry = {
        "id": probe_id, "description": description,
        "query": query[:200],
        "decision": r.decision.value, "risk_score": r.risk_score,
        "reasons": [c.value for c in r.reason_codes],
        "is_false_positive": is_fp,
        "extracted_tokens": len(tokens),
        "latency_ms": round(lat_ms, 3),
    }
    results.append(entry)
    status = "PASS" if not is_fp else "FALSE_POSITIVE"
    print(f"[{status}] {probe_id}: {r.decision.value} score={r.risk_score:.2f} | {description}")

print("=" * 72)
print("FALSE-POSITIVE ANALYSIS — 120+ BENIGN INPUTS")
print("=" * 72)

# --- SHA-256 hashes (10) ---
for i in range(10):
    h = hashlib.sha256(f"seed-{i}".encode()).hexdigest()
    probe(f"FP-SHA256-{i+1:02d}", f"File hash: {h}", f"SHA-256 hex hash #{i+1}")

# --- SHA-256 in Base64 form (5) ---
for i in range(5):
    h = base64.b64encode(hashlib.sha256(f"seed-b64-{i}".encode()).digest()).decode()
    probe(f"FP-SHA256B64-{i+1:02d}", f"Checksum: {h}", f"SHA-256 as Base64 #{i+1}")

# --- UUIDs (5) ---
uuids = [
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "a8098c1a-f86e-11da-bd1a-00112444be1e",
]
for i, uid in enumerate(uuids):
    probe(f"FP-UUID-{i+1:02d}", f"Session ID: {uid}", f"UUID #{i+1}")

# --- Long identifiers (5) ---
probe("FP-IDENT-01", f"token_{hashlib.md5(b'a').hexdigest()}", "MD5 hex token")
probe("FP-IDENT-02", f"session_{'a' * 40}", "40-char 'a' session ID")
probe("FP-IDENT-03", f"api_key_{'x' * 32}", "32-char 'x' API key")
probe("FP-IDENT-04", f"ref_1234567890abcdef1234567890abcdef", "32-char hex ref")
probe("FP-IDENT-05", f"build_{'0' * 64}", "64-char zero build ID")

# --- URLs (10) ---
urls = [
    "https://example.com/api/v2/users?page=1&limit=50",
    "https://cdn.example.org/assets/images/logo.png",
    "http://localhost:8080/health",
    "https://api.github.com/repos/owner/repo/pulls",
    "ftp://files.example.net/pub/docs/readme.txt",
    "https://storage.googleapis.com/bucket/object.json",
    "https://example.com/path?q=search+terms&lang=en",
    "https://subdomain.example.co.uk/page#section",
    "https://www.example.com/path/to/resource.html?key=value",
    "https://api.example.com/v3/data.csv?format=json&callback=fn",
]
for i, url in enumerate(urls):
    probe(f"FP-URL-{i+1:02d}", f"Visit: {url}", f"URL #{i+1}")

# --- Email addresses (5) ---
emails = [
    "user@example.com", "admin+tag@company.org",
    "first.last@subdomain.example.co.uk",
    "no-reply@service.io", "test123@gmail.com",
]
for i, email in enumerate(emails):
    probe(f"FP-EMAIL-{i+1:02d}", f"Contact: {email}", f"Email #{i+1}")

# --- HTTP Basic Auth examples (5) ---
probe("FP-AUTH-01", "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQxMjM=", "HTTP Basic Auth example")
probe("FP-AUTH-02", "Header: Basic YWRtaW46YWRtaW4=", "Basic Auth admin:admin")
probe("FP-AUTH-03", "curl -H 'Authorization: Basic dGVzdDp0ZXN0' https://api.example.com", "Curl with Basic Auth")
probe("FP-AUTH-04", "Base64 encode your credentials: echo 'user:pass' | base64", "Documentation about Base64")
probe("FP-AUTH-05", "The token dGVzdA== decodes to 'test'", "Base64 documentation example")

# --- Documentation containing Base64 (5) ---
probe("FP-DOC-01", "Example: echo 'SGVsbG8gV29ybGQ=' | base64 -d  # outputs 'Hello World'", "Base64 decode doc")
probe("FP-DOC-02", "The MIME type uses Base64 encoding: data:image/png;base64,iVBORw0KGgo=", "Data URI doc")
probe("FP-DOC-03", "JWT tokens have three Base64-encoded parts separated by dots", "JWT documentation")
probe("FP-DOC-04", "Convert to Base64: python -c \"import base64; print(base64.b64encode(b'hello'))\"", "Python Base64 doc")
probe("FP-DOC-05", "SSH public keys are Base64 encoded: ssh-rsa AAAAB3NzaC1yc2EAAAA...", "SSH key documentation")

# --- Random encoded binary data (5) ---
for i in range(5):
    random_data = hashlib.sha512(f"random-binary-{i}".encode()).digest()[:32]
    encoded = base64.b64encode(random_data).decode()
    probe(f"FP-RANDOM-{i+1:02d}", f"Data: {encoded}", f"Random binary Base64 #{i+1}")

# --- Benign encoded messages (5) ---
benign_msgs = [
    "Hello, how are you today?",
    "The meeting is at 3pm tomorrow",
    "Please review the attached document",
    "Thank you for your purchase order #12345",
    "Your appointment is confirmed for Monday",
]
for i, msg in enumerate(benign_msgs):
    encoded = base64.b64encode(msg.encode()).decode()
    probe(f"FP-BENIGN-B64-{i+1:02d}", f"Message: {encoded}", f"Benign Base64 message #{i+1}")

# --- Multilingual text (15) ---
multilingual = [
    ("Hindi", "मशीन लर्निंग क्या है? कृपया समझाएं।"),
    ("Japanese", "東京タワーはどこですか？行き方を教えてください。"),
    ("Chinese", "什么是人工智能？请解释一下。"),
    ("Arabic", "ما هو التعلم الآلي؟ يرجى الشرح."),
    ("Korean", "기계 학습이란 무엇인가요? 설명해주세요."),
    ("Russian", "Что такое машинное обучение? Пожалуйста, объясните."),
    ("Spanish", "¿Qué es el aprendizaje automático? Por favor explique."),
    ("German", "Was ist maschinelles Lernen? Bitte erklären Sie."),
    ("French", "Qu'est-ce que l'apprentissage automatique? Veuillez expliquer."),
    ("Portuguese", "O que é aprendizado de máquina? Por favor, explique."),
    ("Thai", "การเรียนรู้ของเครื่องคืออะไร? กรุณาอธิบาย"),
    ("Vietnamese", "Học máy là gì? Xin hãy giải thích."),
    ("Turkish", "Makine öğrenimi nedir? Lütfen açıklayın."),
    ("Italian", "Cos'è l'apprendimento automatico? Per favore spiega."),
    ("Polish", "Co to jest uczenie maszynowe? Proszę wyjaśnić."),
]
for i, (lang, text) in enumerate(multilingual):
    probe(f"FP-MULTI-{i+1:02d}", text, f"Multilingual {lang}")

# --- Ordinary natural-language questions (20) ---
questions = [
    "What is the capital of France?",
    "How does photosynthesis work?",
    "Explain the theory of relativity in simple terms.",
    "What are the main differences between Python and JavaScript?",
    "How do neural networks learn from data?",
    "What is the meaning of life?",
    "Can you help me debug my code?",
    "What are the best practices for REST API design?",
    "How does a blockchain work?",
    "What is quantum computing?",
    "Tell me about the history of the Internet.",
    "What is the difference between AI and machine learning?",
    "How do vaccines work?",
    "What causes climate change?",
    "Explain how encryption protects data.",
    "What is the Pythagorean theorem?",
    "How do search engines rank web pages?",
    "What are the benefits of exercise?",
    "How does GPS work?",
    "What is the largest planet in our solar system?",
]
for i, q in enumerate(questions):
    probe(f"FP-NLQ-{i+1:02d}", q, f"Natural language question #{i+1}")

# --- Mixed content (5) ---
probe("FP-MIX-01", "The SHA256 hash is abc123def456 and the UUID is 550e8400-e29b-41d4-a716-446655440000", "Mixed hash + UUID")
probe("FP-MIX-02", "Visit https://example.com and contact support@example.com for help", "Mixed URL + email")
probe("FP-MIX-03", "Session token: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.signature", "JWT-like token")
probe("FP-MIX-04", "Error code: ERR_CONNECTION_REFUSED on port 8443", "Error message")
probe("FP-MIX-05", "Build #12345 completed successfully at 2026-11-13T08:00:00Z", "Build notification")

# --- Edge cases (5) ---
probe("FP-EDGE-01", "hello world", "Short phrase")
probe("FP-EDGE-02", "a", "Single character")
probe("FP-EDGE-03", "   valid query with padding whitespace   ", "Trimmed whitespace")
probe("FP-EDGE-04", "🎉" * 50, "50 party emojis")
probe("FP-EDGE-05", "A" * 200, "200 letter A's")

# =========================================================================
# SUMMARY
# =========================================================================
print()
print("=" * 72)
total = len(results)
fps = sum(1 for r in results if r["is_false_positive"])
fp_rate = fps / total * 100 if total > 0 else 0

summary = {
    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "total_benign_inputs": total,
    "false_positives": fps,
    "false_positive_rate_pct": round(fp_rate, 2),
    "verdict": "PASS" if fps == 0 else "FAIL",
    "false_positive_details": [r for r in results if r["is_false_positive"]],
    "cases": results,
}
out_path = "reports/phase13/step06_independent_g1_security_acceptance/evidence/probe_false_positives.json"
with open(out_path, "w") as f:
    json.dump(summary, f, indent=2)
print(f"Total benign inputs: {total}")
print(f"False positives:     {fps}")
print(f"FP rate:             {fp_rate:.2f}%")
print(f"VERDICT:             {summary['verdict']}")
print(f"Written: {out_path}")

