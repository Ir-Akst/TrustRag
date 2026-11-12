import { TrustRAGApiClient } from "./api.js";
import {
  renderAuditView,
  renderConfigView,
  renderG1View,
  renderG2View,
  renderG3View,
  renderOverviewView,
  renderSrmView,
  renderMonitoringView,
} from "./views.js";

const tokenInput = document.getElementById("api-token-input");
const savedTok = globalThis.sessionStorage?.getItem("trustrag_token") || "";
if (tokenInput) {
  tokenInput.value = savedTok;
  tokenInput.addEventListener("input", () => {
    globalThis.sessionStorage?.setItem("trustrag_token", tokenInput.value);
  });
}

const api = new TrustRAGApiClient({
  getToken: () => (tokenInput ? tokenInput.value : ""),
});

const state = {
  activeView: "overview",
  health: null,
  srm: null,
  monitoring: null,
  configSnapshot: null,
  auditLogs: null,
  auditRecent: null,
  pipelineResult: null,
  g1Result: null,
  g2Result: null,
  g3Result: null,
  auditFilterEvent: "",
  auditFilterReq: "",
};

function setBanner(msg, type = "info") {
  const b = document.getElementById("global-banner");
  if (!b) return;
  if (!msg) {
    b.className = "banner hidden";
    b.textContent = "";
    return;
  }
  b.className = `banner ${type}`;
  b.textContent = msg;
}

function setConnection(ok, label) {
  const dot = document.getElementById("conn-dot");
  const txt = document.getElementById("conn-label");
  const ts = document.getElementById("last-updated");
  if (dot) dot.className = `dot ${ok ? "ok" : "err"}`;
  if (txt) txt.textContent = label;
  if (ts) ts.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
}

function showConfirmDialog(message, diffObj) {
  return new Promise((resolve) => {
    const dlg = document.getElementById("confirm-dialog");
    const msgEl = document.getElementById("confirm-message");
    const diffEl = document.getElementById("confirm-diff");
    const cancelBtn = document.getElementById("confirm-cancel");
    const okBtn = document.getElementById("confirm-proceed");
    msgEl.textContent = message;
    diffEl.textContent = JSON.stringify(diffObj, null, 2);

    const cleanup = (result) => {
      cancelBtn.removeEventListener("click", onCancel);
      okBtn.removeEventListener("click", onOk);
      if (dlg.open) dlg.close();
      resolve(result);
    };
    const onCancel = () => cleanup(false);
    const onOk = () => cleanup(true);
    cancelBtn.addEventListener("click", onCancel);
    okBtn.addEventListener("click", onOk);
    dlg.showModal();
  });
}

