/**
 * o-my Mission Plan UI
 * Plan console + Routes overview (battlespace table + debrief timeline)
 * + details drawer (battlespace map / threats / tasks).
 */

const state = {
  world: null,
  plan: null,
  overview: null,
  options: null,
  compare: null,
  selectedAircraftId: null,
  selectedRouteId: null,
  selectedEventId: null,
  view: "plan",
};

const BOUNDS = { minLat: 23.5, maxLat: 34.0, minLon: 43.5, maxLon: 51.5 };
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

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

function bandClass(band) {
  return `band band-${String(band || "out").toLowerCase()}`;
}

function markerGlyph(marker) {
  if (marker === "diamond") return "◆";
  if (marker === "caret") return "▼";
  if (marker === "flag") return "⚑";
  return "·";
}

function markerColor(marker) {
  if (marker === "diamond") return "var(--collect)";
  if (marker === "caret") return "var(--strike)";
  if (marker === "flag") return "var(--verify)";
  return "var(--muted)";
}

/* ---------- Plan view (existing) ---------- */

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
          <div class="item-row"><span class="item-id">${t.id}</span>${typeBadge(t.type)}</div>
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
        ? `<div class="reason" role="status">Unsatisfied: ${(plan.unsatisfied_task_ids || []).join(", ")}</div>`
        : "";
      const reason =
        plan?.route?.infeasible_reason || plan?.fuel?.infeasible_reason
          ? `<div class="reason" role="alert">${plan.route?.infeasible_reason || plan.fuel.infeasible_reason}</div>`
          : "";
      const tasks = (plan?.assigned_task_ids || []).join(", ") || "none";
      const dist = plan?.route ? `${plan.route.total_distance_nmi} nmi` : "—";
      const wps = plan?.route?.waypoints?.map((w) => w.id).join(" → ") || "";
      const wpn = a.weapons_loadout != null ? ` · wpn ${a.weapons_loadout}` : "";
      return `
        <article class="item ${selected}" data-aircraft="${a.id}" tabindex="0" role="button">
          <div class="item-row"><span class="item-id">${a.label || a.id}</span>${statusBadge(status)}</div>
          <div class="item-meta">${typeBadge(a.type)} · home ${a.home_base_id} · tasks ${tasks}${wpn}</div>
          <div class="item-meta">Route ${dist} · burn ${a.burn_rate_per_nmi}/nmi · reserve ${a.reserve_fuel}</div>
          ${wps ? `<div class="item-meta">Fixes ${wps}</div>` : ""}
          ${
            fuelPct != null
              ? `<div class="fuel-bar ${low ? "low" : ""}"><span style="width:${fuelPct}%"></span></div>
                 <div class="item-meta">Final fuel ${plan.fuel.final_fuel} / ${a.initial_fuel}</div>`
              : ""
          }
          ${unsat}${reason}
        </article>`;
    })
    .join("");

  list.querySelectorAll("[data-aircraft]").forEach((el) => {
    const pick = () => {
      state.selectedAircraftId = el.dataset.aircraft;
      $("#insert-aircraft").value = state.selectedAircraftId;
      renderFleet();
      renderMap("#map", { showThreats: true });
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

function renderMap(svgSel = "#map", opts = {}) {
  const svg = $(svgSel);
  const w = state.world;
  if (!svg || !w) {
    if (svg) svg.innerHTML = "";
    return;
  }
  const parts = [];
  parts.push(`
    <path d="M80,460 C140,430 180,380 220,300 C260,220 300,160 360,120 C420,80 480,70 540,90 C560,140 550,220 520,280 C490,340 450,400 400,440 C340,480 200,500 80,460 Z"
      fill="rgba(61,214,198,0.04)" stroke="rgba(61,214,198,0.18)" stroke-width="1.5"/>`);

  for (const n of w.navaids || []) {
    const [x, y] = project(n.location.lat, n.location.lon);
    parts.push(`<g><circle cx="${x}" cy="${y}" r="3.5" fill="#5c6b7e"/><text x="${x + 6}" y="${y + 3}" fill="#5c6b7e" font-size="9" font-family="IBM Plex Mono, monospace">${n.id}</text></g>`);
  }
  for (const m of w.mission_waypoints || []) {
    const [x, y] = project(m.location.lat, m.location.lon);
    parts.push(`<g><polygon points="${x},${y - 5} ${x + 4},${y + 3} ${x - 4},${y + 3}" fill="#c9a227"/><text x="${x + 6}" y="${y + 3}" fill="#c9a227" font-size="8" font-family="IBM Plex Mono, monospace">${m.id.replace("MW-", "")}</text></g>`);
  }
  if (opts.showThreats !== false) {
    for (const th of w.threats || []) {
      const loc = th.location || th;
      const lat = loc.lat ?? th.latitude;
      const lon = loc.lon ?? th.longitude;
      const [x, y] = project(lat, lon);
      parts.push(`<g><circle cx="${x}" cy="${y}" r="6" fill="rgba(239,68,68,0.25)" stroke="#ef4444" stroke-width="1.5"/><text x="${x + 8}" y="${y + 3}" fill="#ef4444" font-size="8" font-family="IBM Plex Mono, monospace">${th.id || th.kind}</text></g>`);
    }
  }
  for (const b of w.airbases || []) {
    const [x, y] = project(b.location.lat, b.location.lon);
    const launch = b.id === (w.launch_base_id || "OEPS");
    parts.push(`<g><rect x="${x - 4}" y="${y - 4}" width="8" height="8" fill="${launch ? "#3dd6c6" : "#2a9a8e"}" transform="rotate(45 ${x} ${y})"/><text x="${x + 8}" y="${y - 6}" fill="#e8eef8" font-size="10" font-family="IBM Plex Mono, monospace">${b.id}${launch ? " ★" : ""}</text></g>`);
  }
  for (const t of w.tasks || []) {
    const [x, y] = project(t.location.lat, t.location.lon);
    const color = t.type === "ISR" ? "#4da3ff" : "#ff7a45";
    parts.push(`<g><circle cx="${x}" cy="${y}" r="5" fill="${color}" opacity="0.9"/><text x="${x + 7}" y="${y + 3}" fill="${color}" font-size="9" font-family="IBM Plex Mono, monospace">${t.id}</text></g>`);
  }

  const routeSource = opts.route
    ? [opts.route]
    : (state.plan?.plans || []).filter((p) => p.route?.waypoints?.length);

  for (const p of routeSource) {
    const route = p.route || p;
    const wps = route.waypoints || [];
    if (!wps.length) continue;
    const selected =
      opts.forceSelected ||
      !state.selectedAircraftId ||
      p.aircraft_id === state.selectedAircraftId ||
      p.route_name;
    const pts = wps
      .map((wp) => project(wp.lat ?? wp.location?.lat, wp.lon ?? wp.location?.lon).join(","))
      .join(" ");
    const nogo = (p.status || "") === "NO-GO";
    const cls = nogo ? "route-path nogo" : "route-path";
    const opacity = selected ? 0.95 : 0.25;
    const width = selected ? 2.5 : 1.5;
    // Colored segments if provided
    if (opts.segments?.length) {
      for (const seg of opts.segments) {
        const a = wps[seg.index];
        const b = wps[seg.index + 1];
        if (!a || !b) continue;
        const [x1, y1] = project(a.lat ?? a.location?.lat, a.lon ?? a.location?.lon);
        const [x2, y2] = project(b.lat ?? b.location?.lat, b.lon ?? b.location?.lon);
        parts.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${seg.color}" stroke-width="3" opacity="0.9"/>`);
      }
    } else {
      parts.push(`<polyline class="${cls}" points="${pts}" opacity="${opacity}" stroke-width="${width}"/>`);
    }
    if (selected) {
      for (const wp of wps) {
        const [x, y] = project(wp.lat ?? wp.location?.lat, wp.lon ?? wp.location?.lon);
        parts.push(`<circle cx="${x}" cy="${y}" r="2.5" fill="${nogo ? "#ff5c6c" : "#3dd6c6"}"/>`);
      }
    }
  }
  svg.innerHTML = parts.join("");
}

/* ---------- Routes overview ---------- */

function renderMetrics() {
  const m = state.overview?.metrics;
  const host = $("#routes-metrics");
  if (!m) {
    host.innerHTML = `<div class="empty">Run a plan cycle to populate routes.</div>`;
    return;
  }
  host.innerHTML = `
    <div class="metric"><span class="metric-val">${m.aircraft_count}</span><span class="metric-lbl">Aircraft</span><span class="metric-sub">${m.aircraft_go} GO · ${m.aircraft_nogo} NO-GO · ${m.aircraft_idle} idle</span></div>
    <div class="metric"><span class="metric-val isr">${m.assigned_isr}</span><span class="metric-lbl">Assigned ISR</span><span class="metric-sub">${m.assigned_total} total assigned</span></div>
    <div class="metric"><span class="metric-val strike">${m.assigned_strike}</span><span class="metric-lbl">Assigned strike</span></div>
    <div class="metric"><span class="metric-val warn">${m.skipped_tasks}</span><span class="metric-lbl">Skipped tasks</span><span class="metric-sub">${(m.skipped_task_ids || []).slice(0, 4).join(", ") || "—"}</span></div>
    <div class="metric"><span class="metric-val">${m.weapons_utilized}</span><span class="metric-lbl">Weapons utilized</span><span class="metric-sub">of ${m.weapons_loadout_total} loadout</span></div>
  `;
}

function renderRoutesTable() {
  const tbody = $("#routes-tbody");
  const routes = state.overview?.routes || [];
  if (!routes.length) {
    tbody.innerHTML = `<tr class="empty"><td colspan="9">No routes — run a plan cycle</td></tr>`;
    return;
  }
  tbody.innerHTML = routes
    .map((r) => {
      const prim = r.primary_threat;
      const band = prim?.band || "OUT";
      const closest = prim ? `${prim.closest_approach_nm.toFixed(1)} nm` : "—";
      const sel = state.selectedRouteId === r.aircraft_id ? "selected" : "";
      const sev = (prim?.severity || "").toLowerCase();
      return `<tr class="${sel} ${sev}" data-route="${r.aircraft_id}">
        <td><button type="button" class="linkish"><strong>${r.route_name}</strong></button><div class="item-meta">${r.callsign}</div></td>
        <td>${typeBadge(r.aircraft_type)}</td>
        <td>${r.task_breakout.isr} ISR · ${r.task_breakout.strike} STK</td>
        <td class="num">${r.total_distance_nmi.toFixed(0)} nm</td>
        <td class="num">${closest}</td>
        <td><span class="${bandClass(band)}">${band}</span></td>
        <td class="num">${r.weapons_utilized}/${r.weapons_loadout}</td>
        <td>${statusBadge(r.status)}</td>
        <td><button type="button" class="btn btn-ghost btn-details" data-details="${r.aircraft_id}">Details</button></td>
      </tr>`;
    })
    .join("");

  tbody.querySelectorAll("tr[data-route]").forEach((tr) => {
    tr.addEventListener("click", (e) => {
      if (e.target.closest("[data-details]")) return;
      selectRoute(tr.dataset.route);
    });
  });
  tbody.querySelectorAll("[data-details]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      selectRoute(btn.dataset.details);
      openDetails();
    });
  });
}

