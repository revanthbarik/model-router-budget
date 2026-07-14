async function loadBudget() {
  const data = await apiGet("/budget");
  const usedPct =
    data.monthly_budget > 0
      ? (data.monthly_billable_used / data.monthly_budget) * 100
      : 0;
  const barPct = Math.min(100, Math.max(0, usedPct));

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
    budgetPill.className = statusPillClass(data.status);
    budgetPill.textContent =
      data.status === "healthy"
        ? "Budget healthy"
        : data.status === "warning"
        ? "Budget getting tight"
        : data.status === "overage"
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
}

async function loadMetrics() {
  const data = await apiGet("/metrics");

  const heroRequests = document.getElementById("hero-total-requests");
  if (heroRequests) heroRequests.textContent = data.total_requests;

  const heroCost = document.getElementById("hero-total-cost");
  if (heroCost) heroCost.textContent = formatDollars(data.total_cost);

  const heroLatency = document.getElementById("hero-average-latency");
  if (heroLatency) heroLatency.textContent = `${data.average_latency_ms} ms`;

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
  if (!tbody) return;

  if (!logs.length) {
    tbody.innerHTML =
      '<tr><td colspan="8" class="empty">No logs yet — send a prompt from Chat</td></tr>';
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
      <td>${formatDollars(log.billable_cost ?? log.estimated_cost)}</td>
      <td class="status-${log.budget_status}">${log.budget_status}</td>
    </tr>
  `
    )
    .join("");
}

async function refreshAll() {
  await Promise.all([loadHealth(), loadBudget(), loadMetrics(), loadLogs()]);
}

document.getElementById("refresh-all")?.addEventListener("click", refreshAll);
document.querySelectorAll("[data-refresh]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.refresh;
    if (target === "budget") loadBudget();
    if (target === "metrics") loadMetrics();
    if (target === "logs") loadLogs();
  });
});

refreshAll();
