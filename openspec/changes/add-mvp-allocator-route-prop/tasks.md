# Tasks — add-mvp-allocator-route-prop

## Phase 1 — Domain & Demo World
- [ ] Define Pydantic models: Aircraft, Task, Airbase, Navaid, Leg, Route, FuelState, AllocationResult
- [ ] Create Florida demo fixtures
  - 2 ISR + 3 fighters + 2 bombers (home bases, fuel, burn rate, reserve)
  - ≈4–5 ISR + 2–3 strike tasks
  - commercial navaids + airbases
- [ ] Simple distance helper (haversine)

## Phase 2 — Allocator
- [ ] Group tasks by crude geographic region
- [ ] Assign groups to suitable aircraft (type preference + availability)
- [ ] Always return both allocations **and** the list of unallocated tasks

## Phase 3 — Initial Route Generator
- [ ] Build ordered waypoint list (home → navaids / proximity points → home)
- [ ] Ensure aircraft comes within 80 nmi of each ISR task and within 20 nmi of each strike task
- [ ] Legs may be any length; navaids used where helpful
- [ ] Attach tasks to the appropriate points in the route

## Phase 4 — Route Propagation Service
- [ ] FastAPI app with route create / get / propagate endpoints
- [ ] Constant burn-rate model + fixed reserve
- [ ] Per-leg remaining fuel + overall GO / NO-GO
- [ ] Explicit “unexecutable due to fuel” flag

## Phase 5 — Dynamic Insertion
- [ ] Endpoint to inject a new task
- [ ] Full re-generation of the aircraft’s route + full fuel re-propagation
- [ ] Return updated route + feasibility

## Phase 6 — Polish
- [ ] Swagger examples / demo script that shows unallocated tasks + fuel NO-GO cases
- [ ] Unit tests for allocator, generator, fuel math, feedback
- [ ] Update living OpenSpec after validation
