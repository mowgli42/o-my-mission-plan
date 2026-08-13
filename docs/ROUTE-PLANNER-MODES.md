# Route Planner Modes — Military Phases & Algorithms

**Graham-bell posture:** explore multiple planner concepts, pick simple prototypes that teach, leave production path as beads.

## 1. Why multiple planners (not one “smart” router)

Different phases of a campaign ask for different geometry and risk posture:

| Phase (notional) | Planner need | Failure if you use the wrong mode |
|------------------|--------------|-----------------------------------|
| Opening / SEAD / first look | Threat avoidance, shock corridor | Package attrited before effects |
| Main effort strike / collection | Efficient or synchronized visit order | Fuel waste; missed TOT |
| Dislocation / deception | Unexpected axis, spread the field | Predictable axis; massed in one kill box |
| Hold / ISR dwell | Area loiter / orbit | Gaps in coverage; single-orbit predictability |
| Sustain / attritional | Resilience paths, alternates | No branch when primary corridor dies |

**Choice for prototype:** one **RoutePlannerMode** enum + shared published-waypoint graph; each mode is a different *cost / objective / via policy* on that graph.  
**Rejected:** separate solvers with different waypoint types per mode (splits the data model; breaks UCI export).  
**Revisit when:** production needs continuous 3-D RRT* with kinodynamics → bead.

---

## 2. Planner catalog (main types)

### 2.1 Threat avoidance (`threat_avoid`)

- **Intent:** Minimize cumulative exposure (jam/lethal cost) while still covering assigned tasks.
- **Prototype algorithm:** Dijkstra / constrained shortest path on published-fix graph with edge cost = distance × threat-zone penalties (already partially in `costgrid`).
- **Research anchors:** CSP aircraft routing under SAM risk (NPS); multi-criteria Dijkstra/A*; ACO/PSO in literature for denser grids.
- **Inputs:** threat set, severity→penalty map, optional hard no-fly (infinite cost).
- **Outputs:** published fix sequence + exposure score + geometric distance.
- **Demo learning goal:** show path *bends* vs pure-distance when a HIGH/CRITICAL SAM sits on the direct radial.

### 2.2 Efficient / economy (`efficient`)

- **Intent:** Cover tasks with minimum geometric distance (and thus fuel under constant burn).
- **Prototype algorithm:** greedy nearest covering-fix + optional pure-distance Dijkstra between covers (current fallback).
- **Research anchors:** TSP / covering salesman (visit within sensor radius, not necessarily overfly); mTSP for multi-aircraft.
- **Demo learning goal:** baseline for comparison against threat_avoid and unexpected_axis.

### 2.3 Spread the field (`spread_field`)

- **Intent:** Reduce concentration risk—platforms and paths spaced so one engagement does not attrit the package.
- **Prototype algorithm (simple):** after individual paths, penalize edges near *other platforms’* planned legs (or demand minimum lateral separation between simultaneous segments); optional quadrant assignment of tasks before routing.
- **Alternative considered:** full multi-agent pathfinding (MAPF). Rejected for prototype complexity.
- **Demo learning goal:** two fighters’ routes visibly separate vs both stacking the same navaid corridor.

### 2.4 Area loiter / orbit (`area_loiter`)

- **Intent:** Persistent collection over a region (ISR dwell), not a point-to-point strike run.
- **Prototype algorithm:** select a published fix (or small cycle of fixes) inside the collection radius; emit a short cyclic waypoint list (orbit) with loiter duration / fuel burn estimate; attach task to the orbit center fix.
- **Research anchors:** coverage path planning; lawnmower / spiral for area search; orbit holds in civil IFR as analogy.
- **Demo learning goal:** ISR platform shows a hold pattern metric (time on station) instead of only point-to-point distance.

### 2.5 Unexpected axis / maneuver (`unexpected_axis`)

- **Intent:** Approach from non-obvious corridor (forced vias).
- **Prototype algorithm:** forced via chain + Dijkstra between segments (existing).
- **Demo learning goal:** path includes Jordan-side / western fixes vs direct PSAB→target.

### 2.6 Synchronized approach (`synchronized`)