function selectedRoute() {
  return (state.overview?.routes || []).find((r) => r.aircraft_id === state.selectedRouteId) || null;
}

function selectRoute(id) {
  state.selectedRouteId = id;
  state.selectedEventId = null;
  renderRoutesTable();
  renderInspect();
  $("#btn-more-details").disabled = !selectedRoute();
}

function renderInspect() {
  const r = selectedRoute();
  const title = $("#inspect-title");
  if (!r) {
    title.textContent = "Select a route";
    $("#route-timeline").innerHTML = "";
    $("#route-milestones").innerHTML = `<p class="empty">Pick a route from the table to see the end-to-end timeline and key events.</p>`;
    return;
  }
  title.textContent = `${r.route_name} · ${r.callsign}`;
  renderDebriefTimeline(r);
  renderMilestones(r);
}

function renderDebriefTimeline(route) {
  const events = route.timeline_events || [];
  const host = $("#route-timeline");
  if (!events.length) {
    host.innerHTML = `<div class="empty">No timeline events</div>`;
    return;
  }
  const maxD = Math.max(...events.map((e) => e.distance_nmi), 1);
  const active = events.find((e) => e.event_id === state.selectedEventId) || events[0];
  const fillPct = (active.distance_nmi / maxD) * 100;
  host.innerHTML = `
    <div class="tl-meta">
      <span class="mono">T+0</span>
      <span>Mission timeline · ◆ collect · ▼ strike · ⚑ launch/recover</span>
      <span class="mono">${maxD.toFixed(0)} nm</span>
    </div>
    <div class="tl-track" role="slider" aria-label="Route timeline">
      <div class="tl-fill" style="width:${fillPct}%"></div>
      ${events
        .filter((e) => e.marker && e.marker !== "none")
        .map((e) => {
          const pct = (e.distance_nmi / maxD) * 100;
          const activeCls = e.event_id === active.event_id ? "active" : "";
          return `<button type="button" class="tl-marker ${activeCls}" data-event="${e.event_id}"
            style="left:${pct}%; color:${markerColor(e.marker)}" title="${e.title}">${markerGlyph(e.marker)}</button>`;
        })
        .join("")}
      <div class="tl-playhead" style="left:${fillPct}%"></div>
    </div>
    <div class="item-meta" style="margin-top:0.45rem">${active.sim_offset} · ${active.title}</div>
  `;
  host.querySelectorAll("[data-event]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.selectedEventId = btn.dataset.event;
      renderInspect();
    });
  });
}

