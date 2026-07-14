let pendingBudgetWarningPayload = null;
let chatLogsCache = [];
let activeLogId = null;

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
  if (modal) {
    modal.style.display = "flex";
    modal.classList.add("is-open");
  }
}

function closeBudgetWarningModal() {
  pendingBudgetWarningPayload = null;
  const modal = document.getElementById("budgetWarningModal");
  if (modal) {
    modal.style.display = "none";
    modal.classList.remove("is-open");
  }
}

function updatePromptCount() {
  const prompt = document.getElementById("prompt");
  const counter = document.getElementById("prompt-count");
  if (!prompt || !counter) return;
  counter.textContent = `${prompt.value.length} / ${MAX_PROMPT_CHARS} chars`;
}

async function loadChatBudget() {
  const data = await apiGet("/budget");
  const el = document.getElementById("chat-budget-remaining");
  if (el) el.textContent = formatDollars(data.remaining_budget);
}

function renderHistoryList(logs) {
  const list = document.getElementById("chat-history-list");
  if (!list) return;

  if (!logs.length) {
    list.innerHTML = '<p class="muted">No chats yet.</p>';
    return;
  }

  list.innerHTML = logs
    .map((log) => {
      const active = activeLogId === log.id ? "active" : "";
      return `
        <button type="button" class="chat-history-item ${active}" data-log-id="${log.id}">
          <span class="chat-history-title">${escapeHtml(truncate(log.prompt, 48))}</span>
          <span class="chat-history-meta">
            ${formatProvider(log.provider)} · ${escapeHtml(log.selected_model)} · ${formatDollars(log.billable_cost ?? 0)}
          </span>
        </button>
      `;
    })
    .join("");

  list.querySelectorAll("[data-log-id]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = Number(btn.dataset.logId);
      const log = chatLogsCache.find((item) => item.id === id);
      if (log) showLogInThread(log);
    });
  });
}

function hideEmptyState() {
  const empty = document.getElementById("chat-empty");
  if (empty) empty.hidden = true;
}

function clearThread() {
  const thread = document.getElementById("chat-thread");
  if (!thread) return;
  thread.innerHTML = `
    <div class="chat-empty" id="chat-empty">
      <div class="chat-empty-mark" aria-hidden="true">◇</div>
      <h2>Start a routed conversation</h2>
      <p>Your prompt is scored for difficulty, budget-checked, then sent to the best model tier.</p>
    </div>
  `;
  activeLogId = null;
  renderHistoryList(chatLogsCache);
}

function appendMessage(role, text, metaHtml = "") {
  hideEmptyState();
  const thread = document.getElementById("chat-thread");
  if (!thread) return;

  const bubble = document.createElement("article");
  bubble.className = `chat-bubble chat-${role}`;
  bubble.innerHTML = `
    <div class="chat-bubble-role">${role === "user" ? "You" : "Assistant"}</div>
    <div class="chat-bubble-body">${escapeHtml(text)}</div>
    ${metaHtml ? `<div class="chat-bubble-meta">${metaHtml}</div>` : ""}
  `;
  thread.appendChild(bubble);
  thread.scrollTop = thread.scrollHeight;
}

function showLogInThread(log) {
  activeLogId = log.id;
  renderHistoryList(chatLogsCache);

  const thread = document.getElementById("chat-thread");
  if (!thread) return;
  thread.innerHTML = "";
  hideEmptyState();

  appendMessage("user", log.prompt || "");
  const meta = [
    `<span class="${difficultyClass(log.difficulty)}">${escapeHtml(log.difficulty)}</span>`,
    escapeHtml(log.selected_model),
    formatMode(log.llm_mode),
    formatDollars(log.billable_cost ?? 0),
    `${log.latency_ms} ms`,
    escapeHtml(log.budget_status || ""),
  ].join(" · ");
  appendMessage("assistant", log.answer || "(No answer)", meta);
}

function showRouteResultInChat(prompt, data) {
  appendMessage("user", prompt);
  const meta = [
    `<span class="${difficultyClass(data.difficulty)}">${escapeHtml(data.difficulty)}</span>`,
    escapeHtml(data.selected_model),
    formatMode(data.llm_mode),
    formatDollars(data.actual_cost ?? data.billable_cost ?? 0),
    `${data.latency_ms} ms`,
    escapeHtml(data.budget_status || ""),
  ].join(" · ");
  appendMessage("assistant", data.answer || "", meta);
}

async function loadChatHistory() {
  const logs = await apiGet("/logs");
  chatLogsCache = logs;
  renderHistoryList(logs);
}

async function dispatchRouteRequest(payload) {
  const errEl = document.getElementById("route-error");
  if (errEl) errEl.hidden = true;

  setLoading(true);
  try {
    const data = await apiPost("/route", payload);

    if (data.status === "budget_warning") {
      setLoading(false);
      pendingBudgetWarningPayload = { ...payload, force_run: false };
      const estEl = document.getElementById("modalEstCost");
      const remEl = document.getElementById("modalRemBudget");
      if (estEl) estEl.textContent = formatDollars(data.estimated_cost);
      if (remEl) remEl.textContent = formatDollars(data.remaining_budget);
      openBudgetWarningModal();
      return;
    }

    closeBudgetWarningModal();
    showRouteResultInChat(payload.prompt, data);
    await Promise.all([loadChatBudget(), loadChatHistory()]);
  } catch (err) {
    if (errEl) {
      errEl.textContent = err.message || "Failed to route prompt";
      errEl.hidden = false;
    }
  } finally {
    setLoading(false);
  }
}

document.getElementById("route-form")?.addEventListener("submit", (e) => {
  e.preventDefault();
  const prompt = document.getElementById("prompt")?.value.trim();
  if (!prompt) return;
  dispatchRouteRequest({ prompt, force_run: false });
  const input = document.getElementById("prompt");
  if (input) {
    input.value = "";
    updatePromptCount();
  }
});

document.getElementById("prompt")?.addEventListener("input", updatePromptCount);

document.getElementById("clear-btn")?.addEventListener("click", () => {
  const prompt = document.getElementById("prompt");
  if (prompt) prompt.value = "";
  updatePromptCount();
  const errEl = document.getElementById("route-error");
  if (errEl) errEl.hidden = true;
  closeBudgetWarningModal();
});

document.getElementById("new-chat-btn")?.addEventListener("click", clearThread);
document.getElementById("refresh-history")?.addEventListener("click", loadChatHistory);

document.getElementById("modalCancelBtn")?.addEventListener("click", () => {
  closeBudgetWarningModal();
  document.getElementById("prompt")?.focus();
});

document.getElementById("modalProceedBtn")?.addEventListener("click", async () => {
  if (!pendingBudgetWarningPayload) return;
  const forcedPayload = { ...pendingBudgetWarningPayload, force_run: true };
  pendingBudgetWarningPayload = null;
  closeBudgetWarningModal();
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
  const modal = document.getElementById("budgetWarningModal");
  if (modal && modal.style.display === "flex") {
    closeBudgetWarningModal();
    document.getElementById("prompt")?.focus();
  }
});

updatePromptCount();
Promise.all([loadHealth(), loadChatBudget(), loadChatHistory()]);
