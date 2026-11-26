import test from "node:test";
import assert from "node:assert/strict";

import { ApiError, TrustRAGApiClient } from "../src/api.js";
import {
  SIGNAL_ORDER,
  decisionTone,
  el,
  formatPercentileMetric,
  formatSignalDisplay,
} from "../src/formatters.js";

test("formatSignalDisplay never fabricates unavailable signals", () => {
  assert.equal(SIGNAL_ORDER.length, 6);
  const unavail = formatSignalDisplay({
    signal_id: "F1",
    available: false,
    value: null,
    configured_weight: 0.8,
    effective_weight: 0.0,
    status: "UNAVAILABLE",
  });
  assert.equal(unavail.statusText, "UNAVAILABLE");
  assert.equal(unavail.valueText, "Unavailable (—)");
  assert.equal(unavail.tone, "muted");

  const avail = formatSignalDisplay({
    signal_id: "F4",
    available: true,
    value: 0.95,
    configured_weight: 2.0,
    effective_weight: 1.27,
    status: "AVAILABLE",
  });
  assert.equal(avail.valueText, "0.9500");
  assert.equal(avail.tone, "ok");
});

test("formatPercentileMetric enforces minimum observation count", () => {
  const low = formatPercentileMetric(
    { percentiles_available: false, latency_sample_count: 2, min_percentile_samples: 5 },
    "latency_p95_ms"
  );
  assert.match(low, /Unavailable \(< 5 obs; current=2\)/);

  const ok = formatPercentileMetric(
    { percentiles_available: true, latency_p95_ms: 12.3456 },
    "latency_p95_ms"
  );
  assert.equal(ok, "12.35 ms");
});

test("decisionTone maps security and verification verdicts accurately", () => {
  assert.equal(decisionTone("SUPPORTED"), "ok");
  assert.equal(decisionTone("ALLOW"), "ok");
  assert.equal(decisionTone("FALLBACK_DETERMINISTIC"), "warn");
  assert.equal(decisionTone("CONTRADICTED"), "danger");
  assert.equal(decisionTone("BLOCK"), "danger");
});

test("TrustRAGApiClient sends Bearer token and propagates structured ApiError", async () => {
  const calls = [];
  const mockFetch = async (url, opts) => {
    calls.push({ url, opts });
    if (url.endsWith("/api/v1/health")) {
      return { ok: true, status: 200, json: async () => ({ status: "healthy" }) };
    }
    return {
      ok: false,
      status: 422,
      json: async () => ({ error: "Protected invariant", code: "VALIDATION_ERROR", details: ["guardrails.enabled"] }),
    };
  };

  const client = new TrustRAGApiClient({
    baseUrl: "http://127.0.0.1:8000",
    getToken: () => "tok-abc",
    fetchImpl: mockFetch,
  });

  const health = await client.getHealth();
  assert.equal(health.status, "healthy");
  assert.equal(calls[0].opts.headers.Authorization, "Bearer tok-abc");

  await assert.rejects(
    () => client.applyConfig({ "guardrails.enabled": false }, true),
    (err) => err instanceof ApiError && err.status === 422 && err.code === "VALIDATION_ERROR"
  );
});

test("XSS-safe el() stores untrusted payload strictly as text node", () => {
  const created = [];
  globalThis.document = {
    createElement(tag) {
      const node = {
        tag,
        attrs: {},
        children: [],
        _text: "",
        set textContent(val) {
          this._text = String(val);
        },
        get textContent() {
          return this._text;
        },
        setAttribute(k, v) {
          this.attrs[k] = v;
        },
        appendChild(c) {
          this.children.push(c);
        },
        addEventListener() {},
      };
      created.push(node);
      return node;
    },
    createTextNode(txt) {
      return { nodeType: 3, textContent: txt };
    },
  };

  const xss = "<script>alert('xss')</script>";
  const div = el("div", { text: xss });
  assert.equal(div.textContent, xss);
  assert.equal(div.children.length, 0);
  delete globalThis.document;
});

test("TrustRAGApiClient supports unified verify, status, securityScan, and ingestEvidence", async () => {
  const calls = [];
  const mockFetch = async (url, opts) => {
    calls.push({ url, opts });
    if (url.endsWith("/api/v1/status")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          status: "healthy",
          model_checkpoint: { loaded: true, path: "/path/to/model" },
          components: { g1_input_guard: true, g2_multi_signal_detector: true, g3_evidence_verifier: true },
        }),
      };
    }
    if (url.endsWith("/api/v1/verify")) {
      const body = JSON.parse(opts.body);
      return {
        ok: true,
        status: 200,
        json: async () => ({
          decision: "ALLOW",
          verification_mode: body.enable_neural ? "hybrid" : "heuristic",
          neural_model_loaded: true,
          execution_time_ms: 12.3,
          g3_result: { claims: [{ claim_id: "c1", verdict: "SUPPORTED", confidence: 0.95 }] },
        }),
      };
    }
    if (url.endsWith("/api/v1/evidence")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ingested_count: 1,
          total_corpus_size: 15,
          document_ids: ["doc_1"],
          timestamp: "2026-11-19T00:00:00Z",
        }),
      };
    }
    return { ok: false, status: 404, json: async () => ({ error: "Not found" }) };
  };

  const client = new TrustRAGApiClient({
    baseUrl: "http://127.0.0.1:8000",
    fetchImpl: mockFetch,
  });

  const status = await client.getStatus();
  assert.equal(status.status, "healthy");
  assert.equal(status.model_checkpoint.loaded, true);

  const verifyRes = await client.verify({ query: "Test query?", enable_neural: true });
  assert.equal(verifyRes.decision, "ALLOW");
  assert.equal(verifyRes.verification_mode, "hybrid");

  const ingestRes = await client.ingestEvidence([{ text: "Some fact" }]);
  assert.equal(ingestRes.ingested_count, 1);
  assert.equal(ingestRes.total_corpus_size, 15);
});