function renderMilestones(route) {
  const events = route.timeline_events || [];
  const host = $("#route-milestones");
  host.innerHTML = events
    .map((e) => {
      const active = e.event_id === state.selectedEventId ? "active" : "";
      return `<button type="button" class="milestone ${active}" data-event="${e.event_id}">
        <div class="ms-row">
          <span style="color:${markerColor(e.marker)}">${markerGlyph(e.marker)}</span>
          <span class="mono">${e.sim_offset}</span>
          <span class="badge badge-idle" style="margin-left:auto">${e.status}</span>
        </div>
        <div class="ms-title">${e.title}</div>
        <div class="ms-out">${e.outcome || e.summary}</div>
      </button>`;
    })
    .join("");
  host.querySelectorAll("[data-event]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.selectedEventId = btn.dataset.event;
      renderInspect();
    });
  });
}

/* ---------- Details drawer ---------- */

function openDetails() {
  const r = selectedRoute();
  if (!r) return;
  const drawer = $("#details-drawer");
  drawer.hidden = false;
  $("#drawer-title").textContent = `${r.route_name} · ${r.callsign}`;
  const prim = r.primary_threat;
  $("#drawer-sub").textContent = prim
    ? `Closest threat ${prim.threat_id} · ${prim.closest_approach_nm.toFixed(1)} nm · ${prim.band} · ${prim.severity}`
    : "No threats within 160 nm jam radius";

  const segs = prim?.segments || [];
  renderMap("#detail-map", {
    route: r,
    forceSelected: true,
    segments: segs,
    showThreats: true,
  });
  // Also draw threats from overview
  renderDetailThreats(r);
  renderDetailTasks(r);
  renderSegmentTimeline(r);
}

