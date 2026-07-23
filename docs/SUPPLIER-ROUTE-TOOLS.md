# Supplier Route Tools — Reusing Existing Planners

## Intent

Keep the o-my-mission-plan **core** small (allocation feedback + Route Propagation Service with constant-burn fuel + fixed reserve). Treat richer lateral route construction as **supplier-provided capabilities** that we call over a clean interface and then convert into OMS/UCI-aligned routes with associated tasks.

This document maps the open-source and research tools identified in the attached research to that supplier model, prioritised by **ease of integration** into our FastAPI / Python stack.

## Architecture split

```
┌─────────────────────────────────────────────────────────────┐
│  Supplier capability (external or pluggable)                │
│  - Initial civil-style route generator                      │
│  - Future cost-grid / avoid-zone planner                    │
│  Input: origin, destination, optional vias / no-fly / costs │
│  Output: ordered fixes (id + lat/lon) or polyline           │
└───────────────────────────┬─────────────────────────────────┘
                            │ adapter
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  o-my-mission-plan core                                     │
│  1. Convert supplier output → our Route (published WPs)     │
│  2. Associate tasks by proximity (80 nmi ISR / 20 nmi STK)  │
│  3. Route Propagation Service (fuel per leg + GO/NO-GO)     │
│  4. Surface unallocated tasks + fuel-infeasible routes      │
└─────────────────────────────────────────────────────────────┘
```

Our own hand-rolled generator remains a **fallback / demo mode** so the prototype works with zero external dependencies.

## Tool evaluation (ease of integration first)

| Tool | Type | Integration effort | Best fit | Notes |
|------|------|--------------------|----------|-------|
| **openRouteFinder** (gtxzsxxk / FSUnion forks) | Pure Python, Dijkstra on airway network | **Low** | Initial civil-style route supplier | Portable library + optional HTTP service; already returns shortest airway routes for sim use. Ideal first adapter. |
| **OpenAP / OpenAP-TOP** | Python performance + trajectory optimisation | Medium | Future cost / fuel-aware profile supplier | Excellent aircraft performance models and optimal-control trajectories; better for vertical/cost refinement than for selecting civil airways. |
| **networkx + our navaid graph** | In-process Dijkstra / A* | Low–medium | Controlled cost-grid or multi-cost experiment | We already have Florida navaids + airbases; adding edge costs and avoid zones is straightforward and fully under our control. |
| **BlueSky** | Full Python ATM simulator | High | Later validation / multi-aircraft simulation | pip-installable; powerful for traffic and flow experiments, heavier than we need for a single-route supplier. |
| **Little Navmap** | Desktop planner + rich export formats | High (process/file) | Human-in-the-loop or offline import | Excellent PLN / FMS / GPX export; not a library we call from FastAPI. Useful as a manual supplier or format bridge. |
| Flight Plan Database / web planners | External web services | Medium–high | Optional cloud supplier | Would need scraping or unofficial API; less suitable as a first-class embedded supplier. |

## Recommended initial concept

### 1. Initial route supplier → openRouteFinder (or its Dijkstra core)

**Why easiest:**
- Written in Python, already uses Dijkstra over an airway/waypoint graph.
- Designed as portable services that can be embedded or exposed over HTTP.
- Output is a sequence of fixes — exactly what we need to map into our `Route` model.

**Adapter sketch:**

```text
SupplierRouteRequest
  origin: airbase or lat/lon
  destination: airbase or lat/lon
  optional_vias: list of fix ids
  aircraft_type_hint: ISR | FIGHTER | BOMBER   # optional

SupplierRouteResponse
  fixes: list[{id, lat, lon, name?}]
  total_distance_nmi: float
  source: "openRouteFinder" | "fallback" | …
```

Our adapter then:
1. Calls openRouteFinder (in-process or localhost service).
2. Maps the returned fixes → list of our `Waypoint` (kind = navaid / airbase).
3. Builds `Leg`s with great-circle distances.
4. Runs proximity association: attach tasks whose locations fall within 80/20 nmi of any fix.
5. Hands the `Route` to the existing propagator for fuel + GO/NO-GO.

If openRouteFinder is unavailable or has no coverage for the Florida demo subset, fall back to the current published-waypoint generator (after the PROX-* removal in issue #2).

### 2. Future cost-grid / avoid-zone supplier

Two progressive options, both still “supplier” shaped:

**A. Lightweight in-house (fastest path to a demo)**  
- Build a small graph (or 2-D grid) over the Florida demo navaids + extra cells.  
- Edge/node costs = distance + optional risk / no-fly penalties.  
- Run `networkx.shortest_path` (Dijkstra) or A*.  
- Same adapter contract as above.

**B. OpenAP-TOP (richer physics)**  
- Use OpenAP performance models + optimal-control trajectory optimiser for fuel/emissions-aware 4-D paths.  
- Convert the resulting trajectory samples into a reduced set of waypoints for our Route model.  
- Better long-term supplier for “minimum fuel / climate cost subject to avoid zones.”

BlueSky can sit behind either as a **validation** environment (fly the generated route in a simulated traffic picture) rather than as the generator itself.

## Conversion to OMS / UCI routes + tasks

Regardless of supplier:

1. **Lateral path** → ordered published (or supplier-provided) waypoints + great-circle legs.  
2. **Task association** → proximity check (80 nmi ISR, 20 nmi strike) against the waypoint list; tasks that cannot be associated remain in the unallocated feedback list.  
3. **Fuel** → always our Route Propagation Service (constant burn + fixed reserve).  
4. **UCI surface** → the resulting Route + assignment + feasibility become the messages external consumers see; the supplier itself stays behind the adapter.

This preserves the original design principle: external suppliers own sophisticated planning; we own feasibility, feedback, and the live route state.

## Implementation phases (suggested)

| Phase | Work |
|-------|------|
| 0 | Finish published-waypoint-only generator (issue #2) — becomes the reliable fallback. |
| 1 | Define `SupplierRouteRequest` / `SupplierRouteResponse` Pydantic models and a no-op / fallback adapter. |
| 2 | Spike openRouteFinder (or RouteFinderLib) in a branch; measure coverage on the Florida demo set. |
| 3 | Wire the adapter into `planning.py` behind a feature flag / config (`ROUTE_SUPPLIER=fallback|openroutefinder`). |
| 4 | Document the UCI-oriented contract so a real external supplier can replace the adapter. |
| 5 | Prototype cost-grid supplier (networkx + avoid polygons) or OpenAP-TOP trajectory → waypoint reduction. |

## Non-goals for the first supplier integration

- Replacing the fuel propagator with an external tool.  
- Full SID/STAR procedure encoding or real ARINC 424 navdata.  
- Calling desktop apps (Little Navmap) from the live service path.  
- Multi-objective Pareto optimisation in the first adapter.

## References

- Attached research summary (open-source civil route tools, cost-grid planners, Dijkstra/A*).  
- openRouteFinder — https://github.com/gtxzsxxk/openRouteFinder (and FSUnion forks).  
- OpenAP / trajectory tools — mode-s.org / OpenAP ecosystem.  
- BlueSky — https://github.com/TUDelft-CNS-ATM/bluesky  
- Internal: `docs/ROUTE-GENERATION.md` (published waypoints only).  
