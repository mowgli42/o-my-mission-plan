/**
 * o-my Mission Plan UI
 * IxDF / Nielsen heuristics: status visibility, recognition over recall,
 * explicit error recovery, user control (reset), progressive disclosure.
 */

const state = {
  world: null,
  plan: null,
  selectedAircraftId: null,
};

const $ = (sel) => document.querySelector(sel);

/* ---- Geographic projection (Florida demo bbox) ---- */
const BOUNDS = { minLat: 26.4, maxLat: 30.6, minLon: -83.0, maxLon: -79.6 };

function project(lat, lon) {
  const x = ((lon - BOUNDS.minLon) / (BOUNDS.maxLon - BOUNDS.minLon)) * 600 + 20;
  const y = ((BOUNDS.maxLat - lat) / (BOUNDS.maxLat - BOUNDS.minLat)) * 480 + 20;
  return [x, y];
}

function toast(message, kind = "info") {
  const host = $("#toasts");
  const el = document.createElement("div");
  el.className = `toast ${kind === "error" ? "error" : kind === "warn" ? "warn" : ""}`;
  el.textContent = message;
  host.appendChild(el);
  setTimeout(() => el.remove(), 4200);
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

function typeBadge(type) {
  const t = String(type).toUpperCase();
  if (t === "ISR") return `<span class="badge badge-isr">ISR</span>`;
  if (t === "STRIKE") return `<span class="badge badge-strike">STRIKE</span>`;
  if (t === "FIGHTER") return `<span class="badge badge-fighter">FIGHTER</span>`;
  if (t === "BOMBER") return `<span class="badge badge-bomber">BOMBER</span>`;
  return `<span class="badge badge-idle">${t}</span>`;
}

function statusBadge(status) {
  if (status === "GO") return `<span class="badge badge-go">GO</span>`;
  if (status === "NO-GO") return `<span class="badge badge-nogo">NO-GO</span>`;
  return `<span class="badge badge-idle">IDLE</span>`;
}

function assignedSet() {
  const set = new Set();
  if (!state.plan) return set;
  for (const p of state.plan.plans) {
    for (const tid of p.assigned_task_ids || []) set.add(tid);
  }
  return set;
}

function unallocatedSet() {
  return new Set((state.plan?.unallocated_tasks || []).map((t) => t.id));
}

function renderTasks() {
  const list = $("#task-list");
  const tasks = state.world?.tasks || [];
  $("#pool-count").textContent = String(tasks.length);
  if (!tasks.length) {
    list.innerHTML = `<div class="empty">No tasks in pool.</div>`;
    return;
  }
  const assigned = assignedSet();
  const unalloc = unallocatedSet();
  list.innerHTML = tasks
    .map((t) => {
      let flag = "";
      if (unalloc.has(t.id)) flag = `<span class="badge badge-unalloc">Unallocated</span>`;
      else if (assigned.has(t.id)) flag = `<span class="badge badge-go">Assigned</span>`;
      return `
        <article class="item">
          <div class="item-row">
            <span class="item-id">${t.id}</span>
            ${typeBadge(t.type)}
          </div>
          <div class="item-meta">${t.label || "—"} · ${t.location.lat.toFixed(2)}, ${t.location.lon.toFixed(2)}</div>
          <div class="item-row" style="margin-top:0.35rem">${flag}</div>
        </article>`;
    })
    .join("");
}

function renderFleet() {
  const list = $("#fleet-list");
  const select = $("#insert-aircraft");
  const aircraft = state.world?.aircraft || [];
  const plansById = Object.fromEntries((state.plan?.plans || []).map((p) => [p.aircraft_id, p]));

  select.innerHTML = aircraft
    .map((a) => `<option value="${a.id}">${a.label || a.id} (${a.type})</option>`)
    .join("");
  if (state.selectedAircraftId) select.value = state.selectedAircraftId;

  list.innerHTML = aircraft
    .map((a) => {
      const plan = plansById[a.id];
      const status = plan?.status || "idle";
      const selected = state.selectedAircraftId === a.id ? "selected" : "";
      const fuelPct =
        plan?.fuel != null
          ? Math.max(0, Math.min(100, (plan.fuel.final_fuel / a.initial_fuel) * 100))
          : null;
      const low = plan?.fuel && !plan.fuel.feasible;
      const unsat = (plan?.unsatisfied_task_ids || []).length
        ? `<div class="reason" role="status">Unsatisfied (no published fix in range): ${(plan.unsatisfied_task_ids || []).join(", ")}</div>`
        : "";
      const reason =
        plan?.route?.infeasible_reason || plan?.fuel?.infeasible_reason
          ? `<div class="reason" role="alert">${plan.route?.infeasible_reason || plan.fuel.infeasible_reason}</div>`
          : "";
      const tasks = (plan?.assigned_task_ids || []).join(", ") || "none";
      const dist = plan?.route ? `${plan.route.total_distance_nmi} nmi` : "—";
      const wps = plan?.route?.waypoints?.map((w) => w.id).join(" → ") || "";
      return `
        <article class="item ${selected}" data-aircraft="${a.id}" tabindex="0" role="button" aria-pressed="${selected ? "true" : "false"}">
          <div class="item-row">
            <span class="item-id">${a.label || a.id}</span>
            ${statusBadge(status)}
          </div>
          <div class="item-meta">${typeBadge(a.type)} · home ${a.home_base_id} · tasks ${tasks}</div>
          <div class="item-meta">Route ${dist} · burn ${a.burn_rate_per_nmi}/nmi · reserve ${a.reserve_fuel}</div>
          ${wps ? `<div class="item-meta">Fixes ${wps}</div>` : ""}
          ${
            fuelPct != null
              ? `<div class="fuel-bar ${low ? "low" : ""}" title="Final fuel ${plan.fuel.final_fuel}"><span style="width:${fuelPct}%"></span></div>
                 <div class="item-meta">Final fuel ${plan.fuel.final_fuel} / ${a.initial_fuel}</div>`
              : ""
          }
          ${unsat}
          ${reason}
        </article>`;
    })
    .join("");

  list.querySelectorAll("[data-aircraft]").forEach((el) => {
    const pick = () => {
      state.selectedAircraftId = el.dataset.aircraft;
      $("#insert-aircraft").value = state.selectedAircraftId;
      renderFleet();
      renderMap();
    };
    el.addEventListener("click", pick);
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        pick();
      }
    });
  });
}

