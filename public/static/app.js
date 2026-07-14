const API = "";
const MAX_PROMPT_CHARS = 4000;

function formatDollars(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return "$0.00";
  }

  const num = parseFloat(value);

  // Preserve granular request costs below one cent.
  if (num !== 0 && Math.abs(num) < 0.01) {
    const sign = num < 0 ? "-" : "";
    const absoluteValue = Math.abs(num);
    return sign + "$" + parseFloat(absoluteValue.toFixed(5)).toString();
  }

  return (num < 0 ? "-$" : "$") + Math.abs(num).toFixed(2);
}

let pendingBudgetWarningPayload = null;
let pendingBudgetLimit = null;

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
      /* ignore parse errors */
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
      /* ignore parse errors */
    }
    throw new Error(detail);
  }
  return res.json();
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

function setLoading(loading) {
  const btn = document.getElementById("route-btn");
  if (!btn) return;
  const label = btn.querySelector(".btn-label");
  const spinner = btn.querySelector(".btn-spinner");
  btn.disabled = loading;
  if (label) label.hidden = loading;
  if (spinner) spinner.hidden = !loading;
}

function openBudgetWarningModal() {
  const modal = document.getElementById("budgetWarningModal");
  if (!modal) return;
  modal.style.display = "flex";
}

function closeBudgetWarningModal() {
  pendingBudgetWarningPayload = null;
  const modal = document.getElementById("budgetWarningModal");
  if (modal) modal.style.display = "none";
}

async function loadHealth() {
  try {
    const data = await apiGet("/health");
    setHealthBadge(true, data.status === "ok" ? "API online" : "API unknown");
  } catch {
    setHealthBadge(false, "API offline");
  }
}

async function loadBudget() {
  const data = await apiGet("/budget");
  const usedPct =
    data.monthly_budget > 0
      ? (data.monthly_billable_used / data.monthly_budget) * 100
      : 0;
  const barPct = Math.min(100, Math.max(0, usedPct));
  const budgetHealth = data.status;

  const bar = document.getElementById("budget-used-bar");
  if (bar) {
    bar.style.width = `${barPct}%`;
    bar.classList.toggle("over", usedPct >= 90 || data.remaining_budget < 0);
  }

  const caption = document.getElementById("budget-caption");
  if (caption) {
    caption.textContent = `${formatDollars(data.monthly_billable_used)} of ${formatDollars(data.monthly_budget)} billable this month (${usedPct.toFixed(1)}%)`;
  }

  const heroRemaining = document.getElementById("hero-budget-remaining");
  if (heroRemaining) {
    heroRemaining.textContent = formatDollars(data.remaining_budget);
  }

  const budgetPill = document.getElementById("budget-status-pill");
  if (budgetPill) {
    budgetPill.className = statusPillClass(budgetHealth);
    budgetPill.textContent =
      budgetHealth === "healthy"
        ? "Budget healthy"
        : budgetHealth === "warning"
        ? "Budget getting tight"
        : budgetHealth === "overage"
        ? "Budget overage"
        : "Budget exceeded";
  }

  const stats = document.getElementById("budget-stats");
  if (stats) {
    stats.innerHTML = `
      <div><dt>Current month</dt><dd>${data.current_month}</dd></div>
      <div><dt>Monthly budget</dt><dd>${formatDollars(data.monthly_budget)}</dd></div>
      <div><dt>Billable used</dt><dd>${formatDollars(data.monthly_billable_used)}</dd></div>
      <div><dt>Estimated total</dt><dd>${formatDollars(data.monthly_estimated_cost)}</dd></div>
      <div><dt>Remaining</dt><dd>${formatDollars(data.remaining_budget)}</dd></div>
      <div><dt>Status</dt><dd>${data.status}</dd></div>
    `;
  }

  const limitInput = document.getElementById("budgetLimitInput");
  if (limitInput && document.activeElement !== limitInput) {
    limitInput.value = Number(data.monthly_budget).toFixed(2);
  }
}

