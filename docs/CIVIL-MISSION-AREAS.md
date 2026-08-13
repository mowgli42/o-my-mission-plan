# Civil vs Mission Areas — Routing Regimes & Handoff

**Graham-bell:** two spatial regimes, one exportable route string. Learn the handoff; don’t pretend the whole theater is one IFR airway graph.

---

## 1. Problem

Outside the fight, aircraft should follow **civil-style** published waypoints (navaids, airbases, airway-like links).

Inside a contested or tasked region, the path is driven by **threats with ranges** and a **cost grid** — the platform has more **mission autonomy** (where it flies between effects), not civil ATC structure.

Those two regimes must **connect**: the civil leg delivers the aircraft to a mission entry; the mission leg does collection/strike; civil (or safe corridor) takes it home.

```text
  [Home / civil airspace]  --civil route-->  [ENTRY handoff]
        |                                         |
        |                              [MISSION AREA]
        |                         cost grid + threats
        |                         autonomous mission path
        |                                         |
  [Home / civil]  <--civil/safe egress--  [EXIT handoff]
```

---

## 2. Definitions

### Civil area

- Region where routing uses the **civil published-fix graph** only (airbases, commercial navaids, optional enroute mission fixes that are still “nav DB” points).
- Objective: short / procedural / predictable. Threat penalties are light or zero unless a known no-fly exists.
- Planner modes that dominate here: `efficient`, pure graph Dijkstra, civil supplier (openRouteFinder-style).

### Mission area

- Explicit geographic region (polygon or set of cells) where **mission routing** applies.
- Contains (or is defined by) a **cost grid** derived from threats (lethal + jam radii, severity) and optional terrain/weather layers.
- Inside the area, the planner has **autonomy** to choose path geometry under cost and task coverage — not required to follow civil airway structure.
- Still must **export** a sequence the rest of the system understands (see §4).

### Handoff fixes

- **Entry:** published or designated fix on/near the mission-area boundary where civil routing **ends** and mission routing **begins**.
- **Exit:** boundary fix where mission routing **ends** and civil/safe egress **begins**.
- Handoffs are first-class objects: `id`, location, `area_id`, role `entry|exit|either`.

---

## 3. Composite route structure

A full platform route is a **concatenation of segments**:

| Segment | Regime | Builder |
|---------|--------|---------|
| Ingress | Civil | Civil graph: home → … → **entry handoff** |
| Mission | Mission | Cost-grid / threat-aware planner inside area; covers tasks; **entry → … → exit** |
| Egress | Civil (or safe corridor) | Exit handoff → … → home |

Optional: multiple mission areas (rare in demo) = multiple mission segments with civil connectors between them.

**Fuel** is still propagated on the **full** concatenated leg list (one Route, one GO/NO-GO).

**Tasks** are associated only against waypoints (or mission path samples snapped to fixes) that lie in/near the mission segment.

---

## 4. Autonomy vs export (important tension)

| Concern | Civil segment | Mission segment |
|---------|---------------|-----------------|
| Path freedom | Low — published civil fixes | High — cost grid / denser mission lattice |
| Threat model | Optional avoid | Primary driver |
| Export to UCI / sim | Ordered published fixes | Must **snap or project** onto published + **mission** fixes so we don’t invent anonymous lat/lon on the wire |

**Prototype rule (opinionated):**

1. Mission planner may search on a **dense lattice or hex cost grid** inside the area (true autonomy for *optimization*).
2. Before the route is stored/exported, the mission path is **reduced to a sequence of known fixes**:
   - boundary handoffs,
   - pre-seeded `mission` kind waypoints inside the area,
   - optional grid-snap points that were **registered as mission fixes** when the area was defined (not invented per request).

**Rejected:** shipping raw grid cell centers as route waypoints with random ids (breaks published-only contract and civil continuity).

**Bead:** continuous mission trajectory + separate “nav leg” reduction for ATC/UCI.

---

## 5. Mission area model (data)

```text
MissionArea {
  id: string
  label: string
  polygon: LatLon[]          # or bbox for demo
  threat_ids: string[]       # threats that populate the cost field
  entry_handoff_ids: string[]
  exit_handoff_ids: string[]
  mission_fix_ids: string[] # denser published mission WPs inside
  grid?: { cell_nmi, cost_layer_ref }
}

HandoffFix {
  id, location, kind: "mission" | "navaid" | "airbase"
  area_id, role: entry | exit | either
}
```

Demo (Gulf): one primary mission area covering Kuwait/southern Iraq task belt; entry near RAS / Wadi corridor; exit same or alternate; threats already in `THREATS` bind to the area.

---

## 6. How planners use regimes

```text
plan_composite(aircraft, tasks, mode):
  area = mission_area_containing(tasks) or default theater mission area
  entry = select_entry(home, area, mode)      # civil graph to entry
  exit  = select_exit(area, home, mode)

  civil_in  = civil_route(home → entry)
  mission   = mission_route(entry → cover tasks → exit,
                            cost_grid=area.threats,
                            mode=threat_avoid|loiter|…)
  civil_out = civil_route(exit → home)

  return concatenate(civil_in, mission, civil_out)
```

- **Civil builder:** existing efficient / graph Dijkstra; **no** heavy threat cost (or only hard no-fly).
- **Mission builder:** costgrid / threat_avoid / area_loiter / spread inside area only; autonomy on the grid; snap to handoffs + mission fixes.

Modes from `ROUTE-PLANNER-MODES.md` apply **primarily to the mission segment**; civil segments stay efficient-like unless egress_safe forces a preferred corridor.

---

## 7. Connection contract (civil must meet mission)

1. Civil ingress **last fix** ≡ mission **first fix** ≡ chosen **entry handoff**.
2. Mission **last fix** ≡ civil egress **first fix** ≡ chosen **exit handoff**.
3. No gap: consecutive segments share the handoff waypoint id (compacted once on the full route).
4. If no handoff can reach a task (mission grid can’t cover proximity), task → unsatisfied; do not break civil segment to invent a point.

---

## 8. UI / map implications

- Draw mission area polygon (or hex fill) distinct from civil basemap.
- Cost-grid toggle applies **inside** mission area by default.
- Threat rings primarily annotated in mission area.
- Route style: civil legs one color; mission legs another; handoff markers emphasized.

---

## 9. Relation to prior locked decisions

| Prior decision | How this extends it |
|----------------|---------------------|
| One waypoint *kind set* on the wire | Still airbase/navaid/mission — grid is internal to mission planner |
| Costgrid supplier | Becomes the **mission segment** engine, not whole-home-to-home by default |
| COA modes | Mode shapes mission segment; civil remains the connector |

---

## 10. Validated vs future (graham-bell)

| Behavior | Prototype target |
|----------|------------------|
| One MissionArea with entry/exit handoffs | Yes |
| Composite route civil→mission→civil sharing handoff ids | Yes |
| Mission segment uses threat cost grid; civil does not | Yes |
| Path autonomy on internal grid then snap to mission fixes | Yes (simple) |
| Multiple overlapping areas / dynamic area redraw | Future |
| True free continuous trajectory export | Future bead |

---

## 11. API sketch (additive)

```text
GET  /api/mission-areas
POST /api/route/plan  { …, use_composite: true, mission_area_id?: string }

RoutePlanResult.segments: [
  { regime: civil|mission, fix_ids: [], distance_nmi, exposure_score? }
]
```

Full `Route.waypoints` remains the concatenated, compacted list for fuel and export.
