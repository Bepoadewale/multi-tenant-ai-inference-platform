const $ = (id) => document.getElementById(id);
const app = () => $("app");
const state = { overview: null, activity: [] };
const safe = (value) => String(value ?? "—").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
const short = (value, length = 8) => String(value ?? "—").slice(0, length);
const list = (data, key) => Array.isArray(data?.[key]) ? data[key] : [];
const array = (data) => Array.isArray(data) ? data : [];
const metricValue = (data) => data?.data?.result?.[0]?.value?.[1] ?? "0";
const promValue = (data) => data?.result?.[0]?.value?.[1] ?? "0";
const json = (data) => `<pre class="json">${safe(JSON.stringify(data, null, 2))}</pre>`;

function toast(message) { const node = $("toast"); node.textContent = message; node.style.display = "block"; setTimeout(() => { node.style.display = "none"; }, 5000); }
function recordActivity(label, detail = "") { state.activity.unshift({ label, detail, at: new Date().toLocaleTimeString() }); state.activity = state.activity.slice(0, 8); }
function setTitle(title) { $("page-title").textContent = title; }
function route() { const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean); return { page: parts[0] || "overview", id: parts[1] || null }; }
function link(page, id, label) { return `<a class="row-link" href="#/${page}/${encodeURIComponent(id)}">${safe(label)}</a>`; }
function actions(plan) { const next = []; if (plan.status === "PENDING_APPROVAL") next.push("approve"); if (plan.status === "APPROVED") next.push("canary"); if (plan.status === "CANARY") next.push("promote", "rollback"); return next.length ? `<div class="row-actions">${next.map((action) => `<button data-release="${action}" data-plan="${safe(plan.id)}" data-confirm="${action === "promote" || action === "rollback" ? "true" : "false"}">${safe(action)}</button>`).join("")}</div>` : "—"; }
function remediationActions(plan) { const next = []; if (plan.status === "PENDING_APPROVAL") next.push("approve"); if (plan.status === "APPROVED") next.push("execute"); return next.length ? `<div class="row-actions">${next.map((action) => `<button data-remediation="${action}" data-plan="${safe(plan.id)}" data-confirm="true">${safe(action)}</button>`).join("")}</div>` : "—"; }
function table(headers, rows) { if (!rows.length) return '<p class="empty">No recorded local evidence yet.</p>'; return `<div class="table-wrap"><table><thead><tr>${headers.map((header) => `<th>${safe(header)}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>`; }
function section(eyebrow, title, content, actionsHtml = "") { return `<section class="page"><div class="section-title"><div><p class="eyebrow">${safe(eyebrow)}</p><h2>${safe(title)}</h2></div>${actionsHtml}</div>${content}</section>`; }
function card(title, content, badge = "") { return `<article><div class="card-title"><h3>${safe(title)}</h3>${badge}</div>${content}</article>`; }
function filterControl(target, placeholder = "Filter") { return `<label class="filter"><span class="sr-only">${safe(placeholder)}</span><input data-filter-target="${safe(target)}" type="search" placeholder="${safe(placeholder)}" /></label>`; }
function keyValues(values) { return `<dl class="key-values">${Object.entries(values).map(([key, value]) => `<div><dt>${safe(key)}</dt><dd>${safe(typeof value === "object" ? JSON.stringify(value) : value)}</dd></div>`).join("")}</dl>`; }
function errorView(error) { return `<section class="page"><div class="error"><strong>Unable to load this view.</strong><br />${safe(error.message || error)}</div></section>`; }
async function fetchJson(path) { const response = await fetch(path); const body = await response.json().catch(() => ({})); if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`); return body; }
async function refresh() { try { state.overview = await fetchJson("/console/v1/overview"); $("updated").textContent = `Last refresh ${new Date().toLocaleTimeString()}`; await renderRoute(); } catch (error) { app().innerHTML = errorView(error); toast(`Console refresh failed: ${error.message}`); } }
function activeNav(page) { document.querySelectorAll("[data-nav]").forEach((node) => node.classList.toggle("active", node.dataset.nav === page || (page === "model" && node.dataset.nav === "models") || (page === "release" && node.dataset.nav === "models") || (page === "incident" && node.dataset.nav === "operations") || (page === "sandbox" && node.dataset.nav === "agents") || (page === "developer" && node.dataset.nav === "developers") || (page === "device" && node.dataset.nav === "edge"))); }