function closeDetails() {
  $("#details-drawer").hidden = true;
}

function renderDetailThreats(route) {
  const host = $("#detail-threats");
  const rows = route.threats || [];
  if (!rows.length) {
    host.innerHTML = `<table><tbody><tr class="empty"><td>No threats within jam radius</td></tr></tbody></table>`;
    return;
  }
  host.innerHTML = `<table>
    <thead><tr><th>Threat</th><th>Kind</th><th>Closest</th><th>Band</th><th>Segs</th><th>Severity</th></tr></thead>
    <tbody>
      ${rows
        .map(
          (t) => `<tr class="${(t.severity || "").toLowerCase()}">
        <td><strong>${t.threat_id}</strong><div class="item-meta">${t.threat_label}</div></td>
        <td>${t.threat_kind}</td>
        <td>${t.closest_approach_nm.toFixed(1)} nm</td>
        <td><span class="${bandClass(t.band)}">${t.band}</span></td>
        <td>${t.impacted_segment_count}</td>
        <td>${t.severity}</td>
      </tr>`,
        )
        .join("")}
    </tbody></table>`;
}

function renderDetailTasks(route) {
  const host = $("#detail-tasks");
  const tasks = route.tasks || [];
  if (!tasks.length) {
    host.innerHTML = `<div class="empty">No assigned tasks</div>`;
    return;
  }
  host.innerHTML = tasks
    .map(
      (t) => `<article class="item">
      <div class="item-row"><span class="item-id">${t.id}</span>${typeBadge(t.type)}</div>
      <div class="item-meta">${t.label || "—"} · ${t.lat.toFixed(2)}, ${t.lon.toFixed(2)} · pri ${t.priority}</div>
    </article>`,
    )
    .join("");
}