function renderStats() {
  const s = state.plan?.summary;
  $("#stat-go").textContent = s ? s.go : "—";
  $("#stat-nogo").textContent = s ? s.nogo : "—";
  $("#stat-unalloc").textContent = s ? s.unallocated : "—";
  $("#stat-idle").textContent = s ? s.idle : "—";
}

function renderMap() {
  const svg = $("#map");
  const w = state.world;
  if (!w) {
    svg.innerHTML = "";
    return;
  }

  const parts = [];
  // coastline-ish silhouette (decorative, not geospatial)
  parts.push(`
    <path d="M120,40 C180,30 260,50 320,70 C400,100 460,160 500,240 C530,310 540,390 500,450 C450,490 360,500 280,480 C200,460 140,420 110,360 C80,290 70,180 120,40 Z"
      fill="rgba(61,184,160,0.04)" stroke="rgba(61,184,160,0.18)" stroke-width="1.5"/>
  `);

  for (const n of w.navaids) {
    const [x, y] = project(n.location.lat, n.location.lon);
    parts.push(`
      <g>
        <circle cx="${x}" cy="${y}" r="3.5" fill="#5c6b7e"/>
        <text x="${x + 6}" y="${y + 3}" fill="#5c6b7e" font-size="9" font-family="IBM Plex Mono, monospace">${n.id}</text>
      </g>`);
  }

  for (const b of w.airbases) {
    const [x, y] = project(b.location.lat, b.location.lon);
    parts.push(`
      <g>
        <rect x="${x - 4}" y="${y - 4}" width="8" height="8" fill="#3db8a0" transform="rotate(45 ${x} ${y})"/>
        <text x="${x + 8}" y="${y - 6}" fill="#e6edf5" font-size="10" font-family="IBM Plex Mono, monospace">${b.id}</text>
      </g>`);
  }

  for (const t of w.tasks) {
    const [x, y] = project(t.location.lat, t.location.lon);
    const color = t.type === "ISR" ? "#5aa9e6" : "#e07a3a";
    parts.push(`
      <g>
        <circle cx="${x}" cy="${y}" r="5" fill="${color}" opacity="0.9"/>
        <text x="${x + 7}" y="${y + 3}" fill="${color}" font-size="9" font-family="IBM Plex Mono, monospace">${t.id}</text>
      </g>`);
  }

  const plans = state.plan?.plans || [];
  for (const p of plans) {
    if (!p.route?.waypoints?.length) continue;
    const selected =
      !state.selectedAircraftId || p.aircraft_id === state.selectedAircraftId;
    const pts = p.route.waypoints
      .map((wp) => project(wp.location.lat, wp.location.lon).join(","))
      .join(" ");
    const cls = p.status === "NO-GO" ? "route-path nogo" : "route-path";
    const opacity = selected ? 0.95 : 0.25;
    const width = selected ? 2.5 : 1.5;
    parts.push(
      `<polyline class="${cls}" points="${pts}" opacity="${opacity}" stroke-width="${width}"/>`,
    );
    if (selected) {
      for (const wp of p.route.waypoints) {
        const [x, y] = project(wp.location.lat, wp.location.lon);
        parts.push(
          `<circle cx="${x}" cy="${y}" r="2.5" fill="${p.status === "NO-GO" ? "#d45a5a" : "#3db8a0"}"/>`,
        );
      }
    }
  }

  svg.innerHTML = parts.join("");
}

