# o-my-mission-plan

## Purpose

Enable iterative “guess-and-see” mission planning cycles for the o-my OMS ecosystem, including a **top-three Mission Options** working set (Efficient / Synchronized / Unexpected-axis) as described in `docs/CONOPS.md`.

The system:
- Accepts (or simulates) a set of unassigned ISR/collection and strike tasks (proxy for ATO ingestion), optionally grouped into **targets** and constrained by **time windows**.
- Allocates tasks across platforms using **capacity** and COA bias (minimize platform count vs spread vs synchronized windows).
- Plans lateral paths with explicit **RoutePlannerMode** values (efficient, threat_avoid, spread_field, area_loiter, unexpected_axis, synchronized, …) on a **published-waypoint** graph — see `docs/ROUTE-PLANNER-MODES.md`.
- Propagates fuel and returns GO/NO-GO; persists Mission Options for multi-COA comparison.
- Exposes an **iterate** API so planners can re-run allocation+routing across modes and track tasks, targets, and platform capacity.

## Requirements

### R1 — Unassigned Task Pool

The system SHALL maintain a pool of unassigned tasks.

Each task SHALL have at minimum:
- unique identifier
- type: `ISR` | `STRIKE`
- geographic location (lat/lon)
- optional priority (stubbed or simple integer for now)
- optional **time window** (earliest / latest / nominal TOT)
- optional **target_id** linking to a Target
- status among unassigned | assigned | unsatisfied | complete when tracked across iterations

The system SHALL report which tasks remain unallocated after an allocation cycle.

### R2 — Aircraft Resources & Capacity

The system SHALL maintain a set of aircraft resources.

Demo inventory (prototype):
- 2 × ISR
- 3 × FIGHTER
- 2 × BOMBER

Each aircraft SHALL have at minimum:
- unique identifier
- type: `ISR` | `FIGHTER` | `BOMBER`
- home airbase (identifier + lat/lon)
- initial fuel quantity
- constant burn rate (fuel units per nmi)
- fixed reserve requirement
- **capacity**: max_tasks, weapons_loadout (and remaining after plan)

The system SHALL expose a **platform capacity snapshot** after allocation/iteration.

### R3 — COA-biased Task Allocation

The system SHALL provide an allocator that:
- Assigns tasks to capable aircraft subject to capacity
- MAY respect task time windows (ETA vs earliest/latest) and report **infeasible-by-time** tasks
- Applies **COA bias**:
  - efficient → prefer fewer platforms when capacity allows
  - spread_field → prefer geographic separation / more platforms
  - synchronized → prefer assignments that can share holds and meet common windows
  - threat_avoid → prefer platforms with fuel margin for detours
- Returns assignments, unallocated ids, infeasible-by-time ids, platforms_used, capacity snapshot

### R4 — Route planning (supplier + planner mode)

Given an aircraft and its assigned tasks, the system SHALL obtain an ordered lateral path under a **RoutePlannerMode** and materialize a route that:
- Starts and ends at the home airbase
- Consists **only** of published waypoints (airbases, navaids, fixed mission waypoints)
- Does **not** invent runtime lat/lon points
- Honors mode-specific policy (see R17)
- Validates ISR ≤ 80 nmi / strike ≤ 20 nmi proximity when the published set allows
- Reports unsatisfied task ids
- Uses great-circle legs; fuel via Route Propagation Service (R5)

A zero-dependency **fallback** path SHALL remain available.

### R5 — Route Propagation Service (Fuel & Feasibility)

The system SHALL expose a FastAPI service that, for a given route:
- Tracks remaining fuel after each leg using a constant burn-rate model
- Applies a fixed reserve requirement
- Reports overall feasibility (GO if remaining fuel ≥ reserve at end of route, otherwise NO-GO)
- Supports loiter fuel debit when mode is area_loiter
- Supports stepping / advancing the route (fuel burn simulation)

### R6 — Dynamic Task Insertion

During a live route, the system SHALL accept a newly identified task, **fully re-generate / re-assess** the route for that aircraft (including the new task), re-propagate fuel state, and return an updated feasibility result.

### R7 — Feedback & Observability

The system SHALL provide explicit feedback for:
- Tasks that could not be allocated
- Tasks infeasible by time window
- Assigned tasks unsatisfied by published proximity
- Routes unexecutable due to fuel reserve
- Mode-specific notes (exposure_score, separation_notes, loiter_minutes)

### R8 — UCI-Oriented Contracts

Public interfaces SHALL be designed so they can later be published/consumed as UCI-aligned messages without changing the core domain model. See `docs/API-PROTOTYPE-SERVICES.md`.

### R9 — Mission Options