function renderSegmentTimeline(route) {
  const host = $("#detail-segment-timeline");
  const prim = route.primary_threat;
  const segs = prim?.segments || [];
  const total = route.total_distance_nmi || 0;
  const tasks = route.tasks || [];
  const cum = prim?.cumulative_nmi || [0];
  const closestPct =
    total && cum.length
      ? (((cum[prim.closest_index] || 0) + (cum[prim.closest_index + 1] || 0)) / 2 / total) * 100
      : 0;

  const taskMarks = tasks
    .map((t) => {
      // place near mid-route for display if no exact association
      const wpIdx = (route.waypoints || []).findIndex((w) => w.associated_task_id === t.id);
      let pct = 50;
      if (wpIdx >= 0 && cum[wpIdx] != null && total) pct = (cum[wpIdx] / total) * 100;
      return `<span class="task-mark" style="left:${pct}%" title="${t.id}">${t.type.slice(0, 3)}</span>`;
    })
    .join("");

  host.innerHTML = `
    <h3>Route timeline · ${route.route_name}</h3>
    <p class="hint">${prim ? `${prim.threat_id} closest ${prim.closest_approach_nm.toFixed(1)} nm · ${prim.severity}` : "No primary threat"} · distance axis</p>
    <div class="seg-tracks">
      <div class="seg-label">Impact</div>
      <div class="seg-line">
        ${
          segs.length
            ? segs
                .map(
                  (s) =>
                    `<span class="seg" style="flex:${Math.max(s.length_nmi, 0.5)};background:${s.color}" title="Seg ${s.index + 1} · ${s.closest_nm} nm · ${s.band}"></span>`,
                )
                .join("")
            : `<span class="seg" style="flex:1;background:#64748b"></span>`
        }
        ${prim ? `<span class="threat-mark" style="left:${closestPct}%">▼</span>` : ""}
      </div>
      <div class="seg-label">Onboard</div>
      <div class="task-rail"><div class="rail"></div>${taskMarks}</div>
      <div class="seg-label"></div>
      <div class="seg-axis"><span>0 nm</span><span>${total.toFixed(0)} nm</span></div>
    </div>
  `;
}

/* ---------- View / wiring ---------- */

function setView(name) {
  state.view = name;
  $$(".tab").forEach((t) => {
    const on = t.dataset.view === name;
    t.classList.toggle("active", on);
    t.setAttribute("aria-selected", on ? "true" : "false");
  });
  $$("[data-view-panel]").forEach((p) => {
    const on = p.dataset.viewPanel === name;
    p.hidden = !on;
    p.classList.toggle("active", on);
  });
}

function setPlanReady(ready) {
  $("#btn-insert").disabled = !ready;
  $("#btn-insert-submit").disabled = !ready;
  const hasPref = !!(
    state.compare?.preferred_option_id ||
    state.options?.options?.some((o) => o.preferred)
  );
  $("#btn-export").disabled = !ready && !hasPref;
  $("#tab-routes").disabled = !ready;
}

