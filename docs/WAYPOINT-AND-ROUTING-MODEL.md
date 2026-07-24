# Waypoint Representation vs Route Selection Methods

## The confusion

The current planner feels simplistic, and it is easy to ask whether **routing between tasks** should use different waypoint representations (e.g. task coordinates as waypoints, invented approach points, airway fixes, grid cells).

**Answer: no.** The product uses **one** waypoint representation for every route. What varies by archetype / supplier is **how the sequence of those waypoints is chosen**, not the type of object stored on the route.

---

## 1. Unified representation (always)

A route is only ever a sequence of **published fixes**:

| `Waypoint.kind` | Source | Role |
|-----------------|--------|------|
| `airbase` | `AIRBASES` | Home plate, recovery, staging |
| `navaid` | `NAVAIDS` | Civil/commercial navigation fixes |
| `mission` | Fixed mission waypoints in the nav DB | Theater fixes pre-seeded near task areas when navaid density is thin |

Each waypoint has `id`, `location` (lat/lon), optional `name`, and optional `associated_task_id`.

**Tasks are not waypoints.** A `Task` is a separate object (type, location, priority). Association is a **post-condition**: if some published waypoint on the route lies within 80 nmi (ISR) or 20 nmi (strike) of the task, that waypoint may carry `associated_task_id`. If none does, the task is listed in `unsatisfied_task_ids`.

Legs are always great-circle between consecutive published waypoints (any length). Fuel uses those leg distances.

This matches civil IFR practice and `docs/ROUTE-GENERATION.md`: do not invent `PROX-*` or other runtime lat/lon points.

---

## 2. What *does* differ: selection methods

Different suppliers / archetypes change **selection policy** over the same published set:

| Method | Where | How sequence is built | Best fit |
|--------|-------|------------------------|----------|
| **Greedy cover** | `route_generator.generate_route` / fallback supplier | Nearest unsatisfied task → nearest published fix that covers it; optional forced `vias` first | Simple demo, efficient default |
| **Graph shortest path** | `suppliers/graph_routing.py` + openRouteFinder-style | k-NN graph on published fixes; Dijkstra pure distance; chain origin → covering fixes → home | Efficient / civil-like |
| **Cost-penalized graph** | same graph + `use_penalties` / costgrid supplier | Dijkstra with avoid-node and avoid-zone multiplicative costs | Unexpected axis, threat/corridor avoidance |
| **Forced via chain** | any supplier via `SupplierRouteRequest.vias` | Explicit published fix ids inserted in order, then fill/shortest-path between | Maneuver / surprise geometry |

So:

- **Between tasks** you do **not** switch to a different waypoint type.
- You still fly **fix → fix**.
- The planner decides *which* published fixes appear and in what order (greedy cover vs shortest path vs cost path vs forced vias).

---

## 3. Why not “task location as waypoint”?

Putting the task’s raw lat/lon on the route would:

- Invent a fix not in the navigation database
- Break the published-only contract used for UCI export and civil-supplier adapters
- Mix mission geometry (where the effect is needed) with navigation geometry (what the aircraft is cleared to fly)

Mission need is expressed as **proximity success criteria** and optional **pre-defined mission fixes** in the DB—not as ad-hoc coordinates on the route string.

If the published set cannot cover a strike (20 nmi is tight), the correct fix is to **add a fixed mission waypoint** to the theater DB, not to synthesize one at plan time.

---

## 4. Why the planner still feels simplistic

Legitimate limits of the current implementation:

1. **Task order** is mostly nearest-neighbor, not a real TSP / orienteering solver.
2. **Airway structure** is approximated by k-nearest published links, not real ARINC airways.
3. **Synchronized** options mostly attach timing metadata; they do not yet jointly optimize geometry for TOT.
4. **No vertical profile** (altitudes, SIDs/STARs, threats as 3-D volumes).

Those are algorithm and data richness gaps—not reasons to fork waypoint representation per method.

---

## 5. Guidance for A/B/C and contingencies

| Archetype | Selection method bias | Still emits |
|-----------|----------------------|-------------|
| Efficient | Greedy or pure Dijkstra on published graph | `airbase` / `navaid` / `mission` only |
| Synchronized | Same geometry tools + timing fields on the option | same |
| Unexpected / maneuver | Forced `vias` + costgrid penalties on obvious corridor | same |
| Shock / attrition contingencies | Priority order of tasks + margin; same fix types | same |

Comparison should score distance, GO/NO-GO, unsatisfied tasks, axis/timing fit—not whether waypoints were “a different kind of object.”

---

## 6. Implementation map

| Concern | Module |
|---------|--------|
| Waypoint / Route / Task models | `models.py` |
| Greedy published cover + association | `route_generator.py` |
| Graph + Dijkstra + avoid costs | `suppliers/graph_routing.py` |
| Supplier contract (ordered fixes in, never tasks-as-fixes) | `suppliers/base.py` |
| Fuel on legs | `propagator.py` |

---

## 7. Decision (locked)

**One waypoint representation. Multiple selection methods.**

Routing “between tasks” means: choose the next published fix(es) that advance coverage of remaining tasks under the active method’s objective (short, cheap under avoid costs, or forced axis)—then associate tasks by proximity. Do not introduce a second waypoint metamodel for inter-task segments.