async function loadMetrics() {
  const data = await apiGet("/metrics");

  const heroRequests = document.getElementById("hero-total-requests");
  if (heroRequests) heroRequests.textContent = data.total_requests;

  const heroCost = document.getElementById("hero-total-cost");
  if (heroCost) heroCost.textContent = formatDollars(data.total_cost);

  const heroLatency = document.getElementById("hero-average-latency");
  if (heroLatency) {
    heroLatency.textContent = `${data.average_latency_ms} ms`;
  }

  const metricsStats = document.getElementById("metrics-stats");
  if (metricsStats) {
    metricsStats.innerHTML = `
      <div><dt>Lifetime requests</dt><dd>${data.total_requests}</dd></div>
      <div><dt>Lifetime billable</dt><dd>${formatDollars(data.total_cost)}</dd></div>
      <div><dt>Avg latency</dt><dd>${data.average_latency_ms} ms</dd></div>
      <div><dt>Current month</dt><dd>${data.current_month}</dd></div>
    `;
  }

  const mini = document.getElementById("metrics-mini-stats");
  if (mini) {
    mini.innerHTML = `
      <div class="mini-stat"><span>Monthly requests</span><strong>${data.monthly_requests}</strong></div>
      <div class="mini-stat"><span>Monthly billable</span><strong>${formatDollars(data.monthly_billable_cost)}</strong></div>
      <div class="mini-stat"><span>Monthly estimated</span><strong>${formatDollars(data.monthly_estimated_cost)}</strong></div>
      <div class="mini-stat"><span>Monthly fake</span><strong>${data.monthly_fake_requests}</strong></div>
      <div class="mini-stat"><span>Monthly DeepSeek</span><strong>${data.monthly_deepseek_requests}</strong></div>
      <div class="mini-stat"><span>Monthly OpenAI</span><strong>${data.monthly_openai_requests}</strong></div>
      <div class="mini-stat"><span>Monthly blocked</span><strong>${data.monthly_blocked_requests}</strong></div>
      <div class="mini-stat"><span>Fake requests</span><strong>${data.fake_requests}</strong></div>
      <div class="mini-stat"><span>DeepSeek requests</span><strong>${data.deepseek_requests}</strong></div>
      <div class="mini-stat"><span>OpenAI requests</span><strong>${data.openai_requests}</strong></div>
      <div class="mini-stat"><span>Fallback requests</span><strong>${data.fallback_requests}</strong></div>
      <div class="mini-stat"><span>Blocked requests</span><strong>${data.blocked_requests}</strong></div>
    `;
  }

  const modelItems = Object.entries(data.model_usage || {})
    .map(([k, v]) => `<li><span>${k}</span><span>${v}</span></li>`)
    .join("");
  const diffItems = Object.entries(data.difficulty_usage || {})
    .map(([k, v]) => `<li><span>${k}</span><span>${v}</span></li>`)
    .join("");

  const breakdown = document.getElementById("metrics-breakdown");
  if (breakdown) {
    breakdown.innerHTML = `
      <h4>By model</h4>
      <ul>${modelItems || "<li><span>—</span><span>0</span></li>"}</ul>
      <h4>By difficulty</h4>
      <ul>${diffItems || "<li><span>—</span><span>0</span></li>"}</ul>
    `;
  }
}