function emphasisLabel(e) {
  if (e === "efficient") return "Efficient";
  if (e === "synchronized") return "Synchronized";
  if (e === "unexpected_axis") return "Unexpected axis";
  return e || "—";
}

function renderOptionCards() {
  const host = $("#option-cards");
  if (!host) return;
  const slots = state.compare?.slots || state.options?.slots || { A: null, B: null, C: null };
  const byId = Object.fromEntries((state.options?.options || []).map((o) => [o.option_id, o]));
  const order = ["A", "B", "C"];
  const defaults = {
    A: { emphasis: "efficient", title: "Option A — Efficient" },
    B: { emphasis: "synchronized", title: "Option B — Synchronized" },
    C: { emphasis: "unexpected_axis", title: "Option C — Unexpected axis" },
  };

  host.innerHTML = order
    .map((slot) => {
      const oid = slots[slot];
      const opt = oid ? byId[oid] : null;
      if (!opt) {
        const d = defaults[slot];
        return `
          <article class="option-card empty" data-emphasis="${d.emphasis}">
            <div class="slot-mark">SLOT ${slot}</div>
            <h3>${d.title}</h3>
            <p class="meta">Not built yet. Use <strong>Build A / B / C</strong> to frame the top-three working set.</p>
            <div class="option-metrics">
              <div class="om"><span>Emphasis</span><strong>${emphasisLabel(d.emphasis)}</strong></div>
              <div class="om"><span>Status</span><strong>empty</strong></div>
            </div>
          </article>`;
      }
      const sync = opt.sync;
      let syncHtml = "";
      if (sync) {
        const ok = sync.alignment_ok && sync.bda_lag_ok !== false;
        const cls = ok ? "ok" : "warn";
        const bda =
          sync.bda_lag_ok == null ? "" : sync.bda_lag_ok ? " · BDA ok" : " · BDA early";
        syncHtml = `<div class="sync-chip ${cls}">sync ${sync.timing_alignment} · ΔTOT ${sync.tot_spread_minutes}m · BDA lag ${sync.bda_lag_minutes}m${bda}</div>`;
      }
      const vias = (opt.vias || opt.router_inputs?.vias || []).join(" → ") || "—";
      return `
        <article class="option-card ${opt.preferred ? "preferred" : ""}" data-emphasis="${opt.emphasis}" data-option="${opt.option_id}">
          <div class="slot-mark">SLOT ${slot}${opt.preferred ? " · PREFERRED" : ""}</div>
          <h3>${opt.label}</h3>
          <p class="meta">${emphasisLabel(opt.emphasis)} · supplier ${opt.supplier_id || "fallback"} · vias ${vias}</p>
          <div class="option-metrics">
            <div class="om"><span>GO</span><strong class="go">${opt.go_count}</strong></div>
            <div class="om"><span>NO-GO</span><strong class="nogo">${opt.nogo_count}</strong></div>
            <div class="om"><span>Unallocated</span><strong>${opt.unallocated_count}</strong></div>
            <div class="om"><span>Distance</span><strong>${Number(opt.total_distance_nmi).toFixed(0)} nmi</strong></div>
          </div>
          ${syncHtml}
          <div class="card-actions">
            <button type="button" class="btn btn-primary btn-prefer" data-prefer="${opt.option_id}">Prefer</button>
            <button type="button" class="btn btn-export-option" data-export-option="${opt.option_id}">Export</button>
          </div>
        </article>`;
    })
    .join("");

  host.querySelectorAll("[data-prefer]").forEach((btn) => {
    btn.addEventListener("click", () => preferOption(btn.dataset.prefer));
  });
  host.querySelectorAll("[data-export-option]").forEach((btn) => {
    btn.addEventListener("click", () => exportRoutes(btn.dataset.exportOption));
  });
}

