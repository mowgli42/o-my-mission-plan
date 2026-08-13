# Prototype API — Route Planners, Timed Allocation, Capacity Tracking

**Graham-bell:** contracts first, thin FastAPI implementations second. All paths stay published-waypoints-only; fuel stays in the propagator.

Base path: `/api` (existing app). New resources below are additive.

---

## 1. Domain additions (request/response sketches)

```text
RoutePlannerMode =
  efficient | threat_avoid | spread_field | area_loiter
  | unexpected_axis | synchronized | egress_safe  # last optional stub

TaskWindow { earliest?: ISO8601, latest?: ISO8601, nominal_tot?: ISO8601 }

Task {
  id, type: ISR|STRIKE, location, priority,
  target_id?: string,          # groups tasks on one objective
  window?: TaskWindow,
  status?: unassigned|assigned|unsatisfied|complete
}

Target {
  id, label, location?, task_ids[]
}

PlatformCapacity {
  aircraft_id,
  max_tasks: int,
  weapons_loadout: int,
  weapons_remaining: int,
  fuel_initial, fuel_reserve, burn_rate_per_nmi,
  tasks_assigned: int,
  estimated_fuel_after_plan?: float
}

AllocationRequest {
  task_ids?: string[],           # default: all unassigned
  aircraft_ids?: string[],
  coa_bias: efficient | synchronized | spread_field | threat_avoid | maneuver,
  respect_time_windows: bool = true,
  minimize_platform_count: bool   # true for efficient bias
}

AllocationResult {
  assignments: { aircraft_id: task_id[] },
  unallocated_task_ids: string[],
  infeasible_by_time_task_ids: string[],
  platforms_used: int,
  capacity_snapshot: PlatformCapacity[],
  notes: string[]
}

RoutePlanRequest {
  aircraft_id,
  task_ids: string[],
  mode: RoutePlannerMode,
  vias?: string[],
  avoid_fix_ids?: string[],
  coa_option_id?: string
}

RoutePlanResult {
  route: Route,                 # existing model
  mode: RoutePlannerMode,
  exposure_score?: float,       # threat_avoid
  loiter_minutes?: float,       # area_loiter
  separation_notes?: string[],  # spread_field
  fuel: FuelState
}

IterationRequest {
  coa_option_id?: string,       # create new if omitted
  label?: string,
  archetype: string,
  route_mode: RoutePlannerMode,
  allocation: AllocationRequest,
  # optional per-aircraft mode overrides
}

IterationResult {
  option_id: string,
  allocation: AllocationResult,
  plans: RoutePlanResult[],
  summary: {
    platforms_used, go, nogo, unallocated,
    total_distance_nmi, mean_exposure?, tot_slack_minutes?
  }
}
```

---

## 2. Endpoints (prototype)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/planner-modes` | List modes + short intent strings |
| POST | `/api/allocate` | Timed, capacity-aware allocation with COA bias |
| POST | `/api/route/plan` | Single-platform route under a planner mode |
| POST | `/api/iterate` | Full cycle: allocate → plan each → propagate → store option |
| GET | `/api/tasks` | Task pool + status + windows |
| PATCH | `/api/tasks/{id}` | Update window / status / target_id |
| GET | `/api/targets` | Target groupings |
| POST | `/api/targets` | Create target and bind task ids |
| GET | `/api/platforms/capacity` | Live capacity snapshot |
| GET | `/api/options/{id}/iteration-summary` | Metrics after last iterate |
| POST | `/api/options/compare` | Existing compare + platforms_used + exposure |

Existing: `/api/plan`, `/api/tasks/insert`, `/api/propagate`, options pin/compare — keep; `iterate` is the multi-mode entry point for COA experiments.

---

## 3. Mode behavior contracts (testable)

| Mode | SHALL |
|------|--------|
| `efficient` | Prefer short published paths; allocation may set `minimize_platform_count=true` |
| `threat_avoid` | Apply threat zone penalties; return `exposure_score`; path may differ from efficient |
| `spread_field` | After routing, note or lightly re-cost edges near peer routes; document if only advisory |
| `area_loiter` | For ISR-heavy sets, include cyclic fixes + `loiter_minutes` fuel impact |
| `unexpected_axis` | Honor `vias` order |
| `synchronized` | Preserve shared hold vias; timing in allocation windows / option metadata |

All modes: published fixes only; fuel GO/NO-GO via propagator; unsatisfied tasks listed.

---

## 4. Iteration semantics

1. `POST /api/iterate` runs allocation under `coa_bias`.
2. For each aircraft with tasks, runs `route/plan` with `route_mode` (and COA vias/avoids from option inputs).
3. Propagates fuel; builds `IterationResult` and persists a Mission Option.
4. Client pins to A/B/C, patches windows or mode, iterates again with `parent_option_id`.

**Learning goal:** same task pool → efficient iteration uses fewer platforms than spread_field; threat_avoid increases distance/exposure trade visible in summary.

---

## 5. Sim data extensions

- Tasks gain optional `window` and `target_id`.
- Targets fixture: e.g. `TGT-MUTLA` → STK-01 + nearby ISR.
- Capacity: fighters `max_tasks=2–3`, bombers higher weapons, ISR `weapons=0` / higher task slots for collects.

---

## 6. Non-goals for this API slice

- Optimal MILP allocation
- Real-time replan under moving threats
- Formation / deconfliction clearances
- Guaranteeing spread_field separation in continuous space