async function loadLogs() {
  const logs = await apiGet("/logs");
  const tbody = document.getElementById("logs-body");
  const history = document.getElementById("history-list");

  if (!logs.length) {
    if (tbody) {
      tbody.innerHTML =
        '<tr><td colspan="8" class="empty">No logs yet — route a prompt first</td></tr>';
    }
    if (history) {
      history.innerHTML = '<p class="muted">No prompt history yet.</p>';
    }
    return;
  }

  if (tbody) {
    tbody.innerHTML = logs
      .map(
        (log) => `
      <tr>
        <td>${log.id}</td>
        <td><span class="${difficultyClass(log.difficulty)}">${log.difficulty}</span></td>
        <td>${log.selected_tier}</td>
        <td title="${escapeHtml(log.prompt)}">${truncate(log.selected_model, 18)}</td>
        <td>${formatProvider(log.provider)}</td>
        <td>${formatMode(log.llm_mode)}</td>
        <td>${formatDollars(log.billable_cost ?? log.estimated_cost)}</td>
        <td class="status-${log.budget_status}">${log.budget_status}</td>
      </tr>
    `
      )
      .join("");
  }

  if (history) {
    history.innerHTML = logs
      .map(
        (log) => `
        <details class="history-item">
          <summary>
            <span>${escapeHtml(truncate(log.prompt, 60))}</span>
            <span class="history-summary-meta">${formatProvider(log.provider)} · ${log.selected_model} · ${log.budget_status}</span>
          </summary>
          <div class="history-body">
            <p><strong>Prompt:</strong> ${escapeHtml(log.prompt)}</p>
            <p><strong>Answer:</strong> ${escapeHtml(log.answer || "")}</p>
            <p><strong>Provider:</strong> ${formatProvider(log.provider)}</p>
            <p><strong>LLM mode:</strong> ${formatMode(log.llm_mode)}</p>
            <p><strong>Selected model:</strong> ${escapeHtml(log.selected_model)}</p>
            <p><strong>Selected tier:</strong> ${escapeHtml(log.selected_tier)}</p>
            <p><strong>Difficulty:</strong> ${escapeHtml(log.difficulty)} (${log.difficulty_score})</p>
            <p><strong>Estimated input cost:</strong> ${formatDollars(log.estimated_cost)}</p>
            <p><strong>Billable cost:</strong> ${formatDollars(log.billable_cost ?? 0)}</p>
            <p><strong>Tokens:</strong> In ${log.input_tokens ?? 0} · Out ${log.output_tokens ?? 0}</p>
            <p><strong>Latency:</strong> ${log.latency_ms} ms</p>
            <p><strong>Budget status:</strong> ${escapeHtml(log.budget_status)}</p>
            <p><strong>Timestamp:</strong> ${escapeHtml(log.created_at || "")}</p>
          </div>
        </details>
      `
      )
      .join("");
  }
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

function showRouteResult(data) {
  const card = document.getElementById("route-result");
  if (!card) return;
  card.hidden = false;

  const blocked = document.getElementById("route-blocked");
  if (blocked) blocked.hidden = data.budget_status !== "blocked";

  const diff = document.getElementById("result-difficulty");
  if (diff) {
    diff.textContent = (data.difficulty || "-").toUpperCase();
    diff.className = data.difficulty ? difficultyClass(data.difficulty) : "";
  }

  const score = document.getElementById("result-difficulty-score");
  if (score) score.textContent = `Score: ${data.difficulty_score}`;

  const tier = document.getElementById("result-tier");
  if (tier) tier.textContent = data.selected_tier;

  const model = document.getElementById("result-model");
  if (model) model.textContent = data.selected_model;

  const estTokens = document.getElementById("result-estimated-input-tokens");
  if (estTokens) {
    estTokens.textContent = `${data.estimated_input_tokens ?? 0}`;
  }

  const billable = document.getElementById("result-billable-cost");
  if (billable) {
    billable.textContent = formatDollars(data.actual_cost ?? data.billable_cost ?? 0);
  }

  const estNote = document.getElementById("result-estimated-note");
  if (estNote) {
    estNote.textContent = `Gate estimate (input): ${formatDollars(data.estimated_cost ?? 0)}`;
  }

  const latency = document.getElementById("result-latency");
  if (latency) latency.textContent = `${data.latency_ms} ms`;

  const totalTokens = document.getElementById("result-total-tokens");
  if (totalTokens) totalTokens.textContent = `${data.total_tokens}`;

  const tokenBreakdown = document.getElementById("result-token-breakdown");
  if (tokenBreakdown) {
    tokenBreakdown.textContent = `Input: ${data.input_tokens} · Output: ${data.output_tokens}`;
  }

  const budgetStatus = document.getElementById("result-budget-status");
  if (budgetStatus) {
    budgetStatus.textContent = (data.budget_status || "").toUpperCase();
    budgetStatus.className = badgeClassForBudget(data.budget_status);
  }

  const provider = document.getElementById("result-provider");
  if (provider) {
    provider.textContent = formatProvider(data.provider);
    provider.className = badgeClassForProvider(data.provider);
  }

  const llmMode = document.getElementById("result-llm-mode");
  if (llmMode) {
    llmMode.textContent = formatMode(data.llm_mode);
    llmMode.className = badgeClassForMode(data.llm_mode);
  }

  const reasons = data.difficulty_reasons || [];
  const reasonsEl = document.getElementById("result-reasons");
  if (reasonsEl) {
    reasonsEl.innerHTML = reasons.length
      ? reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")
      : "<li>No difficulty reasons available.</li>";
  }

  const answer = document.getElementById("result-answer");
  if (answer) answer.textContent = data.answer;
}

async function dispatchRouteRequest(payload) {
  const errEl = document.getElementById("route-error");
  if (errEl) errEl.hidden = true;
  const blocked = document.getElementById("route-blocked");
  if (blocked) blocked.hidden = true;

  setLoading(true);
  try {
    const data = await apiPost("/route", payload);

    if (data.status === "budget_warning") {
      setLoading(false);
      pendingBudgetWarningPayload = {
        ...payload,
        force_run: false,
      };
      const estEl = document.getElementById("modalEstCost");
      const remEl = document.getElementById("modalRemBudget");
      if (estEl) estEl.textContent = formatDollars(data.estimated_cost);
      if (remEl) remEl.textContent = formatDollars(data.remaining_budget);
      openBudgetWarningModal();
      return;
    }

    closeBudgetWarningModal();
    showRouteResult(data);
    await Promise.all([loadBudget(), loadMetrics(), loadLogs()]);
  } catch (err) {
    if (errEl) {
      errEl.textContent = err.message || "Failed to route prompt";
      errEl.hidden = false;
    }
    const result = document.getElementById("route-result");
    if (result) result.hidden = true;
  } finally {
    setLoading(false);
  }
}

function openBudgetConfirmModal(limit) {
  pendingBudgetLimit = limit;
  const label = document.getElementById("confirmNewLimit");
  if (label) label.textContent = formatDollars(limit);
  const modal = document.getElementById("budgetConfirmModal");
  if (modal) modal.style.display = "flex";
}

function closeBudgetConfirmModal() {
  pendingBudgetLimit = null;
  const modal = document.getElementById("budgetConfirmModal");
  if (modal) modal.style.display = "none";
}

function requestBudgetLimitChange() {
  const input = document.getElementById("budgetLimitInput");
  const msg = document.getElementById("budgetLimitMessage");
  if (!input) return;

  const limit = Number(input.value);

  if (msg) {
    msg.style.display = "block";
    msg.style.color = "#f87171";
  }

  if (!Number.isFinite(limit) || limit <= 0) {
    if (msg) msg.textContent = "Enter a finite budget limit greater than $0.";
    return;
  }

  if (msg) msg.style.display = "none";
  openBudgetConfirmModal(limit);
}

async function confirmAndSaveBudgetLimit() {
  const input = document.getElementById("budgetLimitInput");
  const msg = document.getElementById("budgetLimitMessage");
  const btn = document.getElementById("updateLimitBtn");
  const confirmBtn = document.getElementById("confirmBudgetConfirmBtn");
  const limit = pendingBudgetLimit;

  if (!Number.isFinite(limit) || limit <= 0) {
    closeBudgetConfirmModal();
    return;
  }

  closeBudgetConfirmModal();

  if (btn) {
    btn.disabled = true;
    btn.textContent = "Saving...";
  }
  if (confirmBtn) confirmBtn.disabled = true;

  try {
    const payload = { limit, reset_usage: true };
    let data;
    try {
      data = await apiPatch("/api/budget/limit", payload);
    } catch (patchErr) {
      // Fallback if PATCH is blocked by the browser/proxy.
      data = await apiPostJson("/api/budget/limit", payload);
    }

    if (msg) {
      msg.style.display = "block";
      msg.style.color = "#34d399";
      msg.textContent = `Budget set to ${formatDollars(data.monthly_budget)}. History cleared — spend is $0.00.`;
    }
    if (input) input.value = Number(data.monthly_budget).toFixed(2);

    const resultCard = document.getElementById("route-result");
    if (resultCard) resultCard.hidden = true;

    await refreshAll();

    if (btn) btn.textContent = "Saved!";
    setTimeout(() => {
      if (btn) {
        btn.textContent = "Save Budget Limit";
        btn.disabled = false;
      }
    }, 1500);
  } catch (err) {
    if (btn) {
      btn.textContent = "Save Budget Limit";
      btn.disabled = false;
    }
    if (msg) {
      msg.style.display = "block";
      msg.style.color = "#f87171";
      msg.textContent = err.message || "Failed to update budget limit";
    }
  } finally {
    if (confirmBtn) confirmBtn.disabled = false;
  }
}

async function refreshAll() {
  await Promise.all([loadHealth(), loadBudget(), loadMetrics(), loadLogs()]);
}

function updatePromptCount() {
  const prompt = document.getElementById("prompt");
  const counter = document.getElementById("prompt-count");
  if (!prompt || !counter) return;
  counter.textContent = `${prompt.value.length} / ${MAX_PROMPT_CHARS} chars`;
}

document.getElementById("route-form")?.addEventListener("submit", (e) => {
  e.preventDefault();
  const prompt = document.getElementById("prompt")?.value.trim();
  if (prompt) {
    dispatchRouteRequest({ prompt, force_run: false });
  }
});

document.getElementById("prompt")?.addEventListener("input", updatePromptCount);

document.getElementById("clear-btn")?.addEventListener("click", () => {
  const prompt = document.getElementById("prompt");
  if (prompt) prompt.value = "";
  updatePromptCount();
  const result = document.getElementById("route-result");
  if (result) result.hidden = true;
  const errEl = document.getElementById("route-error");
  if (errEl) errEl.hidden = true;
  const blocked = document.getElementById("route-blocked");
  if (blocked) blocked.hidden = true;
  closeBudgetWarningModal();
});

document.getElementById("refresh-all")?.addEventListener("click", refreshAll);

document.getElementById("updateLimitBtn")?.addEventListener("click", (e) => {
  e.preventDefault();
  requestBudgetLimitChange();
});

document.getElementById("confirmBudgetCancelBtn")?.addEventListener("click", () => {
  closeBudgetConfirmModal();
});

document.getElementById("confirmBudgetConfirmBtn")?.addEventListener("click", async () => {
  await confirmAndSaveBudgetLimit();
});

document.getElementById("budgetConfirmModal")?.addEventListener("click", (e) => {
  if (e.target?.id === "budgetConfirmModal") closeBudgetConfirmModal();
});

document.getElementById("modalCancelBtn")?.addEventListener("click", () => {
  closeBudgetWarningModal();
  document.getElementById("prompt")?.focus();
});

document.getElementById("modalProceedBtn")?.addEventListener("click", async () => {
  if (!pendingBudgetWarningPayload) return;

  const forcedPayload = {
    ...pendingBudgetWarningPayload,
    force_run: true,
  };

  pendingBudgetWarningPayload = null;
  const modal = document.getElementById("budgetWarningModal");
  if (modal) modal.style.display = "none";

  await dispatchRouteRequest(forcedPayload);
});

document.getElementById("budgetWarningModal")?.addEventListener("click", (e) => {
  if (e.target?.id === "budgetWarningModal") {
    closeBudgetWarningModal();
    document.getElementById("prompt")?.focus();
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  const confirmModal = document.getElementById("budgetConfirmModal");
  if (confirmModal && confirmModal.style.display === "flex") {
    closeBudgetConfirmModal();
    return;
  }
  const modal = document.getElementById("budgetWarningModal");
  if (modal && modal.style.display === "flex") {
    closeBudgetWarningModal();
    document.getElementById("prompt")?.focus();
  }
});

document.querySelectorAll("[data-refresh]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.refresh;
    if (target === "budget") loadBudget();
    if (target === "metrics") loadMetrics();
    if (target === "logs") loadLogs();
  });
});

updatePromptCount();
refreshAll();
