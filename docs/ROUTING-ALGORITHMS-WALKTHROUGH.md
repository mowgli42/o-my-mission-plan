# Routing Algorithms Walkthrough

Companion to [`WAYPOINT-AND-ROUTING-MODEL.md`](WAYPOINT-AND-ROUTING-MODEL.md).

Teaching walkthrough (not a solver spec): why itinerary is split from hop geometry, how weather-routing ideas transfer to threat fields, and **which algorithm each military COA actually uses**.

Schematic plots (PSAB / Mutla teaching sketches, not operational charts) live in the printable PDF walkthrough.

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

## 2. COA options mapped to algorithms

This is the alignment table. A/B/C are the pinned working set; the others are named modes / contingency archetypes.

| COA / slot | Intent | Itinerary (VRP flavor) | Hop engine |
|------------|--------|------------------------|------------|
| **A Efficient** | Economy of force; fewer jets | **CVRP pack** — minimize `platforms_used` | Short Dijkstra / A* (distance) |
| **B Synchronized** | Shared TOT; BDA after strike | **VRPTW + precedence** (strike → BDA) | Shared hold vias; ETA / isochrone slack |
| **C Unexpected axis** | Dislocate; non-obvious approach | Same tasks; vias may change order | **Forced via chain** + Dijkstra |
| **Threat-avoid** | Survive contested ingress | Prefer airframes with fuel margin | **A* on threat cost field** |
| **Spread the field** | Do not stack in one kill box | **mTSP** — more tours, less packing | Optional peer-edge penalty |
| **Area loiter** | Dwell / collect | ISR keeps the collect task | Cyclic published fixes + loiter fuel |
| **Shock / attrition** (pool) | Front-load or stay resilient | Priority order / redundant assigns | Same hop tools; different packing |

Same task pool should produce different `platforms_used` and different geometries across COAs. That is what Mission Option slots exist to compare.

**Do not** assign a new waypoint type per COA. Efficient and threat-avoid differ in *cost*, not in *object model*.

---

## 3. Practical example — Mutla strike from PSAB

- Home: OEPS (PSAB).
- Task: STK-01 near Mutla Ridge (needs a published fix within 20 nmi).
- A SAM umbrella sits on the short radial from the south.
- Civil graph carries the jet to an **entry handoff**; mission routing owns the last hop.

| COA | What the planner does | What you should see |
|-----|----------------------|---------------------|
| Efficient | One fighter; shortest published cover fix | Short radial; nearer the SAM |
| Threat-avoid | Same fighter; A* raises cost in jam/lethal cells | Dogleg west; more nmi; lower exposure |
| Unexpected axis | Forced vias toward a western corridor | Not the PSAB-direct radial |
| Synchronized | Fighter TOT + ISR BDA lag on the option | Geometry may match efficient; **timeline** shows windows |
| Spread | Second fighter takes Basra instead of stacking Mutla | `platforms_used` up; two separated tours |

Ship analogue on the same story: five cargo ports in the Gulf. Weather does not invent a new kind of waypoint. It changes the **cost of each sea leg**. Which ship calls which ports is still VRP — liner rotation vs tramp vs “split the cargo across more hulls.”

---

## 4. Isochrones

An **isochrone** is a line or front of **equal time** from an origin. Every point on the 6-hour front is reachable in six hours given the current speed field.

### Classic ship weather-routing loop (James / Hagiwara)

1. From the start, step forward Δt (for example 6 hours).
2. The set of reachable positions is the new isochrone.
3. Keep the points that look best toward the destination (or lowest fuel).
4. Repeat until a front reaches the goal; trace back the chosen points.

Isochrones answer “where can I be at time *t*?” They shine when the environment changes **speed** (weather). They are awkward as the only engine when the map is a patchwork of hard keep-out cells.

**In o-my:** use isochrones as a **TOT / slack metric** for COA B — earliest time any platform can reach a cover set — not as the default mission path engine.

---

## 5. A* and Dijkstra on a cost field

**Dijkstra** finds the cheapest path when edge costs are non-negative. **A\*** adds a heuristic (usually remaining great-circle) toward the goal.

A weather or threat “map” only sets those edge costs. Green = cheap, yellow = jam/high waves, red = lethal/storm.

| Field source | Typical cell cost | Hop engine | COA that uses it |
|--------------|-------------------|------------|------------------|
| Wind / waves | Time or fuel to cross the cell | Isochrones or A* | Time metric; future weather band |
| Threat jam / lethal | Distance × exposure (or ∞) | A* / Dijkstra | Threat-avoid |
| Civil published graph | Great-circle nmi | Dijkstra | Efficient civil ingress/egress |

```text
cost = distance_weight × length + Σ exposure(threat, cell)
```

