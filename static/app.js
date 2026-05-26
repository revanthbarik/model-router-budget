const API = "";
const MAX_PROMPT_CHARS = 4000;

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

function formatMoney(value) {
  return `$${Number(value).toFixed(6)}`;
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
  if (status === "blocked") return "badge badge-error";
  return "badge badge-pending";
}

function badgeClassForMode(mode) {
  if (mode === "deepseek") return "badge badge-live";
  if (mode === "openai") return "badge badge-live";
  if (mode === "fake") return "badge badge-fake";
  if (mode === "fallback_fake") return "badge badge-fake";
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
  if (status === "exceeded") return "status-pill status-blocked";
  return "status-pill status-pending";
}

function setHealthBadge(ok, message) {
  const el = document.getElementById("health-badge");
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

async function loadBudget() {
  const data = await apiGet("/budget");
  const usedPct = data.monthly_budget > 0
    ? Math.min(100, (data.monthly_billable_used / data.monthly_budget) * 100)
    : 0;
  const budgetHealth = data.status;

  const bar = document.getElementById("budget-used-bar");
  bar.style.width = `${usedPct}%`;
  bar.classList.toggle("over", usedPct >= 90);

  document.getElementById("budget-caption").textContent =
    `${formatMoney(data.monthly_billable_used)} of ${formatMoney(data.monthly_budget)} billable this month (${usedPct.toFixed(1)}%)`;
  document.getElementById("hero-budget-remaining").textContent = formatMoney(
    data.remaining_budget
  );

  const budgetPill = document.getElementById("budget-status-pill");
  budgetPill.className = statusPillClass(budgetHealth);
  budgetPill.textContent =
    budgetHealth === "healthy"
      ? "Budget healthy"
      : budgetHealth === "warning"
      ? "Budget getting tight"
      : "Budget exceeded";

  document.getElementById("budget-stats").innerHTML = `
    <div><dt>Current month</dt><dd>${data.current_month}</dd></div>
    <div><dt>Monthly budget</dt><dd>${formatMoney(data.monthly_budget)}</dd></div>
    <div><dt>Billable used</dt><dd>${formatMoney(data.monthly_billable_used)}</dd></div>
    <div><dt>Estimated total</dt><dd>${formatMoney(data.monthly_estimated_cost)}</dd></div>
    <div><dt>Remaining</dt><dd>${formatMoney(data.remaining_budget)}</dd></div>
    <div><dt>Status</dt><dd>${data.status}</dd></div>
  `;
}

async function loadMetrics() {
  const data = await apiGet("/metrics");

  document.getElementById("hero-total-requests").textContent =
    data.total_requests;
  document.getElementById("hero-total-cost").textContent = formatMoney(
    data.total_cost
  );
  document.getElementById("hero-average-latency").textContent =
    `${data.average_latency_ms} ms`;

  document.getElementById("metrics-stats").innerHTML = `
    <div><dt>Lifetime requests</dt><dd>${data.total_requests}</dd></div>
    <div><dt>Lifetime billable</dt><dd>${formatMoney(data.total_cost)}</dd></div>
    <div><dt>Avg latency</dt><dd>${data.average_latency_ms} ms</dd></div>
    <div><dt>Current month</dt><dd>${data.current_month}</dd></div>
  `;

  document.getElementById("metrics-mini-stats").innerHTML = `
    <div class="mini-stat"><span>Monthly requests</span><strong>${data.monthly_requests}</strong></div>
    <div class="mini-stat"><span>Monthly billable</span><strong>${formatMoney(data.monthly_billable_cost)}</strong></div>
    <div class="mini-stat"><span>Monthly estimated</span><strong>${formatMoney(data.monthly_estimated_cost)}</strong></div>
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

  const modelItems = Object.entries(data.model_usage || {})
    .map(([k, v]) => `<li><span>${k}</span><span>${v}</span></li>`)
    .join("");
  const diffItems = Object.entries(data.difficulty_usage || {})
    .map(([k, v]) => `<li><span>${k}</span><span>${v}</span></li>`)
    .join("");

  document.getElementById("metrics-breakdown").innerHTML = `
    <h4>By model</h4>
    <ul>${modelItems || "<li><span>—</span><span>0</span></li>"}</ul>
    <h4>By difficulty</h4>
    <ul>${diffItems || "<li><span>—</span><span>0</span></li>"}</ul>
  `;
}

async function loadLogs() {
  const logs = await apiGet("/logs");
  const tbody = document.getElementById("logs-body");

  if (!logs.length) {
    tbody.innerHTML =
      '<tr><td colspan="8" class="empty">No logs yet — route a prompt first</td></tr>';
    document.getElementById("history-list").innerHTML =
      '<p class="muted">No prompt history yet.</p>';
    return;
  }

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
      <td>${formatMoney(log.estimated_cost)}</td>
      <td class="status-${log.budget_status}">${log.budget_status}</td>
    </tr>
  `
    )
    .join("");

  document.getElementById("history-list").innerHTML = logs
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
          <p><strong>Cost:</strong> ${formatMoney(log.estimated_cost)}</p>
          <p><strong>Latency:</strong> ${log.latency_ms} ms</p>
          <p><strong>Budget status:</strong> ${escapeHtml(log.budget_status)}</p>
          <p><strong>Timestamp:</strong> ${escapeHtml(log.created_at || "")}</p>
        </div>
      </details>
    `
    )
    .join("");
}

function escapeHtml(str) {
  const el = document.createElement("div");
  el.textContent = str;
  return el.innerHTML;
}

function truncate(str, len) {
  return str.length > len ? `${str.slice(0, len)}…` : str;
}

function showRouteResult(data) {
  const card = document.getElementById("route-result");
  card.hidden = false;
  document.getElementById("route-blocked").hidden =
    data.budget_status !== "blocked";

  const diff = document.getElementById("result-difficulty");
  diff.textContent = data.difficulty.toUpperCase();
  diff.className = data.difficulty ? difficultyClass(data.difficulty) : "";

  document.getElementById("result-difficulty-score").textContent =
    `Score: ${data.difficulty_score}`;
  document.getElementById("result-tier").textContent = data.selected_tier;
  document.getElementById("result-model").textContent = data.selected_model;
  document.getElementById("result-cost").textContent = formatMoney(
    data.estimated_cost
  );
  document.getElementById("result-latency").textContent =
    `${data.latency_ms} ms`;
  document.getElementById("result-total-tokens").textContent =
    `${data.total_tokens}`;
  document.getElementById("result-token-breakdown").textContent =
    `In: ${data.input_tokens} · Out: ${data.output_tokens}`;
  document.getElementById("result-budget-status").textContent =
    data.budget_status.toUpperCase();
  document.getElementById("result-budget-status").className =
    badgeClassForBudget(data.budget_status);
  document.getElementById("result-provider").textContent = formatProvider(
    data.provider
  );
  document.getElementById("result-provider").className = badgeClassForProvider(
    data.provider
  );
  document.getElementById("result-llm-mode").textContent = formatMode(
    data.llm_mode
  );
  document.getElementById("result-llm-mode").className = badgeClassForMode(
    data.llm_mode
  );

  const reasons = data.difficulty_reasons || [];
  document.getElementById("result-reasons").innerHTML = reasons.length
    ? reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")
    : "<li>No difficulty reasons available.</li>";

  document.getElementById("result-answer").textContent = data.answer;
}

function setLoading(loading) {
  const btn = document.getElementById("route-btn");
  const label = btn.querySelector(".btn-label");
  const spinner = btn.querySelector(".btn-spinner");
  btn.disabled = loading;
  label.hidden = loading;
  spinner.hidden = !loading;
}

async function routePrompt(prompt) {
  const errEl = document.getElementById("route-error");
  errEl.hidden = true;
  document.getElementById("route-blocked").hidden = true;

  setLoading(true);
  try {
    const data = await apiPost("/route", { prompt });
    showRouteResult(data);
    await Promise.all([loadBudget(), loadMetrics(), loadLogs()]);
  } catch (err) {
    errEl.textContent = err.message || "Failed to route prompt";
    errEl.hidden = false;
    document.getElementById("route-result").hidden = true;
  } finally {
    setLoading(false);
  }
}

async function refreshAll() {
  await Promise.all([loadHealth(), loadBudget(), loadMetrics(), loadLogs()]);
}

function updatePromptCount() {
  const prompt = document.getElementById("prompt").value;
  document.getElementById("prompt-count").textContent =
    `${prompt.length} / ${MAX_PROMPT_CHARS} chars`;
}

document.getElementById("route-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const prompt = document.getElementById("prompt").value.trim();
  if (prompt) routePrompt(prompt);
});

document.getElementById("prompt").addEventListener("input", updatePromptCount);

document.getElementById("clear-btn").addEventListener("click", () => {
  document.getElementById("prompt").value = "";
  updatePromptCount();
  document.getElementById("route-result").hidden = true;
  document.getElementById("route-error").hidden = true;
  document.getElementById("route-blocked").hidden = true;
});

document.getElementById("refresh-all").addEventListener("click", refreshAll);

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
