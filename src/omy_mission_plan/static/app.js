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
  costgrid: null,
  exposure: null,
  timeline: null,
  scrubMin: 0,
  positions: null,
  selectedAircraftId: null,
  selectedRouteId: null,
  selectedEventId: null,
  selectedThreatId: null,
  hoveredThreatId: null,
  view: "plan",
  routesPane: "table",
  showCostgrid: false,
  showRings: false,
  showThreats: true,
  showRoutes: true,
  showAircraftOnRoute: true,
  groupByType: true,
  cellNmi: 45,
  cellStyle: "hex",
  altitudeFt: 10000,
  legendFilter: null,
  routeExposureMode: true,
};

const COST_RAMP = {
  LOW: "#2ecc71",
  MEDIUM: "#f1c40f",
  HIGH: "#e67e22",
  CRITICAL: "#e74c3c",
};

const EXPOSURE_STROKE = {
  CLEAR: "#3dd6c6",
  JAMMED: "#f0c14a",
  LETHAL: "#ff5c6c",
};

const BOUNDS = { minLat: 23.5, maxLat: 34.0, minLon: 43.5, maxLon: 51.5 };
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

/* ---------- Base map (o-my suite shared dark tiles) ---------- */

/**
 * o-my suite shared dark base map. Same values as o-my-debrief
 * `frontend/src/lib/basemap.js` (reference) and the battlespace-manager copies;
 * see o-my-debrief docs/SHARED-DARK-MAP.md before changing anything here.
 *
 * Esri World Dark Gray Canvas (base + reference labels): key-free from any
 * origin, dark, regional scale. CartoDB Dark Matter was the original pick but
 * CARTO watermarks every un-keyed tile since Sept 2026, so it is no longer
 * usable without committing a key.
 *
 * `opacity` over the dark console background (see `.leaflet-container`) pulls
 * Esri's mid-gray canvas down to the ops-console palette.
 */
const SUITE_DARK_TILES = Object.freeze({
  url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
  attribution: "&copy; Esri, HERE, Garmin, &copy; OpenStreetMap contributors",
  maxZoom: 12,
  opacity: 0.65,
});
const SUITE_DARK_LABELS = Object.freeze({
  url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
  maxZoom: SUITE_DARK_TILES.maxZoom,
  opacity: 0.45,
});
const THEATER_BOUNDS = [
  [BOUNDS.minLat, BOUNDS.minLon],
  [BOUNDS.maxLat, BOUNDS.maxLon],
];
const THEATER_FIT = { padding: [6, 6], animate: false };
const hasLeaflet = typeof window !== "undefined" && typeof window.L !== "undefined";

/** Fixed equirectangular projection onto the legacy 640x520 canvas (offline fallback only). */
function projectFixed(lat, lon) {
  const x = ((lon - BOUNDS.minLon) / (BOUNDS.maxLon - BOUNDS.minLon)) * 600 + 20;
  const y = ((BOUNDS.maxLat - lat) / (BOUNDS.maxLat - BOUNDS.minLat)) * 480 + 20;
  return [x, y];
}

/**
 * Leaflet SVG renderer with one extra <g> that the string-built plan overlays
 * (cost field, rings, routes, markers) are written into. Leaflet keeps the
 * svg positioned / viewBoxed in layer-point space across pan and zoom and fires
 * `update` when overlays must be re-projected.
 */
const PlanOverlayRenderer = hasLeaflet
  ? L.SVG.extend({
      _initContainer() {
        L.SVG.prototype._initContainer.call(this);
        this._planGroup = L.SVG.create("g");
        this._planGroup.setAttribute("class", "plan-overlay");
        this._container.appendChild(this._planGroup);
      },
      planGroup() {
        return this._planGroup;
      },
    })
  : null;

/**
 * Per-container map context:
 * { map, group, project, lastOpts, redraw, home: { bounds, options }, autoFit }
 * `autoFit` keeps the map on `home` through container resizes until the user
 * pans or zooms (the plan frame shrinks once the panels below it render).
 */
const mapCtxs = new Map();

function createBaseMap(el, { interactive = true } = {}) {
  const map = L.map(el, {
    maxZoom: SUITE_DARK_TILES.maxZoom,
    minZoom: 4,
    zoomSnap: 0.25,
    zoomControl: interactive,
    attributionControl: interactive,
    dragging: interactive,
    scrollWheelZoom: interactive,
    doubleClickZoom: interactive,
    boxZoom: interactive,
    keyboard: interactive,
    touchZoom: interactive,
  });
  L.tileLayer(SUITE_DARK_TILES.url, SUITE_DARK_TILES).addTo(map);
  L.tileLayer(SUITE_DARK_LABELS.url, SUITE_DARK_LABELS).addTo(map);
  // Layers (including the overlay renderer) only attach once the map has a view.
  map.fitBounds(THEATER_BOUNDS, THEATER_FIT);
  return map;
}

function fitHome(ctx) {
  if (!ctx?.map || !ctx.home?.bounds) return;
  ctx.map.fitBounds(ctx.home.bounds, ctx.home.options || THEATER_FIT);
}

