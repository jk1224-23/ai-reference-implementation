const form = document.getElementById("chat-form");
const transcriptEl = document.getElementById("transcript");
const tabs = document.querySelectorAll(".tab");
const tabContents = {
  intent: document.getElementById("tab-intent"),
  skill: document.getElementById("tab-skill"),
  policy: document.getElementById("tab-policy"),
  tools: document.getElementById("tab-tools"),
  timeline: document.getElementById("tab-timeline"),
  audit: document.getElementById("tab-audit"),
};

const chipCorrelation = document.getElementById("chip-correlation");
const chipSkill = document.getElementById("chip-skill");
const chipRisk = document.getElementById("chip-risk");
const chipDecision = document.getElementById("chip-decision");
const chipMode = document.getElementById("chip-mode");

const userRoleEl = document.getElementById("userRole");
const userIdEl = document.getElementById("userId");
const messageEl = document.getElementById("message");

const approvalPanelEl = document.getElementById("approval-panel");
const approvalTextEl = document.getElementById("approval-text");
const approveBtn = document.getElementById("approve-btn");
const denyBtn = document.getElementById("deny-btn");

const toggleKbOnlyEl = document.getElementById("toggle-kb-only");
const toggleHitlFirstEl = document.getElementById("toggle-hitl-first");
const toggleCircuitClaimsEl = document.getElementById("toggle-circuit-claims");
const toggleCircuitCaseEl = document.getElementById("toggle-circuit-case");
const applyControlsBtn = document.getElementById("apply-controls-btn");
const refreshControlsBtn = document.getElementById("refresh-controls-btn");

const policyCardEl = document.getElementById("policy-card");
const exportTraceBtn = document.getElementById("export-trace-btn");

let latestPayload = null;
let lastRequest = null;
let pendingApproval = null;

function setChips(payload) {
  chipCorrelation.textContent = `Correlation: ${payload?.audit?.correlationId ?? "—"}`;
  chipSkill.textContent = `Skill: ${payload?.skill?.skillId ?? "—"}`;
  chipRisk.textContent = `Risk: ${payload?.intent?.riskTier ?? "—"}`;
  chipDecision.textContent = `Decision: ${payload?.policy?.decision ?? "—"}`;
  const mode = payload?.policy?.hitlRequired
    ? "HITL"
    : payload?.policy?.decision === "DEGRADED_KB_ONLY"
    ? "KB-only"
    : "Normal";
  chipMode.textContent = `Mode: ${mode}`;
}

function setTabs(payload) {
  tabContents.intent.textContent = JSON.stringify(payload.intent || {}, null, 2);
  tabContents.skill.textContent = JSON.stringify(payload.skill || {}, null, 2);
  tabContents.policy.textContent = JSON.stringify(
    { policy: payload.policy || {}, budgets: payload.budgets || {} },
    null,
    2
  );
  tabContents.tools.textContent = JSON.stringify(payload.toolCalls || [], null, 2);
  tabContents.audit.textContent = JSON.stringify(payload.audit || {}, null, 2);

  const timeline = payload.timeline || [];
  if (!timeline.length) {
    tabContents.timeline.textContent = "(no timeline)";
    return;
  }
  tabContents.timeline.textContent = timeline
    .map((step) => `${step.elapsedMs}ms | ${step.status.padEnd(7)} | ${step.step} | ${step.detail}`)
    .join("\n");
}

function renderDecisionCard(payload) {
  const card = payload?.decisionSupport;
  if (!card) {
    policyCardEl.textContent = "No decision yet.";
    return;
  }
  const why = (card.why || []).slice(0, 5).join(", ") || "No reasons";
  policyCardEl.textContent = [
    `Confidence: ${Number(card.confidence || 0).toFixed(2)}`,
    `Risk Tier: ${card.riskTier || "—"}`,
    `Decision: ${card.decision || "—"}`,
    `Escalated: ${card.escalated ? "Yes" : "No"}`,
    `Why: ${why}`,
  ].join("\n");
}

function addTranscriptEntry(role, text) {
  const div = document.createElement("div");
  div.className = "bubble " + (role === "user" ? "user" : "bot");
  div.textContent = text;
  transcriptEl.prepend(div);
}

function renderApprovalPanel() {
  if (!pendingApproval) {
    approvalPanelEl.classList.add("hidden");
    approvalTextEl.textContent = "No pending approvals.";
    approveBtn.disabled = true;
    denyBtn.disabled = true;
    return;
  }
  approvalPanelEl.classList.remove("hidden");
  approvalTextEl.textContent = `Pending approval ${pendingApproval.approvalId} for "${pendingApproval.message}"`;
  approveBtn.disabled = false;
  denyBtn.disabled = false;
}

async function fetchRuntimeState() {
  const res = await fetch("/runtime/state");
  const data = await res.json();
  const switches = data.killSwitches || {};
  const breakers = switches.tool_circuit_breakers || {};
  toggleKbOnlyEl.checked = Boolean(switches.kb_only_mode);
  toggleHitlFirstEl.checked = Boolean(switches.hitl_first_mode);
  toggleCircuitClaimsEl.checked = Boolean(breakers["claims.read.v1"]);
  toggleCircuitCaseEl.checked = Boolean(breakers["case.create.v1"]);
}

