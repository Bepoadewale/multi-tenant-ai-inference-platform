const $ = (id) => document.getElementById(id);
const app = () => $("app");
const state = { overview: null };
const safe = (value) => String(value ?? "—").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
const short = (value, length = 8) => String(value ?? "—").slice(0, length);
const list = (data, key) => Array.isArray(data?.[key]) ? data[key] : [];
const array = (data) => Array.isArray(data) ? data : [];
const metricValue = (data) => data?.data?.result?.[0]?.value?.[1] ?? "0";
const json = (data) => `<pre class="json">${safe(JSON.stringify(data, null, 2))}</pre>`;

function toast(message) { const node = $("toast"); node.textContent = message; node.style.display = "block"; setTimeout(() => { node.style.display = "none"; }, 5000); }
function setTitle(title) { $("page-title").textContent = title; }
function route() { const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean); return { page: parts[0] || "overview", id: parts[1] || null }; }
function link(page, id, label) { return `<a class="row-link" href="#/${page}/${encodeURIComponent(id)}">${safe(label)}</a>`; }
function actions(plan) { const next = []; if (plan.status === "PENDING_APPROVAL") next.push("approve"); if (plan.status === "APPROVED") next.push("canary"); if (plan.status === "CANARY") next.push("promote", "rollback"); return next.length ? `<div class="row-actions">${next.map((action) => `<button data-release="${action}" data-plan="${safe(plan.id)}">${safe(action)}</button>`).join("")}</div>` : "—"; }
function table(headers, rows) { if (!rows.length) return '<p class="empty">No recorded local evidence yet.</p>'; return `<div class="table-wrap"><table><thead><tr>${headers.map((header) => `<th>${safe(header)}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>`; }
function section(eyebrow, title, content, actionsHtml = "") { return `<section class="page"><div class="section-title"><div><p class="eyebrow">${safe(eyebrow)}</p><h2>${safe(title)}</h2></div>${actionsHtml}</div>${content}</section>`; }
function card(title, content, badge = "") { return `<article><div class="card-title"><h3>${safe(title)}</h3>${badge}</div>${content}</article>`; }
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
    </div>`, '<span class="status good">SYSTEM HEALTHY</span>');
}

function tenantsPage(data) {
  const rows = array(data.tenants).map((tenant) => `<tr><td>${link("tenant", tenant.id, tenant.id)}</td><td>${safe((tenant.allowed_models || []).join(", "))}</td><td>${safe(tenant.max_requests_per_minute ?? "—")}</td><td>${safe(tenant.max_concurrency ?? "—")}</td></tr>`);
  return section("TENANTS", "Tenant admission and isolation", `<div class="panel"><p class="table-caption">Tenant identity is derived server-side from signed JWTs. Select a tenant for quota and usage evidence.</p>${table(["Tenant", "Assigned models", "Rate limit", "Concurrency"], rows)}</div>`);
}

function modelsPage(data) {
  const plans = list(data.release_plans, "plans"); const registry = list(data.registry, "registered_models");
  const modelRows = array(data.models).map((model) => `<tr><td>${link("model", model.name, model.name)}</td><td>${safe(model.serving_mode)}</td><td>${safe(Object.keys(model.targets || {}).join(", "))}</td></tr>`);
  const registryRows = registry.map((model) => `<tr><td>${safe(model.name)}</td><td>${safe((model.aliases || []).find((item) => item.alias === "champion")?.version)}</td><td>${safe((model.aliases || []).find((item) => item.alias === "candidate")?.version)}</td></tr>`);
  const planRows = plans.map((plan) => `<tr><td>${link("release", plan.id, short(plan.id))}</td><td>${safe(plan.status)}</td><td>${safe(plan.champion_version)} → ${safe(plan.candidate_version)}</td><td>${safe(plan.canary_weight)}%</td><td>${actions(plan)}</td></tr>`);
  return section("MODEL CONTROL", "Models, evidence and releases", `<div class="grid two">${card("Serving aliases", table(["Alias", "Mode", "Targets"], modelRows))}${card("MLflow registry", table(["Model", "Champion", "Candidate"], registryRows), '<span class="pill">Artifact evidence</span>')}</div><div class="grid"><article><div class="card-title"><h3>Release plans</h3><span class="pill">Approval gated</span></div>${table(["Plan", "State", "Version", "Canary", "Actions"], planRows)}</article></div>`, '<button class="primary" data-release="create">Create canary plan</button>');
}