function overviewPage(data) {
  const tenants = array(data.tenants); const models = array(data.models); const plans = list(data.release_plans, "plans"); const devices = list(data.devices, "devices");
  const metrics = [[metricValue(data.requests), "Recorded requests", "Prometheus"], [metricValue(data.throttles), "Admission throttles", "Bounded policy"], [plans.filter((plan) => plan.status === "CANARY").length, "Active canaries", "MLflow + Redis"], [devices.length, "Registered devices", "Simulated hardware"]];
  const tenantRows = tenants.map((tenant) => `<tr><td>${link("tenant", tenant.id, tenant.id)}</td><td>${safe((tenant.allowed_models || []).join(", "))}</td><td>${safe(tenant.max_concurrency ?? "—")}</td></tr>`);
  const modelRows = models.map((model) => `<tr><td>${link("model", model.name, model.name)}</td><td>${safe(model.serving_mode)}</td><td>${safe(Object.keys(model.targets || {}).join(", "))}</td></tr>`);
  const planRows = plans.slice(0, 6).map((plan) => `<tr><td>${link("release", plan.id, short(plan.id))}</td><td><span class="badge">${safe(plan.status)}</span></td><td>${safe(plan.canary_weight)}%</td></tr>`);
  const incidentRows = list(data.incidents, "incidents").slice(0, 6).map((incident) => `<tr><td>${link("incident", incident.id, short(incident.id))}</td><td>${safe(incident.state)}</td><td>${safe(incident.outcome)}</td></tr>`);
  return section("OVERVIEW", "Shared AI capacity, governed", `
    <div class="metrics">${metrics.map(([number, label, source]) => `<div class="metric"><span>${safe(label)}</span><strong>${safe(number)}</strong><span>${safe(source)}</span></div>`).join("")}</div>
    <div class="grid two">
      ${card("Tenant admission", table(["Tenant", "Assigned models", "Concurrency"], tenantRows), '<span class="pill">Redis shared</span>')}
      ${card("Serving routes", table(["Alias", "Mode", "Targets"], modelRows), '<a class="text-button" href="#/models">View models</a>')}
    </div>
    <div class="grid two">
      ${card("Model releases", table(["Plan", "State", "Canary"], planRows), '<a class="text-button" href="#/models">Release control</a>')}
      ${card("Operations", table(["Incident", "State", "Outcome"], incidentRows), '<a class="text-button" href="#/operations">View incidents</a>')}
    </div>
    <div class="grid two">
      ${card("Console activity", state.activity.length ? `<ol class="activity">${state.activity.map((entry) => `<li><strong>${safe(entry.label)}</strong><span>${safe(entry.detail)} · ${safe(entry.at)}</span></li>`).join("")}</ol>` : '<p class="empty">Actions completed through the console appear here for this browser session. Durable records remain in the owning service audit.</p>', '<span class="pill">Session view</span>')}
      ${card("Operator workflow", '<p class="table-caption">Open a tenant, model, incident, agent, developer profile, or edge device to inspect evidence and use only the action that its owning service permits.</p><div class="workflow-links"><a href="#/tenants">Tenants</a><a href="#/models">Releases</a><a href="#/operations">Incidents</a><a href="#/agents">Agents</a></div>')}
    </div>`, '<span class="status good">SYSTEM HEALTHY</span>');
}

function tenantsPage(data) {
  const rows = array(data.tenants).map((tenant) => `<tr><td>${link("tenant", tenant.id, tenant.id)}</td><td>${safe((tenant.allowed_models || []).join(", "))}</td><td>${safe(tenant.max_requests_per_minute ?? "—")}</td><td>${safe(tenant.max_concurrency ?? "—")}</td></tr>`);
  return section("TENANTS", "Tenant admission and isolation", `<div class="panel"><div class="split-header"><p class="table-caption">Tenant identity is derived server-side from signed JWTs. Select a tenant for quota and usage evidence.</p>${filterControl("tenant-table", "Filter tenants")}</div><div id="tenant-table">${table(["Tenant", "Assigned models", "Rate limit", "Concurrency"], rows)}</div></div>`);
}

