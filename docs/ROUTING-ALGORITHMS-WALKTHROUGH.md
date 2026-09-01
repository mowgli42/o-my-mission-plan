# Routing Algorithms Walkthrough

Companion to [`WAYPOINT-AND-ROUTING-MODEL.md`](WAYPOINT-AND-ROUTING-MODEL.md).

This is a teaching walkthrough, not a solver spec. It explains **why** the planner splits itinerary from hop geometry, how weather-routing ideas transfer to threat fields, and which algorithm belongs on which layer.

---

## 1. The locked model (read this first)

A route is always a sequence of **published fixes** only: `airbase`, `navaid`, or pre-seeded `mission` waypoints. Tasks are not waypoints. A task is satisfied if some fix already on the route lies within 80 nmi (ISR) or 20 nmi (strike). Legs are great-circle. Fuel uses those distances.

What changes across COAs and suppliers is **selection policy** — which published fixes, in what order — not a second waypoint type.

| Layer | Question | Family |
|-------|----------|--------|
| Itinerary / allocation | Which platform, which tasks, what order? | VRP / mTSP / greedy cover |
| Hop (civil) | Home → entry handoff on published graph | Dijkstra / A* (distance) |
| Hop (mission) | Entry → cover tasks → exit on cost field | A* / Dijkstra (threat or weather cost) |
| Time fronts (optional) | Where can I be at time *t*? TOT slack? | Isochrones |
| Feasibility | Can this airframe finish with reserve? | Constant-burn propagator |

VRP builds the skeleton. A* or isochrones shape each arrow. The propagator scores the stitched route.

---

## 2. Isochrones

An **isochrone** is a line or front of **equal time** from an origin. Every point on the 6-hour front is reachable in six hours given the current speed field (winds and waves for ships; groundspeed for aircraft).

### Classic ship weather-routing loop (James / Hagiwara)

1. From the start, step forward Δt (for example 6 hours).
2. The set of reachable positions is the new isochrone.
3. Keep the points that look best toward the destination (or lowest fuel).
4. Repeat until a front reaches the goal; trace back the chosen points.

Isochrones answer “where can I be at time *t*?” They shine when the environment changes **speed** (weather). They are awkward as the only engine when the map is a patchwork of hard keep-out cells (lethal umbrellas, no-fly).

**In o-my:** use isochrones as a **TOT / slack metric** — earliest time any platform can reach a cover set — not as the default mission path engine.

---

## 3. A* and Dijkstra on a cost field

**Dijkstra** finds the cheapest path on a graph when every edge cost is non-negative. **A\*** is Dijkstra plus a heuristic (usually remaining great-circle distance) so the search leans toward the goal.

A weather or threat “map” is just a way to set those edge costs. Paint each cell: green (cheap), yellow (slow or jammed), red (lethal / storm = very high or infinite). Search prefers green.

| Field source | Typical cell cost | Hop engine |
|--------------|-------------------|------------|
| Wind / waves | Time or fuel to cross the cell | Isochrones or A* |
| Threat jam / lethal | Distance × exposure (or ∞) | A* / Dijkstra |
| Civil published graph | Great-circle nmi | Dijkstra (already in repo) |

Prototype cell cost inside a mission area:

```text
cost = distance_weight × length + Σ exposure(threat, cell)
```

Jam range is a soft penalty; lethal range may be treated as hard avoid. The same code path can later accept a weather band. Do not vendor a ship stack just to paint a different field.

---

## 4. VRP — why the itinerary layer exists

The **Vehicle Routing Problem** assigns stops to a fleet and orders each vehicle’s tour under capacity and (often) time windows. TSP is one traveler visiting every city. VRP is several vehicles, not every stop on every truck, return to depot, do not overload.

A beautiful A* hop on a bad assignment still wastes an airframe. VRP decides the skeleton; hop engines only shape the arrows.

| Variant | Rule | o-my analogue |
|---------|------|----------------|
| CVRP | Capacity per vehicle | Weapons, max_tasks, fuel range |
| VRPTW | Time windows on stops | TOT earliest/latest, BDA lag |
| mTSP | Several tours, weak packing | Spread-the-field COA |
| Covering VRP | Get near, not onto, the point | 80 / 20 nmi proximity |
| Pickup & delivery | A before B | Strike then BDA |
| Dynamic VRP | Stops appear mid-tour | Insert task; full re-assess |

### Algorithms you will actually meet

- **Construct.** Clarke–Wright savings (merge two routes if it saves distance and capacity holds). Insertion (put the next stop where extra cost is smallest). Sweep / cluster-first (group nearby tasks, then tour each group) — close to the current regional allocator.
- **Improve.** 2-opt / relocate / swap between vehicles.
- **Exact (small *n*).** MIP, branch-and-cut, column generation.
- **Metaheuristics.** Tabu, ALNS — production logistics; a bead, not the MVP.

