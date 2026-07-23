# Civil Route Generation — Development Guide

## Scope

Civil-style route generation means: **select and sequence published waypoints** (airports, navaids, intersections) the way an IFR planner or dispatch tool would, then connect them with great-circle legs. No runtime-invented lat/lon points.

In o-my-mission-plan this is the preferred engine for **Efficient (option A)** routes and a reusable building block for other options when constraints can be expressed as vias / corridor preferences.

Primary references:
- `docs/ROUTE-GENERATION.md` — published-waypoint-only rules
- `docs/SUPPLIER-ROUTE-TOOLS.md` — openRouteFinder and other suppliers
- `docs/CONOPS.md` — where civil routes sit in the planning cycle

---

## Mental model (from civil IFR practice)

1. Navigation database of **published** fixes
2. Planner chooses origin, destination, optional airways / vias
3. Algorithm (often Dijkstra / A* on the airway graph) returns an ordered list of fixes
4. System computes great-circle course and distance per leg
5. FMS / consumer loads the sequence; wind and performance corrections come later

We deliberately stop at step 4 inside the supplier. Wind, VNAV, and SIDs/STARs are out of scope for the prototype supplier.

---

## What “done” looks like for a civil supplier adapter

**Input (SupplierRouteRequest)**
- Origin (airbase id or lat/lon)
- Destination (airbase id or lat/lon)
- Optional vias (fix ids)
- Optional avoid hints (fix ids or coarse polygons) — soft for pure civil tools
- Aircraft type hint (optional)

**Output (SupplierRouteResponse)**
- Ordered list of fixes: `{id, lat, lon, name?}`
- Total distance nmi
- Source tag (`openroutefinder`, `fallback`, …)

**Our adapter then**
1. Maps fixes → `Waypoint` (kind = airbase | navaid | mission_fix)
2. Builds `Leg`s via `haversine_nmi`
3. Does **not** invent PROX points
4. Returns a `Route` ready for task proximity association + fuel propagation

---

## Development steps

### 1. Fallback civil generator (in-repo)

Already required by issue #2:
- Only emit published waypoints from the demo nav database
- Greedy or nearest-navaid sequencing is acceptable
- Validate proximity after the fact; report unsatisfied tasks

This is the zero-dependency path and the reference for adapter tests.

### 2. openRouteFinder spike

1. Vendor or submodule / pip-path the library (gtxzsxxk/openRouteFinder or FSUnion fork).
2. Feed it origin/destination pairs from the current demo theater (OEPS ↔ task-region fixes).
3. Capture returned fix lists; check that ids/lat/lons map cleanly into our models.
4. If coverage is thin for the demo nav set, either:
   - extend the published fix list with additional fixed mission waypoints, or
   - keep openRouteFinder for “long” legs and fall back for short tactical segments.

### 3. Adapter module layout (suggested)

```text
src/omy_mission_plan/
  suppliers/
    __init__.py
    base.py          # Protocol + Request/Response models
    fallback.py      # Current published-waypoint generator
    openroutefinder.py
    registry.py      # ROUTE_SUPPLIER env/config → instance
```

### 4. Tests

- Fallback still produces start/end at home base, no PROX-* ids
- Adapter maps a mocked SupplierRouteResponse into a valid Route
- Planning cycle works with `ROUTE_SUPPLIER=fallback` and (when available) `openroutefinder`
- Fuel propagator unchanged regardless of supplier

---

## Integration checklist

- [ ] `SupplierRouteRequest` / `SupplierRouteResponse` in models or suppliers package
- [ ] Fallback supplier implements the protocol
- [ ] Config switch documented in README
- [ ] openRouteFinder optional extra in `pyproject.toml`
- [ ] Gherkin still passes with fallback (civil path is an implementation detail of “published waypoints”)
- [ ] CONOPS Efficient slot can be filled by a civil-supplier-backed option

---

## Non-goals

- Full ARINC 424 or commercial navdata licensing
- SID/STAR procedure encoding
- Wind / performance / VNAV inside the civil supplier
- Calling Little Navmap as a live service (export/import only, if ever)