function operationsPage(data) {
  const rows = list(data.incidents, "incidents").map((incident) => `<tr><td>${link("incident", incident.id, short(incident.id))}</td><td>${safe(incident.model)}</td><td>${safe(incident.state)}</td><td>${safe(incident.outcome)}</td><td>${safe(incident.release_phase)}</td></tr>`);
  const capacity = data.capacity || {}; const detail = { state: capacity.state, hardware: capacity.hardware, warning: capacity.warning, pools: capacity.pools || capacity.pool || "—" };
  return section("OPERATIONS", "Evidence, recovery and bounded remediation", `<div class="grid two">${card("Remediation incidents", table(["Incident", "Model", "State", "Outcome", "Release phase"], rows), '<span class="pill">Bounded recovery</span>')}${card("Capacity evidence", `${keyValues(detail)}<p class="empty">The pool is Redis accounting only. It is not physical GPU scheduling.</p>`, '<span class="pill simulated">SIMULATED HARDWARE</span>')}</div>`);
}

function agentsPage(data) {
  const events = list(data.agent_audit, "events").slice().reverse(); const tasks = list(data.sandbox_tasks, "tasks").slice().reverse();
  const agentRows = events.map((event) => `<tr><td>${safe(event.tool)}</td><td>${safe(event.actor)}</td><td>${safe(event.event)}</td><td>${safe(event.created_at)}</td></tr>`);
  const taskRows = tasks.map((task) => `<tr><td>${link("sandbox", task.id, task.task_kind)}</td><td>${safe(task.state)}</td><td>${safe(task.exit_code)}</td><td>${safe(task.created_at)}</td></tr>`);
  return section("AGENTS & SANDBOX", "Delegated authority and containment", `<div class="grid two">${card("Delegated agent audit", table(["Tool", "Actor", "Event", "Time"], agentRows), '<a class="text-button" href="#/agents">Filtered discovery</a>')}${card("Sandbox tasks", table(["Task", "State", "Exit", "Time"], taskRows), '<button class="text-button" data-sandbox="fixture_patch">Run patch task</button>')}</div><div class="panel"><p class="table-caption">Agents may retrieve same-tenant metadata evidence or prepare a rollback plan. They cannot approve or execute remediation, receive platform credentials, or run arbitrary sandbox commands.</p></div>`, '<button class="outline" data-sandbox="containment_probe">Run containment probe</button>');
}

function developersPage(data) {
  const profiles = list(data.integrations, "integrations"); const rows = profiles.map((profile) => `<tr><td>${link("developer", profile.id, profile.service_name || short(profile.id))}</td><td>${safe(profile.owner)}</td><td>${safe(profile.model)}</td><td>${safe(profile.environment)}</td><td>${safe(profile.tenant)}</td></tr>`);
  return section("DEVELOPER INTEGRATIONS", "Tenant-bound golden-path contracts", `<div class="panel"><p class="table-caption">These generated starter artifacts are token-free. They preserve tenant/model binding without granting rollout or platform authority.</p>${table(["Service", "Owner", "Model", "Environment", "Tenant"], rows)}</div>`);
}

