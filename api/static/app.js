const els = {
  health: document.querySelector("#health"),
  syncStatus: document.querySelector("#syncStatus"),
  syncText: document.querySelector("#syncText"),
  project: document.querySelector("#project"),
  trade: document.querySelector("#trade"),
  aiChat: document.querySelector("#aiChat"),
  aiPrompt: document.querySelector("#aiPrompt"),
  aiSave: document.querySelector("#aiSave"),
  aiRefineBtn: document.querySelector("#aiRefineBtn"),
  packageName: document.querySelector("#packageName"),
  region: document.querySelector("#region"),
  generateBtn: document.querySelector("#generateBtn"),
  totals: document.querySelector("#totals"),
  log: document.querySelector("#log"),
  lineItems: document.querySelector("#lineItems"),
  files: document.querySelector("#files"),
  tabs: document.querySelectorAll(".tab-btn"),
  panes: document.querySelectorAll(".tab-pane"),
  projectDocs: document.querySelector("#projectDocs"),
  agentFindings: document.querySelector("#agentFindings"),
};

const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});
const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });

let syncSocket = null;
const sessionId = Math.random().toString(36).substring(7);
let agentMessages = JSON.parse(localStorage.getItem("agentMessages") || "[]");

// --- Core Logic ---

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${detail}`);
  }
  return response.json();
}

function log(message) {
  const stamp = new Date().toLocaleTimeString();
  els.log.textContent += `\n[${stamp}] ${message}`;
  els.log.scrollTop = els.log.scrollHeight;
}

function addMessage(role, content = "", reasoning = "") {
  const div = document.createElement("div");
  div.className = `message ${role}`;

  if (reasoning) {
    const thoughtDiv = document.createElement("details");
    thoughtDiv.className = "thought-bubble";
    thoughtDiv.innerHTML = `<summary>Thinking Process</summary><div class="thought-content">${reasoning}</div>`;
    div.appendChild(thoughtDiv);
  }

  const contentSpan = document.createElement("span");
  contentSpan.className = "msg-text";
  contentSpan.textContent = content;
  div.appendChild(contentSpan);

  els.aiChat.appendChild(div);
  els.aiChat.scrollTop = els.aiChat.scrollHeight;
  return div;
}

// --- Sync & State ---

function initSync() {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  // Fixed WebSocket URL to match the router prefix without /api/v1/
  syncSocket = new WebSocket(
    `${protocol}://${window.location.host}/ws/sync/${sessionId}`,
  );

  syncSocket.onopen = () => {
    els.syncStatus.className = "status-dot ok";
    els.syncText.textContent = "Live Sync";
    log("Bolt Sync Active.");
  };

  syncSocket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === "state_update") {
      log("Remote update received.");
      applyRemoteState(message.data);
    }
  };

  syncSocket.onclose = () => {
    els.syncStatus.className = "status-dot";
    els.syncText.textContent = "Offline";
    setTimeout(initSync, 3000);
  };
}

function sendEdit(update) {
  if (syncSocket && syncSocket.readyState === WebSocket.OPEN) {
    syncSocket.send(JSON.stringify({ type: "edit", update }));
  }
}

function applyRemoteState(update) {
  if (update.project_id) {
    els.project.value = update.project_id;
    localStorage.setItem("selectedProject", update.project_id);
  }
  if (update.trade) {
    els.trade.value = update.trade;
    localStorage.setItem("selectedTrade", update.trade);
  }
  if (update.project_id || update.trade) preview();
}

// --- UI Actions ---

async function preview() {
  try {
    const data = await api("/api/v1/bids/preview", {
      method: "POST",
      body: JSON.stringify({
        project_id: els.project.value,
        trade: els.trade.value,
        region: els.region.value || null,
        run_validation: true,
      }),
    });
    renderPreview(data);
  } catch (error) {
    log(`Preview failed: ${error.message}`);
  }
}