function setPlanReady(ready) {
  $("#btn-insert").disabled = !ready;
  $("#btn-insert-submit").disabled = !ready;
}

async function loadWorld() {
  state.world = await api("/api/world");
  if (!state.selectedAircraftId && state.world.aircraft.length) {
    state.selectedAircraftId = state.world.aircraft[0].id;
  }
  renderTasks();
  renderFleet();
  renderStats();
  renderMap();
}

async function runPlan() {
  try {
    state.plan = await api("/api/plan", { method: "POST" });
    setPlanReady(true);
    // refresh world in case labels unchanged but we need task flags
    await loadWorld();
    const s = state.plan.summary;
    toast(
      `Plan complete · ${s.go} GO · ${s.nogo} NO-GO · ${s.unallocated} unallocated`,
      s.nogo || s.unallocated ? "warn" : "info",
    );
  } catch (err) {
    toast(String(err.message || err), "error");
  }
}

async function resetWorld() {
  try {
    await api("/api/reset", { method: "POST" });
    state.plan = null;
    setPlanReady(false);
    await loadWorld();
    toast("Demo world reset");
  } catch (err) {
    toast(String(err.message || err), "error");
  }
}

async function insertTask(fromForm = true) {
  try {
    const aircraft_id = fromForm
      ? $("#insert-aircraft").value
      : state.selectedAircraftId || $("#insert-aircraft").value;
    const body = {
      aircraft_id,
      task_id: $("#insert-id").value.trim() || `STK-NEW-${Date.now() % 10000}`,
      type: "STRIKE",
      lat: Number($("#insert-lat").value),
      lon: Number($("#insert-lon").value),
      priority: 3,
      label: "Injected strike (dynamic)",
    };
    const planned = await api("/api/tasks/insert", {
      method: "POST",
      body: JSON.stringify(body),
    });
    state.selectedAircraftId = planned.aircraft_id;
    // bump id for next insert (error prevention / uniqueness)
    $("#insert-id").value = `STK-NEW-${Date.now() % 10000}`;
    state.world = await api("/api/world");
    state.plan = await api("/api/plan").catch(() => state.plan);
    // Merge updated aircraft into latest plan locally if GET works
    if (state.plan) {
      state.plan.plans = state.plan.plans.map((p) =>
        p.aircraft_id === planned.aircraft_id ? planned : p,
      );
      state.plan.summary = {
        ...state.plan.summary,
        go: state.plan.plans.filter((p) => p.status === "GO").length,
        nogo: state.plan.plans.filter((p) => p.status === "NO-GO").length,
        aircraft_planned: state.plan.plans.filter((p) => p.status !== "idle").length,
        idle: state.plan.plans.filter((p) => p.status === "idle").length,
      };
    }
    renderTasks();
    renderFleet();
    renderStats();
    renderMap();
    toast(
      `${planned.aircraft_id} re-assessed → ${planned.status}`,
      planned.status === "NO-GO" ? "warn" : "info",
    );
  } catch (err) {
    toast(String(err.message || err), "error");
  }
}

function wire() {
  $("#btn-plan").addEventListener("click", runPlan);
  $("#btn-reset").addEventListener("click", resetWorld);
  $("#btn-insert").addEventListener("click", () => insertTask(false));
  $("#insert-form").addEventListener("submit", (e) => {
    e.preventDefault();
    insertTask(true);
  });
  $("#insert-aircraft").addEventListener("change", (e) => {
    state.selectedAircraftId = e.target.value;
    renderFleet();
    renderMap();
  });

  document.addEventListener("keydown", (e) => {
    if (e.target.matches("input, select, textarea")) return;
    if (e.key === "p" || e.key === "P") runPlan();
    if (e.key === "r" || e.key === "R") resetWorld();
    if ((e.key === "i" || e.key === "I") && !$("#btn-insert").disabled) insertTask(false);
    if (e.key === "?") {
      const help = document.querySelector(".help");
      help.open = !help.open;
    }
  });
}

wire();
loadWorld().catch((err) => toast(String(err.message || err), "error"));