function modelsPage(data) {
  const plans = list(data.release_plans, "plans"); const registry = list(data.registry, "registered_models");
  const modelRows = array(data.models).map((model) => `<tr><td>${link("model", model.name, model.name)}</td><td>${safe(model.serving_mode)}</td><td>${safe(Object.keys(model.targets || {}).join(", "))}</td></tr>`);
  const registryRows = registry.map((model) => `<tr><td>${safe(model.name)}</td><td>${safe((model.aliases || []).find((item) => item.alias === "champion")?.version)}</td><td>${safe((model.aliases || []).find((item) => item.alias === "candidate")?.version)}</td></tr>`);
  const planRows = plans.map((plan) => `<tr><td>${link("release", plan.id, short(plan.id))}</td><td>${safe(plan.status)}</td><td>${safe(plan.champion_version)} → ${safe(plan.candidate_version)}</td><td>${safe(plan.canary_weight)}%</td><td>${actions(plan)}</td></tr>`);
  return section("MODEL CONTROL", "Models, evidence and releases", `<div class="grid two">${card("Serving aliases", table(["Alias", "Mode", "Targets"], modelRows))}${card("MLflow registry", table(["Model", "Champion", "Candidate"], registryRows), '<span class="pill">Artifact evidence</span>')}</div><div class="grid"><article><div class="card-title"><h3>Release plans</h3><span class="pill">Approval gated</span></div><p class="table-caption">The candidate must pass the existing evaluation, independent approval, and canary state machine. This console cannot edit model artifacts or bypass release gates.</p><div id="release-table">${table(["Plan", "State", "Version", "Canary", "Actions"], planRows)}</div></article></div>`, '<button class="primary" data-open-dialog="release">Create canary plan</button>');
}

function operationsPage(data) {
  const rows = list(data.incidents, "incidents").map((incident) => `<tr><td>${link("incident", incident.id, short(incident.id))}</td><td>${safe(incident.model)}</td><td>${safe(incident.state)}</td><td>${safe(incident.outcome)}</td><td>${safe(incident.release_phase)}</td></tr>`);
  const capacity = data.capacity || {}; const detail = { state: capacity.state, hardware: capacity.hardware, warning: capacity.warning, pools: capacity.pools || capacity.pool || "—" };
  return section("OPERATIONS", "Evidence, recovery and bounded remediation", `<div class="grid two">${card("Remediation incidents", table(["Incident", "Model", "State", "Outcome", "Release phase"], rows), '<span class="pill">Bounded recovery</span>')}${card("Capacity evidence", `${keyValues(detail)}<p class="empty">The pool is Redis accounting only. It is not physical GPU scheduling.</p>`, '<span class="pill simulated">SIMULATED HARDWARE</span>')}</div>`);
}

function agentsPage(data) {
  const events = list(data.agent_audit, "events").slice().reverse(); const tasks = list(data.sandbox_tasks, "tasks").slice().reverse(); const tools = list(data.agent_tools, "tools");
  const agentRows = events.map((event) => `<tr><td>${safe(event.tool)}</td><td>${safe(event.actor)}</td><td>${safe(event.event)}</td><td>${safe(event.created_at)}</td></tr>`);
  const taskRows = tasks.map((task) => `<tr><td>${link("sandbox", task.id, task.task_kind)}</td><td>${safe(task.state)}</td><td>${safe(task.exit_code)}</td><td>${safe(task.created_at)}</td></tr>`);
  return section("AGENTS & SANDBOX", "Delegated authority and containment", `<div class="grid two">${card("Delegated permissions", `<div class="permission-list">${tools.map((tool) => `<div><strong>${safe(tool.name)}</strong><span>${safe(tool.description)}</span></div>`).join("") || '<p class="empty">No tools are delegated.</p>'}</div>`, '<span class="pill">Filtered discovery</span>')}${card("Sandbox controls", '<ul class="control-list"><li>Named fixture tasks only</li><li>Non-root, read-only child</li><li>No Docker socket or host mount</li><li>Network disabled by default</li></ul>', '<span class="pill">Hardened child</span>')}</div><div class="grid two">${card("Delegated agent audit", table(["Tool", "Actor", "Event", "Time"], agentRows), '<a class="text-button" href="#/agents">Filtered discovery</a>')}${card("Sandbox tasks", table(["Task", "State", "Exit", "Time"], taskRows), '<button class="text-button" data-sandbox="fixture_patch">Run patch task</button>')}</div><div class="panel"><p class="table-caption">Agents may retrieve same-tenant metadata evidence or prepare a rollback plan. They cannot approve or execute remediation, receive platform credentials, or run arbitrary sandbox commands.</p></div>`, '<button class="outline" data-sandbox="containment_probe">Run containment probe</button>');
}