Same code path can later accept a weather band. Do not vendor a ship stack just to paint a different field.

---

## 6. VRP — why the itinerary layer exists

TSP is one traveler visiting every city. **VRP** is several vehicles, not every stop on every truck, return to depot, do not overload.

A beautiful A* hop on a bad assignment still wastes an airframe.

| Variant | Rule | COA analogue |
|---------|------|----------------|
| CVRP | Capacity per vehicle | Efficient pack |
| VRPTW | Time windows | Synchronized TOT / BDA |
| mTSP | Several tours, weak packing | Spread the field |
| Covering VRP | Get near, not onto, the point | 80 / 20 nmi |
| Pickup & delivery | A before B | Strike then BDA |
| Dynamic VRP | Stops appear mid-tour | Insert task; full re-assess |

**Prototype lock:** greedy insertion + capacity + time-window check. Report unallocated and infeasible-by-time.

---

## 7. Ships vs packages — same split

| Decision | Cargo + weather | Mission + threats |
|----------|-----------------|-------------------|
| Must visit | Contracted ports (sometimes skip) | Assigned tasks |
| Close enough | Usually the berth | 80 nmi collect / 20 nmi strike |
| Field | Wind, waves, currents | Jam / lethal / CAP layers |
| Hop | Isochrones or grid A* | Grid A* on threat field |
| Multi-stop | VRP / liner rotation + per-leg router | Allocate + order + per-leg router |
| Replan | New forecast; closed port | New task; new threat; missed TOT |

Ships rarely let weather reorder the whole rotation by itself. Threats should work the same way unless a hop becomes infeasible — then VRP re-orders or drops the task.

---

## 8. Combining multi-task + varying field (COA-aware pick)

```text
position = entry handoff (after civil ingress)
while remaining tasks:
    cost(t) = A*(position → cover(t)) on current field
    pick next t by COA:
        efficient     → cheapest hop that still fits capacity
        synchronized  → cheapest hop that meets TOT / precedence
        spread        → hop that increases separation from peers
        threat_avoid  → cheapest hop under exposure-weighted cost
        unexpected    → hop that still honors forced vias
    append hop; update position; maybe refresh field
A*(position → exit); civil egress home
```

Do not grow one isochrone that tries to swallow every target.

---

## 9. Civil vs mission areas

Civil airspace: published navaid graph (cheap Dijkstra). **Mission area:** polygon with a weather-map cost field. Civil ingress ends on **ENTRY**; mission owns ENTRY → tasks → **EXIT**; civil egress home. Shared handoff ids — no gap.

See [`CIVIL-MISSION-AREAS.md`](CIVIL-MISSION-AREAS.md) and [`THREAT-COST-GRID-OPTIONS.md`](THREAT-COST-GRID-OPTIONS.md).

---

## 10. What the current code already is

| Piece | Today | Walkthrough name |
|-------|-------|------------------|
| `route_generator` greedy cover | Nearest task → nearest covering fix | Constructive VRP / covering salesman |
| `graph_routing` Dijkstra | k-NN published graph | Efficient / civil hop |
| `costgrid` penalties | Threat circles on graph edges | Thin threat_avoid field |
| allocator regions | Type + geography | Cluster-first VRP |
| option vias | Forced published ids | Unexpected-axis hop |
| option timing metadata | TOT / BDA stored, not solved | Synchronized VRPTW stub |
| propagator | Constant burn + reserve | Feasibility |

---

## 11. Validated vs future

| Validated target | Future bead |
|------------------|----------------|
| Greedy cover + Dijkstra hops; published fixes only | Optimal MIP VRP / ALNS |
| Threat cost on graph or 2-D hex field + A* | Time-dependent A*; full isochrone engine |
| Capacity + window check; unallocated / infeasible-by-time | Tight VRPTW with shared TOT solver |
| Composite civil → mission → civil with shared handoffs | Multi-area connectors; 3-D voxels |
| COA comparison of `platforms_used` and exposure | Auto-pick best option |

---

## 12. Related docs

- [`WAYPOINT-AND-ROUTING-MODEL.md`](WAYPOINT-AND-ROUTING-MODEL.md) — locked representation
- [`FORCE-APPROACHES.md`](FORCE-APPROACHES.md) — historical archetypes behind COAs
- [`CIVIL-MISSION-AREAS.md`](CIVIL-MISSION-AREAS.md) — handoffs
- [`THREAT-COST-GRID-OPTIONS.md`](THREAT-COST-GRID-OPTIONS.md) — weather-map grid
- [`ROUTE-PLANNER-MODES.md`](ROUTE-PLANNER-MODES.md) — mode catalog
- [`API-PROTOTYPE-SERVICES.md`](API-PROTOTYPE-SERVICES.md) — iterate API