function getMapCtx(sel) {
  const el = $(sel);
  if (!el) return null;
  let ctx = mapCtxs.get(sel);
  if (ctx) return ctx;

  if (!hasLeaflet) {
    // Leaflet CDN unavailable: keep the overlays alive on a plain SVG.
    el.innerHTML = `<svg class="fallback-svg" viewBox="0 0 640 520"><g class="plan-overlay"></g></svg>`;
    ctx = { map: null, group: el.querySelector("g"), project: projectFixed, lastOpts: null };
    mapCtxs.set(sel, ctx);
    return ctx;
  }

  const interactive = !el.closest(".inset-overview");
  const map = createBaseMap(el, { interactive });
  const renderer = new PlanOverlayRenderer({ padding: 0.5 }).addTo(map);
  ctx = {
    map,
    group: renderer.planGroup(),
    project(lat, lon) {
      const p = map.latLngToLayerPoint([lat, lon]);
      return [p.x, p.y];
    },
    lastOpts: null,
    home: { bounds: THEATER_BOUNDS, options: THEATER_FIT },
    autoFit: true,
  };
  ctx.redraw = () => {
    if (ctx.lastOpts) renderMap(sel, ctx.lastOpts);
  };
  renderer.on("update", ctx.redraw);

  if (interactive) {
    const userTouched = () => {
      ctx.autoFit = false;
    };
    el.addEventListener("pointerdown", userTouched);
    el.addEventListener("wheel", userTouched, { passive: true });
    el.addEventListener("keydown", userTouched);
  }
  if (typeof ResizeObserver !== "undefined") {
    new ResizeObserver(() => {
      if (!el.clientWidth || !el.clientHeight) return;
      map.invalidateSize({ animate: false });
      if (ctx.autoFit) fitHome(ctx);
    }).observe(el);
  }
  mapCtxs.set(sel, ctx);
  return ctx;
}

function fitTheater(sel = "#map") {
  const ctx = mapCtxs.get(sel);
  if (!ctx?.map) return;
  ctx.home = { bounds: THEATER_BOUNDS, options: THEATER_FIT };
  ctx.autoFit = true;
  ctx.map.fitBounds(THEATER_BOUNDS, { padding: [6, 6] });
}

/** Call after a hidden map container becomes visible / changes size. */
function refreshMapSize(sel) {
  const ctx = mapCtxs.get(sel);
  if (!ctx?.map) return;
  ctx.map.invalidateSize({ animate: false });
  if (ctx.autoFit) fitHome(ctx);
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

function exposureClass(exposure) {
  return `exposure-pill exposure-${String(exposure || "clear").toLowerCase()}`;
}

function frequencyBandLabel(threat) {
  return threat?.frequency_band ? `RF ${threat.frequency_band}` : "RF band —";
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

function orderedAircraft() {
  const aircraft = state.world?.aircraft || [];
  const order = state.world?.platform_order || aircraft.map((a) => a.id);
  const rank = Object.fromEntries(order.map((id, i) => [id, i]));
  return [...aircraft].sort((a, b) => (rank[a.id] ?? 999) - (rank[b.id] ?? 999));
}

function renderFleet() {
  const list = $("#fleet-list");
  const select = $("#insert-aircraft");
  const aircraft = orderedAircraft();
  const plansById = Object.fromEntries((state.plan?.plans || []).map((p) => [p.aircraft_id, p]));
  const group = $("#tog-group-type")?.checked ?? state.groupByType;
  state.groupByType = group;

  select.innerHTML = aircraft
    .map((a) => `<option value="${a.id}">${a.label || a.id} (${a.type})</option>`)
    .join("");
  if (state.selectedAircraftId) select.value = state.selectedAircraftId;

  const renderCard = (a, idx, arr) => {
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
        <div class="item-row">
          <span class="item-id">${a.label || a.id}</span>${statusBadge(status)}
          <span class="reorder">
            <button type="button" class="btn-icon" data-move="-1" title="Move up" ${idx === 0 ? "disabled" : ""}>↑</button>
            <button type="button" class="btn-icon" data-move="1" title="Move down" ${idx === arr.length - 1 ? "disabled" : ""}>↓</button>
          </span>
        </div>
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
  };

  if (group) {
    const types = ["ISR", "FIGHTER", "BOMBER"];
    list.innerHTML = types
      .map((t) => {
        const groupAc = aircraft.filter((a) => a.type === t);
        if (!groupAc.length) return "";
        return `<div class="fleet-group"><div class="fleet-group-head">${t}</div>${groupAc
          .map((a, i) => renderCard(a, aircraft.indexOf(a), aircraft))
          .join("")}</div>`;
      })
      .join("");
  } else {
    list.innerHTML = aircraft.map((a, i) => renderCard(a, i, aircraft)).join("");
  }

  list.querySelectorAll("[data-aircraft]").forEach((el) => {
    const pick = () => {
      state.selectedAircraftId = el.dataset.aircraft;
      $("#insert-aircraft").value = state.selectedAircraftId;
      renderFleet();
      refreshMap();
    };
    el.addEventListener("click", (e) => {
      if (e.target.closest("[data-move]")) return;
      pick();
    });
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        pick();
      }
    });
    el.querySelectorAll("[data-move]").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const delta = Number(btn.dataset.move);
        const order = orderedAircraft().map((a) => a.id);
        const idx = order.indexOf(el.dataset.aircraft);
        const j = idx + delta;
        if (j < 0 || j >= order.length) return;
        [order[idx], order[j]] = [order[j], order[idx]];
        await api("/api/platforms/order", {
          method: "POST",
          body: JSON.stringify({ order, group_by_type: state.groupByType }),
        });
        state.world = await api("/api/world");
        renderFleet();
        if (state.timeline) await loadTimeline();
        refreshMap();
      });
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

function costLevelColor(level, intensity = 1) {
  // Solid fills only: fully opaque, non-overlapping cells, so no alpha
  // stacking. A legend filter dims non-selected levels to a solid slate.
  void intensity;
  if (state.legendFilter && state.legendFilter !== level) return "#263449";
  return COST_RAMP[level] || "#94a3b8";
}

function syncCostLegend() {
  const host = $("#cost-legend");
  if (!host) return;
  host.hidden = !state.showCostgrid;
  host.querySelectorAll(".cost-level").forEach((btn) => {
    btn.classList.toggle("active", state.legendFilter === btn.dataset.level);
  });
}

function nmToSvgRadius(project, lat, lon, radiusNmi) {
  const [x0] = project(lat, lon);
  const [x1] = project(lat, lon + radiusNmi / (60 * Math.cos((lat * Math.PI) / 180)));
  return Math.max(4, Math.abs(x1 - x0));
}

