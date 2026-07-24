# o-my-mission-plan

## Purpose

Enable iterative “guess-and-see” mission planning cycles for the o-my OMS ecosystem, including a **top-three Mission Options** working set (Efficient / Synchronized / Unexpected-axis) as described in `docs/CONOPS.md`.

The system:
- Accepts (or simulates) a set of unassigned ISR/collection and strike tasks (proxy for ATO ingestion).
- Allocates groups of tasks in a geographic region to suitable aircraft resources (ISR, fighter, or bomber) that have an assigned takeoff/landing airbase.
- Obtains lateral paths from a **pluggable route supplier** (fallback published-waypoint generator, optional openRouteFinder / cost-grid adapters — see `docs/SUPPLIER-ROUTE-TOOLS.md` and the civil/mission route guides). Routes remain sequences of **published waypoints** only; proximity (80 nmi ISR / 20 nmi strike) is validated after the supplier returns fixes; the system does not invent lat/lon points at planning time.
- Provides a Route Propagation Service that tracks fuel remaining and burn rate for each leg and answers whether the platform can safely complete the remaining route (including fixed reserves).
- Persists **Mission Options** with saved router inputs so the planner can pin A/B/C, compare, patch inputs, and re-run.
- Supports insertion of a newly identified task during execution by **fully re-assessing / regenerating** the route and re-propagating fuel state.
- Surfaces clear feedback when tasks remain unallocated or when a route is unexecutable due to fuel reserve constraints.

Richer planning services (full ATO parsing, advanced allocation with priorities, loadout determination, optimization, threat avoidance) are out of scope for this capability and will be supplied externally via UCI messages. Priority handling is acknowledged as a future need; the prototype must at least report unallocated tasks.

## Requirements

### R1 — Unassigned Task Pool

The system SHALL maintain a pool of unassigned tasks.

Each task SHALL have at minimum:
- unique identifier
- type: `ISR` | `STRIKE`
- geographic location (lat/lon)
- optional priority (stubbed or simple integer for now)

The system SHALL report which tasks remain unallocated after an allocation cycle.

### R2 — Aircraft Resources

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
- fixed reserve requirement (absolute or percentage)

### R3 — Simple Regional Task Allocation

The system SHALL provide a simple allocator that:
- Groups tasks that fall in the same geographic region
- Assigns a group to a suitable aircraft (matching capability type when possible)
- Leaves residual tasks unassigned if no suitable aircraft remains
- Returns both the allocations **and** the list of unallocated tasks

### R4 — Initial Route Generator (supplier-backed)

Given an aircraft and its assigned tasks, the system SHALL obtain an ordered lateral path from the configured **route supplier** and materialize a route that:
- Starts at the aircraft’s home airbase
- Consists **only** of published waypoints from the navigation database (airbases, commercial navaids, and optional fixed mission waypoints)
- Does **not** invent runtime lat/lon points (no `PROX-*` / `task_proximity` waypoints)
- May include forced published **vias** from Mission Option router inputs (unexpected-axis / corridor)
- Is validated so that at least one published waypoint on the route lies **within 80 nmi** of each ISR/collection task and **within 20 nmi** of each strike task when the published set allows
- Explicitly reports assigned tasks that cannot be satisfied by any published fix
- Ends at the aircraft’s home airbase
- Uses great-circle legs of any length between consecutive published waypoints

A zero-dependency **fallback** supplier SHALL remain available. See `docs/ROUTE-GENERATION.md` and `docs/SUPPLIER-ROUTE-TOOLS.md`.

### R5 — Route Propagation Service (Fuel & Feasibility)

The system SHALL expose a FastAPI service that, for a given route:
- Tracks remaining fuel after each leg using a constant burn-rate model
- Applies a fixed reserve requirement
- Reports overall feasibility (GO if remaining fuel ≥ reserve at end of route, otherwise NO-GO / unexecutable)
- Clearly indicates when a route is unexecutable due to fuel constraints
- Supports stepping / advancing the route (fuel burn simulation)

### R6 — Dynamic Task Insertion

During a live route, the system SHALL accept a newly identified task, **fully re-generate / re-assess** the route for that aircraft (including the new task), re-propagate fuel state, and return an updated feasibility result. Partial splicing of the existing route is not required in the prototype.

### R7 — Feedback & Observability

