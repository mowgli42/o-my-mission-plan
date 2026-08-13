# Threat Cost Grid Options — Weather-Map Analogy & Spatial Discretization

**Graham-bell:** explore representations, pick one for the mission-area prototype, leave 3-D fidelity as beads.

Related: `docs/CIVIL-MISSION-AREAS.md` (mission area owns the grid), `docs/ROUTE-PLANNER-MODES.md` (`threat_avoid`).

---

## 1. Weather map ≈ threat map (same abstract machine)

Both problems are:

> Discretize space → assign a **scalar cost** (or multi-layer costs) per cell → run a shortest-path / isochrone search that prefers low cost → optionally snap to navigable points.

| Weather routing | Threat routing (mission area) |
|-----------------|-------------------------------|
| Wind, waves, turbulence, convective cells | SAM/AAA jam & lethal radii, CAP zones, no-fly |
| Cost = time, fuel, or risk from met fields | Cost = exposure × distance (or hard forbid) |
| Avoid or partially transit “red” cells | Same |
| Forecast timesteps (4-D) | Static for prototype; dynamic later |
| A*, Dijkstra, isochrones, DP on a grid | Same family |

Military aviation tools (e.g. concepts like AWRT — Aviation Weather Routing Tool) already treat **weather impacts grids** + A* with cost = hazard/fuel/time. Ship routers (SIMROUTE, VISIR-2, 52°North WRT, libweatherrouting) use **gridded metocean fields** + A*/Dijkstra/isochrones.

**Reuse insight:** you do **not** need a different *engine class* for threats. You need a different **cost field builder**. The path search can be the same code path as “route around weather.”

```text
  cost_field = from_weather(wind, waves, …)     # commercial / research tools
  cost_field = from_threats(SAM, AAA, CAP, …)   # our builder
  path = A_star_or_Dijkstra(graph_or_grid, cost_field)
```

What does **not** port blindly: ship isochrones assume 2-D ocean and vessel polars; civil flight planners assume airways + flight levels. Our mission segment is closer to **UAV/tactical CSP on a risk grid** than to oceanic isochrones—but the **grid + weighted A*** pattern is identical.

---

## 2. Options for representing the field

### Option A — Single 2-D layer (plan view)

- One horizontal grid over the MissionArea (hex or square cells, e.g. 5–20 nmi for demo, finer later).
- Cell cost = max (or sum) of threat contributions at a **representative altitude** (e.g. medium-altitude package).
- Search: 4/8-connected grid A* or our existing published-fix graph with edge costs sampled from the field.

| Pros | Cons |
|------|------|
| Matches current UI “hex costgrid” mental model | Cannot go *over* or *under* a threat |
| Cheap, easy to viz like a weather radar overlay | SAM envelopes are 3-D; 2-D is conservative or wrong |
| Same as many ship/weather 2-D routers | — |

**Best for:** prototype learning, map toggle, composite civil→mission demo.

---

### Option B — Stack of 2-D layers (flight levels)

- Same horizontal grid, repeated at discrete altitudes (e.g. FL050 / FL100 / FL200, or 1000 ft steps).
- Each layer has its own cost field (threat radar horizon / effective envelope differs by height).
- Moves: within layer (N/E/S/W) + climb/descend to adjacent layer with a climb cost.
- Classic “layered airspace” simplification used in UAV and ATM research; weather flight planning often optimizes lateral path then assigns levels, or searches a small set of levels.

| Pros | Cons |
|------|------|
| Captures “go high / go low” without full 3-D | Vertical resolution is coarse |
| Still weather-map-like (one map per level, scrub altitude) | More cells than A; UI needs level picker |
| Aligns with how packages think about altitude blocks | Inter-layer transitions need simple performance model |

**Best for:** next fidelity step after A; still demoable.

---

### Option C — Full 3-D voxels (e.g. 1 km cubes)

- Volume tessellation: horizontal ~1 km × vertical ~1 km (or 0.5–2 km).
- Over a Gulf mission box ~400×400×15 km → order **10⁵–10⁶** cells before pruning.
- 6- or 26-connected search; costs from full 3-D threat volumes (spherical/conical envelopes).

| Pros | Cons |
|------|------|
| Faithful 3-D engagement geometry | Memory/CPU; harder real-time replan |
| Natural home for terrain masking later | Visualization is hard (slices, isosurfaces) |
| Matches some urban UAS “air matrix” designs | Overkill for graham-bell COA comparison |

**Best for:** production bead / research spike—not the default MVP grid.

---

### Option D — Hybrid (recommended architecture)

```text
  Planning search:  Option A or B (fast)
  Threat truth:     analytical circles/spheres (continuous radii)
  Export path:      snap to handoffs + mission fixes (CIVIL-MISSION-AREAS)
  Display:          weather-map style 2-D (or per-level) color field
```