function refreshMap() {
  renderMap("#map", {
    showThreats: state.showThreats,
    showRings: state.showRings,
    showRoutes: state.showRoutes,
    showCostgrid: state.showCostgrid,
    showAircraft: state.showAircraftOnRoute,
  });
  syncCostLegend();
  renderExposurePanel();
}

function renderExposurePanel() {
  const host = $("#exposure-panel");
  if (!host) return;
  const platforms = state.exposure?.platforms || [];
  if (!platforms.length) {
    host.innerHTML = "";
    return;
  }
  const rows = platforms
    .filter((p) => (p.threats_that_see || []).length)
    .map((p) => {
      const sees = (p.threats_that_see || [])
        .map((t) => `${t.threat_id} (${String(t.exposure || "").toLowerCase()}, ${frequencyBandLabel(t)})`)
        .join(", ");
      return `<div><strong>${p.label || p.aircraft_id}</strong> exposed to ${sees}</div>`;
    });
  host.innerHTML = rows.length
    ? `<div class="exposure-head">Threat exposure on routes (jammed / lethal · RF frequency band per threat)</div>${rows.join("")}`
    : `<div class="exposure-head">No jammed or lethal exposure on current routes</div>`;
}

function legWorstExposure(leg) {
  return leg?.worst_exposure || "CLEAR";
}