async function aiRefine() {
  const prompt = els.aiPrompt.value.trim();
  if (!prompt) return;

  addMessage("user", prompt);
  agentMessages.push({ role: "user", content: prompt });
  saveChat();

  els.aiPrompt.value = "";
  els.aiRefineBtn.disabled = true;

  try {
    const response = await fetch("/api/v1/agent/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: agentMessages,
        project_id: els.project.value,
      }),
    });

    if (!response.ok) throw new Error(await response.text());

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let currentAiMsg = null;
    let fullContent = "";
    let fullReasoning = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const dataStr = line.substring(6).trim();
          if (dataStr === "[DONE]") break;

          try {
            const data = JSON.parse(dataStr);
            if (data.type === "thought") {
              if (!currentAiMsg) currentAiMsg = addMessage("ai");
              let thoughtBubble = currentAiMsg.querySelector(".thought-bubble");
              if (!thoughtBubble) {
                thoughtBubble = document.createElement("details");
                thoughtBubble.className = "thought-bubble";
                thoughtBubble.innerHTML = `<summary>Thinking Process</summary><div class="thought-content"></div>`;
                currentAiMsg.prepend(thoughtBubble);
              }
              const thoughtContent =
                thoughtBubble.querySelector(".thought-content");
              thoughtContent.textContent += data.delta;
              fullReasoning += data.delta;
            } else if (data.type === "content") {
              if (!currentAiMsg) currentAiMsg = addMessage("ai");
              let textSpan = currentAiMsg.querySelector(".msg-text");
              if (!textSpan) {
                textSpan = document.createElement("span");
                textSpan.className = "msg-text";
                currentAiMsg.appendChild(textSpan);
              }
              textSpan.textContent += data.delta;
              fullContent += data.delta;
            } else if (data.type === "tool_call") {
              addMessage("system", `Executing: ${data.name}...`);
            } else if (data.type === "tool_result") {
              log(`Agent used ${data.name}`);
              if (data.name === "list_source_documents")
                renderProjectDocs(data.result);
              if (data.name === "read_document_text")
                appendFinding("Research", data.result);
            }
          } catch (e) {
            // Partial JSON
          }
        }
      }
      els.aiChat.scrollTop = els.aiChat.scrollHeight;
    }

    agentMessages.push({
      role: "assistant",
      content: fullContent,
      reasoning_content: fullReasoning,
    });
    saveChat();
    preview();
  } catch (error) {
    addMessage("system", `Error: ${error.message}`);
  } finally {
    els.aiRefineBtn.disabled = false;
  }
}

function saveChat() {
  localStorage.setItem("agentMessages", JSON.stringify(agentMessages));
}

function restoreChat() {
  els.aiChat.innerHTML = "";
  agentMessages.forEach((m) =>
    addMessage(m.role, m.content, m.reasoning_content),
  );
  if (agentMessages.length === 0) {
    addMessage("system", "How can I help you refine this bid?");
  }
}

async function generate() {
  els.generateBtn.disabled = true;
  els.generateBtn.textContent = "Generating...";

  try {
    const data = await api("/api/v1/bids/generate", {
      method: "POST",
      body: JSON.stringify({
        project_id: els.project.value,
        trade: els.trade.value,
        package_name: els.packageName.value,
        region: els.region.value || null,
      }),
    });
    renderFiles(data.generated_files);
    log("Package generated successfully.");
  } catch (error) {
    log(`Generation failed: ${error.message}`);
  } finally {
    els.generateBtn.disabled = false;
    els.generateBtn.textContent = "Generate PDF Package";
  }
}

// --- Rendering ---