function renderCompareTable() {
  const tbody = $("#compare-tbody");
  if (!tbody) return;
  const rows = state.compare?.options || [];
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="hint">Build the top-three to populate comparison.</td></tr>`;
    return;
  }
  tbody.innerHTML = rows
    .map((o) => {
      const syncBits = o.sync
        ? `${o.sync.timing_alignment} (Δ${o.sync.tot_spread_minutes}m)`
        : (o.vias || []).length
          ? (o.vias || []).slice(0, 3).join(" → ")
          : "—";
      return `
        <tr class="${o.preferred ? "preferred-row" : ""}" data-option="${o.option_id}">
          <td>${o.slot || "—"}</td>
          <td>${emphasisLabel(o.emphasis)}</td>
          <td>${o.go_count}</td>
          <td>${o.nogo_count}</td>
          <td>${o.unallocated_count}</td>
          <td>${Number(o.total_distance_nmi).toFixed(0)}</td>
          <td>${syncBits}</td>
          <td>${o.preferred ? "yes" : "—"}</td>
          <td>
            <button type="button" class="btn btn-ghost btn-prefer" data-prefer="${o.option_id}">Prefer</button>
          </td>
        </tr>`;
    })
    .join("");
  tbody.querySelectorAll("[data-prefer]").forEach((btn) => {
    btn.addEventListener("click", () => preferOption(btn.dataset.prefer));
  });
}

async function loadOptions() {
  state.options = await api("/api/options");
  state.compare = await api("/api/options/compare");
  const suppliers = await api("/api/suppliers").catch(() => null);
  if (suppliers?.active && $("#options-supplier")) {
    $("#options-supplier").value = suppliers.active;
  }
  renderOptionCards();
  renderCompareTable();
  const hasPref = !!(
    state.compare?.preferred_option_id || state.options?.options?.some((o) => o.preferred)
  );
  if (hasPref) $("#btn-export").disabled = false;
}

async function buildTopThree() {
  try {
    const supplier = $("#options-supplier")?.value || "fallback";
    const data = await api(
      `/api/options/top-three?force=true&supplier_id=${encodeURIComponent(supplier)}`,
      { method: "POST" },
    );
    state.options = { slots: data.slots, options: data.options };
    state.compare = await api("/api/options/compare");
    renderOptionCards();
    renderCompareTable();
    toast(`Top-three ready · session supplier ${supplier}`, "info");
    setView("options");
    if (data.options?.length) {
      try {
        state.plan = await api("/api/plan");
        setPlanReady(true);
        await loadOverview();
      } catch {
        setPlanReady(true);
      }
    }
  } catch (err) {
    toast(String(err.message || err), "error");
  }
}

async function preferOption(optionId) {
  try {
    await api(`/api/options/${optionId}/prefer`, {
      method: "POST",
      body: JSON.stringify({ preferred: true }),
    });
    await loadOptions();
    $("#btn-export").disabled = false;
    toast("Preferred option set — Export uses this by default");
  } catch (err) {
    toast(String(err.message || err), "error");
  }
}

async function loadWorld() {
  state.world = await api("/api/world");
  if (state.world?.scenario_id) {
    const badge = $("#scenario-badge");
    if (badge) badge.textContent = state.world.scenario_id;
  }
  if (!state.selectedAircraftId && state.world.aircraft.length) {
    state.selectedAircraftId = state.world.aircraft[0].id;
  }
  renderTasks();
  renderFleet();
  renderStats();
  renderMap("#map", { showThreats: true });
}

async function loadOverview() {
  state.overview = await api("/api/routes/overview");
  if (!state.selectedRouteId && state.overview.routes?.length) {
    state.selectedRouteId = state.overview.routes[0].aircraft_id;
  }
  renderMetrics();
  renderRoutesTable();
  renderInspect();
  $("#btn-more-details").disabled = !selectedRoute();
}

async function runPlan() {
  try {
    state.plan = await api("/api/plan", { method: "POST" });
    setPlanReady(true);
    await loadWorld();
    await loadOverview();
    const s = state.plan.summary;
    toast(`Plan complete · ${s.go} GO · ${s.nogo} NO-GO · ${s.unallocated} unallocated`, s.nogo || s.unallocated ? "warn" : "info");
    setView("routes");
  } catch (err) {
    toast(String(err.message || err), "error");
  }
}

async function resetWorld() {
  try {
    await api("/api/reset", { method: "POST" });
    state.plan = null;
    state.overview = null;
    state.options = null;
    state.compare = null;
    state.selectedRouteId = null;
    setPlanReady(false);
    closeDetails();
    setView("plan");
    await loadWorld();
    await loadOptions();
    toast("Demo world reset");
  } catch (err) {
    toast(String(err.message || err), "error");
  }
}

async function exportRoutes(optionId = null) {
  try {
    const body = { include_nogo: false, write: true };
    if (optionId) body.option_id = optionId;
    const bundle = await api("/api/routes/export", {
      method: "POST",
      body: JSON.stringify(body),
    });
    const n = bundle.summary?.route_count ?? bundle.routes?.length ?? 0;
    const src = bundle.export_source || "session";
    const opt = bundle.option_id ? ` · option ${bundle.option_id.slice(0, 8)}` : "";
    toast(`Exported ${n} GO route(s) (${src}${opt}) → ${bundle.written_paths?.latest || "data/routes/"}`);
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
      label: "Injected strike (dynamic) — Kuwait north",
    };
    const planned = await api("/api/tasks/insert", { method: "POST", body: JSON.stringify(body) });
    state.selectedAircraftId = planned.aircraft_id;
    $("#insert-id").value = `STK-NEW-${Date.now() % 10000}`;
    state.world = await api("/api/world");
    state.plan = await api("/api/plan").catch(() => state.plan);
    if (state.plan) {
      state.plan.plans = state.plan.plans.map((p) =>
        p.aircraft_id === planned.aircraft_id ? planned : p,
      );
    }
    await loadOverview();
    renderTasks();
    renderFleet();
    renderStats();
    renderMap("#map", { showThreats: true });
    toast(`${planned.aircraft_id} re-assessed → ${planned.status}`, planned.status === "NO-GO" ? "warn" : "info");
  } catch (err) {
    toast(String(err.message || err), "error");
  }
}

function wire() {
  $("#btn-plan").addEventListener("click", runPlan);
  $("#btn-export").addEventListener("click", () => exportRoutes());
  $("#btn-reset").addEventListener("click", resetWorld);
  $("#btn-insert").addEventListener("click", () => insertTask(false));
  $("#btn-more-details").addEventListener("click", openDetails);
  $("#btn-top-three")?.addEventListener("click", buildTopThree);
  $("#btn-refresh-options")?.addEventListener("click", () =>
    loadOptions().catch((err) => toast(String(err.message || err), "error")),
  );
  $("#insert-form").addEventListener("submit", (e) => {
    e.preventDefault();
    insertTask(true);
  });
  $("#insert-aircraft").addEventListener("change", (e) => {
    state.selectedAircraftId = e.target.value;
    renderFleet();
    renderMap("#map", { showThreats: true });
  });
  $$(".tab").forEach((t) => {
    t.addEventListener("click", () => {
      if (t.disabled) return;
      setView(t.dataset.view);
      if (t.dataset.view === "options") {
        loadOptions().catch((err) => toast(String(err.message || err), "error"));
      }
    });
  });
  $$("[data-close-drawer]").forEach((el) => el.addEventListener("click", closeDetails));

  document.addEventListener("keydown", (e) => {
    if (e.target.matches("input, select, textarea")) return;
    if (e.key === "p" || e.key === "P") runPlan();
    if (e.key === "o" || e.key === "O") {
      setView("options");
      loadOptions().catch((err) => toast(String(err.message || err), "error"));
    }
    if (e.key === "e" || e.key === "E") {
      if (!$("#btn-export").disabled) exportRoutes();
    }
    if (e.key === "r" || e.key === "R") resetWorld();
    if ((e.key === "i" || e.key === "I") && !$("#btn-insert").disabled) insertTask(false);
    if (e.key === "1") setView("plan");
    if (e.key === "2") {
      setView("options");
      loadOptions().catch(() => {});
    }
    if (e.key === "3" && !$("#tab-routes").disabled) setView("routes");
    if (e.key === "Escape") closeDetails();
    if (e.key === "?") {
      const help = document.querySelector(".help");
      help.open = !help.open;
    }
  });
}

wire();
loadWorld()
  .then(() => loadOptions())
  .catch((err) => toast(String(err.message || err), "error"));