function developersPage(data) {
  const profiles = list(data.integrations, "integrations"); const rows = profiles.map((profile) => `<tr><td>${link("developer", profile.id, profile.service_name || short(profile.id))}</td><td>${safe(profile.owner)}</td><td>${safe(profile.model)}</td><td>${safe(profile.environment)}</td><td>${safe(profile.tenant)}</td></tr>`);
  return section("DEVELOPER INTEGRATIONS", "Tenant-bound golden-path contracts", `<div class="grid two"><div class="panel"><h3>Create a developer integration</h3><p class="table-caption">Creates only a tenant-bound, token-free starter profile through the existing self-service API. The downstream service validates the assigned model and persists audit-safe metadata.</p><form id="integration-form" class="form-grid"><label>Service name<input name="service_name" required pattern="[a-z][a-z0-9-]{2,62}" placeholder="search-api" /></label><label>Owner<input name="owner" required pattern="[a-z][a-z0-9-]{2,62}" placeholder="search" /></label><label>Model<select name="model"><option value="chat-default">chat-default</option></select></label><label>Environment<select name="environment"><option value="development">development</option><option value="staging">staging</option></select></label><button class="primary" type="submit">Create profile</button></form></div>${card("Guardrail", '<p class="table-caption">Profiles are tenant and model bound. This UI cannot create a platform administrator, add a tenant, or grant rollout authority.</p>', '<span class="pill">Scoped contract</span>')}</div><div class="panel"><div class="split-header"><p class="table-caption">Generated starter artifacts are token-free. Select a profile to inspect the files.</p>${filterControl("developer-table", "Filter profiles")}</div><div id="developer-table">${table(["Service", "Owner", "Model", "Environment", "Tenant"], rows)}</div></div>`);
}

function edgePage(data) {
  const rows = list(data.devices, "devices").map((device) => `<tr><td>${link("device", device.device_id, device.device_id)}</td><td>${safe(device.profile)}</td><td><span class="badge">${safe(device.network)}</span></td><td>${safe((device.local_models || []).join(", ") || "none")}</td><td>${safe(device.last_seen || device.updated_at)}</td><td><div class="row-actions"><button data-edge-network="online" data-device="${safe(device.device_id)}">online</button><button data-edge-network="offline" data-device="${safe(device.device_id)}" data-confirm="true">offline</button></div></td></tr>`);
  return section("EDGE FLEET", "Local-first routes with simulated devices", `<div class="panel"><p class="table-caption">Each row is an independent local device-agent container with a signed device identity. Network controls are an explicit local simulation only; hardware profile fields are simulated.</p>${table(["Device", "Profile", "Network", "Local models", "Last seen", "Simulate"], rows)}</div>`, '<span class="pill simulated">HARDWARE SIMULATED</span>');
}

function boundariesPage() { return section("EVIDENCE BOUNDARY", "What this local console proves", `<div class="boundary"><div><strong>Executed locally</strong><p>Signed identity, tenant admission, Redis quotas, CPU ONNX serving, MLflow release control, tracing, remediation, edge policy, developer profiles, delegated tools, hardened Docker fixture tasks, and this scoped browser console.</p></div><div><strong>Not claimed</strong><p>Physical GPU scheduling, vLLM/DCGM, Kubernetes/EKS production deployment, cloud-hosted models, enterprise browser SSO, or production BFF token exchange.</p></div></div>`); }