function edgePage(data) {
  const rows = list(data.devices, "devices").map((device) => `<tr><td>${link("device", device.device_id, device.device_id)}</td><td>${safe(device.profile)}</td><td>${safe(device.network)}</td><td>${safe((device.local_models || []).join(", ") || "none")}</td><td>${safe(device.last_seen || device.updated_at)}</td></tr>`);
  return section("EDGE FLEET", "Local-first routes with simulated devices", `<div class="panel"><p class="table-caption">Each row is an independent local device-agent container with a signed device identity. Hardware profile fields are simulated.</p>${table(["Device", "Profile", "Network", "Local models", "Last seen"], rows)}</div>`, '<span class="pill simulated">HARDWARE SIMULATED</span>');
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
  if (kind === "model") return section("MODEL DETAIL", id, `${breadcrumb(parent, id)}<div class="detail-grid"><div class="panel"><h3>Routing & audit context</h3>${json(data.rollout)}</div><div class="panel"><h3>Registry & deployment evidence</h3>${json({ deployments: data.deployments, registry: data.registry })}</div></div>`);
  if (kind === "release") return section("RELEASE DETAIL", short(id), `${breadcrumb(parent, short(id))}<div class="detail-grid"><div class="panel"><h3>Immutable release plan</h3>${keyValues(data)}<div class="section-actions">${actions(data)}</div></div><div class="panel"><h3>Plan evidence</h3>${json(data)}</div></div>`);
  if (kind === "incident") { const incident = data.incident.incident || data.incident; const events = array(data.timeline); return section("INCIDENT DETAIL", short(id), `${breadcrumb(parent, short(id))}<div class="detail-grid"><div class="panel"><h3>Incident state</h3>${keyValues(incident)}</div><div class="panel"><h3>Audit timeline</h3><ol class="timeline">${events.map((event) => `<li><strong>${safe(event.event || event.type)}</strong><span>${safe(event.created_at || event.timestamp)} · ${safe(event.actor)}</span></li>`).join("") || '<li><strong>No timeline events</strong></li>'}</ol></div></div>`); }
  if (kind === "sandbox") return section("SANDBOX TASK", data.task.task_kind, `${breadcrumb(parent, data.task.task_kind)}<div class="detail-grid"><div class="panel"><h3>Task outcome</h3>${keyValues(data.task)}</div><div class="panel"><h3>Hardening evidence</h3>${json(data.task.hardening)}</div></div>`);
  if (kind === "developer") return section("DEVELOPER PROFILE", data.profile.service_name, `${breadcrumb(parent, data.profile.service_name)}<div class="detail-grid"><div class="panel"><h3>Profile</h3>${keyValues(data.profile)}</div><div class="panel"><h3>Token-free generated files</h3>${json(Object.keys(data.files || {}))}</div></div>`);
  if (kind === "device") return section("EDGE DEVICE", data.device.device_id, `${breadcrumb(parent, data.device.device_id)}<div class="detail-grid"><div class="panel"><h3>Device inventory</h3>${keyValues(data.device)}</div><div class="panel"><h3>Hardware boundary</h3><span class="pill simulated">${safe(data.hardware)}</span><p class="empty">Device profiles are local simulation inputs, not physical hardware measurements.</p></div></div>`);
  return errorView(new Error("unknown detail view"));
}

async function renderRoute() {
  const current = route(); activeNav(current.page);
  if (["tenant", "model", "release", "incident", "sandbox", "developer", "device"].includes(current.page) && current.id) { try { app().innerHTML = await detailPage(current.page, current.id); } catch (error) { app().innerHTML = errorView(error); } return; }
  if (!state.overview) { app().innerHTML = '<section class="page"><p class="loading">Loading platform state…</p></section>'; return; }
  const pages = { overview: overviewPage, tenants: tenantsPage, models: modelsPage, operations: operationsPage, agents: agentsPage, developers: developersPage, edge: edgePage, boundaries: boundariesPage };
  const renderer = pages[current.page] || overviewPage; setTitle(current.page === "overview" ? "Operator Console" : current.page.replace(/\b\w/g, (letter) => letter.toUpperCase())); app().innerHTML = renderer(state.overview);
}

async function action(path) { const response = await fetch(path, { method: "POST" }); const body = await response.json().catch(() => ({})); if (!response.ok) throw new Error(body.detail || "action denied"); toast("Action completed through an existing scoped platform API."); await refresh(); }
document.addEventListener("click", async (event) => { const button = event.target.closest("button"); if (!button) return; try { if (button.id === "refresh") return refresh(); if (button.dataset.release) { const query = button.dataset.plan ? `?plan_id=${encodeURIComponent(button.dataset.plan)}` : ""; await action(`/console/v1/releases/${button.dataset.release}${query}`); } if (button.dataset.sandbox) await action(`/console/v1/sandbox/${button.dataset.sandbox}`); } catch (error) { toast(`Action not applied: ${error.message}`); } });
window.addEventListener("hashchange", renderRoute);
refresh(); setInterval(refresh, 15000);