function renderMap(mapSel = "#map", opts = {}) {
  const ctx = getMapCtx(mapSel);
  if (!ctx) return;
  ctx.lastOpts = opts;
  const { group: svg, project } = ctx;
  const w = state.world;
  if (!w) {
    svg.innerHTML = "";
    return;
  }
  const showThreatPoints = opts.showThreats !== false && state.showThreats !== false;
  const showRings = opts.showRings ?? state.showRings;
  const ringsOnlyHover = opts.ringsOnlyHover === true;
  const showRoutes = opts.showRoutes !== false && (opts.route || state.showRoutes !== false);
  const showCostgrid = opts.showCostgrid ?? state.showCostgrid;
  const showAircraft = opts.showAircraft ?? state.showAircraftOnRoute;
  const exposureMode = opts.exposureMode === true;
  // Strict z-order above the dark tile base:
  // cost field → rings → routes → markers → labels.
  const fieldParts = [];
  const ringParts = [];
  const routeParts = [];
  const markerParts = [];
  const labelParts = [];

  if (showCostgrid && state.costgrid?.cells?.length) {
    fieldParts.push(`<g class="cost-field">`);
    for (const cell of state.costgrid.cells) {
      const pts = (cell.vertices || [])
        .map(([la, lo]) => project(la, lo).join(","))
        .join(" ");
      // Solid opaque fill, no stroke — neighbours abut without alpha stacking.
      fieldParts.push(
        `<polygon class="cost-cell" data-level="${cell.level}" points="${pts}" fill="${costLevelColor(cell.level, cell.intensity)}" stroke="none"/>`,
      );
    }
    fieldParts.push(`</g>`);
  }

  // Limit navaid labels when dense
  const navaids = w.navaids || [];
  const labelEvery = navaids.length > 20 ? 2 : 1;
  navaids.forEach((n, i) => {
    const [x, y] = project(n.location.lat, n.location.lon);
    markerParts.push(`<circle cx="${x}" cy="${y}" r="2.5" fill="#5c6b7e"/>`);
    if (i % labelEvery === 0) {
      labelParts.push(`<text x="${x + 5}" y="${y + 3}" fill="#5c6b7e" font-size="8" font-family="IBM Plex Mono, monospace">${n.id}</text>`);
    }
  });
  for (const m of w.mission_waypoints || []) {
    const [x, y] = project(m.location.lat, m.location.lon);
    markerParts.push(`<polygon points="${x},${y - 5} ${x + 4},${y + 3} ${x - 4},${y + 3}" fill="#c9a227"/>`);
    labelParts.push(`<text x="${x + 6}" y="${y + 3}" fill="#c9a227" font-size="8" font-family="IBM Plex Mono, monospace">${m.id.replace("MW-", "")}</text>`);
  }

  const activeThreatId = state.hoveredThreatId || state.selectedThreatId;
  for (const th of w.threats || []) {
    const loc = th.location || th;
    const lat = loc.lat ?? th.latitude;
    const lon = loc.lon ?? th.longitude;
    const [x, y] = project(lat, lon);
    const jamR = nmToSvgRadius(project, lat, lon, th.jam_radius_nmi || 160);
    const lethR = nmToSvgRadius(project, lat, lon, th.lethal_radius_nmi || 50);
    const isActive = activeThreatId === th.id;
    const drawRings = showRings && (!ringsOnlyHover || isActive);
    if (drawRings) {
      // Only the active threat's rings in exposure mode; thin, no fill wash.
      ringParts.push(`<g class="threat-rings" data-threat="${th.id}">
        <circle cx="${x}" cy="${y}" r="${jamR}" fill="none" stroke="rgba(239,68,68,0.55)" stroke-dasharray="4 3" stroke-width="1.1"/>
        <circle cx="${x}" cy="${y}" r="${lethR}" fill="none" stroke="#ef4444" stroke-width="1.4"/></g>`);
    }
    if (showThreatPoints) {
      markerParts.push(`<g class="threat-g" data-threat="${th.id}"><circle cx="${x}" cy="${y}" r="${isActive ? 6 : 5}" fill="#ef4444"/></g>`);
      labelParts.push(`<text x="${x + 8}" y="${y + 3}" fill="#ef4444" font-size="8" font-family="IBM Plex Mono, monospace">${th.id}</text>`);
    }
  }

  for (const b of w.airbases || []) {
    const [x, y] = project(b.location.lat, b.location.lon);
    const launch = b.id === (w.launch_base_id || "OEPS");
    markerParts.push(`<rect x="${x - 4}" y="${y - 4}" width="8" height="8" fill="${launch ? "#3dd6c6" : "#2a9a8e"}" transform="rotate(45 ${x} ${y})"/>`);
    labelParts.push(`<text x="${x + 8}" y="${y - 6}" fill="#e8eef8" font-size="10" font-family="IBM Plex Mono, monospace">${b.id}${launch ? " ★" : ""}</text>`);
  }
  for (const t of w.tasks || []) {
    const [x, y] = project(t.location.lat, t.location.lon);
    const color = t.type === "ISR" ? "#4da3ff" : "#ff7a45";
    markerParts.push(`<circle cx="${x}" cy="${y}" r="5" fill="${color}"/>`);
    labelParts.push(`<text x="${x + 7}" y="${y + 3}" fill="${color}" font-size="9" font-family="IBM Plex Mono, monospace">${t.id}</text>`);
  }

  const routeSource = opts.route
    ? [opts.route]
    : (state.plan?.plans || []).filter((p) => p.route?.waypoints?.length);

  const exposureByAc = Object.fromEntries(
    (state.exposure?.platforms || []).map((p) => [p.aircraft_id, p]),
  );

  if (showRoutes) {
    for (const p of routeSource) {
      const route = p.route || p;
      const wps = route.waypoints || [];
      if (!wps.length) continue;
      const selected =
        opts.forceSelected ||
        !state.selectedAircraftId ||
        p.aircraft_id === state.selectedAircraftId ||
        p.route_name;
      const nogo = (p.status || "") === "NO-GO";
      const opacity = selected ? 0.95 : 0.28;
      const width = selected ? 2.5 : 1.5;
      const pts = wps
        .map((wp) => project(wp.lat ?? wp.location?.lat, wp.lon ?? wp.location?.lon).join(","))
        .join(" ");
      // Base route stays crisp and neutral; exposure is an overlay of the
      // exact impacted sub-segments/points, never a whole-leg wash.
      routeParts.push(`<polyline class="route-path" points="${pts}" opacity="${opacity}" stroke-width="${width}" stroke="${nogo ? "#ff5c6c" : "#3dd6c6"}" fill="none"/>`);

      const exp = exposureByAc[p.aircraft_id] || opts.exposurePlatform;
      if (exposureMode && exp?.legs?.length) {
        const seenPoints = new Set();
        for (const leg of exp.legs) {
          const spans = activeThreatId
            ? (leg.threats || []).find((t) => t.threat_id === activeThreatId)?.spans || []
            : leg.exposure_spans || [];
          for (const span of spans) {
            const [x1, y1] = project(span.from.lat, span.from.lon);
            const [x2, y2] = project(span.to.lat, span.to.lon);
            routeParts.push(
              `<line class="route-exposure-span" data-exposure="${span.exposure}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${EXPOSURE_STROKE[span.exposure]}" stroke-width="4.5" opacity="${opacity}" stroke-linecap="round"/>`,
            );
            for (const point of [span.from, span.to]) {
              const key = `${point.lat},${point.lon},${span.exposure}`;
              if (seenPoints.has(key)) continue;
              seenPoints.add(key);
              const [px, py] = project(point.lat, point.lon);
              markerParts.push(
                `<circle class="exposure-point" data-exposure="${span.exposure}" cx="${px}" cy="${py}" r="3.5" fill="${EXPOSURE_STROKE[span.exposure]}" stroke="#0b1220" stroke-width="1.2"/>`,
              );
            }
          }
          if (!activeThreatId) {
            for (const point of leg.impacted_points || []) {
              if (point.fraction !== 0 && point.fraction !== 1) continue;
              const key = `${point.lat},${point.lon},${point.exposure}`;
              if (seenPoints.has(key)) continue;
              seenPoints.add(key);
              const [px, py] = project(point.lat, point.lon);
              markerParts.push(
                `<circle class="exposure-point" data-exposure="${point.exposure}" cx="${px}" cy="${py}" r="3.5" fill="${EXPOSURE_STROKE[point.exposure]}" stroke="#0b1220" stroke-width="1.2"/>`,
              );
            }
          }
        }
      }
      if (selected) {
        for (const wp of wps) {
          const [x, y] = project(wp.lat ?? wp.location?.lat, wp.lon ?? wp.location?.lon);
          markerParts.push(`<circle cx="${x}" cy="${y}" r="2.5" fill="${nogo ? "#ff5c6c" : "#3dd6c6"}"/>`);
        }
      }
    }
  }

  if (showAircraft && state.positions?.positions) {
    for (const pos of state.positions.positions) {
      if (!pos.position) continue;
      const [x, y] = project(pos.position.lat, pos.position.lon);
      const color =
        pos.aircraft_type === "ISR" ? "#4da3ff" : pos.aircraft_type === "BOMBER" ? "#9b7fd4" : "#c9a227";
      markerParts.push(`<circle cx="${x}" cy="${y}" r="7" fill="${color}" stroke="#0b1220" stroke-width="2"/>`);
      labelParts.push(`<text x="${x + 9}" y="${y - 6}" fill="${color}" font-size="9" font-family="IBM Plex Mono, monospace">${pos.label || pos.aircraft_id}</text>`);
    }
  }

  svg.innerHTML = [...fieldParts, ...ringParts, ...routeParts, ...markerParts, ...labelParts].join("");
  svg.querySelectorAll("[data-threat]").forEach((el) => {
    el.addEventListener("click", () => {
      state.selectedThreatId =
        state.selectedThreatId === el.dataset.threat ? null : el.dataset.threat;
      const th = (state.world?.threats || []).find((t) => t.id === state.selectedThreatId);
      if (th) {
        toast(
          `${th.id} · ${th.kind} · ${th.severity} · frequency band ${frequencyBandLabel(th)} · lethal ${th.lethal_radius_nmi}nm / jam ${th.jam_radius_nmi}nm`,
        );
      }
      if (opts.onThreatChange) opts.onThreatChange();
      else refreshMap();
    });
    el.addEventListener("mouseenter", () => {
      state.hoveredThreatId = el.dataset.threat;
      if (ringsOnlyHover) {
        if (opts.onThreatChange) opts.onThreatChange();
        else refreshMap();
      }
    });
    el.addEventListener("mouseleave", () => {
      state.hoveredThreatId = null;
      if (ringsOnlyHover) {
        if (opts.onThreatChange) opts.onThreatChange();
        else refreshMap();
      }
    });
  });
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
    tbody.innerHTML = `<tr class="empty"><td colspan="10">No routes — run a plan cycle</td></tr>`;
    return;
  }
  tbody.innerHTML = routes
    .map((r) => {
      const prim = r.primary_threat;
      const exposure = prim?.exposure || "CLEAR";
      const closest = prim ? `${prim.closest_approach_nm.toFixed(1)} nm` : "—";
      const sel = state.selectedRouteId === r.aircraft_id ? "selected" : "";
      const sev = (prim?.severity || "").toLowerCase();
      return `<tr class="${sel} ${sev}" data-route="${r.aircraft_id}">
        <td><button type="button" class="linkish"><strong>${r.route_name}</strong></button><div class="item-meta">${r.callsign}</div></td>
        <td>${typeBadge(r.aircraft_type)}</td>
        <td>${r.task_breakout.isr} ISR · ${r.task_breakout.strike} STK</td>
        <td class="num">${r.total_distance_nmi.toFixed(0)} nm</td>
        <td class="num">${closest}</td>
        <td><span class="${exposureClass(exposure)}">${exposure}</span></td>
        <td>${prim?.frequency_band || "—"}</td>
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

function detailExposurePlatform(route) {
  const acId = route.aircraft_id;
  const fromApi = (state.exposure?.platforms || []).find((p) => p.aircraft_id === acId);
  if (fromApi?.legs?.some((leg) => leg.exposure_spans?.length || leg.threats?.length)) {
    return fromApi;
  }
  // Fallback from the route-overview per-threat sub-segments.
  const wps = route.waypoints || [];
  const legs = [];
  for (let i = 0; i < wps.length - 1; i++) {
    legs.push({
      leg_index: i,
      exposed: false,
      worst_exposure: "CLEAR",
      exposure_spans: [],
      impacted_points: [],
      threats: [],
    });
  }
  for (const t of route.threats || []) {
    const spansByLeg = new Map();
    for (const span of t.exposure_spans || []) {
      if (!legs[span.leg_index]) continue;
      legs[span.leg_index].exposure_spans.push(span);
      legs[span.leg_index].exposed = true;
      if (!spansByLeg.has(span.leg_index)) spansByLeg.set(span.leg_index, []);
      spansByLeg.get(span.leg_index).push(span);
    }
    for (const point of t.impacted_points || []) {
      if (legs[point.leg_index]) legs[point.leg_index].impacted_points.push(point);
    }
    for (const [legIndex, spans] of spansByLeg.entries()) {
      legs[legIndex].threats.push({
        threat_id: t.threat_id,
        kind: t.threat_kind,
        severity: t.severity,
        frequency_band: t.frequency_band,
        exposure: t.exposure,
        closest_nm: t.closest_approach_nm,
        spans,
      });
    }
  }
  return { aircraft_id: acId, legs, threats_that_see: route.threats || [] };
}

function renderDetailMaps(route) {
  const expPlat = detailExposurePlatform(route);
  const redraw = () => {
    renderDetailMaps(route);
    renderSegmentTimeline(route);
  };
  renderMap("#detail-map", {
    route,
    forceSelected: true,
    showThreats: true,
    showRings: true,
    ringsOnlyHover: true,
    showCostgrid: false,
    showAircraft: false,
    exposureMode: true,
    exposurePlatform: expPlat,
    onThreatChange: redraw,
  });
  // Inset: same solid field, simplified only by scale (still opaque fills).
  renderMap("#detail-inset", {
    route,
    forceSelected: true,
    showThreats: false,
    showRings: false,
    showCostgrid: true,
    showAircraft: false,
    showRoutes: true,
    exposureMode: false,
  });
}

function routeBounds(route) {
  if (!hasLeaflet) return null;
  const pts = (route.waypoints || [])
    .map((wp) => [wp.lat ?? wp.location?.lat, wp.lon ?? wp.location?.lon])
    .filter(([la, lo]) => Number.isFinite(la) && Number.isFinite(lo));
  return pts.length ? L.latLngBounds(pts).pad(0.25) : null;
}

function fitDetailMaps(route) {
  const detail = mapCtxs.get("#detail-map");
  const b = detail && routeBounds(route);
  if (detail && b) {
    detail.home = { bounds: b, options: { maxZoom: 9, animate: false } };
    detail.autoFit = true;
  }
  const inset = mapCtxs.get("#detail-inset");
  if (inset) inset.home = { bounds: THEATER_BOUNDS, options: { padding: [2, 2], animate: false } };
  refreshMapSize("#detail-map");
  refreshMapSize("#detail-inset");
}

function openDetails() {
  const r = selectedRoute();
  if (!r) return;
  const drawer = $("#details-drawer");
  drawer.hidden = false;
  $("#drawer-title").textContent = `${r.route_name} · ${r.callsign}`;
  const prim = r.primary_threat;
  $("#drawer-sub").textContent = prim
    ? `Route exposure · closest ${prim.threat_id} · ${prim.closest_approach_nm.toFixed(1)} nm · ${String(prim.exposure || "").toLowerCase()} · frequency band ${prim.frequency_band || "—"} · ${prim.severity}`
    : "Route exposure · clear of all threat jam radii";

  const ensureField = state.costgrid
    ? Promise.resolve()
    : loadCostgrid(true);
  ensureField.then(() => {
    renderDetailMaps(r);
    fitDetailMaps(r);
    renderDetailThreats(r);
    renderDetailTasks(r);
    renderSegmentTimeline(r);
  });
}

function closeDetails() {
  $("#details-drawer").hidden = true;
}

function severityBadge(sev) {
  const s = String(sev || "MEDIUM").toUpperCase();
  return `<span class="sev-badge sev-${s.toLowerCase()}">${s}</span>`;
}

function renderDetailThreats(route) {
  const host = $("#detail-threats");
  const rows = route.threats || [];
  if (!rows.length) {
    host.innerHTML = `<table><tbody><tr class="empty"><td>Clear of threat jam radii</td></tr></tbody></table>`;
    return;
  }
  host.innerHTML = `<table>
    <thead><tr><th>Threat</th><th>Kind</th><th>Closest</th><th>Exposure</th><th>Frequency band</th><th>Sub-segs</th><th>Severity</th></tr></thead>
    <tbody>
      ${rows
        .map(
          (t) => `<tr class="threat-row ${(t.severity || "").toLowerCase()}" data-threat-row="${t.threat_id}" style="cursor:pointer" title="${t.threat_id}: exposure ${String(t.exposure || "").toLowerCase()} · frequency band ${t.frequency_band || "—"}">
        <td><strong>${t.threat_id}</strong><div class="item-meta">${t.threat_label || ""}</div></td>
        <td>${t.threat_kind || "—"}</td>
        <td>${Number(t.closest_approach_nm || 0).toFixed(1)} nm</td>
        <td><span class="${exposureClass(t.exposure)}">${t.exposure}</span></td>
        <td>${t.frequency_band || "—"}</td>
        <td>${t.impacted_segment_count ?? "—"}</td>
        <td>${severityBadge(t.severity)}</td>
      </tr>`,
        )
        .join("")}
    </tbody></table>`;
  host.querySelectorAll("[data-threat-row]").forEach((row) => {
    row.addEventListener("click", () => {
      state.selectedThreatId =
        state.selectedThreatId === row.dataset.threatRow ? null : row.dataset.threatRow;
      renderDetailMaps(route);
      renderSegmentTimeline(route);
    });
    row.addEventListener("mouseenter", () => {
      state.hoveredThreatId = row.dataset.threatRow;
      renderDetailMaps(route);
      renderSegmentTimeline(route);
    });
    row.addEventListener("mouseleave", () => {
      state.hoveredThreatId = null;
      renderDetailMaps(route);
      renderSegmentTimeline(route);
    });
  });
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

function jamSupportMarks(entries, total) {
  if (!total || !entries?.length) return "";
  return entries
    .map((e) => {
      const left = (e.from_nmi / total) * 100;
      const width = Math.max(((e.to_nmi - e.from_nmi) / total) * 100, 1.5);
      const band = e.frequency_band || "RF —";
      const who = e.provider_callsign || e.provider_aircraft_id || "";
      return `<span class="jam-mark jam-${e.source}" style="left:${left}%;width:${width}%" title="${e.label} · ${e.role} · frequency band ${band}${who ? ` · ${who}` : ""}">${e.label}</span>`;
    })
    .join("");
}

function renderSegmentTimeline(route) {
  const host = $("#detail-segment-timeline");
  const activeId = state.hoveredThreatId || state.selectedThreatId;
  const prim =
    (route.threats || []).find((t) => t.threat_id === activeId) || route.primary_threat;
  const weather = route.weather_impact || {};
  const weatherSegs = weather.segments || [];
  const jam = route.jam_support || {};
  const total = route.total_distance_nmi || weather.total_distance_nmi || 0;
  const tasks = route.tasks || [];
  const cum = prim?.cumulative_nmi || [0];
  const closestPct =
    total && cum.length && prim
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

  const peak = weather.peak_level || "CLEAR";
  const peakNote =
    peak === "CLEAR"
      ? "clear of threat weather"
      : `peak weather ${String(peak).toLowerCase()}`;
  const primNote = prim
    ? ` · selected ${prim.threat_id} exposure ${String(prim.exposure || "").toLowerCase()} · frequency band ${prim.frequency_band || "—"}`
    : "";

  const impactHtml = weatherSegs.length
    ? weatherSegs
        .map(
          (s) =>
            `<span class="seg" style="flex:${Math.max(s.length_nmi, 0.5)};background:${s.color}" title="${s.from_nmi}–${s.to_nmi} nm · weather ${String(s.level || "").toLowerCase()} · intensity ${s.intensity}"></span>`,
        )
        .join("")
    : `<span class="seg" style="flex:1;background:#1e293b"></span>`;

  const onboardJam = jamSupportMarks(jam.onboard, total);
  const offboardJam = jamSupportMarks(jam.offboard, total);

  host.innerHTML = `
    <h3>Route timeline · ${route.route_name}</h3>
    <p class="hint">Impact = route colour through the threat-weather cost field (${peakNote})${primNote} · distance axis</p>
    <div class="seg-tracks">
      <div class="seg-label">Impact</div>
      <div class="seg-line weather-impact">
        ${impactHtml}
        ${prim ? `<span class="threat-mark" style="left:${closestPct}%">▼</span>` : ""}
      </div>
      <div class="seg-label">Onboard</div>
      <div class="task-rail jam-rail">
        <div class="rail"></div>
        ${taskMarks}
        ${onboardJam || `<span class="jam-empty">No onboard jam support</span>`}
      </div>
      <div class="seg-label">Offboard</div>
      <div class="task-rail jam-rail">
        <div class="rail"></div>
        ${offboardJam || `<span class="jam-empty">No offboard jam support</span>`}
      </div>
      <div class="seg-label"></div>
      <div class="seg-axis"><span>0 nm</span><span>${total.toFixed(0)} nm</span></div>
    </div>
    <div class="weather-ramp-legend" aria-label="Weather impact colour ramp">
      <span><i style="background:#1e293b"></i>Clear</span>
      <span><i style="background:#2ecc71"></i>Low</span>
      <span><i style="background:#f1c40f"></i>Medium</span>
      <span><i style="background:#e67e22"></i>High</span>
      <span><i style="background:#e74c3c"></i>Critical</span>
      <span class="hint">same ramp as Plan cost field</span>
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
  if (name === "plan") refreshMapSize("#map");
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

function archetypeLabel(a) {
  const map = {
    efficient: "Efficient",
    synchronized: "Synchronized",
    maneuver: "Maneuver",
    surprise: "Surprise",
    shock: "Shock",
    attrition: "Attrition",
  };
  return map[a] || a || "—";
}

async function loadCostgrid(force = false) {
  if (!force && !state.showCostgrid) return;
  const q = new URLSearchParams({
    cell_nmi: String(state.cellNmi || 45),
    cell_style: state.cellStyle || "hex",
    altitude_ft: String(state.altitudeFt || 10000),
  });
  state.costgrid = await api(`/api/map/costgrid?${q}`);
}

async function loadExposure() {
  if (!state.plan && !state.compare?.preferred_option_id) {
    state.exposure = null;
    return;
  }
  const pref = state.compare?.preferred_option_id;
  const q = pref ? `?option_id=${pref}` : "";
  try {
    state.exposure = await api(`/api/map/exposure${q}`);
  } catch {
    state.exposure = null;
  }
}

async function loadTimeline() {
  const pref = state.compare?.preferred_option_id;
  const q = pref ? `?option_id=${pref}` : "";
  try {
    state.timeline = await api(`/api/timeline${q}`);
    const scrub = $("#timeline-scrub");
    if (scrub && state.timeline) {
      scrub.max = Math.max(1, Math.ceil(state.timeline.axis_max_minutes || 1));
      scrub.value = Math.min(Number(scrub.value), Number(scrub.max));
    }
    renderAlignedTimeline();
  } catch {
    state.timeline = null;
  }
}

async function loadPositions() {
  if (!state.showAircraftOnRoute) {
    state.positions = null;
    return;
  }
  const pref = state.compare?.preferred_option_id;
  const q = new URLSearchParams({ t_min: String(state.scrubMin || 0) });
  if (pref) q.set("option_id", pref);
  try {
    state.positions = await api(`/api/map/positions?${q}`);
  } catch {
    state.positions = null;
  }
}

function renderAlignedTimeline() {
  const host = $("#aligned-timeline");
  if (!host) return;
  const tl = state.timeline;
  if (!tl?.tracks?.length) {
    host.innerHTML = `<p class="hint">Run a plan or build options to see aligned TOT tracks.</p>`;
    return;
  }
  const maxT = Math.max(1, tl.axis_max_minutes || 1);
  const windows = (tl.sync_windows || [])
    .map((w) => {
      const left = (w.t0 / maxT) * 100;
      const width = ((w.t1 - w.t0) / maxT) * 100;
      return `<div class="tot-window ${w.kind}" style="left:${left}%;width:${width}%" title="${w.label}"></div>`;
    })
    .join("");
  const playhead = `<div class="playhead" style="left:${(state.scrubMin / maxT) * 100}%"></div>`;
  host.innerHTML = `
    <div class="tl-axis"><span>0m</span><span>${maxT.toFixed(0)}m</span></div>
    <div class="tl-tracks">
      ${tl.tracks
        .map((tr) => {
          const segs = (tr.segments || [])
            .map((s) => {
              const left = (s.t0 / maxT) * 100;
              const width = Math.max(0.4, ((s.t1 - s.t0) / maxT) * 100);
              return `<div class="tl-seg" style="left:${left}%;width:${width}%" title="${s.from_id}→${s.to_id}"></div>`;
            })
            .join("");
          const marks = (tr.events || [])
            .filter((e) => e.kind === "strike" || e.kind === "collect")
            .map((e) => {
              const left = (e.t_min / maxT) * 100;
              const cls = e.kind === "strike" ? "strike" : "collect";
              return `<div class="tl-mark ${cls}" style="left:${left}%" title="${e.label}"></div>`;
            })
            .join("");
          return `<div class="tl-row">
            <div class="tl-label">${tr.label || tr.aircraft_id}<div class="item-meta">${tr.aircraft_type} · ${tr.status} · ${tr.total_distance_nmi || 0} nmi</div></div>
            <div class="tl-track">${windows}${segs}${marks}${playhead}</div>
          </div>`;
        })
        .join("")}
    </div>`;
}

function setRoutesPane(name) {
  state.routesPane = name;
  $$(".subtab").forEach((t) => {
    const on = t.dataset.routesPane === name;
    t.classList.toggle("active", on);
    t.setAttribute("aria-selected", on ? "true" : "false");
  });
  $$("[data-routes-panel]").forEach((p) => {
    p.hidden = p.dataset.routesPanel !== name;
  });
  if (name === "timeline") loadTimeline();
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
      const arch = opt.archetype || opt.emphasis;
      return `
        <article class="option-card ${opt.preferred ? "preferred" : ""}" data-emphasis="${opt.emphasis}" data-option="${opt.option_id}">
          <div class="slot-mark">SLOT ${slot}${opt.preferred ? " · PREFERRED" : ""}</div>
          <h3>${opt.label}</h3>
          <p class="meta">${archetypeLabel(arch)} · ${emphasisLabel(opt.emphasis)} · ${opt.supplier_id || "fallback"} · vias ${vias}</p>
          <div class="option-metrics">
            <div class="om"><span>GO</span><strong class="go">${opt.go_count}</strong></div>
            <div class="om"><span>NO-GO</span><strong class="nogo">${opt.nogo_count}</strong></div>
            <div class="om"><span>Unallocated</span><strong>${opt.unallocated_count}</strong></div>
            <div class="om"><span>Distance</span><strong>${Number(opt.total_distance_nmi).toFixed(0)} nmi</strong></div>
          </div>
          ${opt.archetype_fit ? `<div class="sync-chip">${opt.archetype_fit}</div>` : ""}
          ${syncHtml}
          <div class="card-actions">
            <button type="button" class="btn btn-primary btn-prefer" data-prefer="${opt.option_id}">Prefer</button>
            <button type="button" class="btn btn-export-option" data-export-option="${opt.option_id}">Export</button>
            <button type="button" class="btn btn-ghost" data-gaps="${opt.option_id}">Gaps</button>
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
  host.querySelectorAll("[data-gaps]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        const g = await api(`/api/options/${btn.dataset.gaps}/gaps`);
        const n = (g.gaps || []).length;
        const r = (g.risks || []).length;
        toast(`GapReport · ${g.archetype} · ${n} gaps · ${r} risks (advisory)`, n ? "warn" : "info");
      } catch (err) {
        toast(String(err.message || err), "error");
      }
    });
  });
}

function renderCompareTable() {
  const tbody = $("#compare-tbody");
  if (!tbody) return;
  const rows = state.compare?.options || [];
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="hint">Build the top-three to populate comparison. Pool may hold more contingencies.</td></tr>`;
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
          <td>${o.slot || "pool"}</td>
          <td>${archetypeLabel(o.archetype || o.emphasis)}<div class="item-meta">${o.archetype_fit || ""}</div></td>
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
  const navBadge = $("#nav-source-badge");
  if (navBadge) {
    navBadge.textContent = `nav: ${state.world.nav_source || "fixture"} · ${state.world.navaid_count || 0} fixes`;
  }
  if (!state.selectedAircraftId && state.world.aircraft.length) {
    state.selectedAircraftId = state.world.aircraft[0].id;
  }
  state.groupByType = state.world.platform_group_by_type !== false;
  if ($("#tog-group-type")) $("#tog-group-type").checked = state.groupByType;
  renderTasks();
  renderFleet();
  renderStats();
  try {
    state.plan = await api("/api/plan");
    setPlanReady(true);
    await loadOverview().catch(() => {});
  } catch {
    setPlanReady(false);
  }
  await loadCostgrid();
  await loadExposure();
  await loadPositions();
  refreshMap();
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
    await loadExposure();
    await loadPositions();
    refreshMap();
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
    refreshMap();
  });
  $("#tog-costgrid")?.addEventListener("change", async (e) => {
    state.showCostgrid = e.target.checked;
    if (state.showCostgrid) await loadCostgrid();
    refreshMap();
  });
  $("#btn-fit-theater")?.addEventListener("click", () => fitTheater("#map"));
  $("#tog-rings")?.addEventListener("change", (e) => {
    state.showRings = e.target.checked;
    refreshMap();
  });
  $("#tog-threats")?.addEventListener("change", (e) => {
    state.showThreats = e.target.checked;
    refreshMap();
  });
  $("#tog-routes")?.addEventListener("change", (e) => {
    state.showRoutes = e.target.checked;
    refreshMap();
  });
  $("#tog-scrub-ac")?.addEventListener("change", async (e) => {
    state.showAircraftOnRoute = e.target.checked;
    await loadPositions();
    refreshMap();
  });
  $("#sel-cell-nmi")?.addEventListener("change", async (e) => {
    state.cellNmi = Number(e.target.value) || 45;
    if (state.showCostgrid || state.costgrid) await loadCostgrid(true);
    refreshMap();
  });
  $("#sel-cell-style")?.addEventListener("change", async (e) => {
    state.cellStyle = e.target.value || "hex";
    if (state.showCostgrid || state.costgrid) await loadCostgrid(true);
    refreshMap();
  });
  $("#sel-altitude")?.addEventListener("change", async (e) => {
    state.altitudeFt = Number(e.target.value) || 10000;
    if (state.showCostgrid || state.costgrid) await loadCostgrid(true);
    toast(`Altitude ${state.altitudeFt} ft (display-only until stacked layers)`, "info");
    refreshMap();
  });
  $$("#cost-legend .cost-level").forEach((btn) => {
    btn.addEventListener("click", () => {
      const level = btn.dataset.level;
      state.legendFilter = state.legendFilter === level ? null : level;
      refreshMap();
    });
  });
  $("#tog-group-type")?.addEventListener("change", async (e) => {
    state.groupByType = e.target.checked;
    await api("/api/platforms/order", {
      method: "POST",
      body: JSON.stringify({
        order: orderedAircraft().map((a) => a.id),
        group_by_type: state.groupByType,
      }),
    });
    state.world = await api("/api/world");
    renderFleet();
  });
  $$(".subtab").forEach((t) => {
    t.addEventListener("click", () => setRoutesPane(t.dataset.routesPane));
  });
  $("#timeline-scrub")?.addEventListener("input", async (e) => {
    state.scrubMin = Number(e.target.value);
    const lab = $("#timeline-scrub-label");
    if (lab) lab.textContent = `t = ${state.scrubMin}m`;
    await loadPositions();
    renderAlignedTimeline();
    refreshMap();
  });
  $$(".tab").forEach((t) => {
    t.addEventListener("click", () => {
      if (t.disabled) return;
      setView(t.dataset.view);
      if (t.dataset.view === "options") {
        loadOptions().catch((err) => toast(String(err.message || err), "error"));
      }
      if (t.dataset.view === "routes") {
        loadTimeline().catch(() => {});
        loadExposure().then(() => refreshMap());
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