const actions = {
  async refreshAll() {
    setBanner("");
    try {
      const [health, monitoring, srm, auditRecent] = await Promise.all([
        api.getHealth(),
        api.getMonitoring(),
        api.getSrmHealth(),
        api.getAuditLogs({ page: 1, pageSize: 10 }).catch(() => null),
      ]);
      state.health = health;
      state.monitoring = monitoring;
      state.srm = srm;
      state.auditRecent = auditRecent;
      setConnection(true, `API ${health.status.toUpperCase()}`);
      if (state.activeView === "config") {
        state.configSnapshot = await api.getConfig();
      } else if (state.activeView === "audit") {
        state.auditLogs = await api.getAuditLogs({
          eventType: state.auditFilterEvent,
          requestId: state.auditFilterReq,
          page: 1,
        });
      }
    } catch (err) {
      setConnection(false, "API Disconnected");
      setBanner(err.message || "Failed to connect to TrustRAG backend API.", "error");
    }
    render();
  },

  async runPipeline(query, topK) {
    setBanner("Executing full TrustRAG pipeline...", "info");
    try {
      state.pipelineResult = await api.executePipeline(query, topK);
      setBanner("");
      await actions.refreshAll();
    } catch (err) {
      setBanner(err.message, "error");
    }
  },

  async analyzeG1(query, enablePara) {
    setBanner("Running G1 analysis...", "info");
    try {
      state.g1LastQuery = query;
      state.g1EnablePara = enablePara;
      state.g1Result = await api.analyzeG1(query, enablePara);
      setBanner("");
      await actions.refreshAll();
    } catch (err) {
      setBanner(err.message, "error");
    }
  },

  async analyzeG2(query, docsText) {
    setBanner("Running G2 6-signal MSD...", "info");
    try {
      state.g2Query = query;
      state.g2DocsText = docsText;
      const docs = docsText.trim() ? JSON.parse(docsText) : null;
      state.g2Result = await api.analyzeG2(query, docs, 5);
      setBanner("");
      await actions.refreshAll();
    } catch (err) {
      setBanner(err.message, "error");
    }
  },

  async verifyG3(query, answer, docsText) {
    setBanner("Running G3 verification...", "info");
    try {
      state.g3Query = query;
      state.g3Answer = answer;
      state.g3Docs = docsText;
      const docs = docsText.trim() ? JSON.parse(docsText) : null;
      state.g3Result = await api.verifyG3(query, answer, docs);
      setBanner("");
      await actions.refreshAll();
    } catch (err) {
      setBanner(err.message, "error");
    }
  },

  async applyConfig(changes) {
    if (!Object.keys(changes).length) {
      setBanner("No configuration values changed.", "warn");
      return;
    }
    try {
      const validation = await api.validateConfig(changes);
      const confirmed = await showConfirmDialog(
        validation.restart_required
          ? "Restart required for some changes. Confirm applying these validated updates?"
          : "Confirm applying these validated runtime updates?",
        validation.diffs
      );
      if (!confirmed) return;
      const res = await api.applyConfig(changes, true, "dashboard_operator");
      state.configSnapshot = await api.getConfig();
      setBanner(`Configuration applied (backup: ${res.backup_path}).`, "info");
      render();
    } catch (err) {
      setBanner(err.message, "error");
    }
  },

  async restoreConfig() {
    try {
      const preview = await api.restoreConfig(false, "dashboard_operator");
      const confirmed = await showConfirmDialog("Restore all editable settings to baseline defaults?", preview.diffs);
      if (!confirmed) return;
      const res = await api.restoreConfig(true, "dashboard_operator");
      state.configSnapshot = await api.getConfig();
      setBanner(`Restored defaults (backup: ${res.backup_path}).`, "info");
      render();
    } catch (err) {
      setBanner(err.message, "error");
    }
  },

  async loadAudit({ eventType = "", requestId = "", page = 1 } = {}) {
    try {
      state.auditFilterEvent = eventType;
      state.auditFilterReq = requestId;
      state.auditLogs = await api.getAuditLogs({ eventType, requestId, page, pageSize: 25 });
      render();
    } catch (err) {
      setBanner(err.message, "error");
    }
  },
};

function render() {
  const root = document.getElementById("view-root");
  if (!root) return;
  root.replaceChildren();
  const builders = {
    overview: () => renderOverviewView(state, actions),
    g1: () => renderG1View(state, actions),
    g2: () => renderG2View(state, actions),
    g3: () => renderG3View(state, actions),
    srm: () => renderSrmView(state),
    monitoring: () => renderMonitoringView(state),
    config: () => renderConfigView(state, actions),
    audit: () => renderAuditView(state, actions),
  };
  root.appendChild((builders[state.activeView] || builders.overview)());
}

document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", async () => {
    document.querySelectorAll(".nav-btn").forEach((b) => {
      b.classList.remove("active");
      b.removeAttribute("aria-current");
    });
    btn.classList.add("active");
    btn.setAttribute("aria-current", "page");
    state.activeView = btn.dataset.view;
    await actions.refreshAll();
  });
});

document.getElementById("btn-refresh-all")?.addEventListener("click", () => actions.refreshAll());
actions.refreshAll();
