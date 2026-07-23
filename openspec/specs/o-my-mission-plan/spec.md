# o-my-mission-plan

## Purpose

Enable iterative “guess-and-see” mission planning cycles for the o-my OMS ecosystem.

The system:
- Accepts (or simulates) a set of unassigned ISR/collection and strike tasks (proxy for ATO ingestion).
- Allocates groups of tasks in a geographic region to suitable aircraft resources (ISR, fighter, or bomber) that have an assigned takeoff/landing airbase.
- Generates an initial route for each assigned aircraft that starts and ends at its home airbase and is a sequence of **published waypoints** (airbases, commercial navaids, optional fixed mission waypoints). Proximity (80 nmi ISR / 20 nmi strike) is validated against those published fixes; the system does not invent lat/lon points at planning time.
- Provides a Route Propagation Service that tracks fuel remaining and burn rate for each leg and answers whether the platform can safely complete the remaining route (including fixed reserves).
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

### R4 — Initial Route Generator

Given an aircraft and its assigned tasks, the system SHALL generate an ordered route that:
- Starts at the aircraft’s home airbase
- Consists **only** of published waypoints from the navigation database (airbases, commercial navaids, and optional fixed mission waypoints)
- Does **not** invent runtime lat/lon points (no `PROX-*` / `task_proximity` waypoints)
- Is validated so that at least one published waypoint on the route lies **within 80 nmi** of each ISR/collection task and **within 20 nmi** of each strike task when the published set allows
- Explicitly reports assigned tasks that cannot be satisfied by any published fix
- Ends at the aircraft’s home airbase
- Uses great-circle legs of any length between consecutive published waypoints

See `docs/ROUTE-GENERATION.md`.

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

Public interfaces (task, aircraft status, route, allocation results, feasibility) SHALL be designed so they can later be published/consumed as UCI-aligned messages without changing the core domain model.

## Non-goals (prototype)

- Full ATO XML/JSON parsing
- Sophisticated multi-criteria optimization or threat avoidance
- Tanker / aerial refueling modeling
- Multi-ship deconfliction or formation routing
- Detailed loadout / weapons employment calculation
- Weather, airspace restrictions, or NOTAMs
- Priority-based allocation algorithms (report unallocated tasks only)
