# Tasks — add-mvp-allocator-route-prop

## Phase 1 — Domain & Demo World
- [ ] Define Pydantic models: Aircraft, Task, Airbase, Navaid, Leg, Route, FuelState
- [ ] Create Florida demo fixtures (airbases, navaids, 3–4 aircraft, 6–8 tasks)
- [ ] Simple distance helper (haversine or approximate)

## Phase 2 — Allocator
- [ ] Group tasks by crude geographic region
- [ ] Assign groups to suitable aircraft (type preference + availability)
- [ ] Leave residual tasks unassigned

## Phase 3 — Initial Route Generator
- [ ] Build ordered waypoint list (home → navaids/tasks → home)
- [ ] Target ~80 nmi legs for ISR, ~20 nmi for strike
- [ ] Attach tasks to the appropriate legs

## Phase 4 — Route Propagation Service
- [ ] FastAPI app with /api/routes, /api/routes/{id}/propagate, feasibility endpoint
- [ ] Fuel burn model (constant rate per aircraft type + simple reserves)
- [ ] Per-leg remaining fuel + overall GO/NO-GO

## Phase 5 — Dynamic Insertion
- [ ] Endpoint to inject a new task into an existing route
- [ ] Re-generate or splice + re-propagate fuel
- [ ] Return updated route + feasibility

## Phase 6 — Polish
- [ ] Swagger examples / demo script
- [ ] Unit tests for allocator, generator, fuel math
- [ ] Update living OpenSpec after validation
