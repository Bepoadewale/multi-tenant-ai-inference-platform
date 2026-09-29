const $ = (id) => document.getElementById(id);
const value = (data) => data?.data?.result?.[0]?.value?.[1] ?? "0";
const safe = (value) => String(value ?? "—").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[c]));
const list = (data, key) => Array.isArray(data?.[key]) ? data[key] : [];

function table(target, headers, rows) {
  const node = $(target); if (!rows.length) { node.innerHTML = '<p class="empty">No recorded local evidence yet.</p>'; return; }
  node.innerHTML = `<table><thead><tr>${headers.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table>`;
}
function toast(message) { const t=$("toast"); t.textContent=message; t.style.display="block"; setTimeout(()=>t.style.display="none",5000); }
function planActions(plan) { const state=plan.status; const actions=[]; if(state==='PENDING_APPROVAL') actions.push('approve'); if(state==='APPROVED') actions.push('canary'); if(state==='CANARY'){actions.push('promote','rollback');} return `<div class="row-actions">${actions.map(a=>`<button data-plan="${plan.id}" data-release="${a}">${a}</button>`).join('')}</div>` || '—'; }
function render(data) {
  const plans=list(data.release_plans,'plans'), devices=list(data.devices,'devices'), incidents=list(data.incidents,'incidents');
  $("metrics").innerHTML = [
    [value(data.requests),'Recorded requests','Prometheus'], [value(data.throttles),'Admission throttles','Bounded policy'],
    [plans.filter(p=>p.status==='CANARY').length,'Active canaries','MLflow + Redis'], [devices.length,'Registered devices','Simulated hardware'],
  ].map(([n,l,s])=>`<div class="metric"><span>${l}</span><strong>${safe(n)}</strong><span>${s}</span></div>`).join('');
  table('tenants',['Tenant','Models'],list(data.tenants,'tenants').map(t=>`<tr><td>${safe(t.id||t.tenant_id||t.tenant)}</td><td>${safe((t.models||[]).join(', '))}</td></tr>`));
  const cap=data.capacity||{}; table('capacity',['Pool','State','Detail'],[[`simulated-l40s`,`SIMULATED`,safe(JSON.stringify(cap).slice(0,90))]].map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join('')}</tr>`));
  table('registry',['Model','Champion','Candidate'],list(data.registry,'registered_models').map(m=>`<tr><td>${safe(m.name)}</td><td>${safe((m.aliases||[]).find(a=>a.alias==='champion')?.version)}</td><td>${safe((m.aliases||[]).find(a=>a.alias==='candidate')?.version)}</td></tr>`));
  table('plans',['Plan','Status','Canary','Actions'],plans.map(p=>`<tr><td class="label">${safe(p.id.slice(0,8))}</td><td class="state">${safe(p.status)}</td><td>${safe(p.canary_weight)}%</td><td>${planActions(p)}</td></tr>`));
  table('incidents',['Incident','State','Outcome'],incidents.map(i=>`<tr><td class="label">${safe(i.id.slice(0,8))}</td><td>${safe(i.state)}</td><td>${safe(i.outcome)}</td></tr>`));
  table('agents',['Tool','Actor','Event'],list(data.agent_audit,'events').slice(-4).reverse().map(a=>`<tr><td>${safe(a.tool)}</td><td>${safe(a.actor)}</td><td>${safe(a.event)}</td></tr>`));
  table('sandbox',['Task','State','Exit'],list(data.sandbox_tasks,'tasks').slice(-4).reverse().map(s=>`<tr><td>${safe(s.task_kind)}</td><td>${safe(s.state)}</td><td>${safe(s.exit_code)}</td></tr>`));
  table('integrations',['Profile','Model','Tenant'],list(data.integrations,'profiles').map(p=>`<tr><td>${safe(p.name||p.id?.slice(0,8))}</td><td>${safe(p.model_alias)}</td><td>${safe(p.tenant)}</td></tr>`));
  table('devices',['Device','Profile','Route'],devices.map(d=>`<tr><td>${safe(d.device_id)}</td><td>${safe(d.profile)}</td><td>${safe((d.local_models||[]).length ? 'LOCAL READY' : 'PUBLIC FALLBACK')}</td></tr>`));
  $("updated").textContent=`Last refresh ${new Date().toLocaleTimeString()}`;
}
async function refresh(){ try{ const r=await fetch('/console/v1/overview'); if(!r.ok) throw new Error(await r.text()); render(await r.json()); }catch(e){toast(`Console refresh failed: ${e.message}`);} }
async function action(path){ const r=await fetch(path,{method:'POST'}); const body=await r.json(); if(!r.ok) throw new Error(body.detail||'action denied'); toast('Action completed through the existing scoped API.'); await refresh(); }
document.addEventListener('click',async e=>{ const b=e.target.closest('button'); if(!b)return; try{if(b.id==='refresh')return refresh(); if(b.dataset.release){const id=b.dataset.plan?`?plan_id=${encodeURIComponent(b.dataset.plan)}`:''; await action(`/console/v1/releases/${b.dataset.release}${id}`);} if(b.dataset.sandbox) await action(`/console/v1/sandbox/${b.dataset.sandbox}`);}catch(err){toast(`Action not applied: ${err.message}`);}});
refresh(); setInterval(refresh,15000);
