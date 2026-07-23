# Mission Route Generation — Development Guide

## Scope

Mission route generation builds on civil published-waypoint routing and adds **operational constraints** that pure airway Dijkstra does not know about:

- Task proximity (80 nmi ISR / 20 nmi strike) as a success criterion
- Synchronized effects (common TOT windows, BDA after strike, shared holds)
- Unexpected approach axis (forced vias / corridors so the inbound path is not the obvious radial from the main base)
- Optional avoid / threat regions as cost or hard constraints

These are the differentiators behind CONOPS options **B (Synchronized)** and **C (Unexpected axis)**. Option **A (Efficient)** may use the civil supplier almost unchanged.

References: `docs/CONOPS.md`, `docs/CIVIL-ROUTE-DEV-GUIDE.md`, `docs/SUPPLIER-ROUTE-TOOLS.md`, `docs/ROUTE-GENERATION.md`.

---

## Constraint types the router must accept

| Constraint | Used by | Representation in router inputs |
|------------|---------|----------------------------------|
| Task proximity | All | Post-process association; not a reason to invent waypoints |
| Optional vias | A/B/C | Ordered or unordered fix ids the path should include |
| Corridor / approach axis | C | Soft or hard preference for a sequence of fixes or a polygon corridor |
| Avoid regions | B/C | Polygons or fix blacklists (cost or forbidden) |
| Timing windows | B | Per-task or per-effect earliest/latest; used for comparison more than pure geometry |
| Shared holds / IPs | B | Named fixes that multiple aircraft routes should reference |

Router inputs are **saved with each Mission Option** so the planner can tweak one constraint and re-run.

---

## Development approach

### Phase M1 — Express constraints without a new solver

1. Extend `SupplierRouteRequest` (or a mission-specific wrapper) with:
   - `vias: list[str]`
   - `avoid_fix_ids: list[str]`
   - `approach_axis_label: str | None` (e.g. `"west-via-jordan"`)
   - `sync_group_id: str | None`
2. Fallback generator: if vias are present, force them into the published sequence in order; still no invented points.
3. Synchronized option: same geometry as efficient for v1, but tag routes with timing metadata for comparison (TOT offsets, BDA lag targets).
4. Unexpected-axis option: require a documented via list that encodes the axis (e.g. north to a Jordan-side fix, then east into the target area).

### Phase M2 — Cost-grid supplier

1. Build a graph (or coarse grid) over published fixes + optional grid cells.
2. Edge cost = distance + penalties for “obvious” corridor (for option C) or for avoid regions.
3. Dijkstra / A* via networkx; output still a list of published (or grid-snapped) fixes.
4. Same adapter contract as civil supplier.

### Phase M3 — Richer physics (optional)

- OpenAP-TOP or similar for fuel-aware trajectories once lateral path is fixed.
- Still reduced to a waypoint list before our propagator runs.

---

## Synchronized effects (option B) — practical v1

Do **not** build a full multi-vehicle temporal optimizer yet.

Minimum:

- Allow the planner to mark a set of strike tasks as a sync group with a nominal TOT.
- ISR tasks can be marked “BDA after {strike_id}” with a desired lag.
- Comparison view shows whether routes’ estimated times-along-route are compatible with those windows (using constant groundspeed assumptions).
- Geometry may still be efficient-style; the “mission” part is the saved timing intent + comparison, not a new path algorithm.

---

## Unexpected axis (option C) — practical v1

Example narrative (Gulf theater): avoid the direct PSAB → target radial; route north toward a Jordan corridor and enter from the west.

Implementation:

1. Define a named axis profile in fixtures, e.g. `west_entry_via_jordan: [fix_n1, fix_n2, fix_w1]`.
2. When the option emphasis is `unexpected-axis`, inject those vias into the supplier request.
3. Comparison scores how well the resulting path matches the axis (e.g. fraction of forced vias present, or max penetration into the “obvious” corridor).

---

## Tests and Gherkin hooks

- Building an Efficient option does not require vias.
- Building an Unexpected-axis option with a via list includes those published fixes in order.
- Saving an option persists router inputs; re-run with one via changed produces a new candidate.
- Comparison endpoint/table returns at least distance, GO counts, unallocated count, and emphasis label for each slot.

---

## Non-goals

- Automated multi-objective optimization across A/B/C
- Live threat-driven replan
- Full tanker / refueling legs
- Inventing waypoints to force proximity or axis geometry
