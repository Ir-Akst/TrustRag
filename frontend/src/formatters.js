/**
 * Pure formatting and XSS-safe DOM helpers for TrustRAG Dashboard.
 * Never interpolates untrusted strings as raw HTML.
 */

export const SIGNAL_ORDER = [
  "perplexity",
  "embedding_norm",
  "query_match",
  "instruction_content",
  "consensus_deviation",
  "provenance",
];

export const SIGNAL_LABELS = {
  perplexity: "F1: Perplexity",
  embedding_norm: "F2: Embedding Norm",
  query_match: "F3: Query Match",
  instruction_content: "F4: Instruction Content",
  consensus_deviation: "F5: Consensus Deviation",
  provenance: "F6: Provenance Prior",
};

export function formatSignalDisplay(signal) {
  if (!signal || !signal.available || signal.value === null || signal.value === undefined) {
    return {
      statusText: (signal && signal.status) || "UNAVAILABLE",
      valueText: "Unavailable (—)",
      weightText: signal ? `${Number(signal.effective_weight || 0).toFixed(2)} / ${Number(signal.configured_weight || 0).toFixed(2)}` : "0.00 / 0.00",
      tone: "muted",
    };
  }
  const v = Number(signal.value);
  return {
    statusText: signal.status || "AVAILABLE",
    valueText: v.toFixed(4),
    weightText: `${Number(signal.effective_weight || 0).toFixed(2)} / ${Number(signal.configured_weight || 0).toFixed(2)}`,
    tone: v >= 0.65 ? "ok" : v >= 0.4 ? "warn" : "danger",
  };
}

export function formatPercentileMetric(monitoring, key) {
  if (!monitoring || !monitoring.percentiles_available) {
    const count = monitoring ? monitoring.latency_sample_count : 0;
    const minReq = monitoring ? monitoring.min_percentile_samples : 5;
    return `Unavailable (< ${minReq} obs; current=${count})`;
  }
  const val = monitoring[key];
  return val === null || val === undefined ? "—" : `${Number(val).toFixed(2)} ms`;
}

export function decisionTone(decision) {
  const d = String(decision || "").toUpperCase();
  if (["ALLOW", "CLEAN", "SUPPORTED", "VERIFIED", "OK", "HEALTHY", "ACTIVE", "READY"].includes(d)) return "ok";
  if (["FLAG", "UNCERTAIN", "PARTIALLY_SUPPORTED", "ABSTAINED", "DEGRADED", "FALLBACK_DETERMINISTIC"].includes(d)) return "warn";
  if (["BLOCK", "BLOCKED", "POISONED", "CONTRADICTED", "ERROR", "NOT_READY", "UNAVAILABLE", "COMPROMISED"].includes(d)) return "danger";
  return "muted";
}

export function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined) continue;
    if (k === "className") node.className = v;
    else if (k === "text") node.textContent = String(v);
    else if (k.startsWith("on") && typeof v === "function") {
      node.addEventListener(k.slice(2).toLowerCase(), v);
    } else {
      node.setAttribute(k, String(v));
    }
  }
  for (const child of Array.isArray(children) ? children : [children]) {
    if (child === null || child === undefined) continue;
    if (typeof child === "string" || typeof child === "number") {
      node.appendChild(document.createTextNode(String(child)));
    } else {
      node.appendChild(child);
    }
  }
  return node;
}

export function badge(label, tone = null) {
  const resolved = tone || decisionTone(label);
  return el("span", { className: `badge badge-${resolved}`, text: String(label) });
}