function breadcrumb(parent, label) { return `<div class="breadcrumb"><a href="#/${parent}">${safe(parent)}</a><span>/</span><span>${safe(label)}</span></div>`; }
async function detailPage(kind, id) {
  const endpoints = { tenant: `/console/v1/tenants/${encodeURIComponent(id)}`, model: `/console/v1/models/${encodeURIComponent(id)}`, release: `/console/v1/releases/${encodeURIComponent(id)}`, incident: `/console/v1/incidents/${encodeURIComponent(id)}`, sandbox: `/console/v1/sandbox/tasks/${encodeURIComponent(id)}`, developer: `/console/v1/developer/integrations/${encodeURIComponent(id)}`, device: `/console/v1/edge/devices/${encodeURIComponent(id)}` };
  const parent = { tenant: "tenants", model: "models", release: "models", incident: "operations", sandbox: "agents", developer: "developers", device: "edge" }[kind];
  if (!endpoints[kind]) return errorView(new Error("unknown console route"));
  app().innerHTML = '<section class="page"><p class="loading">Loading scoped platform evidence…</p></section>';
  const data = await fetchJson(endpoints[kind]);
  if (kind === "tenant") return section("TENANT DETAIL", data.tenant.id, `${breadcrumb(parent, data.tenant.id)}<div class="detail-grid"><div class="panel"><h3>Admission policy</h3>${keyValues(data.tenant)}<h3>Usage evidence</h3>${json(data.usage)}</div><div class="panel"><h3>Assigned model and deployment context</h3>${json({ models: data.models, deployments: data.deployments })}</div></div>`);
  if (kind === "model") {
    const telemetry = data.telemetry || {};
    const outcomeRows = array(telemetry.outcomes?.result).map((item) => `<tr><td>${safe(item.metric?.outcome || "unknown")}</td><td>${safe(item.value?.[1] || "0")}</td></tr>`);
    const sloRows = array(telemetry.slo?.result).map((item) => `<tr><td>${safe(item.metric?.status || "unknown")}</td><td>${safe(item.value?.[1] || "0")}</td></tr>`);
    const phaseRows = array(telemetry.release_phase?.result).map((item) => `<tr><td>${safe(item.metric?.phase || "unknown")}</td><td>${safe(item.value?.[1] || "0")}</td></tr>`);
    const telemetryMetrics = [
      [promValue(telemetry.requests), "Recorded requests"],
      [promValue(telemetry.p95_latency_seconds), "p95 latency (seconds)"],
      [promValue(telemetry.p95_ttft_seconds), "p95 time to first token (seconds)"],
      [promValue(telemetry.tokens), "Metered tokens"],
      [promValue(telemetry.estimated_cost_usd), "Estimated cost (USD)"],
    ];
    return section("MODEL DETAIL", id, `${breadcrumb(parent, id)}
      <div class="metrics model-metrics">${telemetryMetrics.map(([number, label]) => `<div class="metric"><span>${safe(label)}</span><strong>${safe(number)}</strong><span>Prometheus</span></div>`).join("")}</div>
      <div class="grid two">
        ${card("Request outcomes", table(["Outcome", "Requests"], outcomeRows), '<span class="pill">Prometheus</span>')}
        ${card("SLO evidence", table(["Status", "Evaluations"], sloRows), '<span class="pill">Prometheus</span>')}
      </div>
      <div class="grid two">
        ${card("Canary phase evidence", table(["Release phase", "Requests"], phaseRows), '<span class="pill">Release-correlated</span>')}
        ${card("Deep observability", '<p class="table-caption">Open the provisioned Grafana dashboard with this model preselected. Local estimated cost is fixture pricing, not cloud billing.</p>', `<a class="text-button" target="_blank" rel="noreferrer" href="${safe(data.grafana_url)}">Open model in Grafana</a>`)}
      </div>
      <div class="detail-grid"><div class="panel"><h3>Routing & audit context</h3>${json(data.rollout)}</div><div class="panel"><h3>Registry & deployment evidence</h3>${json({ deployments: data.deployments, registry: data.registry })}</div></div>`);
  }
  if (kind === "release") return section("RELEASE DETAIL", short(id), `${breadcrumb(parent, short(id))}<div class="detail-grid"><div class="panel"><h3>Immutable release plan</h3>${keyValues(data)}<div class="section-actions">${actions(data)}</div></div><div class="panel"><h3>Plan evidence</h3>${json(data)}</div></div>`);
  if (kind === "incident") {
    const incident = data.incident || {}; const events = array(data.timeline); const plans = array(data.plans);
    const planRows = plans.map((plan) => `<tr><td>${safe(short(plan.id))}</td><td>${safe(plan.status)}</td><td>${safe(plan.action)}</td><td>${remediationActions(plan)}</td></tr>`);
    const planAction = incident.state === "DETECTED" ? `<button class="primary" data-remediation-create="${safe(id)}">Create rollback plan</button>` : "";
    return section("INCIDENT DETAIL", short(id), `${breadcrumb(parent, short(id))}<div class="detail-grid"><div class="panel"><h3>Incident state</h3>${keyValues(incident)}<div class="section-actions">${planAction}</div></div><div class="panel"><h3>Audit timeline</h3><ol class="timeline">${events.map((event) => `<li><strong>${safe(event.event || event.type)}</strong><span>${safe(event.created_at || event.timestamp)} · ${safe(event.actor)}</span></li>`).join("") || '<li><strong>No timeline events</strong></li>'}</ol></div></div><div class="grid"><article><div class="card-title"><h3>Bounded remediation plans</h3><span class="pill">Approval required</span></div><p class="table-caption">The console can only create the known canary-rollback plan, then forward approval and execution to the existing remediation control API.</p>${table(["Plan", "State", "Action", "Next action"], planRows)}</article></div>`);
  }
  if (kind === "sandbox") return section("SANDBOX TASK", data.task.task_kind, `${breadcrumb(parent, data.task.task_kind)}<div class="detail-grid"><div class="panel"><h3>Task outcome</h3>${keyValues(data.task)}</div><div class="panel"><h3>Hardening evidence</h3>${json(data.task.hardening)}</div></div>`);
  if (kind === "developer") return section("DEVELOPER PROFILE", data.profile.service_name, `${breadcrumb(parent, data.profile.service_name)}<div class="detail-grid"><div class="panel"><h3>Profile</h3>${keyValues(data.profile)}</div><div class="panel"><h3>Token-free generated files</h3>${json(Object.keys(data.files || {}))}</div></div>`);
  if (kind === "device") return section("EDGE DEVICE", data.device.device_id, `${breadcrumb(parent, data.device.device_id)}<div class="detail-grid"><div class="panel"><h3>Device inventory</h3>${keyValues(data.device)}<div class="section-actions"><button data-edge-network="online" data-device="${safe(data.device.device_id)}">Simulate online</button><button data-edge-network="offline" data-device="${safe(data.device.device_id)}" data-confirm="true">Simulate offline</button></div></div><div class="panel"><h3>Hardware boundary</h3><span class="pill simulated">${safe(data.hardware)}</span><p class="empty">Device profiles and network controls are local simulation inputs, not physical hardware measurements.</p></div></div>`);
  return errorView(new Error("unknown detail view"));
}