async function applyRuntimeControls() {
  const breakers = [];
  if (toggleCircuitClaimsEl.checked) breakers.push("claims.read.v1");
  if (toggleCircuitCaseEl.checked) breakers.push("case.create.v1");
  const body = {
    kbOnlyMode: toggleKbOnlyEl.checked,
    hitlFirstMode: toggleHitlFirstEl.checked,
    toolCircuitBreakers: breakers,
  };
  const res = await fetch("/runtime/state", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`Failed to update runtime controls (${res.status})`);
  }
  await fetchRuntimeState();
}

async function submitApproval(decision) {
  if (!pendingApproval) return;
  const res = await fetch("/runtime/approval", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      approvalId: pendingApproval.approvalId,
      decision,
      approver: "demo-approver",
    }),
  });
  if (!res.ok) {
    throw new Error(`Failed to submit approval (${res.status})`);
  }
}

async function sendRequest(requestPayload) {
  const res = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestPayload),
  });
  if (!res.ok) {
    throw new Error(`Server returned ${res.status}`);
  }
  return res.json();
}

async function sendMessage(event) {
  event.preventDefault();
  const message = messageEl.value.trim();
  if (!message) return;

  const requestPayload = {
    message,
    channel: document.getElementById("channel").value,
    userRole: userRoleEl.value,
    userId: userIdEl.value,
  };
  lastRequest = { ...requestPayload };
  addTranscriptEntry("user", message);

  try {
    const data = await sendRequest(requestPayload);
    latestPayload = data;
    addTranscriptEntry("bot", data.response?.message || "(no message)");
    setChips(data);
    setTabs(data);
    renderDecisionCard(data);

    const approvalId = data?.policy?.approvalId;
    const approvalPending = data?.policy?.approvalStatus === "PENDING";
    if (approvalPending && approvalId) {
      pendingApproval = { approvalId, message, requestPayload: lastRequest };
    } else {
      pendingApproval = null;
    }
    renderApprovalPanel();
  } catch (err) {
    addTranscriptEntry("bot", `Error: ${err.message}`);
  }
}

async function approvePending() {
  if (!pendingApproval || !lastRequest) return;
  try {
    await submitApproval("APPROVED");
    addTranscriptEntry("bot", `Approval ${pendingApproval.approvalId} approved. Re-running action...`);
    const data = await sendRequest({ ...pendingApproval.requestPayload, approvalId: pendingApproval.approvalId });
    latestPayload = data;
    addTranscriptEntry("bot", data.response?.message || "(no message)");
    setChips(data);
    setTabs(data);
    renderDecisionCard(data);
    pendingApproval = null;
    renderApprovalPanel();
  } catch (err) {
    addTranscriptEntry("bot", `Approval error: ${err.message}`);
  }
}

async function denyPending() {
  if (!pendingApproval) return;
  try {
    await submitApproval("REJECTED");
    addTranscriptEntry("bot", `Approval ${pendingApproval.approvalId} denied.`);
    pendingApproval = null;
    renderApprovalPanel();
  } catch (err) {
    addTranscriptEntry("bot", `Approval error: ${err.message}`);
  }
}

function exportLatestTrace() {
  if (!latestPayload) {
    addTranscriptEntry("bot", "No trace available yet.");
    return;
  }
  const correlationId = latestPayload?.audit?.correlationId || "trace";
  const blob = new Blob([JSON.stringify(latestPayload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${correlationId}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

form.addEventListener("submit", sendMessage);
approveBtn.addEventListener("click", approvePending);
denyBtn.addEventListener("click", denyPending);
applyControlsBtn.addEventListener("click", async () => {
  try {
    await applyRuntimeControls();
    addTranscriptEntry("bot", "Runtime controls updated.");
  } catch (err) {
    addTranscriptEntry("bot", `Runtime controls error: ${err.message}`);
  }
});
refreshControlsBtn.addEventListener("click", async () => {
  try {
    await fetchRuntimeState();
    addTranscriptEntry("bot", "Runtime controls refreshed.");
  } catch (err) {
    addTranscriptEntry("bot", `Runtime controls error: ${err.message}`);
  }
});
exportTraceBtn.addEventListener("click", exportLatestTrace);

userIdEl.addEventListener("change", () => {
  userRoleEl.value = userIdEl.value === "demo-agent-1" ? "AGENT" : "MEMBER";
});

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const target = tab.dataset.tab;
    Object.entries(tabContents).forEach(([key, el]) => {
      if (key === target) {
        el.classList.remove("hidden");
      } else {
        el.classList.add("hidden");
      }
    });
  });
});

fetchRuntimeState().catch((err) => {
  addTranscriptEntry("bot", `Runtime controls unavailable: ${err.message}`);
});
renderApprovalPanel();