The system SHALL allow creation of named Mission Options that capture emphasis/archetype, router inputs, route_mode, allocation result, per-aircraft plans, and unallocated tasks.

### R10 — Top-three slots

The system SHALL support pinning Mission Options into slots **A**, **B**, and **C** for side-by-side comparison.

### R11 — Saved router inputs

Each Mission Option SHALL persist inputs (supplier/mode, vias, avoids, axis profile, sync metadata, allocation bias) for patch-and-re-run. Re-runs SHOULD link parent_option_id.

### R12 — Comparison

Comparison metrics SHALL include GO/NO-GO counts, unallocated count, total distance, platforms_used, emphasis/archetype, optional mean_exposure and tot_slack, without auto-selecting a best option.

### R13 — Force engagement archetypes & contingency pool

Per `docs/FORCE-APPROACHES.md`: archetype on each option; pool may exceed three; pinned trio for continuous comparison; rules-only GapReport stub.

### R14 — Theater navigation sources

Fixture and optional X-Plane extract (`NAV_SOURCE=fixture|xplane`); published-waypoints-only.

### R15 — Map layers (cost grid, threats, exposure, scrub)

Toggleable cost-grid overlay; threat radii; legs threats “see”; scrubbable aircraft along route.

### R16 — Aligned multi-platform timeline & platform list order

Metrics + aligned timeline; platform list group-by-type and manual reorder.

### R17 — RoutePlannerMode catalog

The system SHALL support at least these modes on the published-fix graph (`docs/ROUTE-PLANNER-MODES.md`):

| Mode | Prototype behavior |
|------|--------------------|
| `efficient` | Short cover path / pure distance |
| `threat_avoid` | Threat-penalized Dijkstra; exposure_score |
| `spread_field` | Separation heuristic or advisory notes vs peer routes |
| `area_loiter` | Cyclic published fixes for ISR dwell; loiter_minutes |
| `unexpected_axis` | Forced via chain |
| `synchronized` | Shared hold vias + timing metadata on option |

Modes SHALL NOT introduce non-published waypoint kinds.

### R18 — Targets

The system SHALL allow grouping tasks under a **Target** (id, label, task_ids) for allocation and display.

### R19 — Iteration service

The system SHALL provide an **iterate** operation that: allocates under COA bias → plans each assigned platform under a RoutePlannerMode → propagates fuel → stores/returns a Mission Option and summary (platforms_used, go, nogo, unallocated, distance, optional exposure/TOT slack).

### R20 — Prototype API surface

The HTTP API SHALL expose planner-modes listing, allocate, route/plan, iterate, tasks/targets, and platforms/capacity as specified in `docs/API-PROTOTYPE-SERVICES.md` (additive to existing plan/options endpoints).

## Non-goals (prototype)

- Full ATO XML/JSON parsing
- RRT*/ACO/MILP optimal mission route planning (document as beads)
- True multi-agent pathfinding (MAPF) deconfliction
- Automated selection of a single “best” Mission Option
- Tanker / AAR geometry beyond stub vias
- Live threat-driven replanning
- Weather/NOTAMs as first-class products (may appear as extra avoid zones later)

Literature algorithms (Dijkstra/CSP, covering TSP, ACO, PSO, RRT*) inform mode design; the prototype deliberately implements graph + greedy variants only.

### R21 — Fuzzy-reconciler fixed threats

The planner SHALL ingest fuzzy-reconciler region JSON (`id`, `name`, `lat`, `lon`, `category`, `attributes`) and treat SAM / radar / BM / coastal / C2 / ELINT sites as **fixed** threats. Airport categories SHALL be ignored. Each ingested site SHALL become a `Threat`, an ISR or STRIKE `Task`, and a published **mission** waypoint (not a runtime `PROX-*` point).

#### Scenario: Gulf region sample yields only IADS-class threats

- **GIVEN** the bundled gulf threat fixture
- **WHEN** the planner loads threats
- **THEN** every threat has a fixed-threat category
- **AND** no airport records are planned against

### R22 — UCI 2.5 MissionPlan export

After a plan cycle the system SHALL export `MissionPlan`, `RoutePlan`, `TaskPlan`, and `RouteActivityPlan` XML using UCI 2.5 element names (`GET /api/uci/export`). `CorrelationID` SHALL equal `MissionPlanID`. JSON `uci.route` export for o-my-sim SHALL remain available.

### R23 — Plan-vs-actual and in-mission feedback

The system SHALL measure cross-track error vs the planned route and return `MissionPlanExecutionStatus` plus an Attention item (`PLAN_DEVIATION`) that includes kind, title, tone, and icon. Dynamic task insertion SHALL return a `TaskCommand` acknowledgement (`RETASK`) so the operator sees accepted/rejected without a silent side channel.