The system SHALL provide explicit feedback for:
- Tasks that could not be allocated
- Assigned tasks that cannot be satisfied by any published waypoint within the required proximity
- Routes that are unexecutable because they would violate the fuel reserve constraint

### R8 — UCI-Oriented Contracts

Public interfaces (task, aircraft status, route, allocation results, feasibility, Mission Option metadata) SHALL be designed so they can later be published/consumed as UCI-aligned messages without changing the core domain model.

### R9 — Mission Options

The system SHALL allow creation of named Mission Options that capture:
- emphasis: `efficient` | `synchronized` | `unexpected_axis`
- router inputs used to produce the option
- task and aircraft sets for the cycle
- resulting per-aircraft routes, fuel state, and GO / NO-GO status
- unallocated tasks for that cycle

See `docs/CONOPS.md` and Gherkin CONOPS scenarios.

### R10 — Top-three slots

The system SHALL support pinning Mission Options into slots **A**, **B**, and **C** corresponding to Efficient / Synchronized / Unexpected-axis for holistic side-by-side comparison. Slot assignment SHALL be mutable so the planner can replace an option in a slot.

### R11 — Saved router inputs

Each Mission Option SHALL persist the inputs used to produce it (at minimum: supplier id, vias, avoid fix ids, axis profile when applicable, sync group and BDA lag when synchronized) so the planner can duplicate, patch one constraint, and re-run allocate → supplier route → fuel propagation. Re-runs SHOULD link to a parent option id when creating a new option.

### R12 — Comparison

The system SHALL provide comparison metrics across Mission Options including: GO count, NO-GO count, unallocated count, total distance (or equivalent fuel/distance aggregate), emphasis label, **force-approach archetype**, archetype-fit hint, and (for synchronized options) timing-alignment indicators when present. Comparison SHALL be advisory for a human planner; the system SHALL NOT automatically select a single best option in the prototype. The planner MAY mark a preferred option for the next experiment or export.

### R13 — Force engagement archetypes & contingency pool

Each Mission Option SHALL carry a primary **archetype** (`efficient` | `synchronized` | `maneuver` | `surprise` | `shock` | `attrition`) and optional hybrid tags per `docs/FORCE-APPROACHES.md`. The system SHALL store a contingency **pool** that may exceed three options while supporting exactly three **pinned** slots A/B/C for continuous comparison. The system SHALL expose a rules-only **GapReport** stub (coverage, feasibility, archetype fit, SPF, dependencies, contingency hints) without auto-selecting a best option.

### R14 — Theater navigation sources

The system SHALL load published fixes from fixture data and MAY augment navaids from an X-Plane–style `earth_nav.dat` extract filtered to the theater bbox (`NAV_SOURCE=fixture|xplane`). Routes SHALL remain published-waypoints-only. See `docs/NAV-DATA.md`.

### R15 — Map layers (cost grid, threats, exposure, scrub)

The UI/API SHALL support a toggleable hex cost-grid overlay derived from threat severities, draw threat lethal/jam radii, highlight route legs that threats “see,” and place aircraft markers along routes at a scrubbable mission time. Cost-grid display SHALL NOT by itself change route geometry.

### R16 — Aligned multi-platform timeline & platform list order

The Routes view SHALL provide metrics and an aligned multi-platform timeline (shared time axis, one track per platform, TOT/BDA windows when present). The platform list SHALL support grouping by type and session-persisted manual reorder that drives timeline/map stack order without changing allocation.

## Non-goals (prototype)

- Full ATO XML/JSON parsing
- Sophisticated multi-criteria optimization or threat avoidance (beyond supplier stubs / adapters)
- Automated selection of a single “best” Mission Option
- Full temporal multi-ship optimization (timing is stored and compared, not globally optimized)
- Tanker / aerial refueling modeling
- Multi-ship deconfliction or formation routing
- Detailed loadout / weapons employment calculation
- Weather, airspace restrictions, or NOTAMs
- Priority-based allocation algorithms (report unallocated tasks only)
- Live threat-driven replanning

Civil and mission route construction beyond the fallback published-waypoint generator is provided by external suppliers behind the adapter (`docs/CIVIL-ROUTE-DEV-GUIDE.md`, `docs/MISSION-ROUTE-DEV-GUIDE.md`, `docs/INTEGRATION-GUIDE.md`).