async function renderRoute() {
  const current = route(); activeNav(current.page);
  if (["tenant", "model", "release", "incident", "sandbox", "developer", "device"].includes(current.page) && current.id) { try { app().innerHTML = await detailPage(current.page, current.id); } catch (error) { app().innerHTML = errorView(error); } return; }
  if (!state.overview) { app().innerHTML = '<section class="page"><p class="loading">Loading platform state…</p></section>'; return; }
  const pages = { overview: overviewPage, tenants: tenantsPage, models: modelsPage, operations: operationsPage, agents: agentsPage, developers: developersPage, edge: edgePage, boundaries: boundariesPage };
  const renderer = pages[current.page] || overviewPage; setTitle(current.page === "overview" ? "Operator Console" : current.page.replace(/\b\w/g, (letter) => letter.toUpperCase())); app().innerHTML = renderer(state.overview);
}

async function action(path, options = {}) { const response = await fetch(path, { method: "POST", headers: options.body ? { "Content-Type": "application/json" } : {}, body: options.body ? JSON.stringify(options.body) : undefined }); const body = await response.json().catch(() => ({})); if (!response.ok) throw new Error(body.detail || "action denied"); recordActivity(options.label || "Scoped action completed", options.detail || path); toast("Action completed through the owning scoped platform API."); await refresh(); return body; }
function openDialog(kind) { const dialog = $("action-dialog"); $("dialog-kind").value = kind; $("dialog-title").textContent = "Create canary release plan"; $("dialog-copy").textContent = "Creates an immutable release plan through the existing release controller. Evaluation, independent approval, and canary gates still apply."; $("dialog-confirm").textContent = "Create plan"; dialog.showModal(); }
function closeDialog() { $("action-dialog").close(); }
async function confirmButton(button) { if (button.dataset.confirm !== "true") return true; return window.confirm(`Continue with ${button.textContent.trim()}? The request will be forwarded to the existing governed control API.`); }
document.addEventListener("click", async (event) => { const button = event.target.closest("button"); if (!button) return; try {
  if (button.id === "refresh") return refresh();
  if (button.dataset.openDialog) return openDialog(button.dataset.openDialog);
  if (button.id === "dialog-cancel" || button.id === "dialog-cancel-secondary") return closeDialog();
  if (!(await confirmButton(button))) return;
  if (button.dataset.release) { const query = button.dataset.plan ? `?plan_id=${encodeURIComponent(button.dataset.plan)}` : ""; await action(`/console/v1/releases/${button.dataset.release}${query}`, { label: `Release ${button.dataset.release}`, detail: button.dataset.plan || "new plan" }); }
  if (button.dataset.sandbox) await action(`/console/v1/sandbox/${button.dataset.sandbox}`, { label: "Sandbox task started", detail: button.dataset.sandbox });
  if (button.dataset.remediationCreate) await action(`/console/v1/remediation/incidents/${encodeURIComponent(button.dataset.remediationCreate)}/plan`, { label: "Remediation plan created", detail: button.dataset.remediationCreate });
  if (button.dataset.remediation) await action(`/console/v1/remediation/plans/${encodeURIComponent(button.dataset.plan)}/${button.dataset.remediation}`, { label: `Remediation ${button.dataset.remediation}`, detail: button.dataset.plan });
  if (button.dataset.edgeNetwork) await action(`/console/v1/edge/devices/${encodeURIComponent(button.dataset.device)}/network/${button.dataset.edgeNetwork}`, { label: "Simulated edge network changed", detail: `${button.dataset.device} → ${button.dataset.edgeNetwork}` });
} catch (error) { toast(`Action not applied: ${error.message}`); } });
document.addEventListener("submit", async (event) => { const form = event.target; if (!(form instanceof HTMLFormElement)) return; event.preventDefault(); try {
  if (form.id === "canary-form") { const data = new FormData(form); const weight = encodeURIComponent(data.get("canary_weight")); await action(`/console/v1/releases/create?canary_weight=${weight}`, { label: "Release plan created", detail: `${data.get("canary_weight")}% canary` }); closeDialog(); }
  if (form.id === "integration-form") { const data = Object.fromEntries(new FormData(form)); const result = await action("/console/v1/developer/integrations", { body: data, label: "Developer profile created", detail: String(data.service_name) }); if (result.profile?.id) location.hash = `#/developer/${encodeURIComponent(result.profile.id)}`; }
} catch (error) { toast(`Action not applied: ${error.message}`); } });
document.addEventListener("input", (event) => { const input = event.target; if (!(input instanceof HTMLInputElement) || !input.dataset.filterTarget) return; const target = $(input.dataset.filterTarget); if (!target) return; const query = input.value.trim().toLowerCase(); target.querySelectorAll("tbody tr").forEach((row) => { row.hidden = !row.textContent.toLowerCase().includes(query); }); });
window.addEventListener("hashchange", renderRoute);
refresh(); setInterval(refresh, 15000);
