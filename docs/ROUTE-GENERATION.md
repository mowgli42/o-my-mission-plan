# Route Generation Design — Published Waypoints Only

## Problem

The first version of the route generator mixed two concepts:

1. **Published waypoints** from a navigation database (commercial navaids, airbases).
2. **Invented intermediate points** (`PROX-*` waypoints) computed on the fly so the aircraft lands just inside the 80 nmi (ISR) or 20 nmi (strike) proximity radius of a task.

Real IFR / mission route construction does **not** invent lat/lon points at planning time. Pilots and dispatch systems select and sequence **published** fixes from a navigation database; the FMS then flies great-circle (or airway) legs between those fixes.

## Correct mental model (civil IFR reference)

- A route is a sequence of published waypoints (VORs, VORTACs, intersections, RNAV fixes, SIDs/STARs, airbases).
- The planner chooses which published fixes to use; the system does not synthesize new coordinates to satisfy a radius.
- Legs between successive waypoints are great-circle (later corrected for wind/performance).
- Mission constraints (e.g. “get within 80 nmi of this collection area”) are **success criteria** evaluated against the chosen published fixes, not generators of new waypoints.

## Required change for the prototype

### Published waypoint database

The only legal waypoints are:

- Home airbases (already in `demo_world.AIRBASES`)
- Commercial navaids (already in `demo_world.NAVAIDS`)
- Optionally a small number of additional **fixed, pre-defined** mission waypoints that are treated as part of the navigation database (not computed at runtime). These may be added near strike locations if the existing navaid density cannot satisfy the 20 nmi rule.

### Generator algorithm (revised)

Given an aircraft and its assigned tasks:

1. Start at the aircraft’s home airbase (published).
2. Select an ordered sequence of **published** waypoints only.
3. A task is satisfied if **at least one waypoint already present in the route** lies within:
   - 80 nmi of an ISR / collection task, or
   - 20 nmi of a strike task.
4. Legs = great-circle distance between consecutive published waypoints (any length is acceptable).
5. End at the home airbase.
6. **Do not** emit synthetic `PROX-*` or any other runtime-invented lat/lon points.

### Validation

After the sequence is built, `route_satisfies_proximity()` (or equivalent) must confirm every assigned task has at least one published waypoint within its required radius. If a task cannot be satisfied with the current published set, the generator should either:

- leave the task unsatisfied and surface that fact, or
- require that additional fixed mission waypoints be added to the demo navigation database.

### Dynamic insertion

When a new task is injected, the **entire** route for that aircraft is re-generated under the same published-waypoint-only rules and fuel is fully re-propagated. No mid-route splicing of invented points.

## Non-goals

- Full airway / SID / STAR procedure encoding
- Wind, performance, or VNAV profile computation
- Turn anticipation / RF legs / Dubins paths
- Inventing intermediate coordinates to force proximity

## Implementation notes for the fix

- `src/omy_mission_plan/route_generator.py` currently creates `kind="task_proximity"` waypoints with ids like `PROX-{task.id}`. These must be removed.
- Selection heuristic can remain simple (nearest useful navaid, greedy nearest-task ordering, etc.) as long as only published points are emitted.
- Update unit tests in `tests/test_route_and_fuel.py` that assert the existence or location of `PROX-*` points.
- Update OpenSpec / Gherkin language from “navaids + proximity points” to “sequence of published waypoints that satisfy proximity”.
- Update UI copy / help text if it mentions invented proximity points.

## References

- Civil IFR route construction summary (pilot/dispatcher workflow, published waypoints, great-circle legs, FMS).
- Existing demo navaid / mission set: PSA, HFR, DHA, BAH, KWI, RAS + airbases OEPS, OEDR, OKBK, ORBI + fixed mission waypoints (MW-MUTLA, MW-BASRA, …). See `docs/DEMO-WORLD.md`.
