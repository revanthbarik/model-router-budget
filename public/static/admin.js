let pendingBudgetLimit = null;

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

  const limitEl = document.getElementById("admin-monthly-limit");
  if (limitEl) limitEl.textContent = formatDollars(data.monthly_budget);

  const usedEl = document.getElementById("admin-billable-used");
  if (usedEl) usedEl.textContent = formatDollars(data.monthly_billable_used);

  const remEl = document.getElementById("admin-remaining");
  if (remEl) remEl.textContent = formatDollars(data.remaining_budget);

  const statusEl = document.getElementById("admin-status");
  if (statusEl) statusEl.textContent = data.status;

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

  const limitInput = document.getElementById("budgetLimitInput");
  if (limitInput && document.activeElement !== limitInput) {
    limitInput.value = Number(data.monthly_budget).toFixed(2);
  }
}

async function refreshAll() {
  await Promise.all([loadHealth(), loadBudget()]);
}

function openBudgetConfirmModal(limit) {
  pendingBudgetLimit = limit;
  const label = document.getElementById("confirmNewLimit");
  if (label) label.textContent = formatDollars(limit);
  const modal = document.getElementById("budgetConfirmModal");
  if (modal) {
    modal.style.display = "flex";
    modal.classList.add("is-open");
  }
}

function closeBudgetConfirmModal() {
  pendingBudgetLimit = null;
  const modal = document.getElementById("budgetConfirmModal");
  if (modal) {
    modal.style.display = "none";
    modal.classList.remove("is-open");
  }
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
    } catch {
      data = await apiPostJson("/api/budget/limit", payload);
    }

    if (msg) {
      msg.style.display = "block";
      msg.style.color = "#34d399";
      msg.textContent = `Budget set to ${formatDollars(data.monthly_budget)}. History cleared — spend is $0.00.`;
    }
    if (input) input.value = Number(data.monthly_budget).toFixed(2);
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

document.getElementById("refresh-all")?.addEventListener("click", refreshAll);
document.getElementById("updateLimitBtn")?.addEventListener("click", (e) => {
  e.preventDefault();
  requestBudgetLimitChange();
});
document.getElementById("confirmBudgetCancelBtn")?.addEventListener("click", closeBudgetConfirmModal);
document.getElementById("confirmBudgetConfirmBtn")?.addEventListener("click", confirmAndSaveBudgetLimit);
document.getElementById("budgetConfirmModal")?.addEventListener("click", (e) => {
  if (e.target?.id === "budgetConfirmModal") closeBudgetConfirmModal();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeBudgetConfirmModal();
});
document.querySelectorAll("[data-refresh]").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (btn.dataset.refresh === "budget") loadBudget();
  });
});

refreshAll();
