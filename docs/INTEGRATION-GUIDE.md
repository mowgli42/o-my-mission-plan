# Integration Guide — Route Suppliers, Options, and Core Services

## Audience

Developers wiring a civil or mission route supplier into o-my-mission-plan, or extending the planning cycle to support the top-three Mission Options (Efficient / Synchronized / Unexpected-axis).

---

## Core contracts (stay stable)

| Component | Responsibility | Must not |
|-----------|----------------|----------|
| Allocator | Task → aircraft; report unallocated | Build routes |
| Route supplier adapter | Origin/dest/constraints → ordered published fixes | Invent PROX points; decide fuel GO/NO-GO |
| Task association | Bind tasks to route by 80/20 nmi proximity | Change geometry |
| Route Propagation Service | Fuel per leg + reserve → GO/NO-GO | Choose waypoints |
| Mission Option store | Save router inputs + results for comparison | Call external navdata |

UCI-oriented messages should be derivable from: AllocationResult, Route, FuelState, MissionOption metadata.

---

## Supplier integration steps

1. **Implement protocol** in `suppliers/base.py` (or equivalent):
   - `plan(request: SupplierRouteRequest) -> SupplierRouteResponse`
2. **Register** under a config key (`ROUTE_SUPPLIER`).
3. **Map response → Route** using only published waypoint kinds.
4. **Associate tasks** with existing proximity helpers.
5. **Propagate fuel** via existing `propagator.propagate`.
6. **Attach** the finished plan to a Mission Option slot with saved inputs.

Fallback supplier must always work with no extra packages installed.

---

## Mission Option record (minimum fields)

```text
MissionOption
  id, label
  emphasis: efficient | synchronized | unexpected_axis
  slot: A | B | C | none
  router_inputs: { supplier, origin, vias, avoids, axis_profile, sync_group, … }
  task_ids: [...]
  aircraft_ids: [...]
  plans: list[PlannedAircraft]   # routes + fuel + status
  summary: { go, nogo, unallocated, total_distance_nmi, … }
  created_at, parent_option_id?
```

API sketch (to be formalized in OpenSpec):

- `POST /api/options` — create option from current world + emphasis + router inputs (runs allocate → route → propagate)
- `GET /api/options` — list saved options
- `POST /api/options/{id}/rerun` — same inputs with patches
- `POST /api/options/{id}/slot` — pin to A/B/C
- `GET /api/options/compare?ids=...` — side-by-side metrics

---

## Iterative loop (integrator view)

```text
load world → create option (emphasis + inputs)
  → inspect GO/NO-GO + unallocated
  → pin to slot A/B/C
  → duplicate + patch inputs → rerun
  → compare
  → export accepted GO routes to o-my-sim / UCI
```

Dynamic task insert should target a specific option (or the “working” option), re-generate that aircraft’s route with the same saved emphasis/inputs, and refresh comparison metrics.

---

## Theater / nav database

Current Gherkin centers on **OEPS (PSAB)** with Kuwait/Iraq published fixes. Civil and mission suppliers must read the same demo (or configured) nav database. When swapping theaters, only fixtures + supplier graph coverage should change—not the core contracts.

---

## Related issues / docs

- Issue #2 — published waypoints only (no PROX-*)
- Issue #3 — pluggable route supplier adapter
- `docs/CONOPS.md` — cycle and top-three options
- `docs/CIVIL-ROUTE-DEV-GUIDE.md` / `docs/MISSION-ROUTE-DEV-GUIDE.md`
