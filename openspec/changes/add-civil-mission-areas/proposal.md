# Proposal: Civil vs mission areas with handoff-connected routes

## Why

Treating the entire PSAB→target theater as one civil waypoint graph under-uses threat cost grids and over-constrains mission autonomy. Planners need a **civil regime** (normal published waypoints) and a **mission regime** (cost grid + threat ranges, freer pathing), joined at **entry/exit handoffs** so civil-generated legs connect cleanly to mission-generated legs.

## What

- `MissionArea` + handoff fixes in the demo world
- Composite planner: civil ingress → mission segment → civil egress
- Mission segment: threat cost grid autonomy; snap/export to published + mission fixes
- Civil segment: efficient graph without full threat field
- OpenSpec R21–R23; Gherkin; API segment metadata
- Update mental model docs (waypoint model still one export kind set; grid is internal)

## Non-goals

- Free continuous trajectory as the only route representation
- Dynamic redraw of areas in the first slice
- Separate UCI message types per regime (one concatenated route is enough for prototype)