- Don’t force the search graph to be 1 km cubes just because threats are 3-D.
- Sample continuous threat intensity onto the planning lattice when building costs.
- Optional: run B with 3–5 altitude layers only where packages actually fly.

---

## 3. Cost field construction (shared with weather)

For each cell (and layer if B):

```text
cost = distance_weight * edge_length
     + Σ_threats exposure(threat, cell_center, altitude)

exposure =
  0                         if outside jam radius
  w_jam(severity)           if inside jam, outside lethal
  w_lethal(severity)        if inside lethal   # or ∞ for hard avoid
```

Weather analogue: turbulence index or wave height → soft cost; convective polygon → hard avoid (∞).

**Partial transit** (weather “yellow”): soft high cost so path may clip the edge if the detour is huge—same knob for “accept risk to save fuel.”

---

## 4. Can we reuse a common weather-routing application?

| Approach | Feasibility for o-my |
|----------|----------------------|
| **Reuse algorithm pattern** (grid + A*/Dijkstra + cost layers) | **Yes — do this** |
| **Reuse ship libraries** (VISIR, SIMROUTE, libweatherrouting) | Awkward: ocean 2-D, vessel polars, coast KD-trees; cost plug-in possible but API is metocean-centric |
| **Reuse aviation weather routers** (AWRT-class, commercial EFB optimizers) | Concept match is strong; rarely open/embeddable; treat as design reference |
| **Shared internal service** `CostFieldRouter` | **Best prototype:** one module, two field builders (`WeatherFieldBuilder` stub, `ThreatFieldBuilder` real) |

**Opinionated choice:** implement **one** `grid_router` (A* on hex/square lattice). Feed it threat costs today; keep a stub interface so a future weather layer is another cost band, not another product.

Do **not** vendor a full maritime stack just to dodge writing A* on a grid—we already have Dijkstra on the fix graph; extending to lattice cells is the small step.

---

## 5. Layers vs 1 km cubes — decision matrix

| Criterion | 2-D single | Altitude layers | 1 km cubes |
|-----------|------------|-----------------|------------|
| Demo speed / teachability | ★★★ | ★★ | ★ |
| Map = weather overlay | ★★★ | ★★ (per FL) | ★ |
| Over/under threat | ✗ | ✓ | ✓ |
| Cell count (Gulf box) | ~10²–10³ | × N_levels | ~10⁵–10⁶ |
| Matches civil handoff story | ★★★ | ★★★ | ★★ |
| Production fidelity | Low | Medium | High |

### Prototype lock (graham-bell)

1. **Mission area default grid = Option A** (single 2-D hex or square cost field), severity-colored like a weather radar.
2. **Threat geometry stays continuous** (center + jam/lethal radius); rasterize onto cells when building the field.
3. **Search** on that lattice (or keep fix-graph costs sampled from the field—both valid; lattice shows the weather-map idea more clearly).
4. **Export** still snaps to entry/exit + mission fixes.
5. **Bead:** Option B (3–5 altitude layers) when packages need explicit high/low COAs.
6. **Bead:** Option C (voxels) only if terrain masking + true 3-D envelopes become a validated requirement.

**Rejected for MVP:** jumping straight to 1 km cubes. Cost is real; learning gain over layered 2-D is small until 3-D threats and terrain dominate the scenario.

---

## 6. Visualization (weather-map UX)

- Fill mission polygon with hex/square cells; color ramp by cost (green → yellow → red), same as convective or wave-height overlays.
- Toggle layer on/off (#15).
- Optional: contour of lethal vs jam as vector rings on top of the field (truth geometry).
- If Option B: altitude scrub or buttons FL1/FL2/… swapping the visible cost slice.

---

## 7. What to implement next

| Step | Outcome |
|------|---------|
| ThreatFieldBuilder → 2-D hex costs inside MissionArea | Weather-like field |
| A* on hex graph entry→exit via low cost + task cover | Mission segment autonomy |
| Snap path to mission fixes + handoffs | Composite route export |
| Same router interface accepts a future WeatherFieldBuilder | Documented reuse path |

---

## 8. Short answers to the design questions

**“Similar to a weather map, not only logically?”**  
Yes: same grid + cost + shortest path; UI as a color field; optional multi-layer costs (threat band today, weather band later).

**“Reuse an app that routes around weather?”**  
Reuse the **pattern and ideally one internal router module**. Full maritime/aviation weather products are poor drop-in dependencies; plug threat fields into *our* grid router instead.

**“Cut into elevation layers as 2-D, or 1 km cubes?”**  
**Start with one 2-D layer** (or a few flight levels next). **Not** 1 km cubes for the prototype—reserve voxels for a production/research bead when 3-D envelopes and terrain justify the cost.
