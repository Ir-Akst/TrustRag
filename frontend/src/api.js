/**
 * Typed HTTP API client for TrustRAG Phase 09 backend endpoints.
 */

export class ApiError extends Error {
  constructor(message, { status = 500, code = "API_ERROR", details = [] } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export class TrustRAGApiClient {
  constructor({ baseUrl = "", getToken = () => "", fetchImpl = null } = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.getToken = getToken;
    this.fetchImpl = fetchImpl || globalThis.fetch.bind(globalThis);
  }

  async request(path, { method = "GET", body = undefined } = {}) {
    const headers = { Accept: "application/json" };
    const token = (this.getToken() || "").trim();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    const opts = { method, headers };
    if (body !== undefined) {
      headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }

    const res = await this.fetchImpl(`${this.baseUrl}${path}`, opts);
    let data = null;
    try {
      data = await res.json();
    } catch {
      data = null;
    }

    if (!res.ok) {
      const msg = (data && data.error) || `HTTP ${res.status} calling ${path}`;
      throw new ApiError(msg, {
        status: res.status,
        code: (data && data.code) || `HTTP_${res.status}`,
        details: (data && data.details) || [],
      });
    }
    return data;
  }

  getHealth() {
    return this.request("/api/v1/health");
  }

  getSrmHealth() {
    return this.request("/api/v1/srm/health");
  }

  analyzeG1(query, enableParaphrasing = null) {
    const payload = { query };
    if (enableParaphrasing !== null) payload.enable_paraphrasing = enableParaphrasing;
    return this.request("/api/v1/g1/analyze", { method: "POST", body: payload });
  }

  analyzeG2(query, documents = null, topK = 5) {
    const payload = { query, top_k: topK };
    if (documents && documents.length) payload.documents = documents;
    return this.request("/api/v1/g2/analyze", { method: "POST", body: payload });
  }

  verifyG3(query, answer, documents = null) {
    const payload = { query, answer };
    if (documents && documents.length) payload.documents = documents;
    return this.request("/api/v1/g3/verify", { method: "POST", body: payload });
  }

  retrieveEvidence(query, topK = 5) {
    return this.request("/api/v1/evidence/retrieve", {
      method: "POST",
      body: { query, top_k: topK },
    });
  }

  executePipeline(query, topK = 5) {
    return this.request("/api/v1/pipeline/execute", {
      method: "POST",
      body: { query, top_k: topK },
    });
  }

  getMonitoring() {
    return this.request("/api/v1/monitoring/metrics");
  }

  getConfig() {
    return this.request("/api/v1/config");
  }

  validateConfig(changes) {
    return this.request("/api/v1/config/validate", {
      method: "POST",
      body: { changes, confirm: false },
    });
  }

  applyConfig(changes, confirm = false, actor = "operator") {
    return this.request("/api/v1/config/apply", {
      method: "POST",
      body: { changes, confirm, actor },
    });
  }

  restoreConfig(confirm = false, actor = "operator") {
    return this.request("/api/v1/config/restore", {
      method: "POST",
      body: { confirm, actor },
    });
  }

  getAuditLogs({ eventType = "", component = "", requestId = "", page = 1, pageSize = 25 } = {}) {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (eventType) params.set("event_type", eventType);
    if (component) params.set("component", component);
    if (requestId) params.set("request_id", requestId);
    return this.request(`/api/v1/audit/logs?${params.toString()}`);
  }
}