**Prototype lock:** greedy insertion + capacity + time-window check. Report unallocated and infeasible-by-time. That is an honest VRP heuristic.

---

## 5. Ships vs packages — same split

| Decision | Cargo + weather | Mission + threats |
|----------|-----------------|-------------------|
| Must visit | Contracted ports (sometimes skip) | Assigned tasks |
| Close enough | Usually the berth | 80 nmi collect / 20 nmi strike |
| Field | Wind, waves, currents | Jam / lethal / CAP layers |
| Hop | Isochrones or grid A* | Grid A* on threat field |
| Multi-stop | VRP / liner rotation + per-leg router | Allocate + order + per-leg router |
| Replan | New forecast; closed port | New task; new threat; missed TOT |

Ships rarely let weather reorder the whole rotation by itself. Weather changes ETA and fuel on each ocean leg. Threats should work the same way unless a hop becomes infeasible — then VRP re-orders or drops the task.

---

## 6. Combining them with multiple tasks and a changing field

Do not grow one isochrone that tries to swallow every target. Do not run one A* whose goal is “all tasks.” Loop:

```text
remaining = tasks
position  = entry handoff (after civil ingress)
while remaining:
    for each task t:
        C_t = published fixes / cells that cover t
        cost(t) = A*(position → C_t) on current field
    pick next t (cheapest cost, or TOT / priority)
    append hop; position = chosen cover fix
    drop t; maybe refresh field
A*(position → exit); then civil egress home
```

If the field is a forecast snapshot, build the grid once. If it is a new weather cycle or a new threat, rebuild costs and re-run remaining hops (full re-assess of that aircraft, per existing CONOPS).

---

## 7. Civil vs mission areas

Civil airspace uses the published navaid graph (cheap Dijkstra). The **mission area** is a polygon whose interior is a weather-map-style cost field. Civil ingress ends on an **entry handoff**; mission routing owns entry → tasks → **exit handoff**; civil egress returns home. The two segments share the handoff fix id — no gap.

Mission autonomy may search a hex lattice internally. Export still snaps to handoffs + registered mission fixes. No anonymous grid-cell ids on the wire.

Grid fidelity for the prototype: one 2-D hex/square layer rasterized from continuous threat radii. Next bead: a few altitude layers. Not 1 km cubes yet.

See [`CIVIL-MISSION-AREAS.md`](CIVIL-MISSION-AREAS.md) and [`THREAT-COST-GRID-OPTIONS.md`](THREAT-COST-GRID-OPTIONS.md).

---

## 8. What the current code already is

| Piece | Today | Walkthrough name |
|-------|-------|------------------|
| `route_generator` greedy cover | Nearest task → nearest covering fix | Constructive VRP / covering salesman |
| `graph_routing` Dijkstra | k-NN published graph | Hop engine (civil / short) |
| `costgrid` penalties | Threat circles on graph edges | Thin threat field |
| allocator regions | Type + geography | Cluster-first VRP |
| propagator | Constant burn + reserve | Feasibility, not routing |

The planner feels simplistic because itinerary is still nearest-neighbor and the threat field is still edge penalties — not because waypoints should become a different object per algorithm.

---

## 9. Validated vs future

| Validated target | Future bead |
|------------------|----------------|
| Greedy cover + Dijkstra hops; published fixes only | Optimal MIP VRP / ALNS |
| Threat cost on graph or 2-D hex field + A* | Time-dependent A*; full isochrone engine |
| Capacity + window check; unallocated / infeasible-by-time | Tight VRPTW with shared TOT solver |
| Composite civil → mission → civil with shared handoffs | Multi-area connectors; 3-D voxels |
| COA comparison of `platforms_used` and exposure | Auto-pick best option |

---

## 10. Related docs

- [`WAYPOINT-AND-ROUTING-MODEL.md`](WAYPOINT-AND-ROUTING-MODEL.md) — locked representation
- [`CIVIL-MISSION-AREAS.md`](CIVIL-MISSION-AREAS.md) — handoffs and regimes
- [`THREAT-COST-GRID-OPTIONS.md`](THREAT-COST-GRID-OPTIONS.md) — weather-map grid; layers vs cubes
- [`ROUTE-PLANNER-MODES.md`](ROUTE-PLANNER-MODES.md) — threat_avoid, loiter, spread, efficient
- [`API-PROTOTYPE-SERVICES.md`](API-PROTOTYPE-SERVICES.md) — allocate / plan / iterate contracts
