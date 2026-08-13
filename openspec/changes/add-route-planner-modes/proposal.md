# Proposal: Route planner modes + timed COA-aligned allocation

## Why

A single greedy router cannot express threat avoidance, spread-the-field, area loiter, and unexpected-axis behaviors needed across campaign phases. Allocation must also respect time windows and platform capacity so different COAs (efficient vs synchronized vs spread) produce different platform counts and alignments—not only different polylines.

## What

- Catalog of **RoutePlannerMode** values with prototype algorithms on the published-fix graph (see `docs/ROUTE-PLANNER-MODES.md`).
- **Timed, capacity-aware allocation** biased by COA (minimize platforms vs spread vs sync windows).
- **Iteration API** that runs allocate → multi-platform route plan → fuel propagate and stores a Mission Option for comparison.
- Tracking of **tasks, targets, platform capacity** across iterations.
- OpenSpec requirements R17–R20; Gherkin scenarios tagged Validated vs Future.

## Non-goals

- RRT*/ACO optimal mission route planning
- Full MAPF deconfliction
- Automated best-COA selection

## Success criteria

- Same task pool yields different `platforms_used` under efficient vs spread_field allocation bias.
- `threat_avoid` route differs from `efficient` when a HIGH threat sits on the direct path.
- `area_loiter` returns loiter duration metric for an ISR assignment.
- Iterate endpoint returns summary suitable for A/B/C compare.
