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
