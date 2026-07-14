const API = "";
const MAX_PROMPT_CHARS = 4000;

function formatDollars(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return "$0.00";
  }

  const num = parseFloat(value);

  if (num !== 0 && Math.abs(num) < 0.01) {
    const sign = num < 0 ? "-" : "";
    const absoluteValue = Math.abs(num);
    return sign + "$" + parseFloat(absoluteValue.toFixed(5)).toString();
  }

  return (num < 0 ? "-$" : "$") + Math.abs(num).toFixed(2);
}

async function apiGet(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json();
}

async function apiPatch(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const payload = await res.json();
      if (payload?.detail) {
        detail =
          typeof payload.detail === "string"
            ? payload.detail
            : JSON.stringify(payload.detail);
      }
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

async function apiPostJson(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const payload = await res.json();
      if (payload?.detail) {
        detail =
          typeof payload.detail === "string"
            ? payload.detail
            : JSON.stringify(payload.detail);
      }
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

function escapeHtml(str) {
  const el = document.createElement("div");
  el.textContent = str == null ? "" : String(str);
  return el.innerHTML;
}

function truncate(str, len) {
  const text = str == null ? "" : String(str);
  return text.length > len ? `${text.slice(0, len)}…` : text;
}

function difficultyClass(level) {
  return `chip chip-${level}`;
}

function formatMode(mode) {
  if (mode === "deepseek") return "DeepSeek Live";
  if (mode === "openai") return "OpenAI Live";
  if (mode === "fake") return "Fake";
  if (mode === "fallback_fake") return "Fallback Fake";
  if (mode === "not_called") return "Not Called";
  return mode || "Unknown";
}

function formatProvider(provider) {
  if (provider === "deepseek") return "DeepSeek";
  if (provider === "openai") return "OpenAI";
  return "Fake";
}

function badgeClassForBudget(status) {
  if (status === "allowed") return "badge badge-ok";
  if (status === "forced") return "badge badge-pending";
  if (status === "blocked") return "badge badge-error";
  return "badge badge-pending";
}

function badgeClassForMode(mode) {
  if (mode === "deepseek" || mode === "openai") return "badge badge-live";
  if (mode === "fake" || mode === "fallback_fake") return "badge badge-fake";
  if (mode === "blocked") return "badge badge-error";
  return "badge badge-pending";
}

function badgeClassForProvider(provider) {
  if (provider === "deepseek" || provider === "openai") return "badge badge-live";
  return "badge badge-fake";
}

function statusPillClass(status) {
  if (status === "healthy") return "status-pill status-allowed";
  if (status === "warning") return "status-pill status-warning";
  if (status === "exceeded" || status === "overage") {
    return "status-pill status-blocked";
  }
  return "status-pill status-pending";
}

function setHealthBadge(ok, message) {
  const el = document.getElementById("health-badge");
  if (!el) return;
  el.textContent = message;
  el.className = `badge ${ok ? "badge-ok" : "badge-error"}`;
}

async function loadHealth() {
  try {
    const data = await apiGet("/health");
    setHealthBadge(true, data.status === "ok" ? "API online" : "API unknown");
  } catch {
    setHealthBadge(false, "API offline");
  }
}