function renderPreview(data) {
  const t = data.totals;
  els.totals.innerHTML = `
    <div class="stat-card"><label>Total Bid</label><span>${money.format(t.total_bid_amount)}</span></div>
    <div class="stat-card"><label>Direct Cost</label><span>${money.format(t.total_direct_cost)}</span></div>
    <div class="stat-card"><label>Labor Hours</label><span>${number.format(t.total_labor_hours)}h</span></div>
    <div class="stat-card"><label>Contingency</label><span>${money.format(t.contingency)}</span></div>
  `;

  els.lineItems.innerHTML = data.line_items
    .map(
      (i) => `
    <tr>
      <td>${i.cost_code}</td>
      <td>${i.description}</td>
      <td>${number.format(i.quantity)}</td>
      <td>${i.unit}</td>
      <td>${money.format(i.total_material)}</td>
      <td>${money.format(i.total_labor)}</td>
      <td>${money.format(i.total_phase)}</td>
    </tr>
  `,
    )
    .join("");
}

function renderFiles(files) {
  els.files.innerHTML = files
    .map(
      (f) => `
    <div class="file-item">
      <a href="${f.url}" target="_blank">${f.filename}</a>
    </div>
  `,
    )
    .join("");
}

function renderProjectDocs(docsText) {
  if (!els.projectDocs) return;
  els.projectDocs.classList.remove("muted");
  els.projectDocs.innerHTML = docsText
    .split("\n")
    .slice(1)
    .map(
      (doc) => `
        <div class="file-item">${doc}</div>
    `,
    )
    .join("");
}

function appendFinding(file, text) {
  if (!els.agentFindings) return;
  els.agentFindings.classList.remove("muted");
  const div = document.createElement("div");
  div.className = "finding-item";
  div.innerHTML = `<strong>${file}</strong><pre style="font-size:0.75rem; white-space:pre-wrap;">${text.substring(0, 500)}...</pre>`;
  els.agentFindings.appendChild(div);
}

// --- Initialization ---

els.tabs.forEach((btn) => {
  btn.addEventListener("click", () => {
    els.tabs.forEach((b) => b.classList.remove("active"));
    els.panes.forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    const target = document.getElementById(`tab-${btn.dataset.tab}`);
    if (target) target.classList.add("active");
  });
});

els.project.addEventListener("change", () => {
  const val = els.project.value;
  localStorage.setItem("selectedProject", val);
  sendEdit({ project_id: val });
  preview();
  // Reset agent chat ONLY when user explicitly changes project
  // agentMessages = [];
  // localStorage.removeItem("agentMessages");
  // restoreChat();
});

els.trade.addEventListener("change", () => {
  const val = els.trade.value;
  localStorage.setItem("selectedTrade", val);
  sendEdit({ trade: val });
  preview();
});

els.aiRefineBtn.addEventListener("click", aiRefine);
els.generateBtn.addEventListener("click", generate);

// Add Clear Chat button capability
const clearBtn = document.createElement("button");
clearBtn.textContent = "Clear Chat";
clearBtn.className = "btn-sm danger";
clearBtn.style.margin = "10px 0";
clearBtn.onclick = () => {
  agentMessages = [];
  localStorage.removeItem("agentMessages");
  restoreChat();
};
els.aiChat.parentElement.insertBefore(clearBtn, els.aiChat);

async function loadOptions() {
  try {
    const [projects, trades] = await Promise.all([
      api("/api/v1/projects"),
      api("/api/v1/trades"),
    ]);

    els.project.innerHTML = projects
      .map((p) => `<option value="${p.id}">${p.name}</option>`)
      .join("");
    els.trade.innerHTML = trades
      .map((t) => `<option value="${t.id}">${t.name}</option>`)
      .join("");

    // Restore selections
    const savedProj = localStorage.getItem("selectedProject");
    const savedTrade = localStorage.getItem("selectedTrade");
    if (savedProj) els.project.value = savedProj;
    if (savedTrade) els.trade.value = savedTrade;

    els.health.textContent = "System Healthy";
    els.health.className = "status-tag ok";

    restoreChat();
    preview();
  } catch (error) {
    els.health.textContent = "Connection Error";
    log(error.message);
  }
}

loadOptions();
initSync();