- **Intent:** Geometry supports shared holds/IPs; timing metadata (TOT, BDA lag) lives on the option.
- **Prototype algorithm:** same lateral tools + required shared hold fix ids in vias; timing is allocation/timeline concern, not pure geometry.
- **Demo learning goal:** two strikes share an IP fix; timeline shows aligned TOTs.

### 2.7 Additional modes (prototype-light / beads-heavy)

| Mode | Phase | Prototype stub | Production bead |
|------|-------|----------------|-----------------|
| `ingress_low_level` | Penetrate under radar | Extra cost on high-exposure edges only | Terrain masking + 3-D |
| `egress_safe` | RTB after weapons | Prefer known safe corridor vias post-last-task | Dynamic threat update |
| `rejoin_tanker` | Sustain | Via list to tanker track fix (stub) | Real AAR geometry |
| `search_pattern` | Find relocatable target | Covering salesman subset of fixes | GA site selection |

---

## 3. Algorithm cheatsheet (what literature uses vs what we prototype)

| Family | Examples | Use in military routing | Prototype choice |
|--------|----------|-------------------------|------------------|
| Graph shortest path | Dijkstra, A*, CSP | Threat+distance on discretized airspace | **Yes** — primary |
| Covering / TSP | TSP, mTSP, covering salesman | Visit order within sensor range | **Yes** — greedy cover now; optional 2-opt later |
| Sampling | RRT, RRT* | Kinodynamic, cluttered 3-D | Bead only |
| Metaheuristics | ACO, PSO, GA | Large combinatorial MRP | Bead only |
| Geometry | Voronoi, Dubins | Threat-field skeleton; turn radius | Optional Dubins bead |
| Multi-agent | MAPF, Hungarian + path | Deconflict / assign | Spread_field light; Hungarian bead |

**Opinionated pick:** stay on **published-fix graph + Dijkstra variants + greedy cover**. Teaches the COA differences without solving NP-hard MRP to optimality.

---

## 4. Task allocation with time constraints (COA-aligned)

Allocation is not only “who is nearest.” For multi-COA iteration:

1. **Capacity:** each platform has `max_tasks`, `weapons_loadout`, fuel-derived max range, optional `max_simultaneous`.
2. **Time windows:** task `earliest` / `latest` (or nominal TOT ± slack); platform speed assumption → earliest arrival estimate.
3. **COA bias:**
   - Efficient COA → minimize platform count (bin-pack tasks onto fewer airframes if capacity allows).
   - Synchronized COA → prefer assigning sync-group strikes to platforms that can share an IP and meet the same window.
   - Spread-field COA → prefer *more* platforms / separated regions even if count rises.
   - Threat-avoid COA → prefer platforms with fuel margin for longer detours.
4. **Output:** assignments + unallocated + **infeasible-by-time** list (tasks that fit capacity but miss windows).

**Prototype algorithm:** greedy by priority, then capacity, then simple ETA check; optional second pass to merge ISR with nearby strike on same ISR-capable platform.  
**Rejected for now:** full MILP / column generation.  
**Bead:** replace with time-window mTSP or auction-based multi-UAV allocation.

---

## 5. Iteration loop (platforms × COAs)

```text
for each COA option in pool (or pinned A/B/C):
  allocate(tasks, platforms, coa_bias, time_windows)
  for each assigned platform:
    plan_route(mode=coa.route_mode, tasks, threats, vias)
    propagate_fuel(route, platform)
  score(option)  # platforms_used, exposure, TOT_slack, unallocated
compare options → human pin / patch / re-run
```

Tracking state the API must hold:

- **Tasks** (status: unassigned | assigned | unsatisfied | complete)
- **Targets** (optional grouping of tasks on same geographic objective)
- **Platform capacity** (weapons remaining, fuel state, task slots used)
- **COA option** id + mode + scores after each iteration

---

## 6. What “validated” means in graham-bell for this slice

| Behavior | Validated in prototype (target) | Aspirational |
|----------|--------------------------------|--------------|
| threat_avoid bends path vs efficient | Yes | Continuous 3-D |
| spread_field separates two routes | Yes (heuristic) | True MAPF |
| area_loiter emits orbit + dwell fuel | Yes (simple cycle) | Optimal coverage |
| timed allocation reduces platform count on efficient COA | Yes (greedy) | Optimal bin-pack |
| same task set yields different platform counts across COAs | Yes | — |
| RRT* / ACO optimal MRP | No | Bead |
